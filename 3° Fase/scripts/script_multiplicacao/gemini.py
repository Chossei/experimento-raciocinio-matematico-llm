import os
import re
import json
import pandas as pd
from dotenv import load_dotenv
import logging
from datetime import datetime
from google import genai
from google.oauth2 import service_account
from google.cloud import storage

# ==========================================
# CONFIGURAÇÃO DE LOGS E DIRETÓRIOS
# ==========================================
PASTA_GEMINI = os.path.dirname(os.path.abspath(__file__))
PASTA_RAIZ = os.path.dirname(PASTA_GEMINI)
LOGS_DIR = os.path.join(PASTA_GEMINI, 'logs_gemini')
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

data_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = os.path.join(LOGS_DIR, f'batch_inteiros_{data_hora}.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logging.info("=== Iniciando Preparação de Lotes (Batch) para Gemini Vertex AI ===")

# ==========================================
# VARIÁVEIS DE AMBIENTE E AUTENTICAÇÃO
# ==========================================
env_path = os.path.join(PASTA_RAIZ, 'chave.env')
load_dotenv(env_path)

gemini_api_key_str = os.environ.get("GEMINI_API_KEY", "")
if not gemini_api_key_str:
    with open(env_path, 'r', encoding='utf-8') as f:
        content = f.read()
        if "GEMINI_API_KEY =" in content:
            gemini_api_key_str = content.split("GEMINI_API_KEY =")[1].strip()
            if gemini_api_key_str.startswith('"') and gemini_api_key_str.endswith('"'):
                gemini_api_key_str = gemini_api_key_str[1:-1]
            elif gemini_api_key_str.startswith("'") and gemini_api_key_str.endswith("'"):
                gemini_api_key_str = gemini_api_key_str[1:-1]

try:
    creds_dict = json.loads(gemini_api_key_str)
    project_id = creds_dict.get("project_id", "plataformas-aula-ufba")
    credentials = service_account.Credentials.from_service_account_info(creds_dict)

    chave_path = os.path.join(PASTA_GEMINI, 'vertex_chave.json')
    with open(chave_path, 'w', encoding='utf-8') as f:
        json.dump(creds_dict, f)
    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = chave_path

    client = genai.Client(enterprise=True, project=project_id, location="global")
    storage_client = storage.Client(project=project_id, credentials=credentials)

    logging.info(f"SDK inicializado para o projeto {project_id}")
except Exception as e:
    logging.error(f"Erro ao carregar credenciais: {e}")
    raise

# ==========================================
# CONFIGURAÇÕES DO EXPERIMENTO
# ==========================================
NOME_BUCKET = "experimento-matematico-ufba"

# Taxa de câmbio (Agosto de 2026): 1 USD = ~R$ 5,15
taxa_cambio = 5.15

# Preços por milhão de tokens (em dólares)
dados_api = [
    {"modelo": "gemini-3.8-flash", "input_usd": 0.75, "output_usd": 3.75, "rpm": 1000, "rpd": 10000},
    {"modelo": "gemini-3.7-flash", "input_usd": 0.75, "output_usd": 3.75, "rpm":1000 , "rpd":10000 },
    {"modelo": "gemini-3.6-flash", "input_usd": 0.75, "output_usd": 3.75, "rpm":1000 , "rpd":10000 },
    {"modelo": "gemini-3.5-flash", "input_usd": 1.50, "output_usd": 9.00, "rpm":1000 , "rpd":10000 },
    {"modelo": "gemini-3.5-flash-lite", "input_usd": 0.30, "output_usd": 2.50, "rpm":4000, "rpd":150000 },
    {"modelo": "gemini-3.1-flash-lite", "input_usd": 0.25, "output_usd": 1.50, "rpm": 4000, "rpd":150000 },
    {"modelo": "gemini-3.1-pro-preview", "input_usd": 2.00, "output_usd": 12.00, "rpm": 25, "rpd": 250},
    {"modelo": "gemini-3-flash-preview", "input_usd": 0.50, "output_usd": 3.00, "rpm": 1000, "rpd":10000},
    {"modelo": "gemini-2.5-pro", "input_usd": 1.25, "output_usd": 10.00, "rpm": 150, "rpd":1000},
    {"modelo": "gemini-2.5-flash", "input_usd": 0.30, "output_usd": 2.50, "rpm": 1000, "rpd":10000}
]

modelos_lista = [d["modelo"] for d in dados_api]

DADOS_DIR = os.path.join(PASTA_RAIZ, 'dados')
ARQUIVO_OPERACOES = os.path.join(DADOS_DIR, 'operacoes.csv')
ARQUIVO_RESULTADOS = os.path.join(DADOS_DIR, 'resultados_gemini.csv')
ARQUIVO_JOBS = os.path.join(PASTA_GEMINI, 'jobs_ativos.json')

# ==========================================
# FUNÇÕES DE APOIO
# ==========================================
def extrair_numero(texto):
    """Extrai somente dígitos de uma resposta textual e retorna um inteiro."""
    padrao = re.compile(r'\d+')
    numeros = padrao.findall(texto)
    if numeros:
        return int("".join(numeros))
    return None

def calcular_custo(modelo_nome, input_tokens, output_tokens):
    for d in dados_api:
        if d['modelo'] == modelo_nome:
            if not d.get('input_usd') or not d.get('output_usd'):
                return ""
            try:
                in_usd = float(d['input_usd'])
                out_usd = float(d['output_usd'])
                custo_usd = (input_tokens * in_usd / 1_000_000) + (output_tokens * out_usd / 1_000_000)
                custo_brl = custo_usd * taxa_cambio
                return round(custo_brl, 6)
            except ValueError:
                return ""
    return ""

# ==========================================
# FLUXO PRINCIPAL
# ==========================================
def main():
    if not os.path.exists(DADOS_DIR):
        os.makedirs(DADOS_DIR)

    if not os.path.exists(ARQUIVO_OPERACOES):
        logging.error("Arquivo de operações não encontrado. Execute o pipeline primeiro.")
        return

    df_operacoes = pd.read_csv(ARQUIVO_OPERACOES)

    # Determinar quais operações já foram feitas
    concluidos = set()
    if os.path.exists(ARQUIVO_RESULTADOS):
        df_resultados = pd.read_csv(ARQUIVO_RESULTADOS)
        for _, row in df_resultados.iterrows():
            chave = f"{row['Nome_do_modelo']}||{row['Conta']}"
            concluidos.add(chave)

    # Organizar pendências por modelo
    pendencias_por_modelo = {modelo: [] for modelo in modelos_lista}

    for _, row in df_operacoes.iterrows():
        for modelo in modelos_lista:
            chave = f"{modelo}||{row['string']}"
            if chave not in concluidos:
                prompt = (
                    "Sua tarefa é resolver operações matemáticas.\n"
                    "Responda a pergunta a seguir e retorne o resultado "
                    "SOMENTE em formato de número, sem unidades ou caracteres especiais.\n"
                    f"{row['string']}"
                )
                req_json = {
                    "request": {
                        "contents": [
                            {"role": "user", "parts": [{"text": prompt}]}
                        ]
                    }
                }
                pendencias_por_modelo[modelo].append({
                    "chave": chave,
                    "conta": row['string'],
                    "operacao": row['tipo'],
                    "resultado_original": row['resultado'],
                    "req": req_json
                })

    # Carregar jobs existentes
    jobs_criados = {}
    if os.path.exists(ARQUIVO_JOBS):
        with open(ARQUIVO_JOBS, 'r', encoding='utf-8') as f:
            jobs_criados = json.load(f)

    bucket = storage_client.bucket(NOME_BUCKET)

    for modelo, reqs in pendencias_por_modelo.items():
        if not reqs:
            logging.info(f"Modelo {modelo} já completou todas as operações inteiras. Pulando.")
            continue

        logging.info(f"Preparando lote de {len(reqs)} requisições para {modelo}...")

        # Salvar arquivo JSONL localmente
        jsonl_filename = f"pedidos_inteiros_{modelo}.jsonl"
        jsonl_path = os.path.join(PASTA_GEMINI, jsonl_filename)
        with open(jsonl_path, 'w', encoding='utf-8') as f:
            for r in reqs:
                f.write(json.dumps(r["req"]) + '\n')

        # Salvar mapeamento de chaves para reconstruir resultados depois
        mapeamento_filename = f"mapa_inteiros_{modelo}.json"
        mapeamento_path = os.path.join(PASTA_GEMINI, mapeamento_filename)
        mapa = []
        for r in reqs:
            mapa.append({
                "chave": r["chave"],
                "conta": r["conta"],
                "operacao": r["operacao"],
                "resultado_original": r["resultado_original"]
            })
        with open(mapeamento_path, 'w', encoding='utf-8') as f:
            json.dump(mapa, f, ensure_ascii=False, indent=2)

        # Upload para GCS
        gcs_input_path = f"inputs/{jsonl_filename}"
        blob = bucket.blob(gcs_input_path)
        logging.info(f"Fazendo upload para gs://{NOME_BUCKET}/{gcs_input_path}")
        blob.upload_from_filename(jsonl_path)

        input_uri = f"gs://{NOME_BUCKET}/{gcs_input_path}"
        dest_uri = f"gs://{NOME_BUCKET}/outputs_inteiros/{modelo}/"

        try:
            logging.info(f"Submetendo Job Batch para {modelo}...")
            job = client.batches.create(
                model=modelo,
                src=input_uri,
                dest=dest_uri
            )

            job_name = job.name
            jobs_criados[job_name] = {
                "tipo": "inteiros",
                "modelo": modelo,
                "input_uri": input_uri,
                "dest_uri": dest_uri,
                "mapeamento_file": mapeamento_filename,
                "total_requisicoes": len(reqs),
                "data_submissao": data_hora
            }
            logging.info(f"Job criado com sucesso! ID do Job: {job_name}")

        except Exception as e:
            logging.error(f"Erro ao submeter job para {modelo}: {e}")

    # Salvar registro de jobs
    with open(ARQUIVO_JOBS, 'w', encoding='utf-8') as f:
        json.dump(jobs_criados, f, indent=4, ensure_ascii=False)

    logging.info(f"Total de jobs registrados: {len(jobs_criados)}")
    logging.info("Submissão concluída! Use o verificador_batch.py para acompanhar o status dos jobs.")


if __name__ == '__main__':
    main()

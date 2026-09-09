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
log_filename = os.path.join(LOGS_DIR, f'verificador_{data_hora}.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logging.info("=== Verificador de Jobs Batch ===")

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
# CONFIGURAÇÕES
# ==========================================
NOME_BUCKET = "experimento-matematico-ufba"

# Taxa de câmbio (Agosto de 2026): 1 USD = ~R$ 5,15
taxa_cambio = 5.15

dados_api = [
    {"modelo": "gemini-3.8-flash", "input_usd": 0.75, "output_usd": 3.75},
    {"modelo": "gemini-3.7-flash", "input_usd": 0.75, "output_usd": 3.75},
    {"modelo": "gemini-3.6-flash", "input_usd": 0.75, "output_usd": 3.75},
    {"modelo": "gemini-3.5-flash", "input_usd": 1.50, "output_usd": 9.00},
    {"modelo": "gemini-3.5-flash-lite", "input_usd": 0.30, "output_usd": 2.50},
    {"modelo": "gemini-3.1-flash-lite", "input_usd": 0.25, "output_usd": 1.50},
    {"modelo": "gemini-3.1-pro-preview", "input_usd": 2.00, "output_usd": 12.00},
    {"modelo": "gemini-3-flash-preview", "input_usd": 0.50, "output_usd": 3.00},
    {"modelo": "gemini-2.5-pro", "input_usd": 1.25, "output_usd": 10.00},
    {"modelo": "gemini-2.5-flash", "input_usd": 0.30, "output_usd": 2.50}
]

DADOS_DIR = os.path.join(PASTA_RAIZ, 'dados')
ARQUIVO_RESULTADOS_INT = os.path.join(DADOS_DIR, 'resultados_gemini.csv')
ARQUIVO_RESULTADOS_DEC = os.path.join(DADOS_DIR, 'resultados_gemini_decimal.csv')
ARQUIVO_JOBS = os.path.join(PASTA_GEMINI, 'jobs_ativos.json')

# ==========================================
# FUNÇÕES DE APOIO
# ==========================================
def extrair_numero_inteiro(texto):
    """Extrai somente dígitos de uma resposta textual e retorna um inteiro."""
    padrao = re.compile(r'\d+')
    numeros = padrao.findall(texto)
    if numeros:
        return int("".join(numeros))
    return None

def extrair_numero_decimal(texto):
    """Extrai um número decimal da resposta do modelo como string."""
    texto_limpo = texto.strip()
    padrao = re.compile(r'-?\d+\.?\d*')
    match = padrao.search(texto_limpo)
    if match:
        return match.group()
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

def baixar_resultados_gcs(dest_uri):
    """Baixa todos os arquivos JSONL de resultados de um prefix no GCS.
    
    Retorna uma lista de dicts, onde cada dict é uma linha de resposta do batch.
    """
    # dest_uri formato: gs://bucket/outputs_inteiros/modelo/
    prefix = dest_uri.replace(f"gs://{NOME_BUCKET}/", "")
    bucket = storage_client.bucket(NOME_BUCKET)
    blobs = list(bucket.list_blobs(prefix=prefix))
    
    resultados = []
    for blob in blobs:
        if blob.name.endswith('.jsonl'):
            conteudo = blob.download_as_text()
            for linha in conteudo.strip().split('\n'):
                if linha.strip():
                    try:
                        resultados.append(json.loads(linha))
                    except json.JSONDecodeError:
                        logging.warning(f"Linha inválida no JSONL do GCS: {linha[:100]}")
    
    return resultados

def processar_resultados_inteiros(job_info, respostas_gcs):
    """Processa resultados de batch de inteiros e retorna lista de dicts para o CSV."""
    modelo = job_info["modelo"]
    mapeamento_path = os.path.join(PASTA_GEMINI, job_info["mapeamento_file"])
    
    with open(mapeamento_path, 'r', encoding='utf-8') as f:
        mapa = json.load(f)
    
    resultados = []
    for i, resposta in enumerate(respostas_gcs):
        if i >= len(mapa):
            logging.warning(f"Mais respostas do que requisições para {modelo}. Ignorando excedentes.")
            break
            
        info = mapa[i]
        
        # Extrair texto da resposta do batch
        texto_resposta = ""
        try:
            candidates = resposta.get("response", {}).get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    texto_resposta = parts[0].get("text", "")
        except (KeyError, IndexError, TypeError):
            logging.warning(f"Resposta malformada na posição {i} para {modelo}")
            continue
        
        if not texto_resposta:
            continue
            
        valor_extraido = extrair_numero_inteiro(texto_resposta)
        acerto_formato = not bool(re.search(r'[a-zA-Z]', texto_resposta))
        acerto_operacao = (valor_extraido == info["resultado_original"])
        
        # Extrair tokens do usage metadata
        input_tokens = 0
        output_tokens = 0
        try:
            usage = resposta.get("response", {}).get("usageMetadata", {})
            input_tokens = usage.get("promptTokenCount", 0)
            output_tokens = usage.get("candidatesTokenCount", 0)
        except (KeyError, TypeError):
            pass
            
        custo_total = calcular_custo(modelo, input_tokens, output_tokens)
        
        resultados.append({
            'Nome_do_modelo': modelo,
            'Operacao': info["operacao"],
            'Resultado_do_modelo': valor_extraido,
            'Resposta_bruta': texto_resposta,
            'Resultado_original': info["resultado_original"],
            'Acerto_da_operacao': acerto_operacao,
            'Acerto_do_formato_de_resposta': acerto_formato,
            'Conta': info["conta"],
            'custo_total': custo_total
        })
    
    return resultados

def processar_resultados_decimais(job_info, respostas_gcs):
    """Processa resultados de batch de decimais e retorna lista de dicts para o CSV."""
    modelo = job_info["modelo"]
    mapeamento_path = os.path.join(PASTA_GEMINI, job_info["mapeamento_file"])
    
    with open(mapeamento_path, 'r', encoding='utf-8') as f:
        mapa = json.load(f)
    
    resultados = []
    for i, resposta in enumerate(respostas_gcs):
        if i >= len(mapa):
            logging.warning(f"Mais respostas do que requisições para {modelo}. Ignorando excedentes.")
            break
            
        info = mapa[i]
        
        # Extrair texto da resposta do batch
        texto_resposta = ""
        try:
            candidates = resposta.get("response", {}).get("candidates", [])
            if candidates:
                parts = candidates[0].get("content", {}).get("parts", [])
                if parts:
                    texto_resposta = parts[0].get("text", "")
        except (KeyError, IndexError, TypeError):
            logging.warning(f"Resposta malformada na posição {i} para {modelo}")
            continue
        
        if not texto_resposta:
            continue
            
        # Comparação como string para precisão exata com Decimal
        valor_extraido = extrair_numero_decimal(texto_resposta)
        acerto_formato = not bool(re.search(r'[a-zA-Z]', texto_resposta))
        
        # Comparação textual (string vs string) para evitar erros de ponto flutuante
        resultado_esperado = str(info["resultado_original_decimal"])
        acerto_operacao = (valor_extraido == resultado_esperado)
        
        # Extrair tokens do usage metadata
        input_tokens = 0
        output_tokens = 0
        try:
            usage = resposta.get("response", {}).get("usageMetadata", {})
            input_tokens = usage.get("promptTokenCount", 0)
            output_tokens = usage.get("candidatesTokenCount", 0)
        except (KeyError, TypeError):
            pass
            
        custo_total = calcular_custo(modelo, input_tokens, output_tokens)
        
        resultados.append({
            'Nome_do_modelo': modelo,
            'Operacao': info["operacao"],
            'Resultado_do_modelo': valor_extraido,
            'Resposta_bruta': texto_resposta,
            'Resultado_original_decimal': resultado_esperado,
            'Acerto_da_operacao': acerto_operacao,
            'Acerto_do_formato_de_resposta': acerto_formato,
            'Conta_decimal': info["conta_decimal"],
            'custo_total': custo_total
        })
    
    return resultados

# ==========================================
# FLUXO PRINCIPAL
# ==========================================
def main():
    if not os.path.exists(ARQUIVO_JOBS):
        logging.info("Nenhum arquivo de jobs encontrado. Nada para verificar.")
        return

    with open(ARQUIVO_JOBS, 'r', encoding='utf-8') as f:
        jobs = json.load(f)

    if not jobs:
        logging.info("Nenhum job registrado.")
        return

    jobs_concluidos = []
    
    for job_name, job_info in jobs.items():
        logging.info(f"Verificando job: {job_name} (modelo: {job_info['modelo']}, tipo: {job_info['tipo']})")
        
        try:
            job = client.batches.get(name=job_name)
            estado = job.state.name if hasattr(job.state, 'name') else str(job.state)
            
            logging.info(f"  Estado: {estado}")
            
            if estado in ("JOB_STATE_SUCCEEDED", "SUCCEEDED"):
                logging.info(f"  Job CONCLUÍDO! Baixando resultados do GCS...")
                
                respostas = baixar_resultados_gcs(job_info["dest_uri"])
                logging.info(f"  Total de respostas obtidas: {len(respostas)}")
                
                if job_info["tipo"] == "inteiros":
                    resultados = processar_resultados_inteiros(job_info, respostas)
                    arquivo_csv = ARQUIVO_RESULTADOS_INT
                elif job_info["tipo"] == "decimais":
                    resultados = processar_resultados_decimais(job_info, respostas)
                    arquivo_csv = ARQUIVO_RESULTADOS_DEC
                else:
                    logging.warning(f"  Tipo de job desconhecido: {job_info['tipo']}")
                    continue
                
                if resultados:
                    novo_df = pd.DataFrame(resultados)
                    if os.path.exists(arquivo_csv):
                        df_existente = pd.read_csv(arquivo_csv)
                        df_existente = pd.concat([df_existente, novo_df], ignore_index=True)
                        df_existente.to_csv(arquivo_csv, index=False)
                    else:
                        novo_df.to_csv(arquivo_csv, index=False)
                    
                    # Contabilizar acertos
                    acertos = sum(1 for r in resultados if r['Acerto_da_operacao'])
                    total = len(resultados)
                    taxa = (acertos / total * 100) if total > 0 else 0
                    
                    logging.info(f"  {acertos}/{total} acertos ({taxa:.1f}%) salvos em {os.path.basename(arquivo_csv)}")
                
                jobs_concluidos.append(job_name)
                
            elif estado in ("JOB_STATE_FAILED", "FAILED"):
                logging.error(f"  Job FALHOU!")
                if hasattr(job, 'error') and job.error:
                    logging.error(f"  Detalhes do erro: {job.error}")
                jobs_concluidos.append(job_name)
                
            elif estado in ("JOB_STATE_CANCELLED", "CANCELLED"):
                logging.warning(f"  Job foi CANCELADO.")
                jobs_concluidos.append(job_name)
                
            else:
                logging.info(f"  Job ainda em andamento ({estado}). Aguardando...")
                
        except Exception as e:
            logging.error(f"  Erro ao verificar job {job_name}: {e}")
    
    # Remover jobs concluídos do registro
    if jobs_concluidos:
        for job_name in jobs_concluidos:
            del jobs[job_name]
        
        with open(ARQUIVO_JOBS, 'w', encoding='utf-8') as f:
            json.dump(jobs, f, indent=4, ensure_ascii=False)
        
        logging.info(f"\n{len(jobs_concluidos)} job(s) processado(s) e removido(s) do registro.")
        logging.info(f"{len(jobs)} job(s) restante(s) ainda em andamento.")
    else:
        logging.info("\nNenhum job foi concluído ainda. Execute novamente mais tarde.")


if __name__ == '__main__':
    main()

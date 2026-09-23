import os
import re
import json
import time
import asyncio
import pandas as pd
from dotenv import load_dotenv
import logging
from datetime import datetime
from google import genai
from google.oauth2 import service_account

# ==========================================
# CONFIGURAÇÃO DE LOGS E DIRETÓRIOS
# ==========================================
PASTA_GEMINI = os.path.dirname(os.path.abspath(__file__))
PASTA_RAIZ = os.path.dirname(PASTA_GEMINI)
LOGS_DIR = os.path.join(PASTA_GEMINI, 'logs_gemini')
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

data_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = os.path.join(LOGS_DIR, f'flex_inteiros_{data_hora}.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logging.info("=== Iniciando Inferência Flexível (Flex) para Gemini - Inteiros ===")

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

    logging.info(f"SDK inicializado para o projeto {project_id}")
except Exception as e:
    logging.error(f"Erro ao carregar credenciais: {e}")
    raise

# ==========================================
# CONFIGURAÇÕES DO EXPERIMENTO
# ==========================================

# Taxa de câmbio (Agosto de 2026): 1 USD = ~R$ 5,15
taxa_cambio = 5.15

# Preços por milhão de tokens (em dólares) — Flex tem 50% de desconto
dados_api = [
    {"modelo": "gemini-3.8-flash", "input_usd": 0.375, "output_usd": 1.875, "rpm": 1000, "rpd": 10000},
    {"modelo": "gemini-3.7-flash", "input_usd": 0.375, "output_usd": 1.875, "rpm":1000 , "rpd":10000 },
    {"modelo": "gemini-3.6-flash", "input_usd": 0.375, "output_usd": 1.875, "rpm":1000 , "rpd":10000 },
    {"modelo": "gemini-3.5-flash", "input_usd": 0.75, "output_usd": 4.50, "rpm":1000 , "rpd":10000 },
    {"modelo": "gemini-3.5-flash-lite", "input_usd": 0.15, "output_usd": 1.25, "rpm":4000, "rpd":150000 },
    {"modelo": "gemini-3.1-flash-lite", "input_usd": 0.125, "output_usd": 0.75, "rpm": 4000, "rpd":150000 },
    {"modelo": "gemini-3.1-pro-preview", "input_usd": 1.00, "output_usd": 6.00, "rpm": 25, "rpd": 250},
    {"modelo": "gemini-3-flash-preview", "input_usd": 0.25, "output_usd": 1.50, "rpm": 1000, "rpd":10000},
    # {"modelo": "gemini-2.5-pro", "input_usd": 0.625, "output_usd": 5.00, "rpm": 150, "rpd":1000}, n suportado flex
    {"modelo": "gemini-2.5-flash", "input_usd": 0.15, "output_usd": 1.25, "rpm": 1000, "rpd":10000}
]

modelos_lista = [d["modelo"] for d in dados_api]

DADOS_DIR = os.path.join(PASTA_RAIZ, 'dados')
ARQUIVO_OPERACOES = os.path.join(DADOS_DIR, 'operacoes.csv')
ARQUIVO_RESULTADOS = os.path.join(DADOS_DIR, 'resultados_gemini.csv')

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

def obter_rpm(modelo_nome):
    """Retorna o RPM (requests per minute) do modelo."""
    for d in dados_api:
        if d['modelo'] == modelo_nome:
            return d.get('rpm', 60)
    return 60

def salvar_resultados(resultados, arquivo_csv):
    """Salva resultados no CSV de forma incremental sem reescrever o arquivo.

    Usa mode='a' para apenas acrescentar as novas linhas, evitando que o
    Pandas releia e converta colunas de string para float64 na sobrescrita.
    """
    if not resultados:
        return
    novo_df = pd.DataFrame(resultados)
    arquivo_existe = os.path.exists(arquivo_csv)
    novo_df.to_csv(arquivo_csv, mode='a', header=not arquivo_existe, index=False)

# ==========================================
# INFERÊNCIA FLEX ASSÍNCRONA
# ==========================================
async def processar_requisicao(semaforo, client, modelo, req_info):
    """Processa uma única requisição com o rate limiter (semáforo)."""
    async with semaforo:
        prompt = (
            "Sua tarefa é resolver operações matemáticas.\n"
            "Responda a pergunta a seguir e retorne o resultado "
            "SOMENTE em formato de número, sem unidades ou caracteres especiais.\n"
            f"{req_info['conta']}"
        )

        tentativas = 0
        max_tentativas = 5
        espera_base = 10  # segundos

        while tentativas < max_tentativas:
            try:
                response = await client.aio.models.generate_content(
                    model=modelo,
                    contents=prompt,
                    config={
                        "http_options": {
                            "headers": {
                                "X-Vertex-AI-LLM-Request-Type": "shared",
                                "X-Vertex-AI-LLM-Shared-Request-Type": "flex"
                            }
                        }
                    }
                )

                texto_resposta = response.text or ""
                valor_extraido = extrair_numero(texto_resposta)
                acerto_formato = not bool(re.search(r'[a-zA-Z]', texto_resposta))
                acerto_operacao = (valor_extraido == req_info["resultado_original"])

                # Extrair tokens do usage metadata
                input_tokens = 0
                output_tokens = 0
                if response.usage_metadata:
                    input_tokens = response.usage_metadata.prompt_token_count or 0
                    output_tokens = response.usage_metadata.candidates_token_count or 0

                custo_total = calcular_custo(modelo, input_tokens, output_tokens)

                return {
                    'Nome_do_modelo': modelo,
                    'Operacao': req_info["operacao"],
                    'Resultado_do_modelo': valor_extraido,
                    'Resposta_bruta': texto_resposta,
                    'Resultado_original': req_info["resultado_original"],
                    'Acerto_da_operacao': acerto_operacao,
                    'Acerto_do_formato_de_resposta': acerto_formato,
                    'Conta': req_info["conta"],
                    'custo_total': custo_total
                }

            except Exception as e:
                tentativas += 1
                erro_str = str(e).lower()
                if "429" in erro_str or "resource_exhausted" in erro_str or "rate" in erro_str:
                    espera = espera_base * (2 ** (tentativas - 1))
                    logging.warning(
                        f"Rate limit atingido para {modelo} ({req_info['conta']}). "
                        f"Tentativa {tentativas}/{max_tentativas}. Aguardando {espera}s..."
                    )
                    await asyncio.sleep(espera)
                else:
                    logging.error(
                        f"Erro ao processar {req_info['conta']} com {modelo}: {e} "
                        f"(tentativa {tentativas}/{max_tentativas})"
                    )
                    if tentativas < max_tentativas:
                        await asyncio.sleep(espera_base)

        logging.error(f"Falha definitiva para {req_info['conta']} com {modelo} após {max_tentativas} tentativas.")
        return None


async def processar_modelo(client, modelo, requisicoes):
    """Processa todas as requisições de um modelo respeitando o RPM."""
    rpm = obter_rpm(modelo)
    # Usar 90% do RPM como margem de segurança
    concorrencia = max(1, int(rpm * 0.9))
    semaforo = asyncio.Semaphore(concorrencia)

    logging.info(f"Processando {len(requisicoes)} requisições para {modelo} (RPM: {rpm}, concorrência: {concorrencia})...")

    # Dividir em lotes por minuto para respeitar o RPM
    resultados = []
    lote_tamanho = rpm
    total_lotes = (len(requisicoes) + lote_tamanho - 1) // lote_tamanho

    for i in range(0, len(requisicoes), lote_tamanho):
        lote = requisicoes[i:i + lote_tamanho]
        num_lote = (i // lote_tamanho) + 1
        logging.info(f"  [{modelo}] Lote {num_lote}/{total_lotes} ({len(lote)} requisições)...")

        inicio_lote = time.monotonic()

        tarefas = [
            processar_requisicao(semaforo, client, modelo, req)
            for req in lote
        ]
        resultados_lote = await asyncio.gather(*tarefas)

        # Filtrar resultados válidos
        validos = [r for r in resultados_lote if r is not None]
        resultados.extend(validos)

        # Salvar resultados parciais após cada lote
        if validos:
            salvar_resultados(validos, ARQUIVO_RESULTADOS)
            logging.info(f"  [{modelo}] Lote {num_lote}: {len(validos)} resultados salvos.")

        # Sleep dinâmico: desconta o tempo já gasto no lote
        if i + lote_tamanho < len(requisicoes):
            decorrido = time.monotonic() - inicio_lote
            tempo_restante = 60.0 - decorrido
            if tempo_restante > 0:
                logging.info(f"  [{modelo}] Lote processado em {decorrido:.1f}s. Aguardando {tempo_restante:.1f}s para respeitar o RPM...")
                await asyncio.sleep(tempo_restante)
            else:
                logging.info(f"  [{modelo}] Lote processado em {decorrido:.1f}s (>= 60s). Avançando imediatamente.")

    return resultados


async def main_async():
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
                pendencias_por_modelo[modelo].append({
                    "chave": chave,
                    "conta": row['string'],
                    "operacao": row['tipo'],
                    "resultado_original": row['resultado']
                })

    total_pendentes = sum(len(v) for v in pendencias_por_modelo.values())
    if total_pendentes == 0:
        logging.info("Todas as operações inteiras já foram processadas. Nada a fazer.")
        return

    logging.info(f"Total de requisições pendentes: {total_pendentes}")

    # Processar cada modelo sequencialmente (cada modelo respeita seu próprio RPM)
    total_resultados = 0
    for modelo in modelos_lista:
        reqs = pendencias_por_modelo[modelo]
        if not reqs:
            logging.info(f"Modelo {modelo} já completou todas as operações inteiras. Pulando.")
            continue

        resultados = await processar_modelo(client, modelo, reqs)
        acertos = sum(1 for r in resultados if r['Acerto_da_operacao'])
        total = len(resultados)
        taxa = (acertos / total * 100) if total > 0 else 0
        total_resultados += total

        logging.info(f"[{modelo}] Concluído: {acertos}/{total} acertos ({taxa:.1f}%)")

    logging.info(f"\n=== Inferência Flex concluída! Total processado: {total_resultados} ===")


def main():
    asyncio.run(main_async())


if __name__ == '__main__':
    main()

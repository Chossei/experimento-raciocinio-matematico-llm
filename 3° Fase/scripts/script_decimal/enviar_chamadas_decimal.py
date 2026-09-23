"""
Módulo de Envio em Lote (Batch API OpenRouter) - Experimento: Multiplicação Decimal

Este script:
1. Lê as operações decimais em 'operacoes/operacoes_decimal.csv' (ou 'dados/operacoes.csv').
2. Identifica as operações pendentes/faltantes para o modelo especificado (ex: gemini-3.1-pro-preview com 320 pendentes).
3. Constrói o payload padronizado da Batch API do OpenRouter ('/api/beta/batches').
4. Aplica os budgets de raciocínio (thinking effort) mínimos necessários.
5. Submete os lotes via API Batch do OpenRouter.
6. Registra os batch IDs em 'jobs/jobs_decimal/controle_jobs_batch.json'.
7. Gera logs detalhados em 'logs/logs_decimal/'.
"""

import os
import sys
import json
import logging
import argparse
from datetime import datetime
from dotenv import load_dotenv
import requests
import pandas as pd

# =============================================================================
# CONFIGURAÇÃO DE DIRETÓRIOS E LOGS
# =============================================================================
PASTA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
PASTA_SCRIPTS = os.path.dirname(PASTA_SCRIPT)
PASTA_RAIZ = os.path.dirname(PASTA_SCRIPTS)

# Diretórios na 3° Fase
LOGS_DIR = os.path.join(PASTA_RAIZ, "logs", "logs_decimal")
JOBS_DIR = os.path.join(PASTA_RAIZ, "jobs", "jobs_decimal")
OPERACOES_DIR = os.path.join(PASTA_RAIZ, "operacoes")
RESULTADOS_DIR = os.path.join(PASTA_RAIZ, "dados_resultados", "resultados_decimal")

os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(JOBS_DIR, exist_ok=True)

data_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = os.path.join(LOGS_DIR, f"enviar_chamadas_decimal_{data_hora}.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_filename, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logging.info("=== Inicializando Módulo de Envio de Lotes - Multiplicação Decimal ===")

# =============================================================================
# CARREGAMENTO DA CHAVE OPENROUTER
# =============================================================================
def carregar_openrouter_key():
    candidatos = [
        os.path.join(PASTA_RAIZ, "chave.env"),
        os.path.join(PASTA_RAIZ, "..", "chave.env"),
        os.path.join(os.path.dirname(PASTA_RAIZ), "chave.env"),
        "chave.env"
    ]
    for c in candidatos:
        if os.path.exists(c):
            load_dotenv(c)
            chave = os.environ.get("OPEN_ROUTER_API_KEY_2", "")
            if chave and chave.strip():
                return chave.strip().strip('"').strip("'")
            try:
                with open(c, "r", encoding="utf-8", errors="ignore") as f:
                    for linha in f:
                        l = linha.strip()
                        if l.startswith("OPEN_ROUTER_API_KEY_2") and "=" in l:
                            return l.split("=", 1)[1].strip().strip('"').strip("'")
            except Exception:
                pass
    return os.environ.get("OPEN_ROUTER_API_KEY_2", "").strip().strip('"').strip("'")

# =============================================================================
# MATRIZ DE MODELOS E LIMITES DE TAXA
# =============================================================================
dados_api = [
    {"modelo": "gemini-3.8-flash", "input_usd": 0.75, "output_usd": 3.75, "rpm": 1000, "rpd": 10000},
    {"modelo": "gemini-3.7-flash", "input_usd": 0.75, "output_usd": 3.75, "rpm": 250, "rpd": 10000},
    {"modelo": "gemini-3.6-flash", "input_usd": 0.75, "output_usd": 3.75, "rpm": 1000, "rpd": 10000},
    {"modelo": "gemini-3.5-flash", "input_usd": 1.50, "output_usd": 9.00, "rpm": 1000, "rpd": 10000},
    {"modelo": "gemini-3.5-flash-lite", "input_usd": 0.30, "output_usd": 2.50, "rpm": 4000, "rpd": 150000},
    {"modelo": "gemini-3.1-flash-lite", "input_usd": 0.25, "output_usd": 1.50, "rpm": 4000, "rpd": 150000},
    {"modelo": "gemini-3.1-pro-preview", "input_usd": 2.00, "output_usd": 12.00, "rpm": 25, "rpd": 1000},
    {"modelo": "gemini-3-flash-preview", "input_usd": 0.50, "output_usd": 3.00, "rpm": 1000, "rpd": 10000},
    {"modelo": "gemini-2.5-pro", "input_usd": 1.25, "output_usd": 10.00, "rpm": 150, "rpd": 1000},
    {"modelo": "gemini-2.5-flash", "input_usd": 0.30, "output_usd": 2.50, "rpm": 1000, "rpd": 10000}
]

def obter_config_reasoning(modelo_nome):
    """Configura o esforço mínimo de raciocínio (thinking) conforme exigência de cada modelo."""
    if any(x in modelo_nome for x in ["2.5-flash", "3.1-flash-lite", "3-flash-preview"]):
        return {"effort": "none"}
    elif any(x in modelo_nome for x in ["3.6-flash", "3.5-flash", "3.5-flash-lite"]):
        return {"effort": "minimal"}
    else:
        return {"effort": "low"}

ARQUIVO_CONTROLE = os.path.join(JOBS_DIR, "controle_jobs_batch.json")

def obter_arquivo_operacoes():
    candidatos = [
        os.path.join(OPERACOES_DIR, "operacoes_decimal.csv"),
        os.path.join(PASTA_RAIZ, "operacoes", "operacoes_decimal.csv"),
        os.path.join(PASTA_RAIZ, "..", "dados", "operacoes.csv"),
        os.path.join(PASTA_RAIZ, "dados", "operacoes.csv"),
        "dados/operacoes.csv"
    ]
    for c in candidatos:
        if os.path.exists(c):
            return c
    return candidatos[0]

def obter_arquivo_resultados():
    candidatos = [
        os.path.join(RESULTADOS_DIR, "resultados_decimal.csv"),
        os.path.join(PASTA_RAIZ, "..", "dados", "resultados_gemini_decimal_openrouter.csv"),
        os.path.join(PASTA_RAIZ, "dados", "resultados_gemini_decimal_openrouter.csv"),
        "dados/resultados_gemini_decimal_openrouter.csv"
    ]
    for c in candidatos:
        if os.path.exists(c):
            return c
    return candidatos[0]

# =============================================================================
# MONTAGEM DO PAYLOAD BATCH
# =============================================================================
def montar_requests_lote(modelo, df_operacoes):
    """Constrói a lista de requisições formatadas para o lote da API Batch."""
    modelo_openrouter = f"google/{modelo}" if not modelo.startswith("google/") else modelo
    config_reasoning = obter_config_reasoning(modelo)
    requests_payload = []

    for idx, row in df_operacoes.iterrows():
        conta = row.get("Conta_decimal") or row.get("conta") or row.get("string")
        resultado_orig = row.get("Resultado_original_decimal") or row.get("resultado")
        tipo_op = row.get("tipo") or row.get("Operacao") or row.get("quantidade de digitos")

        prompt = (
            "Sua tarefa é resolver operações matemáticas.\n"
            "Responda a pergunta a seguir e retorne o resultado "
            "SOMENTE em formato de número decimal, sem unidades ou caracteres especiais.\n"
            f"{conta}"
        )

        custom_id = f"{modelo}||{idx}||{conta}"

        item = {
            "custom_id": custom_id,
            "body": {
                "model": modelo_openrouter,
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.0,
                "max_tokens": 1000,
                "extra_body": {
                    "reasoning": config_reasoning
                }
            },
            "metadata": {
                "modelo": modelo,
                "conta_decimal": conta,
                "resultado_original_decimal": str(resultado_orig).strip(),
                "operacao": str(tipo_op)
            }
        }
        requests_payload.append(item)

    return requests_payload

# =============================================================================
# SUBMISSÃO PARA A BATCH API
# =============================================================================
def submeter_batch_openrouter(api_key, modelo, requests_payload):
    url = "https://openrouter.ai/api/beta/batches"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://tcc-experimento.ufba.br",
        "X-Title": "Experimento TCC Decimal Batch API"
    }
    modelo_openrouter = f"google/{modelo}" if not modelo.startswith("google/") else modelo
    # 'model' DEVE vir antes de 'requests' no corpo do JSON
    payload = {
        "model": modelo_openrouter,
        "endpoint": "/v1/chat/completions",
        "requests": [
            {
                "custom_id": req["custom_id"],
                "body": req["body"]
            }
            for req in requests_payload
        ]
    }
    resp = requests.post(url, headers=headers, json=payload, timeout=120)
    resp.raise_for_status()
    return resp.json()

# =============================================================================
# FLUXO PRINCIPAL
# =============================================================================
def main():
    parser = argparse.ArgumentParser(description="Envio de Lotes - Experimento: Multiplicação Decimal Batch API")
    parser.add_argument("--dry-run", action="store_true", help="Valida os payloads e rotas sem chamar a API OpenRouter")
    parser.add_argument("--modelo", type=str, default="gemini-3.1-pro-preview", help="Modelo a ser enviado (padrão: gemini-3.1-pro-preview)")
    parser.add_argument("--todas", action="store_true", help="Ignora filtro de pendências e tenta enviar todas as 900 operações")
    parser.add_argument("--limite", type=int, default=None, help="Limite de requisições por lote (para testes)")
    args = parser.parse_args()

    api_key = carregar_openrouter_key()
    if not api_key and not args.dry_run:
        logging.error("ERRO CRÍTICO: Chave OPEN_ROUTER_API_KEY_2 não encontrada em chave.env.")
        sys.exit(1)

    arquivo_ops = obter_arquivo_operacoes()
    if not os.path.exists(arquivo_ops):
        logging.error(f"Arquivo de operações '{arquivo_ops}' não encontrado.")
        sys.exit(1)

    df_operacoes = pd.read_csv(arquivo_ops, dtype=str)
    logging.info(f"Carregadas {len(df_operacoes)} operações de: {arquivo_ops}")

    # Carregar controle existente
    controle = {}
    if os.path.exists(ARQUIVO_CONTROLE):
        try:
            with open(ARQUIVO_CONTROLE, "r", encoding="utf-8") as f:
                controle = json.load(f)
        except Exception as e:
            logging.warning(f"Erro ao ler controle existente: {e}. Criando novo.")

    modelos_alvo = [d["modelo"] for d in dados_api]
    if args.modelo:
        modelos_alvo = [m for m in modelos_alvo if args.modelo.lower() in m.lower()]

    logging.info(f"Modelos selecionados para envio ({len(modelos_alvo)}): {modelos_alvo}")

    # Identificar operações já concluídas se não foi passado --todas
    arquivo_res = obter_arquivo_resultados()
    contas_concluidas_por_modelo = {m: set() for m in modelos_alvo}

    if not args.todas and os.path.exists(arquivo_res):
        logging.info(f"Carregando histórico de resultados existentes de: {arquivo_res}")
        try:
            df_res_existente = pd.read_csv(arquivo_res, dtype=str)
            for m in modelos_alvo:
                df_m = df_res_existente[df_res_existente["Nome_do_modelo"] == m]
                contas_concluidas_por_modelo[m] = set(df_m["Conta_decimal"].dropna().tolist())
                logging.info(f"[{m}] Operações já registradas anteriormente no CSV: {len(contas_concluidas_por_modelo[m])}")
        except Exception as e:
            logging.warning(f"Erro ao carregar resultados existentes: {e}")

    for modelo in modelos_alvo:
        if modelo in controle and controle[modelo].get("status") in ["validating", "in_progress", "completed"]:
            status_atual = controle[modelo].get("status")
            logging.info(f"[{modelo}] Job já existe no controle (Batch ID: {controle[modelo].get('batch_id')}, Status: {status_atual}).")
            if not args.dry_run:
                # Perguntar ou permitir sobrescrever se falhou ou se usuário quiser
                logging.info(f"[{modelo}] Se desejar reenviar, remova a chave correspondente de {ARQUIVO_CONTROLE}.")
                continue

        logging.info(f"\n--- Preparando lote para o modelo: {modelo} ---")

        # Filtrar operações pendentes
        concluidas = contas_concluidas_por_modelo.get(modelo, set())
        if not args.todas and concluidas:
            # Para evitar supressão indevida se houver contas repetidas, filtramos pelo índice de execução se possível
            # No caso do gemini-3.1-pro-preview, as primeiras 580 já foram realizadas
            df_modelo_ops = df_operacoes[~df_operacoes["Conta_decimal"].isin(concluidas)]
            logging.info(f"[{modelo}] Operações pendentes identificadas: {len(df_modelo_ops)} de {len(df_operacoes)}")
        else:
            df_modelo_ops = df_operacoes.copy()
            logging.info(f"[{modelo}] Enviando conjunto completo de {len(df_modelo_ops)} operações")

        if len(df_modelo_ops) == 0:
            logging.info(f"[{modelo}] Nenhuma operação pendente. Modelo 100% completo!")
            continue

        if args.limite:
            df_modelo_ops = df_modelo_ops.head(args.limite)
            logging.info(f"[{modelo}] Limitando envio a {len(df_modelo_ops)} requisições (--limite)")

        requests_payload = montar_requests_lote(modelo, df_modelo_ops)
        logging.info(f"[{modelo}] Total de requisições preparadas: {len(requests_payload)}")

        if args.dry_run:
            logging.info(f"[{modelo}] [DRY-RUN] Exemplo de payload custom_id: {requests_payload[0]['custom_id']}")
            logging.info(f"[{modelo}] [DRY-RUN] Exemplo de prompt:\n{requests_payload[0]['body']['messages'][0]['content']}")
            logging.info(f"[{modelo}] [DRY-RUN] Validação concluída com sucesso.")
            continue

        try:
            logging.info(f"[{modelo}] Submetendo lote para OpenRouter Batch API...")
            resposta_batch = submeter_batch_openrouter(api_key, modelo, requests_payload)
            batch_id = resposta_batch.get("id") or resposta_batch.get("data", {}).get("id")
            status = resposta_batch.get("status") or "in_progress"

            logging.info(f"[{modelo}] LOTE SUBMETIDO COM SUCESSO! Batch ID: {batch_id} | Status: {status}")

            controle[modelo] = {
                "modelo": modelo,
                "batch_id": batch_id,
                "total_requests": len(requests_payload),
                "timestamp_envio": datetime.now().isoformat(),
                "status": status,
                "resposta_criacao": resposta_batch
            }

            with open(ARQUIVO_CONTROLE, "w", encoding="utf-8") as f:
                json.dump(controle, f, indent=2, ensure_ascii=False)

        except requests.exceptions.HTTPError as he:
            logging.error(f"[{modelo}] Falha HTTP ao submeter lote: {he.response.status_code} - {he.response.text}")
        except Exception as e:
            logging.error(f"[{modelo}] Erro inesperado ao submeter lote: {e}")

    logging.info("\n=== Processamento do Envio Concluído ===")
    logging.info(f"Controle salvo em: {ARQUIVO_CONTROLE}")

if __name__ == "__main__":
    main()

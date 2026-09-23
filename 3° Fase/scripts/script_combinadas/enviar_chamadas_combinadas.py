"""Módulo de Envio em Lote (Batch API OpenRouter) - 3° Experimento: Expressões Combinadas a * (b + c)

Este script:
1. Lê o arquivo de operações combinadas em 'operacoes/operacoes_combinadas.csv'.
2. Constrói as 450 requisições por modelo para os 10 modelos Gemini selecionados.
3. Aplica os budgets de raciocínio (thinking effort) mínimos necessários.
4. Submete os lotes via API Batch do OpenRouter ('/api/beta/batches').
5. Registra os batch IDs em 'jobs/jobs_combinadas/controle_jobs_batch.json'.
6. Gera logs detalhados em 'logs/logs_combinadas/'.
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

LOGS_DIR = os.path.join(PASTA_RAIZ, "logs", "logs_combinadas")
JOBS_DIR = os.path.join(PASTA_RAIZ, "jobs", "jobs_combinadas")
OPERACOES_DIR = os.path.join(PASTA_RAIZ, "operacoes")

os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(JOBS_DIR, exist_ok=True)

data_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = os.path.join(LOGS_DIR, f"enviar_chamadas_combinadas_{data_hora}.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_filename, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logging.info("=== Inicializando Módulo de Envio de Lotes - Expressões Combinadas a * (b + c) ===")

# =============================================================================
# CARREGAMENTO DA CHAVE OPENROUTER
# =============================================================================
def carregar_openrouter_key():
    candidatos = [
        os.path.join(PASTA_RAIZ, "chave.env"),
        os.path.join(PASTA_RAIZ, "..", "chave.env"),
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
    """Configura o esforço mínimo de raciocínio (thinking) conforme o plano:
    - Gemini 2.5: thinking_budget nulo / effort: none para flash, low para pro
    - Gemini 3: minimal ou low conforme exigência da Google
    """
    if any(x in modelo_nome for x in ["2.5-flash", "3.1-flash-lite", "3-flash-preview"]):
        return {"effort": "none"}
    elif any(x in modelo_nome for x in ["3.6-flash", "3.5-flash", "3.5-flash-lite"]):
        return {"effort": "minimal"}
    else:
        return {"effort": "low"}

ARQUIVO_CONTROLE = os.path.join(JOBS_DIR, "controle_jobs_batch.json")
ARQUIVO_OPERACOES = os.path.join(OPERACOES_DIR, "operacoes_combinadas.csv")

# =============================================================================
# MONTAGEM DO PAYLOAD BATCH
# =============================================================================
def montar_requests_lote(modelo, df_operacoes):
    modelo_openrouter = f"google/{modelo}" if not modelo.startswith("google/") else modelo
    config_reasoning = obter_config_reasoning(modelo)
    requests_payload = []

    for idx, row in df_operacoes.iterrows():
        conta = row.get("conta") or row.get("string") or row.get("Conta")
        resultado_orig = row.get("resultado da operacao") or row.get("resultado") or row.get("Resultado_original")
        tipo_op = row.get("quantidade de digitos") or row.get("tipo") or row.get("Operacao")

        prompt = (
            "Sua tarefa é resolver uma operação matemática. "
            "Responda a pergunta a seguir e retorne o resultado "
            "somente em formato de número, sem unidades ou caracteres especiais.\n\n"
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
                "conta": conta,
                "resultado_original": str(resultado_orig).strip(),
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
        "X-Title": "Experimento TCC Combinadas Batch API"
    }
    modelo_openrouter = f"google/{modelo}" if not modelo.startswith("google/") else modelo
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
    parser = argparse.ArgumentParser(description="Envio de Lotes - 3° Experimento: Expressões Combinadas")
    parser.add_argument("--dry-run", action="store_true", help="Valida os payloads e rotas sem chamar a API OpenRouter")
    parser.add_argument("--modelo", type=str, default=None, help="Filtrar submissão para um modelo específico")
    args = parser.parse_args()

    api_key = carregar_openrouter_key()
    if not api_key and not args.dry_run:
        logging.error("ERRO CRÍTICO: Chave OPEN_ROUTER_API_KEY_2 não encontrada em chave.env.")
        sys.exit(1)

    if not os.path.exists(ARQUIVO_OPERACOES):
        logging.error(f"Arquivo de operações '{ARQUIVO_OPERACOES}' não encontrado. Execute o gerador primeiro.")
        sys.exit(1)

    df_operacoes = pd.read_csv(ARQUIVO_OPERACOES, dtype=str)
    logging.info(f"Carregadas {len(df_operacoes)} operações de: {ARQUIVO_OPERACOES}")

    # Carregar ou inicializar controle de jobs
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

    for modelo in modelos_alvo:
        # Se o modelo já tem batch registrado e em andamento
        if modelo in controle and controle[modelo].get("status") in ["validating", "in_progress", "completed"]:
            status_atual = controle[modelo].get("status")
            logging.info(f"[{modelo}] Job já existe no controle (Batch ID: {controle[modelo].get('batch_id')}, Status: {status_atual}). Pulando.")
            continue

        logging.info(f"\n--- Preparando lote para o modelo: {modelo} ---")
        requests_payload = montar_requests_lote(modelo, df_operacoes)
        logging.info(f"[{modelo}] Montadas {len(requests_payload)} requisições. Amostra custom_id: {requests_payload[0]['custom_id']}")

        if args.dry_run:
            logging.info(f"[{modelo}] [DRY-RUN] Simulação bem sucedida. Nenhuma requisição enviada.")
            continue

        try:
            logging.info(f"[{modelo}] Enviando {len(requests_payload)} requisições para a Batch API OpenRouter...")
            resp_batch = submeter_batch_openrouter(api_key, modelo, requests_payload)
            batch_id = resp_batch.get("id")
            status_retornado = resp_batch.get("status", "validating")
            logging.info(f"[{modelo}] LOTE SUBMETIDO COM SUCESSO! Batch ID: {batch_id} (Status: {status_retornado})")

            controle[modelo] = {
                "modelo": modelo,
                "batch_id": batch_id,
                "total_requests": len(requests_payload),
                "timestamp_envio": datetime.now().isoformat(),
                "status": status_retornado,
                "resposta_criacao": resp_batch
            }

            with open(ARQUIVO_CONTROLE, "w", encoding="utf-8") as f:
                json.dump(controle, f, indent=2, ensure_ascii=False)

        except requests.exceptions.RequestException as e:
            logging.error(f"[{modelo}] Falha ao submeter lote para API OpenRouter: {e}")
            if hasattr(e, "response") and e.response is not None:
                logging.error(f"[{modelo}] Resposta da API: {e.response.text}")

    logging.info("\n=== Processamento do script de envio finalizado ===")

if __name__ == "__main__":
    main()

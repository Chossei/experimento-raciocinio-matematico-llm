"""Módulo de Envio de Lotes (Batch API) - Experimento de Operações de Soma (Gemini via OpenRouter)

Este script lê a base 'operacoes_soma.csv', monta os payloads para a Batch API
do OpenRouter para cada modelo Gemini especificado no plano, configura o raciocínio
mínimo necessário, e submete os lotes registrando os identificadores dos jobs
no arquivo de controle 'controle_jobs_batch.json'.
"""

import os
import re
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
PASTA_ATUAL = os.path.dirname(os.path.abspath(__file__))
PASTA_OPENROUTER = os.path.dirname(PASTA_ATUAL)
PASTA_GEMINI = os.path.dirname(PASTA_OPENROUTER)
PASTA_RAIZ = os.path.dirname(PASTA_GEMINI)

LOGS_DIR = os.path.join(PASTA_ATUAL, 'logs_soma')
os.makedirs(LOGS_DIR, exist_ok=True)

data_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = os.path.join(LOGS_DIR, f'enviar_chamadas_{data_hora}.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logging.info("=== Inicializando Módulo de Envio de Lotes (Batch API - Soma) ===")

# =============================================================================
# AUTENTICAÇÃO E CARREGAMENTO DE CHAVE
# =============================================================================
def carregar_openrouter_key():
    """Carrega OPEN_ROUTER_API_KEY_2 de múltiplos caminhos candidatos."""
    candidatos = [
        os.path.join(PASTA_RAIZ, 'chave.env'),
        os.path.join(PASTA_GEMINI, 'chave.env'),
        os.path.join(PASTA_ATUAL, 'chave.env'),
        'chave.env',
        '../chave.env',
        '../../chave.env',
        '../../../chave.env'
    ]
    for c in candidatos:
        if os.path.exists(c):
            load_dotenv(c)
            chave = os.environ.get("OPEN_ROUTER_API_KEY_2", "")
            if chave and chave.strip():
                return chave.strip().strip('"').strip("'")
            try:
                with open(c, 'r', encoding='utf-8', errors='ignore') as f:
                    for linha in f:
                        linha_limpa = linha.strip()
                        if linha_limpa.startswith("OPEN_ROUTER_API_KEY_2") and "=" in linha_limpa:
                            partes = linha_limpa.split("=", 1)
                            if len(partes) == 2:
                                val = partes[1].strip().strip('"').strip("'")
                                if val:
                                    return val
            except Exception:
                pass
    return os.environ.get("OPEN_ROUTER_API_KEY_2", "").strip().strip('"').strip("'")

# =============================================================================
# CONFIGURAÇÕES DO EXPERIMENTO: MODELOS, CUSTOS E LIMITES
# =============================================================================
taxa_cambio = 5.15

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

modelos_lista = [d["modelo"] for d in dados_api]

def obter_config_reasoning(modelo_nome):
    """Configura o esforço mínimo de raciocínio (thinking) conforme o plano do TCC:

    - Gemini 2.5: thinking_budget o mais próximo possível de nulo (none para flash, low para pro)
    - Gemini 3: thinking_level como minimal ou low
    """
    if any(x in modelo_nome for x in ['2.5-flash', '3.1-flash-lite', '3-flash-preview']):
        return {'effort': 'none'}
    elif any(x in modelo_nome for x in ['3.6-flash', '3.5-flash', '3.5-flash-lite']):
        return {'effort': 'minimal'}
    else:
        # Modelos onde a API Google/OpenRouter exige obrigatoriamente reasoning
        return {'effort': 'low'}

# =============================================================================
# LOCALIZAÇÃO DO ARQUIVO DE OPERAÇÕES E CONTROLE
# =============================================================================
def encontrar_arquivo_operacoes():
    candidatos = [
        os.path.join(PASTA_ATUAL, 'operacoes_soma.csv'),
        os.path.join(PASTA_RAIZ, 'dados', 'operacoes_soma.csv'),
        os.path.join('dados', 'operacoes_soma.csv'),
        'operacoes_soma.csv'
    ]
    for c in candidatos:
        if os.path.exists(c):
            return c
    return os.path.join(PASTA_ATUAL, 'operacoes_soma.csv')

ARQUIVO_CONTROLE = os.path.join(PASTA_ATUAL, 'controle_jobs_batch.json')

# =============================================================================
# MONTAGEM E SUBMISSÃO DE BATCH
# =============================================================================
def montar_requests_lote(modelo, df_operacoes):
    """Monta o array de requisições inline para a Batch API do OpenRouter."""
    modelo_openrouter = f"google/{modelo}" if not modelo.startswith("google/") else modelo
    config_reasoning = obter_config_reasoning(modelo)
    requests_payload = []

    for idx, row in df_operacoes.iterrows():
        conta = row.get('string') or row.get('Conta')
        resultado_orig = row.get('resultado') or row.get('Resultado_original')
        tipo_op = row.get('tipo') or row.get('Operacao')

        prompt = (
            "Sua tarefa é resolver operações matemáticas. "
            "Responda a pergunta a seguir e retorne o resultado "
            "somente em formato de número, sem unidades ou caracteres especiais. "
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
            # Metadados adicionais para facilitar posterior cruzamento
            "metadata": {
                "modelo": modelo,
                "conta": conta,
                "resultado_original": int(resultado_orig),
                "operacao": str(tipo_op)
            }
        }
        requests_payload.append(item)

    return requests_payload

def submeter_batch_openrouter(api_key, modelo, requests_payload):
    """Submete uma requisição POST /api/beta/batches na OpenRouter Batch API."""
    url = "https://openrouter.ai/api/beta/batches"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://tcc-experimento.ufba.br",
        "X-Title": "Experimento TCC Soma Batch API"
    }

    modelo_openrouter = f"google/{modelo}" if not modelo.startswith("google/") else modelo

    # OpenRouter exige o campo 'model' no nível raiz antes de 'requests'
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

    resp = requests.post(url, headers=headers, json=payload, timeout=60)
    if resp.status_code >= 400:
        logging.error(f"[{modelo}] Detalhes do erro da API ({resp.status_code}): {resp.text}")
        resp.raise_for_status()
    return resp.json()

def carregar_controle_jobs():
    if os.path.exists(ARQUIVO_CONTROLE):
        try:
            with open(ARQUIVO_CONTROLE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def salvar_controle_jobs(controle):
    with open(ARQUIVO_CONTROLE, 'w', encoding='utf-8') as f:
        json.dump(controle, f, indent=2, ensure_ascii=False)

# =============================================================================
# FLUXO PRINCIPAL
# =============================================================================
def main():
    parser = argparse.ArgumentParser(description="Envio de Lotes para Batch API OpenRouter (Operações de Soma)")
    parser.add_argument("--modelo", type=str, default=None, help="Executar apenas um modelo específico (ex: gemini-3.8-flash)")
    parser.add_argument("--executar", action="store_true", help="ATENÇÃO: Flag obrigatória para realizar o envio real das chamadas via API")
    parser.add_argument("--limite", type=int, default=None, help="Limitar quantidade de operações (para testes)")
    args = parser.parse_args()

    api_key = carregar_openrouter_key()
    if not api_key:
        logging.error("A chave OPEN_ROUTER_API_KEY_2 não foi encontrada em chave.env!")
        logging.error("Verifique se o arquivo 'chave.env' está presente.")
        return

    logging.info("Chave OPEN_ROUTER_API_KEY_2 localizada com sucesso.")

    caminho_op = encontrar_arquivo_operacoes()
    if not os.path.exists(caminho_op):
        logging.error(f"Base de operações não encontrada em: {caminho_op}")
        logging.info("Execute 'gerar_operacoes_soma.py' para gerar 'operacoes_soma.csv'.")
        return

    df_operacoes = pd.read_csv(caminho_op)
    logging.info(f"Base de operações carregada: {len(df_operacoes)} contas.")

    if args.limite:
        df_operacoes = df_operacoes.head(args.limite)
        logging.info(f"Limite aplicado: testando apenas {len(df_operacoes)} operações.")

    modelos_alvo = [args.modelo] if args.modelo else modelos_lista
    controle = carregar_controle_jobs()

    logging.info(f"Modelos selecionados para envio ({len(modelos_alvo)}): {modelos_alvo}")

    for modelo in modelos_alvo:
        # Se já existe um job concluído ou ativo registrado, avisar
        if modelo in controle and controle[modelo].get("status") in ["completed", "in_progress"]:
            logging.info(f"[{modelo}] Já possui job registrado no controle (ID: {controle[modelo].get('batch_id')}, Status: {controle[modelo].get('status')}). Pulando envio duplicado.")
            continue

        requests_lote = montar_requests_lote(modelo, df_operacoes)
        logging.info(f"[{modelo}] Lote estruturado com {len(requests_lote)} requisições. Reasoning config: {obter_config_reasoning(modelo)}")

        if not args.executar:
            logging.info(f"[{modelo}] MODO ESTRUTURAL / DRY-RUN (Nenhuma chamada enviada).")
            logging.info(f"  Exemplo de payload montado (custom_id: {requests_lote[0]['custom_id']}):")
            logging.info(f"  Mensagem: {requests_lote[0]['body']['messages'][0]['content']}")
            logging.info(f"  Modelo OpenRouter: {requests_lote[0]['body']['model']}")
            logging.info(f"  Extra body reasoning: {requests_lote[0]['body']['extra_body']}")
            continue

        try:
            logging.info(f"[{modelo}] Submetendo lote para OpenRouter Batch API...")
            resultado_api = submeter_batch_openrouter(api_key, modelo, requests_lote)
            batch_id = resultado_api.get("id") or resultado_api.get("batch_id")
            status = resultado_api.get("status", "in_progress")

            logging.info(f"[{modelo}] Lote submetido com sucesso! Batch ID: {batch_id} (Status: {status})")

            controle[modelo] = {
                "modelo": modelo,
                "batch_id": batch_id,
                "total_requests": len(requests_lote),
                "timestamp_envio": datetime.now().isoformat(),
                "status": status,
                "resposta_criacao": resultado_api
            }
            salvar_controle_jobs(controle)

        except Exception as e:
            logging.error(f"[{modelo}] Erro ao submeter lote na API: {e}")

    if not args.executar:
        logging.info("\n=========================================================================")
        logging.info("ESTRUTURA CONCLUÍDA COM SUCESSO!")
        logging.info("Para efetivamente disparar as chamadas para a Batch API da OpenRouter, execute:")
        logging.info("  python enviar_chamadas.py --executar")
        logging.info("=========================================================================")

if __name__ == '__main__':
    main()

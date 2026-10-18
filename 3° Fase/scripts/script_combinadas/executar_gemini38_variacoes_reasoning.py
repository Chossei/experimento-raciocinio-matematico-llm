"""Módulo de Execução em Lote - Gemini 3.8 Flash com Variações de Reasoning (mid e high)
Operação: Expressões Combinadas a * (b + c)

Este script:
1. Carrega as 450 operações de 'operacoes/operacoes_combinadas.csv'.
2. Constrói e submete 2 lotes (Batch API OpenRouter):
   - gemini-3.8-flash-mid (reasoning: {"effort": "medium"})
   - gemini-3.8-flash-high (reasoning: {"effort": "high"})
3. Salva os Batch IDs em 'jobs/jobs_combinadas/controle_jobs_gemini38_variacoes.json'.
4. Monitora o status dos lotes até a conclusão.
5. Faz backup bruto em json lines / json completo em 'jobs/jobs_combinadas/backup_bruto/'.
6. Trata os resultados com precisão Decimal, extrai tokens de raciocínio, acerto de operação, acerto de formato e custos.
7. Gera base tratada e atualiza os CSVs de resultados combinadas.
"""

import os
import sys
import re
import json
import time
import logging
from datetime import datetime
from decimal import Decimal, getcontext
import requests
import pandas as pd
from dotenv import load_dotenv

getcontext().prec = 100

# =============================================================================
# CONFIGURAÇÃO DE DIRETÓRIOS E LOGS
# =============================================================================
PASTA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
PASTA_SCRIPTS = os.path.dirname(PASTA_SCRIPT)
PASTA_RAIZ = os.path.dirname(PASTA_SCRIPTS)

LOGS_DIR = os.path.join(PASTA_RAIZ, "logs", "logs_combinadas")
JOBS_DIR = os.path.join(PASTA_RAIZ, "jobs", "jobs_combinadas")
BACKUP_DIR = os.path.join(JOBS_DIR, "backup_bruto")
RESULTADOS_DIR = os.path.join(PASTA_RAIZ, "dados_resultados", "resultados_combinadas")
OPERACOES_DIR = os.path.join(PASTA_RAIZ, "operacoes")

os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(JOBS_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs(RESULTADOS_DIR, exist_ok=True)

data_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = os.path.join(LOGS_DIR, f"gemini38_variacoes_reasoning_{data_hora}.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_filename, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logging.info("=== Inicializando Experimento: Gemini 3.8 Flash (Variações mid e high) ===")

# =============================================================================
# CARREGAMENTO DE CHAVE OPENROUTER
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

API_KEY = carregar_openrouter_key()
if not API_KEY:
    logging.error("ERRO CRÍTICO: Chave OPEN_ROUTER_API_KEY_2 não encontrada!")
    sys.exit(1)

ARQUIVO_OPERACOES = os.path.join(OPERACOES_DIR, "operacoes_combinadas.csv")
ARQUIVO_CONTROLE = os.path.join(JOBS_DIR, "controle_jobs_gemini38_variacoes.json")

# Preços OpenRouter para gemini-3.8-flash (com desconto de 50% em Batch)
PRECO_INPUT_USD = 0.75
PRECO_OUTPUT_USD = 3.75

# =============================================================================
# MONTAGEM DE REQUISIÇÕES BATCH
# =============================================================================
def criar_requests_payload(modelo_label, effort_str, df_operacoes):
    requests_payload = []
    for idx, row in df_operacoes.iterrows():
        conta = row.get("conta") or row.get("string") or row.get("Conta")
        resultado_orig = row.get("resultado da operacao") or row.get("resultado") or row.get("Resultado_original")
        qtd_digitos = row.get("quantidade de digitos") or row.get("tipo") or row.get("Operacao")

        prompt = (
            "Sua tarefa é resolver uma operação matemática. "
            "Responda a pergunta a seguir e retorne o resultado "
            "somente em formato de número, sem unidades ou caracteres especiais.\n\n"
            f"{conta}"
        )

        custom_id = f"{modelo_label}||{idx}||{conta}"

        item = {
            "custom_id": custom_id,
            "body": {
                "model": "google/gemini-3.8-flash",
                "messages": [{"role": "user", "content": prompt}],
                "temperature": 0.0,
                "max_tokens": 3000,
                "reasoning": {
                    "effort": effort_str
                }
            },
            "metadata": {
                "modelo": modelo_label,
                "conta": conta,
                "resultado_original": str(resultado_orig).strip(),
                "operacao": str(qtd_digitos)
            }
        }
        requests_payload.append(item)
    return requests_payload

def submeter_batch(api_key, modelo_label, requests_payload):
    url = "https://openrouter.ai/api/beta/batches"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://tcc-experimento.ufba.br",
        "X-Title": f"Experimento Combinadas {modelo_label}"
    }
    payload = {
        "model": "google/gemini-3.8-flash",
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

def consultar_batch(api_key, batch_id):
    url = f"https://openrouter.ai/api/beta/batches/{batch_id}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    resp = requests.get(url, headers=headers, timeout=60)
    resp.raise_for_status()
    return resp.json()

def extrair_numero_decimal(texto):
    if not texto:
        return None
    padrao = re.compile(r"\d+")
    numeros = padrao.findall(str(texto))
    if numeros:
        try:
            return Decimal("".join(numeros))
        except Exception:
            return None
    return None

def validar_formato_resposta(texto):
    if not texto:
        return False
    texto_limpo = str(texto).strip()
    if re.search(r"[a-zA-Z]", texto_limpo):
        return False
    return bool(re.fullmatch(r"\d+", texto_limpo))

def calcular_custos(prompt_tokens, completion_tokens, reasoning_tokens):
    in_usd = PRECO_INPUT_USD
    out_usd = PRECO_OUTPUT_USD
    # Batch API do OpenRouter tem 50% de desconto em prompt e completion
    custo_in = (prompt_tokens * in_usd / 1_000_000.0) * 0.5
    custo_out = (completion_tokens * out_usd / 1_000_000.0) * 0.5
    custo_reasoning = (reasoning_tokens * out_usd / 1_000_000.0) * 0.5
    custo_total = custo_in + custo_out
    return {
        "custo_input": round(custo_in, 6),
        "custo_output": round(custo_out, 6),
        "custo_reasoning": round(custo_reasoning, 6),
        "custo_total": round(custo_total, 6)
    }

def processar_resultados(modelo_label, dados_batch, mapa_operacoes):
    linhas_tratadas = []
    results = dados_batch.get("results") or dados_batch.get("data") or []
    
    for item in results:
        custom_id = item.get("custom_id", "")
        partes = custom_id.split("||")
        conta_idx = int(partes[1]) if len(partes) > 1 and partes[1].isdigit() else None
        conta_str = partes[2] if len(partes) > 2 else ""

        op_info = mapa_operacoes.get(conta_idx) or {}
        res_orig_raw = op_info.get("resultado da operacao")
        try:
            resultado_original = Decimal(str(res_orig_raw).strip()) if res_orig_raw is not None and not pd.isna(res_orig_raw) else None
        except Exception:
            resultado_original = None

        quantidade_digitos = op_info.get("quantidade de digitos", "")
        conta_gabarito = op_info.get("conta") or conta_str

        resp_obj = item.get("response", {})
        body = resp_obj.get("body", {})

        choices = body.get("choices") or []
        texto_bruto = ""
        resumo_raciocinio = None
        if choices:
            msg = choices[0].get("message", {})
            texto_bruto = msg.get("content") or ""
            resumo_raciocinio = msg.get("reasoning") or msg.get("refusal")

        usage = body.get("usage") or {}
        prompt_tokens = usage.get("prompt_tokens") or 0
        completion_tokens = usage.get("completion_tokens") or 0
        completion_details = usage.get("completion_tokens_details") or {}
        reasoning_tokens = completion_details.get("reasoning_tokens") or 0

        valor_extraido = extrair_numero_decimal(texto_bruto)
        acerto_formato = validar_formato_resposta(texto_bruto)
        acerto_operacao = (valor_extraido == resultado_original) if (valor_extraido is not None and resultado_original is not None) else False

        custos = calcular_custos(prompt_tokens, completion_tokens, reasoning_tokens)

        linhas_tratadas.append({
            "nome do modelo": modelo_label,
            "quantidade de digitos": quantidade_digitos,
            "resultado bruto do modelo": texto_bruto,
            "resultado tratado do modelo": str(valor_extraido) if valor_extraido is not None else None,
            "resultado original": str(resultado_original) if resultado_original is not None else None,
            "acerto da operacao": acerto_operacao,
            "acerto do formato de resposta": acerto_formato,
            "conta": conta_gabarito,
            "custo total": custos["custo_total"],
            "custo de input tokens": custos["custo_input"],
            "custo de output tokens": custos["custo_output"],
            "quantidade de reasoning tokens gerados": reasoning_tokens,
            "resumo do raciocinio": resumo_raciocinio
        })

    return pd.DataFrame(linhas_tratadas)

# =============================================================================
# EXECUÇÃO PRINCIPAL
# =============================================================================
def main():
    if not os.path.exists(ARQUIVO_OPERACOES):
        logging.error(f"Arquivo de operações '{ARQUIVO_OPERACOES}' não encontrado!")
        sys.exit(1)

    df_operacoes = pd.read_csv(ARQUIVO_OPERACOES)
    logging.info(f"Carregadas {len(df_operacoes)} operações de {ARQUIVO_OPERACOES}")

    mapa_operacoes = {idx: row.to_dict() for idx, row in df_operacoes.iterrows()}

    # Carregar ou inicializar controle
    controle = {}
    if os.path.exists(ARQUIVO_CONTROLE):
        try:
            with open(ARQUIVO_CONTROLE, "r", encoding="utf-8") as f:
                controle = json.load(f)
        except Exception:
            controle = {}

    variacoes = [
        {"modelo_label": "gemini-3.8-flash-mid", "effort": "medium"},
        {"modelo_label": "gemini-3.8-flash-high", "effort": "high"}
    ]

    for var in variacoes:
        m_label = var["modelo_label"]
        effort = var["effort"]

        if m_label in controle and controle[m_label].get("batch_id"):
            b_id = controle[m_label]["batch_id"]
            logging.info(f"[{m_label}] Lote já existente no controle: {b_id} (Status: {controle[m_label].get('status')})")
        else:
            logging.info(f"[{m_label}] Montando 450 requisições (effort: '{effort}')...")
            reqs = criar_requests_payload(m_label, effort, df_operacoes)
            logging.info(f"[{m_label}] Enviando lote para a Batch API do OpenRouter...")
            try:
                resp = submeter_batch(API_KEY, m_label, reqs)
                b_id = resp.get("id")
                logging.info(f"[{m_label}] Lote submetido com SUCESSO! Batch ID: {b_id}")
                controle[m_label] = {
                    "modelo": m_label,
                    "effort": effort,
                    "batch_id": b_id,
                    "total_requests": len(reqs),
                    "timestamp_envio": datetime.now().isoformat(),
                    "status": resp.get("status", "validating"),
                    "processado": False
                }
                with open(ARQUIVO_CONTROLE, "w", encoding="utf-8") as f:
                    json.dump(controle, f, indent=2, ensure_ascii=False)
            except Exception as e:
                logging.error(f"[{m_label}] Falha ao submeter lote: {e}")

    logging.info("Lotes enviados com sucesso. Iniciando monitoramento dos status...")

    todos_concluidos = False
    tentativas = 0
    max_tentativas = 120 # Até ~1 hora de polling

    while not todos_concluidos and tentativas < max_tentativas:
        tentativas += 1
        todos_concluidos = True
        
        for var in variacoes:
            m_label = var["modelo_label"]
            info = controle.get(m_label, {})
            b_id = info.get("batch_id")
            if not b_id:
                continue

            if info.get("processado"):
                logging.info(f"[{m_label}] Já processado anteriormente.")
                continue

            try:
                dados_batch = consultar_batch(API_KEY, b_id)
                status = dados_batch.get("status")
                req_counts = dados_batch.get("request_counts", {})
                info["status"] = status
                info["request_counts"] = req_counts
                logging.info(f"[{m_label}] Tentativa {tentativas}: Status '{status}' | Contagens: {req_counts}")

                if status == "completed":
                    # Salvar backup bruto em json lines / json
                    arq_backup = os.path.join(BACKUP_DIR, f"respostas_brutas_{m_label}_{b_id}.json")
                    with open(arq_backup, "w", encoding="utf-8") as fb:
                        json.dump(dados_batch, fb, indent=2, ensure_ascii=False)
                    logging.info(f"[{m_label}] Backup bruto salvo em {arq_backup}")

                    # Também salvar em formato JSONL (1 linha por requisição concluída)
                    arq_jsonl = os.path.join(BACKUP_DIR, f"respostas_brutas_{m_label}_{b_id}.jsonl")
                    results = dados_batch.get("results") or dados_batch.get("data") or []
                    with open(arq_jsonl, "w", encoding="utf-8") as f_jsonl:
                        for res_item in results:
                            f_jsonl.write(json.dumps(res_item, ensure_ascii=False) + "\n")
                    logging.info(f"[{m_label}] Backup JSONL salvo em {arq_jsonl}")

                    # Processar e tabular respostas
                    df_tratado = processar_resultados(m_label, dados_batch, mapa_operacoes)
                    arq_csv_modelo = os.path.join(RESULTADOS_DIR, f"resultados_{m_label}.csv")
                    df_tratado.to_csv(arq_csv_modelo, index=False)
                    logging.info(f"[{m_label}] Base individual salva em {arq_csv_modelo} ({len(df_tratado)} linhas)")

                    info["processado"] = True
                    info["total_processado"] = len(df_tratado)

                elif status in ["failed", "cancelled", "expired"]:
                    logging.error(f"[{m_label}] Lote terminou com status de erro: {status}")
                else:
                    todos_concluidos = False

            except Exception as e:
                logging.warning(f"[{m_label}] Erro na consulta do batch: {e}")
                todos_concluidos = False

        with open(ARQUIVO_CONTROLE, "w", encoding="utf-8") as f:
            json.dump(controle, f, indent=2, ensure_ascii=False)

        if not todos_concluidos:
            logging.info("Aguardando 20 segundos antes da próxima verificação...")
            time.sleep(20)

    logging.info("=== Processo de execução e coleta finalizado ===")

if __name__ == "__main__":
    main()

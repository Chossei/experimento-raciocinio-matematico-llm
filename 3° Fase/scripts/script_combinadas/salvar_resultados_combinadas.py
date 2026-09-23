"""Módulo de Coleta, Backup Bruto e Tratamento - 3° Experimento: Expressões Combinadas a * (b + c)

Este script:
1. Consulta os status dos jobs em 'jobs/jobs_combinadas/controle_jobs_batch.json'.
2. Faz o backup integral imediato das respostas brutas em 'jobs/jobs_combinadas/backup_bruto/'.
3. Trata os resultados com acerto de operação, acerto de formato de resposta, contagem de tokens e custos em BRL.
4. Salva a base final em 'dados_resultados/resultados_combinadas/resultados_combinadas.csv' com colunas do Quadro 2.
"""

import os
import re
import json
import logging
import argparse
from datetime import datetime
from decimal import Decimal, InvalidOperation, getcontext
from dotenv import load_dotenv
import requests
import pandas as pd

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
os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs(RESULTADOS_DIR, exist_ok=True)

data_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = os.path.join(LOGS_DIR, f"salvar_resultados_combinadas_{data_hora}.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_filename, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logging.info("=== Inicializando Módulo de Coleta e Tratamento - Expressões Combinadas a * (b + c) ===")

# =============================================================================
# AUTENTICAÇÃO E CONFIGURAÇÕES
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
tabela_precos = {d["modelo"]: d for d in dados_api}

ARQUIVO_CONTROLE = os.path.join(JOBS_DIR, "controle_jobs_batch.json")
ARQUIVO_RESULTADOS = os.path.join(RESULTADOS_DIR, "resultados_combinadas.csv")
ARQUIVO_OPERACOES = os.path.join(OPERACOES_DIR, "operacoes_combinadas.csv")

# =============================================================================
# FUNÇÕES DE CONSULTA DA API
# =============================================================================
def consultar_status_batch(api_key, batch_id):
    url = f"https://openrouter.ai/api/beta/batches/{batch_id}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    resp = requests.get(url, headers=headers, timeout=60)
    resp.raise_for_status()
    return resp.json()

# =============================================================================
# TRATAMENTO DE TEXTO E CUSTOS
# =============================================================================
def extrair_numero_decimal(texto):
    """Extrai sequência numérica de dígitos e converte para Decimal (precisão arbitrária)."""
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

def calcular_custos_detalhados(modelo, prompt_tokens, completion_tokens, reasoning_tokens):
    precos = tabela_precos.get(modelo, {"input_usd": 0.75, "output_usd": 3.75})
    in_usd = precos["input_usd"]
    out_usd = precos["output_usd"]

    custo_input_brl = (prompt_tokens * in_usd / 1_000_000.0) * taxa_cambio
    custo_output_brl = (completion_tokens * out_usd / 1_000_000.0) * taxa_cambio
    custo_reasoning_brl = (reasoning_tokens * out_usd / 1_000_000.0) * taxa_cambio
    custo_total_brl = custo_input_brl + custo_output_brl

    return {
        "custo_input": round(custo_input_brl, 6),
        "custo_output": round(custo_output_brl, 6),
        "custo_reasoning": round(custo_reasoning_brl, 6),
        "custo_total": round(custo_total_brl, 6)
    }

# =============================================================================
# PROCESSAMENTO DO LOTE
# =============================================================================
def processar_lote_concluido(modelo, batch_id, dados_batch, mapa_operacoes):
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
            # Captura detalhes de raciocínio se retornados
            resumo_raciocinio = msg.get("reasoning") or msg.get("refusal")

        usage = body.get("usage") or {}
        prompt_tokens = usage.get("prompt_tokens") or 0
        completion_tokens = usage.get("completion_tokens") or 0

        completion_details = usage.get("completion_tokens_details") or {}
        reasoning_tokens = completion_details.get("reasoning_tokens") or 0

        # Comparação exata via biblioteca Decimal
        valor_extraido = extrair_numero_decimal(texto_bruto)
        acerto_formato = validar_formato_resposta(texto_bruto)
        acerto_operacao = (valor_extraido == resultado_original) if (valor_extraido is not None and resultado_original is not None) else False

        custos = calcular_custos_detalhados(modelo, prompt_tokens, completion_tokens, reasoning_tokens)

        linhas_tratadas.append({
            # Colunas oficiais do Quadro 2 (Plano FINAL)
            "nome do modelo": modelo,
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
# FLUXO PRINCIPAL
# =============================================================================
def main():
    parser = argparse.ArgumentParser(description="Consulta, Backup e Tratamento - Expressões Combinadas")
    parser.add_argument("--status", action="store_true", help="Apenas consultar o status dos lotes no controle")
    parser.add_argument("--forcar", action="store_true", help="Forçar download e reprocessamento de todos os lotes")
    args = parser.parse_args()

    api_key = carregar_openrouter_key()
    if not api_key:
        logging.warning("Chave OPEN_ROUTER_API_KEY_2 não encontrada. Apenas modo local disponível.")

    if not os.path.exists(ARQUIVO_CONTROLE):
        logging.warning(f"Arquivo de controle '{ARQUIVO_CONTROLE}' ainda não existe.")
        logging.info("Envie as chamadas primeiro com 'enviar_chamadas_combinadas.py'.")
        return

    with open(ARQUIVO_CONTROLE, "r", encoding="utf-8") as f:
        controle = json.load(f)

    if not controle:
        logging.info("Nenhum lote registrado no controle.")
        return

    logging.info(f"Lotes registrados no controle: {len(controle)}")
    for mod, info in controle.items():
        logging.info(f"  - {mod}: Batch ID '{info.get('batch_id')}' | Status: '{info.get('status')}'")

    if args.status:
        if not api_key:
            logging.error("Chave necessária para consultar status na API.")
            return
        logging.info("\nConsultando status na OpenRouter API...")
        for mod, info in controle.items():
            b_id = info.get("batch_id")
            if not b_id:
                continue
            try:
                dados = consultar_status_batch(api_key, b_id)
                novo_status = dados.get("status")
                req_counts = dados.get("request_counts", {})
                logging.info(f"  [{mod}] Status: {novo_status} | Contagens: {req_counts}")
                info["status"] = novo_status
                info["request_counts"] = req_counts
            except Exception as e:
                logging.error(f"  [{mod}] Erro ao consultar batch {b_id}: {e}")

        with open(ARQUIVO_CONTROLE, "w", encoding="utf-8") as f:
            json.dump(controle, f, indent=2, ensure_ascii=False)
        return

    df_op = pd.read_csv(ARQUIVO_OPERACOES, dtype=str) if os.path.exists(ARQUIVO_OPERACOES) else pd.DataFrame()
    mapa_operacoes = {idx: row.to_dict() for idx, row in df_op.iterrows()}

    dfs_novos = []
    for mod, info in controle.items():
        b_id = info.get("batch_id")
        status_atual = info.get("status")
        if not b_id:
            continue

        arq_backup = os.path.join(BACKUP_DIR, f"respostas_brutas_{mod}_{b_id}.json")
        dados_lote = None

        if os.path.exists(arq_backup) and not args.forcar:
            try:
                with open(arq_backup, "r", encoding="utf-8") as fb:
                    dados_lote = json.load(fb)
                logging.info(f"[{mod}] Carregado backup bruto local: {arq_backup}")
            except Exception as e:
                logging.warning(f"[{mod}] Erro ao ler backup local: {e}. Consultando API...")

        if (dados_lote is None or args.forcar) and api_key:
            try:
                logging.info(f"[{mod}] Consultando batch {b_id} na OpenRouter API...")
                dados_lote = consultar_status_batch(api_key, b_id)
                status_atual = dados_lote.get("status")
                info["status"] = status_atual
                info["request_counts"] = dados_lote.get("request_counts", {})

                if status_atual == "completed":
                    with open(arq_backup, "w", encoding="utf-8") as fb:
                        json.dump(dados_lote, fb, indent=2, ensure_ascii=False)
                    logging.info(f"[{mod}] Backup bruto salvo em: {arq_backup}")
                else:
                    logging.info(f"[{mod}] Status atual: '{status_atual}'. Aguardando conclusão.")
            except Exception as e:
                logging.error(f"[{mod}] Erro ao consultar batch {b_id}: {e}")

        if dados_lote and dados_lote.get("status") == "completed":
            logging.info(f"[{mod}] Processando respostas do lote {b_id}...")
            df_tratado = processar_lote_concluido(mod, b_id, dados_lote, mapa_operacoes)
            dfs_novos.append(df_tratado)
            info["processado"] = True
            info["status"] = "completed"
            info["total_processado"] = len(df_tratado)
            logging.info(f"[{mod}] Concluído com sucesso ({len(df_tratado)} operações).")

    with open(ARQUIVO_CONTROLE, "w", encoding="utf-8") as f:
        json.dump(controle, f, indent=2, ensure_ascii=False)

    if dfs_novos:
        df_consolidado = pd.concat(dfs_novos, ignore_index=True)
        if os.path.exists(ARQUIVO_RESULTADOS) and not args.forcar:
            df_antigo = pd.read_csv(ARQUIVO_RESULTADOS)
            df_salvar = pd.concat([df_antigo, df_consolidado], ignore_index=True).drop_duplicates(subset=["nome do modelo", "conta"], keep="last")
        else:
            df_salvar = df_consolidado

        df_salvar.to_csv(ARQUIVO_RESULTADOS, index=False)
        logging.info(f"Base final atualizada com sucesso em: {ARQUIVO_RESULTADOS} ({len(df_salvar)} linhas)")
    else:
        logging.info("Nenhum novo lote concluído para processar.")

if __name__ == "__main__":
    main()

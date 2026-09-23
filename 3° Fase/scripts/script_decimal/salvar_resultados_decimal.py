"""
Módulo de Coleta, Backup Bruto e Tratamento - Experimento: Multiplicação Decimal Batch API

Este script:
1. Consulta os status dos jobs em 'jobs/jobs_decimal/controle_jobs_batch.json'.
2. Faz o backup integral imediato das respostas brutas em 'jobs/jobs_decimal/backup_bruto/'.
3. Trata os resultados com acerto de operação (usando Decimal exato), acerto de formato, contagem de tokens e custos em BRL.
4. Concatena os novos registros aos resultados existentes, assegurando 900/900 para o modelo alvo.
5. Sincroniza as bases de dados em:
   - '3° Fase/dados_resultados/resultados_decimal/resultados_decimal.csv'
   - 'dados/resultados_gemini_decimal_openrouter.csv'
   - '1° e 2° Fase/dados/resultados_gemini_decimal_openrouter.csv'
   - 'github_repo/dados/resultados_gemini_decimal_openrouter.csv'
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

# Precisão arbitrária para comparações decimais exatas
getcontext().prec = 100

# =============================================================================
# CONFIGURAÇÃO DE DIRETÓRIOS E LOGS
# =============================================================================
PASTA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
PASTA_SCRIPTS = os.path.dirname(PASTA_SCRIPT)
PASTA_RAIZ = os.path.dirname(PASTA_SCRIPTS)

LOGS_DIR = os.path.join(PASTA_RAIZ, "logs", "logs_decimal")
JOBS_DIR = os.path.join(PASTA_RAIZ, "jobs", "jobs_decimal")
BACKUP_DIR = os.path.join(JOBS_DIR, "backup_bruto")
RESULTADOS_DIR = os.path.join(PASTA_RAIZ, "dados_resultados", "resultados_decimal")
OPERACOES_DIR = os.path.join(PASTA_RAIZ, "operacoes")

os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)
os.makedirs(RESULTADOS_DIR, exist_ok=True)

data_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = os.path.join(LOGS_DIR, f"salvar_resultados_decimal_{data_hora}.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_filename, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logging.info("=== Inicializando Módulo de Coleta e Tratamento - Multiplicação Decimal Batch ===")

# =============================================================================
# AUTENTICAÇÃO E CONFIGURAÇÕES
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
ARQUIVO_RESULTADOS_LOCAL = os.path.join(RESULTADOS_DIR, "resultados_decimal.csv")

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

# Arquivos de sincronização
ARQUIVOS_SINCRONIZACAO = [
    ARQUIVO_RESULTADOS_LOCAL,
    os.path.join(PASTA_RAIZ, "..", "dados", "resultados_gemini_decimal_openrouter.csv"),
    os.path.join(PASTA_RAIZ, "dados", "resultados_gemini_decimal_openrouter.csv"),
    os.path.join(PASTA_RAIZ, "..", "1° e 2° Fase", "dados", "resultados_gemini_decimal_openrouter.csv"),
    os.path.join(PASTA_RAIZ, "..", "github_repo", "dados", "resultados_gemini_decimal_openrouter.csv")
]

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
# TRATAMENTO DE TEXTO, COMPARAÇÃO DECIMAL E CUSTOS
# =============================================================================
def extrair_numero_decimal(texto):
    """Extrai um número decimal (com ponto) da resposta do modelo."""
    if not texto:
        return None
    texto_limpo = str(texto).strip()
    padrao = re.compile(r'-?\d+\.?\d*')
    match = padrao.search(texto_limpo)
    if match:
        return match.group()
    return None

def validar_formato_resposta(texto):
    """Verifica se a resposta não contém letras (apenas números e símbolos numéricos permitidos)."""
    if not texto:
        return False
    texto_limpo = str(texto).strip()
    return not bool(re.search(r'[a-zA-Z]', texto_limpo))

def comparar_decimais(valor_extraido, valor_esperado):
    """Compara dois valores decimais lidando com precisão arbitrária e zeros à direita."""
    if valor_extraido is None or valor_esperado is None:
        return False
    val_ext = str(valor_extraido).strip()
    val_esp = str(valor_esperado).strip()

    if val_ext == val_esp:
        return True

    try:
        return Decimal(val_ext) == Decimal(val_esp)
    except (InvalidOperation, ValueError):
        return False

def calcular_custo(modelo, prompt_tokens, completion_tokens):
    """Calcula o custo total em Reais (BRL) baseado nos tokens utilizados."""
    precos = tabela_precos.get(modelo, {"input_usd": 0.75, "output_usd": 3.75})
    in_usd = precos["input_usd"]
    out_usd = precos["output_usd"]
    custo_usd = (prompt_tokens * in_usd / 1_000_000.0) + (completion_tokens * out_usd / 1_000_000.0)
    custo_brl = custo_usd * taxa_cambio
    return round(custo_brl, 6)

# =============================================================================
# PROCESSAMENTO DOS RESULTADOS BRUTOS
# =============================================================================
def processar_lote_concluido(modelo, batch_id, dados_batch, mapa_operacoes):
    """Processa a lista de resultados do lote concluído e estrutura as métricas com Decimal exato."""
    linhas_tratadas = []
    results = dados_batch.get("results") or dados_batch.get("data") or []

    for item in results:
        custom_id = item.get("custom_id", "")
        partes = custom_id.split("||")
        conta_idx = int(partes[1]) if len(partes) > 1 and partes[1].isdigit() else None
        conta_str = partes[2] if len(partes) > 2 else ""

        op_info = mapa_operacoes.get(conta_idx) or {}
        resultado_esperado = str(op_info.get("Resultado_original_decimal") or op_info.get("resultado") or "").strip()
        operacao_tipo = op_info.get("tipo") or op_info.get("Operacao") or ""
        conta_gabarito = op_info.get("Conta_decimal") or op_info.get("conta") or conta_str

        resp_obj = item.get("response", {})
        body = resp_obj.get("body", {})

        choices = body.get("choices") or []
        texto_bruto = ""
        if choices:
            msg = choices[0].get("message", {})
            texto_bruto = msg.get("content") or ""

        usage = body.get("usage") or {}
        prompt_tokens = usage.get("prompt_tokens") or 0
        completion_tokens = usage.get("completion_tokens") or 0

        # Extração e validação decimal
        valor_extraido = extrair_numero_decimal(texto_bruto)
        acerto_formato = validar_formato_resposta(texto_bruto)
        acerto_operacao = comparar_decimais(valor_extraido, resultado_esperado)

        custo_total = calcular_custo(modelo, prompt_tokens, completion_tokens)

        # Formato padronizado exato de resultados_gemini_decimal_openrouter.csv:
        # ['Nome_do_modelo', 'Operacao', 'Resultado_do_modelo', 'Resposta_bruta', 'Resultado_original_decimal', 'Acerto_da_operacao', 'Acerto_do_formato_de_resposta', 'Conta_decimal', 'custo_total']
        linhas_tratadas.append({
            "Nome_do_modelo": modelo,
            "Operacao": operacao_tipo,
            "Resultado_do_modelo": valor_extraido,
            "Resposta_bruta": texto_bruto,
            "Resultado_original_decimal": resultado_esperado,
            "Acerto_da_operacao": acerto_operacao,
            "Acerto_do_formato_de_resposta": acerto_formato,
            "Conta_decimal": conta_gabarito,
            "custo_total": custo_total
        })

    return pd.DataFrame(linhas_tratadas)

# =============================================================================
# FLUXO PRINCIPAL
# =============================================================================
def main():
    parser = argparse.ArgumentParser(description="Consulta, Backup e Tratamento dos Resultados Decimal Batch API")
    parser.add_argument("--status", action="store_true", help="Apenas consultar o status atual dos jobs no controle")
    parser.add_argument("--forcar", action="store_true", help="Forçar download e reprocessamento mesmo se já existir backup local")
    args = parser.parse_args()

    api_key = carregar_openrouter_key()
    if not api_key:
        logging.warning("Chave OPEN_ROUTER_API_KEY_2 não encontrada. Apenas modo offline ou status local disponível.")

    if not os.path.exists(ARQUIVO_CONTROLE):
        logging.error(f"Arquivo de controle '{ARQUIVO_CONTROLE}' não encontrado.")
        return

    with open(ARQUIVO_CONTROLE, "r", encoding="utf-8") as f:
        controle = json.load(f)

    if not controle:
        logging.info("Nenhum job registrado no arquivo de controle.")
        return

    if args.status:
        logging.info("\n=== Status Atual dos Jobs de Multiplicação Decimal ===")
        for mod, info in controle.items():
            b_id = info.get("batch_id")
            status_local = info.get("status")
            total_req = info.get("total_requests")
            logging.info(f"[{mod}] ID: {b_id} | Status Local: {status_local} | Total Req: {total_req}")

        if not api_key:
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
                logging.info(f"  [{mod}] Status API: {novo_status} | Contagens: {req_counts}")
                info["status"] = novo_status
                info["request_counts"] = req_counts
            except Exception as e:
                logging.error(f"  [{mod}] Erro ao consultar batch {b_id}: {e}")

        with open(ARQUIVO_CONTROLE, "w", encoding="utf-8") as f:
            json.dump(controle, f, indent=2, ensure_ascii=False)
        return

    arquivo_ops = obter_arquivo_operacoes()
    df_op = pd.read_csv(arquivo_ops, dtype=str) if os.path.exists(arquivo_ops) else pd.DataFrame()
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
                    logging.info(f"[{mod}] Backup bruto salvo com sucesso em: {arq_backup}")
                else:
                    logging.info(f"[{mod}] Status atual: '{status_atual}'. Aguardando conclusão na OpenRouter.")
            except Exception as e:
                logging.error(f"[{mod}] Erro ao consultar batch {b_id}: {e}")

        if dados_lote and dados_lote.get("status") == "completed":
            logging.info(f"[{mod}] Processando respostas do lote {b_id}...")
            df_tratado = processar_lote_concluido(mod, b_id, dados_lote, mapa_operacoes)
            dfs_novos.append(df_tratado)
            info["processado"] = True
            info["status"] = "completed"
            info["total_processado"] = len(df_tratado)
            acertos = df_tratado["Acerto_da_operacao"].sum()
            taxa = (acertos / len(df_tratado) * 100) if len(df_tratado) > 0 else 0
            logging.info(f"[{mod}] Concluído: {acertos}/{len(df_tratado)} acertos ({taxa:.1f}%).")

    with open(ARQUIVO_CONTROLE, "w", encoding="utf-8") as f:
        json.dump(controle, f, indent=2, ensure_ascii=False)

    if dfs_novos:
        df_todas_novas = pd.concat(dfs_novos, ignore_index=True)
        logging.info(f"\nTotal de novas linhas tratadas: {len(df_todas_novas)}")

        for destino in ARQUIVOS_SINCRONIZACAO:
            caminho_abs = os.path.abspath(destino)
            if not os.path.exists(caminho_abs):
                continue

            try:
                df_existente = pd.read_csv(caminho_abs, dtype=str)
                len_antes = len(df_existente)
                df_consolidado = pd.concat([df_existente, df_todas_novas], ignore_index=True)
                # Remove duplicatas mantendo a última execução
                df_consolidado = df_consolidado.drop_duplicates(subset=["Nome_do_modelo", "Conta_decimal"], keep="last")
                df_consolidado.to_csv(caminho_abs, index=False)
                logging.info(f"💾 Sincronizado: {caminho_abs} (Antes: {len_antes} -> Depois: {len(df_consolidado)} linhas)")
            except Exception as e:
                logging.error(f"Erro ao sincronizar {caminho_abs}: {e}")

        logging.info("\n=== Tratamento e Sincronização Decimal Concluídos com Sucesso ===")
    else:
        logging.info("\nNenhum lote novo concluído para processamento.")

if __name__ == "__main__":
    main()

"""Módulo de Coleta, Backup Bruto e Tratamento de Resultados - Experimento de Soma

Este script:
1. Consulta o status dos jobs registrados em 'controle_jobs_batch.json' via Batch API da OpenRouter.
2. Salva a resposta bruta integral em 'backup_bruto/' assim que o lote for concluído.
3. Estrutura os dados tratados com acerto de operação, acerto de formato, métricas de tokens e custos em BRL.
4. Salva a base final 'resultados_gemini_soma_openrouter.csv' em 'dados/' e na pasta local.
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
BACKUP_DIR = os.path.join(PASTA_ATUAL, 'backup_bruto')
os.makedirs(LOGS_DIR, exist_ok=True)
os.makedirs(BACKUP_DIR, exist_ok=True)

data_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = os.path.join(LOGS_DIR, f'salvar_resultados_{data_hora}.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logging.info("=== Inicializando Módulo de Coleta e Tratamento de Resultados (Soma) ===")

# =============================================================================
# AUTENTICAÇÃO E CARREGAMENTO DE CHAVE
# =============================================================================
def carregar_openrouter_key():
    candidatos = [
        os.path.join(PASTA_RAIZ, 'chave.env'),
        os.path.join(PASTA_GEMINI, 'chave.env'),
        os.path.join(PASTA_ATUAL, 'chave.env'),
        'chave.env',
        '../chave.env',
        '../../chave.env'
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
# CONFIGURAÇÕES DO EXPERIMENTO: CUSTOS E TAXA DE CÂMBIO
# =============================================================================
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

ARQUIVO_CONTROLE = os.path.join(PASTA_ATUAL, 'controle_jobs_batch.json')
ARQUIVO_RESULTADOS_FINAL = os.path.join(PASTA_RAIZ, 'dados', 'resultados_gemini_soma_openrouter.csv')

# =============================================================================
# FUNÇÕES DE CONSULTA DA API BATCH
# =============================================================================
def consultar_status_batch(api_key, batch_id):
    """Consulta o endpoint GET /api/beta/batches/:id."""
    url = f"https://openrouter.ai/api/beta/batches/{batch_id}"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    resp = requests.get(url, headers=headers, timeout=60)
    resp.raise_for_status()
    return resp.json()

# =============================================================================
# TRATAMENTO DE TEXTO, EXTRAÇÃO E FORMATO
# =============================================================================
def extrair_inteiro(texto):
    """Extrai sequência numérica e converte para int."""
    if not texto:
        return None
    numeros = re.findall(r'\d+', texto)
    if numeros:
        return int("".join(numeros))
    return None

def validar_formato_resposta(texto):
    """Verifica se a resposta contém apenas números.

    Caso contenha letras ou outros caracteres não permitidos, retorna False.
    """
    if not texto:
        return False
    texto_limpo = texto.strip()
    # Se contém qualquer letra, falhou na instrução de retornar apenas números
    if re.search(r'[a-zA-Z]', texto_limpo):
        return False
    # Retorna True se após remover espaços for puramente dígitos
    return bool(re.fullmatch(r'\d+', texto_limpo))

def calcular_custos_detalhados(modelo, prompt_tokens, completion_tokens, reasoning_tokens):
    """Calcula os custos de input, output, reasoning e total em BRL."""
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
# PROCESSAMENTO DOS RESULTADOS BRUTOS
# =============================================================================
def processar_lote_concluido(modelo, batch_id, dados_batch, mapa_operacoes):
    """Processa a lista de resultados do lote concluído e estrutura as métricas."""
    linhas_tratadas = []
    results = dados_batch.get("results") or dados_batch.get("data") or []

    for item in results:
        custom_id = item.get("custom_id", "")
        partes = custom_id.split("||")
        conta_idx = int(partes[1]) if len(partes) > 1 and partes[1].isdigit() else None
        conta_str = partes[2] if len(partes) > 2 else ""

        # Obter dados esperados do gabarito
        op_info = mapa_operacoes.get(conta_idx) or {}
        res_orig_raw = op_info.get("resultado") if op_info.get("resultado") is not None else op_info.get("Resultado_original")
        try:
            resultado_original = int(res_orig_raw) if res_orig_raw is not None and not pd.isna(res_orig_raw) else None
        except Exception:
            resultado_original = None

        operacao_tipo = op_info.get("tipo", "")
        conta_gabarito = op_info.get("string", conta_str)

        # Extrair corpo da resposta
        resp_obj = item.get("response", {})
        body = resp_obj.get("body", {})

        choices = body.get("choices") or []
        texto_bruto = ""
        if choices:
            texto_bruto = choices[0].get("message", {}).get("content") or ""

        # Métricas de tokens e raciocínio
        usage = body.get("usage") or {}
        prompt_tokens = usage.get("prompt_tokens") or 0
        completion_tokens = usage.get("completion_tokens") or 0

        # Tokens de raciocínio (extraídos de completion_tokens_details se disponíveis)
        completion_details = usage.get("completion_tokens_details") or {}
        reasoning_tokens = completion_details.get("reasoning_tokens") or 0

        # Tratamento de acertos
        valor_extraido = extrair_inteiro(texto_bruto)
        acerto_formato = validar_formato_resposta(texto_bruto)
        acerto_operacao = (valor_extraido == resultado_original) if (valor_extraido is not None and resultado_original is not None) else False

        # Custos
        custos = calcular_custos_detalhados(modelo, prompt_tokens, completion_tokens, reasoning_tokens)

        linhas_tratadas.append({
            # Colunas exigidas no plano de implementação
            "Nome do modelo": modelo,
            "Operacao": operacao_tipo,
            "Resultado bruto do modelo": texto_bruto,
            "Resultado original": resultado_original,
            "Acerto da operacao": acerto_operacao,
            "Acerto do formato de resposta": acerto_formato,
            "Conta": conta_gabarito,
            "Custo total": custos["custo_total"],
            "Custo de input tokens": custos["custo_input"],
            "Custo de output tokens": custos["custo_output"],
            "Custo de reasoning tokens": custos["custo_reasoning"],
            "Quantidade de reasoning tokens gerados": reasoning_tokens,

            # Aliases complementares para compatibilidade direta com os dashboards do projeto
            "Nome_do_modelo": modelo,
            "Resultado_do_modelo": valor_extraido,
            "Resposta_bruta": texto_bruto,
            "Acerto_da_operacao": acerto_operacao,
            "Acerto_do_formato_de_resposta": acerto_formato,
            "custo_total": custos["custo_total"]
        })

    return pd.DataFrame(linhas_tratadas)

# =============================================================================
# FLUXO PRINCIPAL
# =============================================================================
def main():
    parser = argparse.ArgumentParser(description="Consulta, Backup e Tratamento dos Resultados da Batch API")
    parser.add_argument("--status", action="store_true", help="Apenas consultar o status atual dos jobs no controle")
    parser.add_argument("--forcar", action="store_true", help="Forçar download e reprocessamento de todos os lotes")
    parser.add_argument("--simular", action="store_true", help="Simula o fluxo de tratamento com dados sintéticos locais")
    args = parser.parse_args()

    api_key = carregar_openrouter_key()
    if not api_key:
        logging.warning("Chave OPEN_ROUTER_API_KEY_2 não encontrada. Apenas modo offline ou status local disponível.")

    if not os.path.exists(ARQUIVO_CONTROLE):
        logging.warning(f"Arquivo de controle '{ARQUIVO_CONTROLE}' ainda não existe.")
        logging.info("Envie chamadas primeiro com 'enviar_chamadas.py'.")
        return

    with open(ARQUIVO_CONTROLE, 'r', encoding='utf-8') as f:
        controle = json.load(f)

    if not controle:
        logging.info("Nenhum job registrado no arquivo de controle.")
        return

    logging.info(f"Jobs registrados no controle: {len(controle)}")
    for mod, info in controle.items():
        logging.info(f"  - {mod}: Batch ID '{info.get('batch_id')}' | Status: '{info.get('status')}'")

    if args.status:
        # Se solicitou apenas consulta via API dos status
        if not api_key:
            logging.error("É necessária a chave para consultar o status na API.")
            return
        logging.info("\nConsultando status atualizado de cada batch na OpenRouter API...")
        for mod, info in controle.items():
            b_id = info.get("batch_id")
            if not b_id:
                continue
            try:
                dados_atualizados = consultar_status_batch(api_key, b_id)
                novo_status = dados_atualizados.get("status")
                req_counts = dados_atualizados.get("request_counts", {})
                logging.info(f"  [{mod}] Status na API: {novo_status} | Contagens: {req_counts}")
                info["status"] = novo_status
                info["request_counts"] = req_counts
            except Exception as e:
                logging.error(f"  [{mod}] Erro ao consultar status de {b_id}: {e}")

        with open(ARQUIVO_CONTROLE, 'w', encoding='utf-8') as f:
            json.dump(controle, f, indent=2, ensure_ascii=False)
        return

    # Leitura do gabarito de operações de soma
    caminho_op = os.path.join(PASTA_ATUAL, 'operacoes_soma.csv')
    if not os.path.exists(caminho_op):
        caminho_op = os.path.join(PASTA_RAIZ, 'dados', 'operacoes_soma.csv')

    df_op = pd.read_csv(caminho_op) if os.path.exists(caminho_op) else pd.DataFrame()
    mapa_operacoes = {idx: row.to_dict() for idx, row in df_op.iterrows()}

    dfs_novos = []
    for mod, info in controle.items():
        b_id = info.get("batch_id")
        status_atual = info.get("status")

        if not b_id:
            continue

        arq_backup = os.path.join(BACKUP_DIR, f'respostas_brutas_{mod}_{b_id}.json')
        dados_lote = None

        # 1. Se já existe o backup em disco e não foi pedido para forçar novo download
        if os.path.exists(arq_backup) and not args.forcar:
            try:
                with open(arq_backup, 'r', encoding='utf-8') as fb:
                    dados_lote = json.load(fb)
                logging.info(f"[{mod}] Carregado backup bruto local: {arq_backup}")
            except Exception as e:
                logging.warning(f"[{mod}] Erro ao ler backup local: {e}. Consultando API...")

        # 2. Se não temos os dados locais (ou --forcar ativo), busca na API
        if (dados_lote is None or args.forcar) and api_key:
            try:
                logging.info(f"[{mod}] Consultando batch {b_id} na OpenRouter API...")
                dados_lote = consultar_status_batch(api_key, b_id)
                status_atual = dados_lote.get("status")
                info["status"] = status_atual
                info["request_counts"] = dados_lote.get("request_counts", {})

                if status_atual == "completed":
                    with open(arq_backup, 'w', encoding='utf-8') as fb:
                        json.dump(dados_lote, fb, indent=2, ensure_ascii=False)
                    logging.info(f"[{mod}] Backup bruto salvo com sucesso em: {arq_backup}")
                else:
                    logging.info(f"[{mod}] Lote ainda em status '{status_atual}'. Aguardando conclusão.")
            except Exception as e:
                logging.error(f"[{mod}] Erro ao consultar batch {b_id} na API: {e}")

        # 3. Processar lote se estiver concluído
        if dados_lote and dados_lote.get("status") == "completed":
            logging.info(f"[{mod}] Processando respostas do lote {b_id}...")
            df_tratado = processar_lote_concluido(mod, b_id, dados_lote, mapa_operacoes)
            dfs_novos.append(df_tratado)
            info["processado"] = True
            info["status"] = "completed"
            info["total_processado"] = len(df_tratado)
            logging.info(f"[{mod}] Processado com sucesso: {len(df_tratado)} operações.")
        elif not dados_lote:
            logging.warning(f"[{mod}] Dados não disponíveis no momento.")

    with open(ARQUIVO_CONTROLE, 'w', encoding='utf-8') as f:
        json.dump(controle, f, indent=2, ensure_ascii=False)

    if dfs_novos:
        df_consolidado = pd.concat(dfs_novos, ignore_index=True)
        destinos = [
            os.path.join(PASTA_RAIZ, 'dados', 'resultados_gemini_soma_openrouter.csv'),
            os.path.join(PASTA_ATUAL, 'resultados_gemini_soma_openrouter.csv'),
            os.path.join(PASTA_RAIZ, 'github_repo', 'dados', 'resultados_gemini_soma_openrouter.csv'),
            os.path.join(PASTA_RAIZ, 'github_repo', 'gemini', 'openrouter', 'operacoes_soma', 'resultados_gemini_soma_openrouter.csv')
        ]
        for dest in destinos:
            os.makedirs(os.path.dirname(dest), exist_ok=True)
            if os.path.exists(dest) and not args.forcar:
                df_antigo = pd.read_csv(dest)
                df_salvar = pd.concat([df_antigo, df_consolidado], ignore_index=True).drop_duplicates(subset=["Nome_do_modelo", "Conta"], keep="last")
            else:
                df_salvar = df_consolidado
            df_salvar.to_csv(dest, index=False)
            logging.info(f"Base final atualizada com sucesso em: {dest} ({len(df_salvar)} linhas)")
    else:
        logging.info("Nenhum novo lote concluído para processar.")

if __name__ == '__main__':
    main()

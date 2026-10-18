"""Módulo de Execução do Experimento Complementar: JEV (TypeSafe Decision Model)

Este script:
1. Carrega a base consolidada de 1.800 amostras em 'jev/bases_de_dados/base_jev_completa.csv'
   (4 operações x 9 dígitos x 50 amostras: 25 verdadeiras e 25 falsas).
2. Conecta ao endpoint Decisions do OpenRouter ('https://openrouter.ai/api/alpha/decisions').
3. Para cada amostra, formula a requisição de decisão:
   - Question Type: 'noul' (probabilidade de True / Sim) ou 'choice' (['correta', 'incorreta']).
   - Avalia a expressão com o prompt fixo solicitado.
4. Coleta as probabilidades calibradas emitidas pelo modelo:
   - prob_positivo (probabilidade de a expressão estar correta)
   - prob_negativo (probabilidade de a expressão estar incorreta)
5. Classifica o resultado:
   - Decisão do Modelo (True se prob_positivo >= 0.5, False caso contrário)
   - Acerto da Avaliação (Decisão == Rótulo Verdadeiro)
   - Sensibilidade: Identificação correta quando expressão é VERDADEIRA (TP)
   - Especificidade: Identificação correta quando expressão é FALSA (TN)
6. Salva logs em 'jev/logs/', backup bruto em 'jev/resultados/respostas_brutas_jev.jsonl'
   e base tabular final tratada em 'jev/resultados/resultados_jev.csv'.
"""

import os
import sys
import json
import time
import logging
import argparse
from datetime import datetime
import requests
import pandas as pd
from dotenv import load_dotenv

PASTA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
PASTA_JEV = os.path.dirname(PASTA_SCRIPT)
PASTA_RAIZ = os.path.dirname(PASTA_JEV)

BASES_DIR = os.path.join(PASTA_JEV, "bases_de_dados")
RESULTADOS_DIR = os.path.join(PASTA_JEV, "resultados")
LOGS_DIR = os.path.join(PASTA_JEV, "logs")

os.makedirs(RESULTADOS_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

data_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = os.path.join(LOGS_DIR, f"execucao_jev_{data_hora}.log")

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(log_filename, encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logging.info("=== Inicializando Módulo de Execução do Experimento JEV ===")

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

ARQUIVO_BASE = os.path.join(BASES_DIR, "base_jev_completa.csv")
ARQUIVO_RESULTADOS = os.path.join(RESULTADOS_DIR, "resultados_jev.csv")
ARQUIVO_BRUTO_JSONL = os.path.join(RESULTADOS_DIR, "respostas_brutas_jev.jsonl")

MODELO_JEV = "typesafe/jev-1.14"
URL_DECISIONS = "https://openrouter.ai/api/alpha/decisions"

def avaliar_amostra_jev(api_key, id_amostra, expressao_completa, tipo_op, digitos_num):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://tcc-experimento.ufba.br",
        "X-Title": "Experimento Complementar JEV Decision"
    }

    payload = {
        "model": MODELO_JEV,
        "state": {
            "expressao_matematica": expressao_completa,
            "tipo_operacao": tipo_op,
            "digitos": digitos_num
        },
        "questions": {
            "expressao_correta": {
                "type": "noul",
                "instructions": (
                    "A seguinte expressão matemática está correta?\n\n"
                    f"{expressao_completa}"
                )
            }
        }
    }

    t0 = time.time()
    resp = requests.post(URL_DECISIONS, headers=headers, json=payload, timeout=30)
    duracao_ms = round((time.time() - t0) * 1000, 2)

    if resp.status_code == 200:
        dados = resp.json()
        return dados, duracao_ms, None
    else:
        return None, duracao_ms, f"Status {resp.status_code}: {resp.text}"

def extrair_probabilidades(dados_resp):
    """Extrai probabilidade de True e False do retorno de decisions."""
    try:
        # Formato padrão OpenRouter Decisions para tipo noul
        decisao_obj = dados_resp.get("response", {}).get("expressao_correta", {})
        prob_positivo = float(decisao_obj.get("probability", 0.5))
        prob_negativo = round(1.0 - prob_positivo, 6)
        resposta_bool = bool(decisao_obj.get("answer", prob_positivo >= 0.5))
        return prob_positivo, prob_negativo, resposta_bool
    except Exception:
        return 0.5, 0.5, True

def main():
    parser = argparse.ArgumentParser(description="Executar Experimento JEV")
    parser.add_argument("--limite", type=int, default=None, help="Executar apenas N amostras para teste")
    parser.add_argument("--operacao", type=str, default=None, help="Filtrar por operação específica")
    parser.add_argument("--dry-run", action="store_true", help="Simular execução sem gastar créditos")
    args = parser.parse_args()

    api_key = carregar_openrouter_key()
    if not api_key:
        logging.error("ERRO: OPEN_ROUTER_API_KEY_2 não encontrada!")
        sys.exit(1)

    if not os.path.exists(ARQUIVO_BASE):
        logging.error(f"ERRO: Base de dados '{ARQUIVO_BASE}' não encontrada. Execute 'gerar_base_jev.py' primeiro.")
        sys.exit(1)

    df_base = pd.read_csv(ARQUIVO_BASE)
    logging.info(f"Base de dados carregada: {len(df_base)} amostras.")

    if args.operacao:
        df_base = df_base[df_base["tipo_operacao"].str.lower() == args.operacao.lower()].copy()
        logging.info(f"Filtrado por operação '{args.operacao}': {len(df_base)} amostras.")

    if args.limite:
        df_base = df_base.head(args.limite).copy()
        logging.info(f"Limitado a {args.limite} amostras para teste.")

    # Carregar resultados já concluídos para permitir retomada resiliente
    ids_concluidos = set()
    if os.path.exists(ARQUIVO_RESULTADOS):
        try:
            df_existente = pd.read_csv(ARQUIVO_RESULTADOS)
            ids_concluidos = set(df_existente["id_amostra"].tolist())
            logging.info(f"Encontradas {len(ids_concluidos)} amostras já processadas anteriormente.")
        except Exception:
            ids_concluidos = set()

    linhas_resultados = []

    logging.info(f"Iniciando ciclo de avaliações com modelo '{MODELO_JEV}'...")

    for idx, row in df_base.iterrows():
        id_am = row["id_amostra"]
        if id_am in ids_concluidos:
            continue

        expr_comp = row["expressao_completa"]
        tipo_op = row["tipo_operacao"]
        dig_num = row["digitos_num"]
        rotulo_verdadeiro = bool(row["rotulo_verdadeiro"])

        logging.info(f"[{id_am}] Avaliando: '{expr_comp}' ({tipo_op} - {dig_num} dígitos | Gabarito: {rotulo_verdadeiro})")

        if args.dry_run:
            # Modo simulação estruturada
            prob_pos = 0.95 if rotulo_verdadeiro else 0.05
            prob_neg = 1.0 - prob_pos
            pred_bool = prob_pos >= 0.5
            dur_ms = 45.0
            dados_resp = {"dry_run": True, "prob_positivo": prob_pos}
            erro = None
        else:
            dados_resp, dur_ms, erro = avaliar_amostra_jev(api_key, id_am, expr_comp, tipo_op, dig_num)
            if erro:
                logging.error(f"[{id_am}] Falha na chamada da API: {erro}")
                continue
            prob_pos, prob_neg, pred_bool = extrair_probabilidades(dados_resp)

        # Salvar backup bruto em JSONL imediatamente
        with open(ARQUIVO_BRUTO_JSONL, "a", encoding="utf-8") as f_jsonl:
            registro_bruto = {
                "id_amostra": id_am,
                "timestamp": datetime.now().isoformat(),
                "expressao_completa": expr_comp,
                "rotulo_verdadeiro": rotulo_verdadeiro,
                "prob_positivo": prob_pos,
                "prob_negativo": prob_neg,
                "decisao_modelo": pred_bool,
                "duracao_ms": dur_ms,
                "resposta_api": dados_resp
            }
            f_jsonl.write(json.dumps(registro_bruto, ensure_ascii=False) + "\n")

        # Classificação estatística (Matriz de Confusão e Métricas)
        # Sensibilidade: TP quando rotulo é True e pred é True
        # Especificidade: TN quando rotulo é False e pred é False
        acerto_avaliacao = (pred_bool == rotulo_verdadeiro)

        if rotulo_verdadeiro and pred_bool:
            classificacao = "Verdadeiro Positivo (TP)"
        elif not rotulo_verdadeiro and not pred_bool:
            classificacao = "Verdadeiro Negativo (TN)"
        elif not rotulo_verdadeiro and pred_bool:
            classificacao = "Falso Positivo (FP)"
        else:
            classificacao = "Falso Negativo (FN)"

        linha_res = {
            "id_amostra": id_am,
            "tipo_operacao": tipo_op,
            "quantidade_digitos": f"{dig_num} dígitos",
            "digitos_num": dig_num,
            "expressao": row["expressao"],
            "resultado_avaliado": row["resultado_avaliado"],
            "resultado_correto": row["resultado_correto"],
            "expressao_completa": expr_comp,
            "rotulo_verdadeiro": rotulo_verdadeiro,
            "tipo_expressao": row["tipo_expressao"],
            "decisao_modelo": pred_bool,
            "prob_positivo": round(prob_pos * 100.0, 2), # em porcentagem 0-100 para os gráficos
            "prob_negativo": round(prob_neg * 100.0, 2),
            "acerto_avaliacao": acerto_avaliacao,
            "classificacao_matriz": classificacao,
            "tempo_resposta_ms": dur_ms
        }
        linhas_resultados.append(linha_res)

        # Salvar incrementalmente a cada 10 amostras
        if len(linhas_resultados) % 10 == 0:
            df_atual = pd.DataFrame(linhas_resultados)
            if os.path.exists(ARQUIVO_RESULTADOS):
                df_antigo = pd.read_csv(ARQUIVO_RESULTADOS)
                df_salvar = pd.concat([df_antigo, df_atual], ignore_index=True).drop_duplicates(subset=["id_amostra"], keep="last")
            else:
                df_salvar = df_atual
            df_salvar.to_csv(ARQUIVO_RESULTADOS, index=False)
            logging.info(f"Progresso salvo: {len(df_salvar)} amostras consolidadas.")

    if linhas_resultados:
        df_atual = pd.DataFrame(linhas_resultados)
        if os.path.exists(ARQUIVO_RESULTADOS):
            df_antigo = pd.read_csv(ARQUIVO_RESULTADOS)
            df_salvar = pd.concat([df_antigo, df_atual], ignore_index=True).drop_duplicates(subset=["id_amostra"], keep="last")
        else:
            df_salvar = df_atual
        df_salvar.to_csv(ARQUIVO_RESULTADOS, index=False)
        logging.info(f"Experimento JEV concluído com SUCESSO! Total final: {len(df_salvar)} amostras salvas em {ARQUIVO_RESULTADOS}")

if __name__ == "__main__":
    main()

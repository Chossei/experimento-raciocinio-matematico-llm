"""Script de Geração da Base de Dados para o Experimento Complementar (JEV)

Este script:
1. Lê os dados das 4 modalidades (Soma, Multiplicação Inteira, Multiplicação Decimal, Expressões Combinadas)
   diretamente das bases de resultados dos experimentos anteriores (onde estão todas as operações, gabaritos
   e os erros reais cometidos por todos os modelos).
2. Para cada modalidade e para cada quantidade de dígitos (2 a 10 dígitos), gera exatamente 100 amostras:
   - 50 Expressões Verdadeiras (com o gabarito matemático exato: expressao = resultado_correto).
   - 50 Expressões Falsas (expressao = resultado_falso):
     * Primeiro, busca respostas incorretas emitidas por modelos nos experimentos anteriores.
     * Caso não haja erro disponível (ou a conta tenha tido 100% de acertos), aplica a perturbação estrita:
       sorteia um número aleatório entre 1 e a segunda casa decimal do resultado e soma ao resultado.
3. Constrói o prompt padronizado do JEV:
   "A seguinte expressão matemática está correta?

   [expressão]=[resultado]"
4. Salva a base completa consolidada (3.600 amostras: 1.800 verdadeiras e 1.800 falsas) e as bases
   segmentadas por operação em 'jev/bases_de_dados/' e sincroniza com 'github_repo/jev/bases_de_dados/'.
"""

import os
import re
import json
import logging
import numpy as np
import pandas as pd
from decimal import Decimal, getcontext

getcontext().prec = 100

# Fixar seed para reprodutibilidade científica absoluta
np.random.seed(42)

PASTA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
PASTA_JEV = os.path.dirname(PASTA_SCRIPT)
PASTA_RAIZ = os.path.dirname(PASTA_JEV)

BASES_DIR = os.path.join(PASTA_JEV, "bases_de_dados")
LOGS_DIR = os.path.join(PASTA_JEV, "logs")
os.makedirs(BASES_DIR, exist_ok=True)
os.makedirs(LOGS_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, "geracao_base_jev.log"), encoding="utf-8"),
        logging.StreamHandler()
    ]
)

logging.info("=== Iniciando geração da base de dados do experimento JEV (100 chamadas por dígito: 50/50) ===")

CAMINHOS_RESULTADOS = {
    "Soma": os.path.join(PASTA_RAIZ, "repo_dashboard", "dados", "resultados_soma.csv"),
    "Multiplicação Inteira": os.path.join(PASTA_RAIZ, "repo_dashboard", "dados", "resultados_multiplicacao.csv"),
    "Multiplicação Decimal": os.path.join(PASTA_RAIZ, "repo_dashboard", "dados", "resultados_decimal.csv"),
    "Expressões Combinadas": os.path.join(PASTA_RAIZ, "repo_dashboard", "dados", "resultados_combinadas.csv")
}

def normalizar_conta_str(conta_str):
    """Remove sufixos de pergunta como '= ?' ou '=' para obter apenas a expressão matemática."""
    c = str(conta_str).strip()
    c = re.sub(r"\s*=\s*\?\s*$", "", c)
    c = re.sub(r"\s*=\s*$", "", c)
    return c.strip()

def perturbar_resultado(resultado_original_str):
    """Aplica a regra de perturbação metodológica solicitada:
    Sorteia um número aleatório entre 1 e a segunda casa decimal do resultado e soma ao resultado.
    Exemplo do documento: resultado = 24678 -> sorteia entre 1 e 4678 (ex: 3000) -> 24678 + 3000 = 27678.
    """
    res_str = str(resultado_original_str).strip()
    if "." in res_str:
        # Decimal
        try:
            d = Decimal(res_str)
            inteiro_str = str(abs(int(d)))
            if len(inteiro_str) >= 2:
                segunda_casa = int(inteiro_str[1:]) if int(inteiro_str[1:]) > 1 else 10
            else:
                segunda_casa = 10
            delta = Decimal(str(np.random.randint(1, max(2, segunda_casa))))
            novo_res = d + delta
            return str(novo_res)
        except Exception:
            return str(Decimal(res_str) + Decimal("3.14"))
    else:
        # Inteiro
        try:
            if len(res_str) >= 2:
                segunda_parte = res_str[1:]
                lim_sup = int(segunda_parte) if int(segunda_parte) > 1 else 9
            else:
                lim_sup = 9
            delta = np.random.randint(1, max(2, lim_sup + 1))
            novo_res = int(res_str) + delta
            return str(novo_res)
        except Exception:
            return str(int(res_str) + 7)

def gerar_amostras_para_operacao(tipo_op, path_resultados):
    logging.info(f"Processando operação: {tipo_op} a partir de {path_resultados}")
    df = pd.read_csv(path_resultados)

    col_conta = [c for c in df.columns if "conta" in c.lower()][0]
    col_res_orig = [c for c in df.columns if "original" in c.lower()][0]
    col_dig = [c for c in df.columns if "digito" in c.lower() or c.lower() in ["operacao", "tipo"]][0]
    col_acerto = [c for c in df.columns if "acerto" in c.lower() and "operacao" in c.lower()][0]
    col_mod_res = [c for c in df.columns if "resultado" in c.lower() and ("modelo" in c.lower() or "bruto" in c.lower())][0]

    # Mapear erros reais dos modelos por conta normalizada
    df_erros = df[df[col_acerto].astype(str).str.lower().isin(["false", "0"])].copy()
    erros_mapa = {}
    for _, row_err in df_erros.iterrows():
        c_norm = normalizar_conta_str(row_err[col_conta])
        resp_val = str(row_err[col_mod_res]).strip()
        if resp_val and resp_val.lower() not in ["none", "nan", ""]:
            erros_mapa.setdefault(c_norm, []).append(resp_val)

    # Identificar e ordenar os dígitos (2 a 10)
    digitos_unicos = df[col_dig].unique()
    digitos_ordenados = sorted(
        [d for d in digitos_unicos if re.search(r"\d+", str(d)) and 2 <= int(re.search(r"\d+", str(d)).group()) <= 10],
        key=lambda x: int(re.search(r"\d+", str(x)).group())
    )

    amostras_op = []
    total_erros_reais = 0
    total_perturbados = 0

    for dig_rotulo in digitos_ordenados:
        dig_num = int(re.search(r"\d+", str(dig_rotulo)).group())
        df_dig = df[df[col_dig] == dig_rotulo].drop_duplicates(subset=[col_conta]).copy().reset_index(drop=True)

        if len(df_dig) < 50:
            logging.warning(f"[{tipo_op}] Menos de 50 operações únicas para {dig_rotulo}: {len(df_dig)}")

        df_selecionadas = df_dig.head(50).copy()

        # 1. 50 Expressões Verdadeiras
        for _, row in df_selecionadas.iterrows():
            conta_raw = row[col_conta]
            expressao = normalizar_conta_str(conta_raw)
            res_correto = str(row[col_res_orig]).strip()

            expressao_completa = f"{expressao} = {res_correto}"
            prompt_jev = f"A seguinte expressão matemática está correta?\n\n{expressao_completa}"

            amostras_op.append({
                "tipo_operacao": tipo_op,
                "quantidade_digitos": f"{dig_num} dígitos",
                "digitos_num": dig_num,
                "conta_original": conta_raw,
                "expressao": expressao,
                "resultado_correto": res_correto,
                "resultado_avaliado": res_correto,
                "expressao_completa": expressao_completa,
                "rotulo_verdadeiro": True,
                "tipo_expressao": "VERDADEIRA",
                "origem_resultado": "gabarito_correto",
                "prompt_jev": prompt_jev
            })

        # 2. 50 Expressões Falsas
        for _, row in df_selecionadas.iterrows():
            conta_raw = row[col_conta]
            expressao = normalizar_conta_str(conta_raw)
            res_correto = str(row[col_res_orig]).strip()

            erros_disponiveis = [e for e in erros_mapa.get(expressao, []) if e != res_correto]
            if erros_disponiveis:
                res_falso = np.random.choice(erros_disponiveis)
                origem = "erro_modelo_anterior"
                total_erros_reais += 1
            else:
                res_falso = perturbar_resultado(res_correto)
                if res_falso == res_correto:
                    res_falso = str(int(res_correto) + 1 if "." not in res_correto else Decimal(res_correto) + Decimal("1"))
                origem = "perturbacao_numpy"
                total_perturbados += 1

            expressao_completa = f"{expressao} = {res_falso}"
            prompt_jev = f"A seguinte expressão matemática está correta?\n\n{expressao_completa}"

            amostras_op.append({
                "tipo_operacao": tipo_op,
                "quantidade_digitos": f"{dig_num} dígitos",
                "digitos_num": dig_num,
                "conta_original": conta_raw,
                "expressao": expressao,
                "resultado_correto": res_correto,
                "resultado_avaliado": res_falso,
                "expressao_completa": expressao_completa,
                "rotulo_verdadeiro": False,
                "tipo_expressao": "FALSA",
                "origem_resultado": origem,
                "prompt_jev": prompt_jev
            })

    df_resultado = pd.DataFrame(amostras_op)
    logging.info(
        f"[{tipo_op}] Concluído: {len(df_resultado)} amostras "
        f"(Verdadeiras: 450, Falsas: 450 | Erros Reais: {total_erros_reais}, Perturbados: {total_perturbados})"
    )
    return df_resultado

def main():
    todas_amostras = []

    for tipo_op, p_res in CAMINHOS_RESULTADOS.items():
        df_op_gerado = gerar_amostras_para_operacao(tipo_op, p_res)
        
        # Salvar base individual por operação
        slug_op = tipo_op.lower().replace(" ", "_").replace("ç", "c").replace("ã", "a").replace("õ", "o").replace("é", "e")
        p_save_op = os.path.join(BASES_DIR, f"base_jev_{slug_op}.csv")
        df_op_gerado.to_csv(p_save_op, index=False)
        logging.info(f"Salva base individual: {p_save_op}")

        todas_amostras.append(df_op_gerado)

    # Base consolidada
    df_consolidada = pd.concat(todas_amostras, ignore_index=True)
    df_consolidada["id_amostra"] = [f"JEV_{i+1:04d}" for i in range(len(df_consolidada))]

    cols = [
        "id_amostra", "tipo_operacao", "quantidade_digitos", "digitos_num",
        "conta_original", "expressao", "resultado_correto", "resultado_avaliado",
        "expressao_completa", "rotulo_verdadeiro", "tipo_expressao",
        "origem_resultado", "prompt_jev"
    ]
    df_consolidada = df_consolidada[cols]

    p_save_total = os.path.join(BASES_DIR, "base_jev_completa.csv")
    df_consolidada.to_csv(p_save_total, index=False)
    logging.info(f"Base consolidada do JEV salva com SUCESSO: {p_save_total} ({len(df_consolidada)} amostras)")

    # Sincronizar cópia em github_repo/jev/bases_de_dados
    p_github_bases = os.path.join(PASTA_RAIZ, "github_repo", "jev", "bases_de_dados")
    os.makedirs(p_github_bases, exist_ok=True)
    df_consolidada.to_csv(os.path.join(p_github_bases, "base_jev_completa.csv"), index=False)
    logging.info(f"Cópia sincronizada em github_repo: {os.path.join(p_github_bases, 'base_jev_completa.csv')}")

if __name__ == "__main__":
    main()

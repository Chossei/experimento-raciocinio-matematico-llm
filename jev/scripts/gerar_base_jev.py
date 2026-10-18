"""Script de Geração da Base de Dados para o Experimento Complementar (JEV)

Este script:
1. Lê as operações das 4 modalidades (Soma, Multiplicação Inteira, Multiplicação Decimal, Expressões Combinadas).
2. Para cada modalidade e para cada nível de dígitos (2 a 10 dígitos), gera 50 amostras:
   - 25 Expressões Verdadeiras (com o gabarito matemático exato via Decimal).
   - 25 Expressões Falsas:
     * Primeiro, busca respostas incorretas emitidas por modelos no experimento anterior.
     * Caso não haja erro disponível, aplica a perturbação estrita: sorteia um número aleatório
       entre 1 e a segunda casa decimal do resultado e soma ao resultado.
3. Constrói o prompt padronizado do JEV:
   "A seguinte expressão matemática está correta?

   [expressão]=[resultado]"
4. Salva a base completa consolidada e as bases segmentadas por operação em 'jev/bases_de_dados/'.
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

logging.info("=== Iniciando geração da base de dados do experimento JEV ===")

# Caminhos dos arquivos de operações e resultados anteriores
CAMINHOS_OPERACOES = {
    "Soma": os.path.join(PASTA_RAIZ, "3° Fase", "operacoes", "operacoes_soma.csv"),
    "Multiplicação Inteira": os.path.join(PASTA_RAIZ, "3° Fase", "operacoes", "operacoes_multiplicacao.csv"),
    "Multiplicação Decimal": os.path.join(PASTA_RAIZ, "3° Fase", "operacoes", "operacoes_decimal.csv"),
    "Expressões Combinadas": os.path.join(PASTA_RAIZ, "3° Fase", "operacoes", "operacoes_combinadas.csv")
}

CAMINHOS_RESULTADOS_ANTERIORES = {
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
            # Para decimais, perturba a parte inteira ou a primeira fração
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
                # segunda casa do resultado em diante
                segunda_parte = res_str[1:]
                lim_sup = int(segunda_parte) if int(segunda_parte) > 1 else 9
            else:
                lim_sup = 9
            delta = np.random.randint(1, max(2, lim_sup + 1))
            novo_res = int(res_str) + delta
            return str(novo_res)
        except Exception:
            return str(int(res_str) + 7)

def gerar_amostras_para_operacao(tipo_op, path_operacoes, path_resultados):
    logging.info(f"Processando operação: {tipo_op}")
    df_op = pd.read_csv(path_operacoes)

    # Carregar resultados anteriores para coletar erros reais de modelos
    df_res_ant = pd.read_csv(path_resultados) if os.path.exists(path_resultados) else pd.DataFrame()

    erros_mapa = {}
    if not df_res_ant.empty:
        # Encontrar colunas de acerto e resposta do modelo
        col_acerto = [c for c in df_res_ant.columns if "acerto" in c.lower() and "operacao" in c.lower()][0]
        col_resposta = [c for c in df_res_ant.columns if "resultado" in c.lower() and ("modelo" in c.lower() or "bruto" in c.lower())][0]
        col_conta = [c for c in df_res_ant.columns if "conta" in c.lower()][0]

        df_erros = df_res_ant[df_res_ant[col_acerto].astype(str).str.lower().isin(["false", "0"])].copy()
        for _, row_err in df_erros.iterrows():
            c_norm = normalizar_conta_str(row_err[col_conta])
            resp_val = str(row_err[col_resposta]).strip()
            # filtrar apenas respostas numéricas válidas e distintas de None
            if resp_val and resp_val.lower() not in ["none", "nan", ""]:
                if c_norm not in erros_mapa:
                    erros_mapa[c_norm] = []
                erros_mapa[c_norm].append(resp_val)

    amostras_op = []

    # Determinar coluna de quantidade de dígitos
    col_dig = [c for c in df_op.columns if "digito" in c.lower() or "tipo" in c.lower()][0]
    col_res_orig = [c for c in df_op.columns if "resultado" in c.lower() and ("operacao" in c.lower() or "original" in c.lower() or c.lower() == "resultado")][0]
    col_conta_orig = [c for c in df_op.columns if "conta" in c.lower() or "string" in c.lower()][0]

    digitos_unicos = df_op[col_dig].unique()
    # Ordenar numericamente por dígitos (2 a 10)
    digitos_ordenados = sorted(digitos_unicos, key=lambda x: int(re.search(r"\d+", str(x)).group()) if re.search(r"\d+", str(x)) else 0)

    for dig_rotulo in digitos_ordenados:
        dig_num = int(re.search(r"\d+", str(dig_rotulo)).group())
        df_dig = df_op[df_op[col_dig] == dig_rotulo].copy().reset_index(drop=True)

        if len(df_dig) < 50:
            logging.warning(f"[{tipo_op}] Menos de 50 operações para {dig_rotulo}: {len(df_dig)}")

        # Selecionar exatamente 50 operações: 25 para Verdadeiras e 25 para Falsas
        indices = list(range(len(df_dig)))
        np.random.shuffle(indices)

        idx_verdadeiras = indices[:25]
        idx_falsas = indices[25:50]

        # 1. 25 Expressões Verdadeiras
        for idx in idx_verdadeiras:
            row = df_dig.iloc[idx]
            conta_raw = row[col_conta_orig]
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

        # 2. 25 Expressões Falsas
        for idx in idx_falsas:
            row = df_dig.iloc[idx]
            conta_raw = row[col_conta_orig]
            expressao = normalizar_conta_str(conta_raw)
            res_correto = str(row[col_res_orig]).strip()

            # Verificar se temos erro de modelo anterior
            erros_disponiveis = [e for e in erros_mapa.get(expressao, []) if e != res_correto]
            if erros_disponiveis:
                # Escolher um erro real de modelo
                res_falso = np.random.choice(erros_disponiveis)
                origem = "erro_modelo_anterior"
            else:
                # Aplicar fórmula de perturbação
                res_falso = perturbar_resultado(res_correto)
                if res_falso == res_correto:
                    res_falso = str(int(res_correto) + 1 if "." not in res_correto else Decimal(res_correto) + Decimal("1"))
                origem = "perturbacao_numpy"

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
    logging.info(f"[{tipo_op}] Total gerado: {len(df_resultado)} amostras (Verdadeiras: {(df_resultado['tipo_expressao'] == 'VERDADEIRA').sum()}, Falsas: {(df_resultado['tipo_expressao'] == 'FALSA').sum()})")
    return df_resultado

def main():
    todas_amostras = []

    for tipo_op, p_op in CAMINHOS_OPERACOES.items():
        p_res = CAMINHOS_RESULTADOS_ANTERIORES[tipo_op]
        df_op_gerado = gerar_amostras_para_operacao(tipo_op, p_op, p_res)
        
        # Salvar base individual por operação
        slug_op = tipo_op.lower().replace(" ", "_").replace("ç", "c").replace("ã", "a")
        p_save_op = os.path.join(BASES_DIR, f"base_jev_{slug_op}.csv")
        df_op_gerado.to_csv(p_save_op, index=False)
        logging.info(f"Salva base individual: {p_save_op}")

        todas_amostras.append(df_op_gerado)

    # Base consolidada
    df_consolidada = pd.concat(todas_amostras, ignore_index=True)
    df_consolidada["id_amostra"] = [f"JEV_{i+1:04d}" for i in range(len(df_consolidada))]

    # Reordenar colunas
    cols = ["id_amostra", "tipo_operacao", "quantidade_digitos", "digitos_num", "conta_original", "expressao", "resultado_correto", "resultado_avaliado", "expressao_completa", "rotulo_verdadeiro", "tipo_expressao", "origem_resultado", "prompt_jev"]
    df_consolidada = df_consolidada[cols]

    p_save_total = os.path.join(BASES_DIR, "base_jev_completa.csv")
    df_consolidada.to_csv(p_save_total, index=False)
    logging.info(f"Base consolidada do JEV salva com SUCESSO: {p_save_total} ({len(df_consolidada)} amostras)")

    # Também salvar cópia em github_repo/jev/bases_de_dados
    p_github_bases = os.path.join(PASTA_RAIZ, "github_repo", "jev", "bases_de_dados")
    os.makedirs(p_github_bases, exist_ok=True)
    df_consolidada.to_csv(os.path.join(p_github_bases, "base_jev_completa.csv"), index=False)
    logging.info(f"Cópia sincronizada em github_repo: {os.path.join(p_github_bases, 'base_jev_completa.csv')}")

if __name__ == "__main__":
    main()

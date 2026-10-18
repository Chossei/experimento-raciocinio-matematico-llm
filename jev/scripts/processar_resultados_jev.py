"""Módulo de Processamento e Consolidação Estatística - Experimento JEV

Calcula as métricas necessárias para a página do Dashboard Streamlit:
1. Sensibilidade (Taxa de acerto em expressões verdadeiras).
2. Especificidade (Taxa de acerto em expressões falsas).
3. Acurácia Global por operação e por nível de complexidade (dígitos).
4. Curvas de Probabilidade Média (Positivo em verdadeiras vs Negativo em falsas).
5. Consolida em 'jev/resultados/metricas_jev_consolidadas.csv'.
"""

import os
import sys
import logging
import pandas as pd
import numpy as np

PASTA_SCRIPT = os.path.dirname(os.path.abspath(__file__))
PASTA_JEV = os.path.dirname(PASTA_SCRIPT)
PASTA_RAIZ = os.path.dirname(PASTA_JEV)

RESULTADOS_DIR = os.path.join(PASTA_JEV, "resultados")
ARQUIVO_RESULTADOS = os.path.join(RESULTADOS_DIR, "resultados_jev.csv")
ARQUIVO_METRICAS = os.path.join(RESULTADOS_DIR, "metricas_jev_consolidadas.csv")

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

def calcular_metricas(df):
    if df.empty:
        logging.warning("Dataframe vazio.")
        return pd.DataFrame()

    linhas_metricas = []

    # 1. Por Tipo de Operação e Quantidade de Dígitos
    for (tipo_op, digitos_num), sub_df in df.groupby(["tipo_operacao", "digitos_num"]):
        qtd_digitos = f"{digitos_num} dígitos"
        
        # Subconjunto de expressões verdadeiras
        df_verdadeiras = sub_df[sub_df["rotulo_verdadeiro"] == True]
        total_verdadeiras = len(df_verdadeiras)
        acertos_verdadeiras = (df_verdadeiras["decisao_modelo"] == True).sum()
        sensibilidade = (acertos_verdadeiras / total_verdadeiras * 100.0) if total_verdadeiras > 0 else 0.0
        media_prob_positivo_verdadeiras = df_verdadeiras["prob_positivo"].mean() if total_verdadeiras > 0 else 0.0

        # Subconjunto de expressões falsas
        df_falsas = sub_df[sub_df["rotulo_verdadeiro"] == False]
        total_falsas = len(df_falsas)
        acertos_falsas = (df_falsas["decisao_modelo"] == False).sum()
        especificidade = (acertos_falsas / total_falsas * 100.0) if total_falsas > 0 else 0.0
        media_prob_negativo_falsas = df_falsas["prob_negativo"].mean() if total_falsas > 0 else 0.0

        # Métricas globais
        total_amostras = len(sub_df)
        total_acertos = (sub_df["acerto_avaliacao"] == True).sum()
        acuracia_global = (total_acertos / total_amostras * 100.0) if total_amostras > 0 else 0.0

        linhas_metricas.append({
            "tipo_operacao": tipo_op,
            "quantidade_digitos": qtd_digitos,
            "digitos_num": digitos_num,
            "total_amostras": total_amostras,
            "total_verdadeiras": total_verdadeiras,
            "total_falsas": total_falsas,
            "sensibilidade_pct": round(sensibilidade, 2),
            "especificidade_pct": round(especificidade, 2),
            "acuracia_global_pct": round(acuracia_global, 2),
            "media_prob_positivo_verdadeiras": round(media_prob_positivo_verdadeiras, 2),
            "media_prob_negativo_falsas": round(media_prob_negativo_falsas, 2)
        })

    df_metricas = pd.DataFrame(linhas_metricas).sort_values(by=["tipo_operacao", "digitos_num"])
    return df_metricas

def main():
    if not os.path.exists(ARQUIVO_RESULTADOS):
        logging.info(f"Arquivo '{ARQUIVO_RESULTADOS}' ainda não existe. Será gerado quando o experimento rodar.")
        return

    df = pd.read_csv(ARQUIVO_RESULTADOS)
    df_metricas = calcular_metricas(df)
    df_metricas.to_csv(ARQUIVO_METRICAS, index=False)
    logging.info(f"Métricas consolidadas salvas em: {ARQUIVO_METRICAS}")

if __name__ == "__main__":
    main()

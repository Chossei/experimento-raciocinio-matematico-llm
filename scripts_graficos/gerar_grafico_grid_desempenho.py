"""
Script para Geração do Gráfico Grid 5x2 (5 Linhas x 2 Colunas)
"Desempenho dos Modelos por Operação e Complexidade de Dígitos"
Com subtítulo indicando a configuração de reasoning (esforço de raciocínio) utilizada em cada modelo.

Salva os gráficos em alta resolução (PNG e PDF).
"""

import os
import sys
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.ticker as mtick

# Configuração de diretórios
PASTA_ATUAL = os.path.dirname(os.path.abspath(__file__))
PASTA_RAIZ = os.path.dirname(PASTA_ATUAL)
sys.path.insert(0, os.path.join(PASTA_RAIZ, "dashboard_streamlit"))

from utils.data_loader import carregar_todos_dados, MODELOS_GEMINI, REASONING_MODELOS, CORES_OPERACOES

# Diretório de saída dos gráficos
PASTA_GRAFICOS = os.path.join(PASTA_RAIZ, "graficos")
os.makedirs(PASTA_GRAFICOS, exist_ok=True)

# Cores e marcadores padronizados
CONFIG_OPERACOES = {
    "Multiplicação Inteira": {
        "cor": "#8b5cf6",      # Roxo
        "marker": "s",          # Quadrado
        "label": "Multiplicação Inteira"
    },
    "Multiplicação Decimal": {
        "cor": "#f97316",      # Laranja
        "marker": "o",          # Círculo
        "label": "Multiplicação Decimal"
    },
    "Soma": {
        "cor": "#3b82f6",      # Azul
        "marker": "o",          # Círculo
        "label": "Soma"
    },
    "Expressões Combinadas": {
        "cor": "#10b981",      # Verde Esmeralda
        "marker": "o",          # Círculo
        "label": "Expressões Combinadas"
    }
}

# Grid 5x2 ordenado estritamente conforme layout de referência
GRID_MODELOS = [
    ["gemini-2.5-flash", "gemini-2.5-pro"],
    ["gemini-3-flash-preview", "gemini-3.1-flash-lite"],
    ["gemini-3.1-pro-preview", "gemini-3.5-flash-lite"],
    ["gemini-3.5-flash", "gemini-3.6-flash"],
    ["gemini-3.7-flash", "gemini-3.8-flash"]
]

def gerar_grafico():
    print("Carregando base unificada de dados...")
    dfs = carregar_todos_dados()
    df_geral = dfs.get("geral", pd.DataFrame())

    if df_geral.empty:
        raise ValueError("Dados unificados vazios! Verifique os arquivos CSV na pasta dados.")

    # Configuração de estilo geral do Matplotlib
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = ["DejaVu Sans", "Arial", "Helvetica", "sans-serif"]
    plt.rcParams["axes.edgecolor"] = "#94a3b8"
    plt.rcParams["axes.linewidth"] = 0.8

    # Criação da figura 5x2 (espaço generoso no topo para título e legenda)
    fig, axes = plt.subplots(nrows=5, ncols=2, figsize=(11.5, 16), sharex=False, sharey=False)
    plt.subplots_adjust(top=0.90, bottom=0.05, left=0.09, right=0.95, hspace=0.45, wspace=0.18)

    # Título Principal Superior
    fig.suptitle(
        "Desempenho dos Modelos por Operação e Complexidade de Dígitos",
        fontsize=16,
        fontweight="bold",
        color="#0f172a",
        y=0.975
    )

    linhas_legenda = []
    rotulos_legenda = []

    # Iteração sobre o Grid 5x2
    for r in range(5):
        for c in range(2):
            ax = axes[r, c]
            modelo = GRID_MODELOS[r][c]
            reasoning_cfg = REASONING_MODELOS.get(modelo, "Reasoning: default")

            df_mod = df_geral[df_geral["Nome_do_modelo"] == modelo]

            # Plota cada uma das 4 operações
            for op_nome, op_cfg in CONFIG_OPERACOES.items():
                df_op = df_mod[df_mod["Tipo_Operacao"] == op_nome]
                if df_op.empty:
                    continue

                # Agrupamento por dígito numérico (2 a 10)
                df_op_calc = df_op.copy()
                df_op_calc["Digitos_Num"] = pd.to_numeric(df_op_calc["Digitos"], errors="coerce")
                res = (
                    df_op_calc.groupby("Digitos_Num")["Acerto_da_operacao"]
                    .agg(Total="count", Acertos="sum")
                    .reset_index()
                )
                res["Taxa_Acerto"] = (res["Acertos"] / res["Total"]) * 100
                res = res.sort_values(by="Digitos_Num")

                # Plot da linha
                linha, = ax.plot(
                    res["Digitos_Num"],
                    res["Taxa_Acerto"],
                    color=op_cfg["cor"],
                    marker=op_cfg["marker"],
                    markersize=4.2,
                    linewidth=1.75,
                    label=op_cfg["label"],
                    alpha=0.95
                )

                # Coletar elementos para a legenda global única
                if r == 0 and c == 0:
                    linhas_legenda.append(linha)
                    rotulos_legenda.append(op_cfg["label"])

            # Título do Subplot com Subtítulo de Reasoning
            titulo_texto = f"{modelo}\n({reasoning_cfg})"
            ax.set_title(
                titulo_texto,
                fontsize=10.5,
                fontweight="bold",
                color="#0f172a",
                pad=9,
                linespacing=1.2
            )

            # Estilo das grades e eixos
            ax.grid(True, linestyle=":", alpha=0.55, color="#cbd5e1")
            ax.set_xlim(1.7, 10.3)
            ax.set_ylim(-4, 104)

            # Garante que todos os subplots mostrem os números dos dígitos (2 a 10)
            ax.set_xticks(range(2, 11))
            ax.set_yticks([0, 25, 50, 75, 100])
            ax.yaxis.set_major_formatter(mtick.PercentFormatter(xmax=100, decimals=0))

            ax.tick_params(axis="both", which="both", labelsize=8.5, colors="#334155")

            # Labels de eixos
            if c == 0:
                ax.set_ylabel("Taxa de Acerto (%)", fontsize=9.2, fontweight="600", color="#334155", labelpad=6)
            if r == 4:
                ax.set_xlabel("Quantidade de Dígitos", fontsize=9.5, fontweight="600", color="#334155", labelpad=6)

    # Legenda Global Única no topo (centralizada, sem sobreposição com os primeiros cards)
    fig.legend(
        handles=linhas_legenda,
        labels=rotulos_legenda,
        loc="upper center",
        bbox_to_anchor=(0.515, 0.945),
        ncol=4,
        frameon=True,
        facecolor="#ffffff",
        edgecolor="#cbd5e1",
        framealpha=0.95,
        fontsize=9.2,
        handlelength=2.2,
        handletextpad=0.5,
        columnspacing=1.8
    )

    # Salvamento
    caminho_png = os.path.join(PASTA_GRAFICOS, "desempenho_modelos_por_operacao_grid_5x2.png")
    caminho_pdf = os.path.join(PASTA_GRAFICOS, "desempenho_modelos_por_operacao_grid_5x2.pdf")

    plt.savefig(caminho_png, dpi=300, bbox_inches="tight")
    plt.savefig(caminho_pdf, bbox_inches="tight")
    plt.close()

    print(f"Gráfico PNG de alta resolução gerado com sucesso: {caminho_png}")
    print(f"Gráfico vetorial PDF gerado com sucesso: {caminho_pdf}")
    return caminho_png, caminho_pdf

if __name__ == "__main__":
    gerar_grafico()

"""
Página 3: Custos, Formatos e Erros
Composta por 3 abas organizadas via st.tabs com gráficos Plotly Express:
1. Custos financeiros (Gráficos ampliados em 25% com proporção 1.25 : 0.75 e custos estritamente em USD)
2. Conformidade do formato de resposta (Gráfico ampliado em 25% com 1 casa decimal garantida)
3. Inspeção de erros (Diagnóstico granular com múltiplos filtros e busca textual)
"""

import sys
import os
import streamlit as st
import pandas as pd
import plotly.express as px

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_loader import (
    carregar_todos_dados,
    ORDEM_DIGITOS_NUM,
    MODELOS_GEMINI,
    COR_AZUL_PADRAO
)
from utils.styles import aplicar_estilos_globais

aplicar_estilos_globais()

# -----------------------------------------------------------------------------
# CABEÇALHO
# -----------------------------------------------------------------------------
st.markdown('<div class="dash-title">💰 Custos, Formatos e Inspeção de Erros</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="dash-subtitle">'
    'Relato financeiro do experimento (em USD), aderência dos modelos à restrição do formato de resposta estritamente numérico e diagnóstico dos padrões de falha cometidos pelos LLMs.'
    '</div>',
    unsafe_allow_html=True
)

dfs = carregar_todos_dados()

tab_custos, tab_formatos, tab_erros = st.tabs([
    "💵 Custos Financeiros",
    "📋 Conformidade do Formato de Resposta",
    "🔍 Inspeção de Erros"
])

# =============================================================================
# ABA 1: CUSTOS FINANCEIROS (APENAS EM DÓLAR USD - 25% MAIOR)
# =============================================================================
with tab_custos:
    st.markdown("### Avaliação de Custos Financeiros (OpenRouter & Vertex AI)")
    st.caption("Custos computados diretamente em Dólares Americanos ($ USD), sem conversão cambial.")

    col_c1, col_c2 = st.columns([1.25, 0.75])
    with col_c1:
        opcoes_op_custo = ["Todas as Operações", "Soma", "Multiplicação Inteira", "Multiplicação Decimal", "Expressões Combinadas"]
        tipo_custo_sel = st.selectbox("Selecione o tipo de operação:", opcoes_op_custo, key="sel_tipo_custo")
    with col_c2:
        opcoes_dig_custo = ["Todos os Dígitos"] + ORDEM_DIGITOS_NUM
        dig_custo_sel = st.selectbox("Selecione a quantidade de dígitos:", opcoes_dig_custo, key="sel_dig_custo")

    # Filtrar dataframe base
    if tipo_custo_sel == "Soma":
        df_c = dfs.get("soma", pd.DataFrame())
    elif tipo_custo_sel == "Multiplicação Inteira":
        df_c = dfs.get("multiplicacao", pd.DataFrame())
    elif tipo_custo_sel == "Multiplicação Decimal":
        df_c = dfs.get("decimal", pd.DataFrame())
    elif tipo_custo_sel == "Expressões Combinadas":
        df_c = dfs.get("combinadas", pd.DataFrame())
    else:
        df_c = dfs.get("geral", pd.DataFrame())

    if dig_custo_sel != "Todos os Dígitos" and not df_c.empty:
        df_c = df_c[df_c["Digitos"] == str(dig_custo_sel)]

    if not df_c.empty:
        total_gasto_usd = df_c["custo_total"].sum()

        col_m1, _ = st.columns([1.25, 0.75])
        with col_m1:
            st.metric("Custo Total no Recorte", f"${total_gasto_usd:.4f} USD")

        st.markdown("<br>", unsafe_allow_html=True)

        # Gráfico ampliado em 25% (st.columns([1.25, 0.75]))
        col_graf_c, _ = st.columns([1.25, 0.75])
        with col_graf_c:
            res_custos = (
                df_c.groupby("Nome_do_modelo")["custo_total"]
                .agg(Total_Gasto="sum", Total_Req="count")
                .reset_index()
            )

            fig_custos = px.bar(
                res_custos,
                x="Nome_do_modelo",
                y="Total_Gasto",
                category_orders={"Nome_do_modelo": MODELOS_GEMINI},
                color_discrete_sequence=[COR_AZUL_PADRAO],
                labels={
                    "Nome_do_modelo": "Modelo",
                    "Total_Gasto": "Custo Total ($ USD)"
                },
                title=f"Custo por Modelo - {tipo_custo_sel} ({dig_custo_sel})"
            )
            fig_custos.update_traces(
                texttemplate="$%{y:.4f}",
                textposition="outside",
                hovertemplate="<b>%{x}</b><br>Custo: $%{y:.4f} USD<extra></extra>"
            )
            fig_custos.update_layout(
                xaxis_tickangle=-45,
                xaxis=dict(automargin=True, title=None),
                yaxis=dict(title="Custo ($ USD)"),
                height=420,
                margin=dict(l=40, r=20, t=50, b=100)
            )
            st.plotly_chart(fig_custos, use_container_width=True)
    else:
        st.warning("Nenhum dado financeiro disponível para os filtros selecionados.")

# =============================================================================
# ABA 2: CONFORMIDADE DO FORMATO DE RESPOSTA (25% MAIOR E 1 CASA DECIMAL)
# =============================================================================
with tab_formatos:
    st.markdown("### Conformidade com a Instrução de Formato")
    st.markdown(
        "Avalia a capacidade dos modelos em cumprir a restrição instrucional: "
        "*'retorne o resultado somente em formato de número, sem unidades ou caracteres especiais'*. "
        "Respostas que incluíram texto explicativo adicional ou letras são contabilizadas como desconformes."
    )

    col_f1, col_f2 = st.columns([1.25, 0.75])
    with col_f1:
        tipo_formato_sel = st.selectbox("Selecione o tipo de operação:", opcoes_op_custo, key="sel_tipo_formato")
    with col_f2:
        dig_formato_sel = st.selectbox("Selecione a quantidade de dígitos:", opcoes_dig_custo, key="sel_dig_formato")

    # Filtrar dataframe base
    if tipo_formato_sel == "Soma":
        df_f = dfs.get("soma", pd.DataFrame())
    elif tipo_formato_sel == "Multiplicação Inteira":
        df_f = dfs.get("multiplicacao", pd.DataFrame())
    elif tipo_formato_sel == "Multiplicação Decimal":
        df_f = dfs.get("decimal", pd.DataFrame())
    elif tipo_formato_sel == "Expressões Combinadas":
        df_f = dfs.get("combinadas", pd.DataFrame())
    else:
        df_f = dfs.get("geral", pd.DataFrame())

    if dig_formato_sel != "Todos os Dígitos" and not df_f.empty:
        df_f = df_f[df_f["Digitos"] == str(dig_formato_sel)]

    if not df_f.empty:
        res_formato = (
            df_f.groupby("Nome_do_modelo")["Acerto_do_formato_de_resposta"]
            .agg(Total="count", Conformes="sum")
            .reset_index()
        )
        res_formato["Taxa_Conformidade"] = (res_formato["Conformes"] / res_formato["Total"]) * 100

        # Gráfico ampliado em 25% (st.columns([1.25, 0.75])) com 1 casa decimal
        col_graf_f, _ = st.columns([1.25, 0.75])
        with col_graf_f:
            fig_formato = px.bar(
                res_formato,
                x="Nome_do_modelo",
                y="Taxa_Conformidade",
                category_orders={"Nome_do_modelo": MODELOS_GEMINI},
                color_discrete_sequence=[COR_AZUL_PADRAO],
                labels={
                    "Nome_do_modelo": "Modelo",
                    "Taxa_Conformidade": "Conformidade de Formato (%)"
                },
                title=f"Taxa de Conformidade de Formato - {tipo_formato_sel} ({dig_formato_sel})"
            )
            fig_formato.update_traces(
                texttemplate="%{y:.1f}%",
                textposition="outside",
                hovertemplate="<b>%{x}</b><br>Conformidade: %{y:.1f}%<extra></extra>"
            )
            fig_formato.update_layout(
                xaxis_tickangle=-45,
                xaxis=dict(automargin=True, title=None),
                yaxis=dict(range=[0, 115], title="Conformidade (%)"),
                height=420,
                margin=dict(l=40, r=20, t=50, b=100)
            )
            st.plotly_chart(fig_formato, use_container_width=True)
    else:
        st.warning("Nenhum dado disponível para os filtros de formato selecionados.")

# =============================================================================
# ABA 3: INSPEÇÃO DE ERROS
# =============================================================================
with tab_erros:
    st.markdown("### Inspeção Qualitativa e Diagnóstico de Falhas")
    st.markdown(
        "Filtre e examine detalhadamente as respostas emitidas pelos modelos, "
        "comparando a resposta gerada com o gabarito original e avaliando a resposta bruta."
    )

    col_e1, col_e2, col_e3, col_e4 = st.columns(4)
    with col_e1:
        opcoes_op_erro = ["Todas as Operações", "Soma", "Multiplicação Inteira", "Multiplicação Decimal", "Expressões Combinadas"]
        tipo_erro_sel = st.selectbox("Tipo de Operação:", opcoes_op_erro, key="sel_tipo_erro")
    with col_e2:
        modelos_opcoes = ["Todos os Modelos"] + MODELOS_GEMINI
        modelo_erro_sel = st.selectbox("Modelo:", modelos_opcoes, key="sel_mod_erro")
    with col_e3:
        dig_opcoes = ["Todos os Dígitos"] + ORDEM_DIGITOS_NUM
        dig_erro_sel = st.selectbox("Complexidade:", dig_opcoes, key="sel_dig_erro")
    with col_e4:
        status_opcoes = ["Somente Erros", "Somente Acertos", "Todos os Casos"]
        status_erro_sel = st.selectbox("Filtro de Resposta:", status_opcoes, key="sel_status_erro")

    # Filtrar dataframe base
    if tipo_erro_sel == "Soma":
        df_e = dfs.get("soma", pd.DataFrame())
    elif tipo_erro_sel == "Multiplicação Inteira":
        df_e = dfs.get("multiplicacao", pd.DataFrame())
    elif tipo_erro_sel == "Multiplicação Decimal":
        df_e = dfs.get("decimal", pd.DataFrame())
    elif tipo_erro_sel == "Expressões Combinadas":
        df_e = dfs.get("combinadas", pd.DataFrame())
    else:
        df_e = dfs.get("geral", pd.DataFrame())

    if not df_e.empty:
        if modelo_erro_sel != "Todos os Modelos":
            df_e = df_e[df_e["Nome_do_modelo"] == modelo_erro_sel]
        if dig_erro_sel != "Todos os Dígitos":
            df_e = df_e[df_e["Digitos"] == str(dig_erro_sel)]
        if status_erro_sel == "Somente Erros":
            df_e = df_e[~df_e["Acerto_da_operacao"]]
        elif status_erro_sel == "Somente Acertos":
            df_e = df_e[df_e["Acerto_da_operacao"]]

        busca_conta = st.text_input("Buscar por termo ou número específico na conta:", placeholder="Ex: 76 * ou 9868728", key="busca_conta_txt")
        if busca_conta and busca_conta.strip():
            df_e = df_e[df_e["Conta"].str.contains(busca_conta.strip(), case=False, na=False)]

        st.markdown(f"**Total de registros filtrados:** `{len(df_e):,}` casos encontrados.")

        colunas_exibir = [
            c for c in [
                "Nome_do_modelo",
                "Tipo_Operacao",
                "Digitos",
                "Conta",
                "Resultado_original",
                "Resultado_do_modelo",
                "Acerto_da_operacao",
                "Acerto_do_formato_de_resposta",
                "Resposta_bruta"
            ] if c in df_e.columns
        ]

        st.dataframe(
            df_e[colunas_exibir].rename(columns={"Digitos": "Dígitos"}).head(500),
            use_container_width=True,
            hide_index=True
        )
    else:
        st.info("Nenhum registro encontrado para a combinação selecionada.")

"""
Página 2: Resultados
Composta por 4 abas interativas em Plotly Express:
1. Acurácia dos modelos (Visão geral vertical ampliada e Grid 2x5 de Detalhamento)
2. Comparativo: desempenhos por complexidade (Lado a lado perfeitamente alinhado e Grid 2x5 com cores originais e legenda externa)
3. A influência do Raciocínio (Com seletor de dígitos 'Todos' ou pontual, trajetórias conectadas e 1 casa decimal)
4. Como os modelos pensam (Análise qualitativa lado a lado sucesso verde / erro vermelho)
"""

import sys
import os
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_loader import (
    carregar_todos_dados,
    ORDEM_DIGITOS_NUM,
    MODELOS_GEMINI,
    CORES_MODELOS_AZUL,
    COR_AZUL_PADRAO,
    CORES_OPERACOES
)
from utils.styles import aplicar_estilos_globais

aplicar_estilos_globais()

# -----------------------------------------------------------------------------
# CABEÇALHO
# -----------------------------------------------------------------------------
st.markdown('<div class="dash-title">📊 Resultados</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="dash-subtitle">'
    'Acurácia, complexidade por dígitos e o processo cognitivo dos modelos.'
    '</div>',
    unsafe_allow_html=True
)

dfs = carregar_todos_dados()

# -----------------------------------------------------------------------------
# ABAS PRINCIPAIS DA PÁGINA
# -----------------------------------------------------------------------------
tab_acuracia, tab_complexidade, tab_raciocinio, tab_pensam = st.tabs([
    "🎯 Acurácia dos modelos",
    "📉 Comparativo: desempenhos por complexidade",
    "🧠 A influência do Raciocínio",
    "🔍 Como os modelos pensam"
])

# =============================================================================
# ABA 1: ACURÁCIA DOS MODELOS
# =============================================================================
with tab_acuracia:
    st.markdown("### Visão geral")

    col_sel1, _ = st.columns([1.25, 0.75])
    with col_sel1:
        opcoes_macro = [
            "Visão Geral (Todas as Operações)",
            "Multiplicação (Inteira vs Decimal)",
            "Operações de Soma",
            "Expressões Combinadas a * (b + c)"
        ]
        macro_sel = st.selectbox("Selecione o escopo da visão macro:", opcoes_macro, key="sel_macro_acc")

    # Gráfico ampliado em 25% (proporção 1.25 : 0.75)
    col_graf_macro, _ = st.columns([1.25, 0.75])

    with col_graf_macro:
        if macro_sel == "Multiplicação (Inteira vs Decimal)":
            df_m = dfs.get("multiplicacao", pd.DataFrame())
            df_d = dfs.get("decimal", pd.DataFrame())
            df_mult_macro = pd.concat([df_m, df_d], ignore_index=True)

            if not df_mult_macro.empty:
                res_mult = (
                    df_mult_macro.groupby(["Nome_do_modelo", "Tipo_Operacao"])["Acerto_da_operacao"]
                    .agg(Total="count", Acertos="sum")
                    .reset_index()
                )
                res_mult["Taxa_Acerto"] = (res_mult["Acertos"] / res_mult["Total"]) * 100

                fig_macro = px.bar(
                    res_mult,
                    x="Nome_do_modelo",
                    y="Taxa_Acerto",
                    color="Tipo_Operacao",
                    barmode="group",
                    category_orders={
                        "Nome_do_modelo": MODELOS_GEMINI,
                        "Tipo_Operacao": ["Multiplicação Inteira", "Multiplicação Decimal"]
                    },
                    color_discrete_map={
                        "Multiplicação Inteira": "#93c5fd",
                        "Multiplicação Decimal": "#2563eb"
                    },
                    labels={
                        "Nome_do_modelo": "Modelo",
                        "Taxa_Acerto": "Taxa de Acerto (%)",
                        "Tipo_Operacao": "Operação"
                    },
                    title="Taxa de Acerto por Modelo: Multiplicação Inteira vs Decimal"
                )
                fig_macro.update_traces(
                    texttemplate="%{y:.1f}%",
                    textposition="outside"
                )
                fig_macro.update_layout(
                    xaxis_tickangle=-45,
                    xaxis=dict(automargin=True, title=None),
                    yaxis=dict(range=[0, 115], title="Taxa de Acerto (%)"),
                    height=420,
                    margin=dict(l=40, r=20, t=50, b=100),
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
                )
                st.plotly_chart(fig_macro, use_container_width=True)

        else:
            if macro_sel == "Operações de Soma":
                df_macro = dfs.get("soma", pd.DataFrame())
                nome_op_grafico = "Operações de Soma"
            elif macro_sel == "Expressões Combinadas a * (b + c)":
                df_macro = dfs.get("combinadas", pd.DataFrame())
                nome_op_grafico = "Expressões Combinadas"
            else:
                df_macro = dfs.get("geral", pd.DataFrame())
                nome_op_grafico = "Todas as Operações"

            if not df_macro.empty:
                res_macro = (
                    df_macro.groupby("Nome_do_modelo")["Acerto_da_operacao"]
                    .agg(Total="count", Acertos="sum")
                    .reset_index()
                )
                res_macro["Taxa_Acerto"] = (res_macro["Acertos"] / res_macro["Total"]) * 100

                fig_macro = px.bar(
                    res_macro,
                    x="Nome_do_modelo",
                    y="Taxa_Acerto",
                    category_orders={"Nome_do_modelo": MODELOS_GEMINI},
                    color_discrete_sequence=[COR_AZUL_PADRAO],
                    labels={"Nome_do_modelo": "Modelo", "Taxa_Acerto": "Taxa de Acerto (%)"},
                    title=f"Taxa de Acerto por Modelo - {nome_op_grafico}"
                )
                fig_macro.update_traces(
                    texttemplate="%{y:.1f}%",
                    textposition="outside"
                )
                fig_macro.update_layout(
                    xaxis_tickangle=-45,
                    xaxis=dict(automargin=True, title=None),
                    yaxis=dict(range=[0, 115], title="Taxa de Acerto (%)"),
                    height=420,
                    margin=dict(l=40, r=20, t=50, b=100)
                )
                st.plotly_chart(fig_macro, use_container_width=True)

    st.markdown("---")

    # 2. Detalhamento por modelo (Grid 2x5 sem menção no título)
    st.markdown("### Detalhamento por modelo")
    col_sel2, _ = st.columns([1, 1])
    with col_sel2:
        opcoes_det_op = ["Multiplicação Inteira", "Multiplicação Decimal", "Soma", "Expressões Combinadas"]
        det_op_sel = st.selectbox("Selecione o tipo de operação para o detalhamento:", opcoes_det_op, key="sel_det_op_grid")

    mapa_df = {
        "Multiplicação Inteira": dfs.get("multiplicacao", pd.DataFrame()),
        "Multiplicação Decimal": dfs.get("decimal", pd.DataFrame()),
        "Soma": dfs.get("soma", pd.DataFrame()),
        "Expressões Combinadas": dfs.get("combinadas", pd.DataFrame())
    }
    df_det = mapa_df.get(det_op_sel, pd.DataFrame())

    if not df_det.empty:
        # Linha 1 (modelos 0 a 4)
        cols_linha1 = st.columns(5)
        for idx in range(5):
            modelo_card = MODELOS_GEMINI[idx]
            df_m = df_det[df_det["Nome_do_modelo"] == modelo_card]
            with cols_linha1[idx]:
                if not df_m.empty:
                    res_m = (
                        df_m.groupby("Digitos")["Acerto_da_operacao"]
                        .agg(Total="count", Acertos="sum")
                        .reset_index()
                    )
                    res_m["Taxa_Acerto"] = (res_m["Acertos"] / res_m["Total"]) * 100
                    fig_card = px.bar(
                        res_m,
                        x="Digitos",
                        y="Taxa_Acerto",
                        category_orders={"Digitos": ORDEM_DIGITOS_NUM},
                        color_discrete_sequence=[CORES_MODELOS_AZUL.get(modelo_card, COR_AZUL_PADRAO)],
                        labels={"Digitos": "Dígitos", "Taxa_Acerto": "Acerto (%)"},
                        title=f"<b>{modelo_card}</b>"
                    )
                    fig_card.update_traces(
                        texttemplate="%{y:.1f}%",
                        textposition="outside"
                    )
                    fig_card.update_layout(
                        height=240,
                        margin=dict(l=15, r=15, t=35, b=30),
                        yaxis=dict(range=[0, 120], showgrid=True, dtick=50, title=None),
                        xaxis=dict(title=None)
                    )
                    st.plotly_chart(fig_card, use_container_width=True)
                else:
                    st.info(f"{modelo_card}: Sem dados")

        # Linha 2 (modelos 5 a 9)
        cols_linha2 = st.columns(5)
        for idx in range(5, 10):
            modelo_card = MODELOS_GEMINI[idx]
            df_m = df_det[df_det["Nome_do_modelo"] == modelo_card]
            with cols_linha2[idx - 5]:
                if not df_m.empty:
                    res_m = (
                        df_m.groupby("Digitos")["Acerto_da_operacao"]
                        .agg(Total="count", Acertos="sum")
                        .reset_index()
                    )
                    res_m["Taxa_Acerto"] = (res_m["Acertos"] / res_m["Total"]) * 100
                    fig_card = px.bar(
                        res_m,
                        x="Digitos",
                        y="Taxa_Acerto",
                        category_orders={"Digitos": ORDEM_DIGITOS_NUM},
                        color_discrete_sequence=[CORES_MODELOS_AZUL.get(modelo_card, COR_AZUL_PADRAO)],
                        labels={"Digitos": "Dígitos", "Taxa_Acerto": "Acerto (%)"},
                        title=f"<b>{modelo_card}</b>"
                    )
                    fig_card.update_traces(
                        texttemplate="%{y:.1f}%",
                        textposition="outside"
                    )
                    fig_card.update_layout(
                        height=240,
                        margin=dict(l=15, r=15, t=35, b=30),
                        yaxis=dict(range=[0, 120], showgrid=True, dtick=50, title=None),
                        xaxis=dict(title=None)
                    )
                    st.plotly_chart(fig_card, use_container_width=True)
                else:
                    st.info(f"{modelo_card}: Sem dados")

# =============================================================================
# ABA 2: COMPARATIVO POR COMPLEXIDADE
# =============================================================================
with tab_complexidade:
    st.markdown("### Desempenho por quantidade de dígitos")

    # Dispor Gráfico e Tabela lado a lado perfeitamente alinhados
    col_comp_graf, col_comp_tab = st.columns([1, 1])

    with col_comp_graf:
        opcoes_comp = ["Soma", "Multiplicação Inteira", "Multiplicação Decimal", "Expressões Combinadas", "Geral (Média Ponderada)"]
        comp_sel = st.selectbox("Selecione o tipo de operação para comparar os modelos:", opcoes_comp, key="sel_comp_lines")

        if comp_sel == "Soma":
            df_comp = dfs.get("soma", pd.DataFrame())
        elif comp_sel == "Multiplicação Inteira":
            df_comp = dfs.get("multiplicacao", pd.DataFrame())
        elif comp_sel == "Multiplicação Decimal":
            df_comp = dfs.get("decimal", pd.DataFrame())
        elif comp_sel == "Expressões Combinadas":
            df_comp = dfs.get("combinadas", pd.DataFrame())
        else:
            df_comp = dfs.get("geral", pd.DataFrame())

        if not df_comp.empty:
            res_comp = (
                df_comp.groupby(["Nome_do_modelo", "Digitos"])["Acerto_da_operacao"]
                .agg(Total="count", Acertos="sum")
                .reset_index()
            )
            res_comp["Taxa_Acerto"] = (res_comp["Acertos"] / res_comp["Total"]) * 100
            res_comp["Digitos_Num"] = pd.to_numeric(res_comp["Digitos"], errors="coerce")
            res_comp = res_comp.sort_values(by=["Nome_do_modelo", "Digitos_Num"])

            fig_linhas = px.line(
                res_comp,
                x="Digitos",
                y="Taxa_Acerto",
                color="Nome_do_modelo",
                markers=True,
                category_orders={
                    "Nome_do_modelo": MODELOS_GEMINI,
                    "Digitos": ORDEM_DIGITOS_NUM
                },
                color_discrete_map=CORES_MODELOS_AZUL,
                labels={"Digitos": "Dígitos", "Taxa_Acerto": "Taxa de Acerto (%)", "Nome_do_modelo": "Modelo"},
                title=f"Comparativo de Modelos por Complexidade ({comp_sel})"
            )
            fig_linhas.update_traces(
                hovertemplate="<b>%{data.name}</b><br>Dígitos: %{x}<br>Acerto: %{y:.1f}%<extra></extra>"
            )
            fig_linhas.update_layout(
                yaxis=dict(range=[-5, 105], title="Taxa de Acerto (%)"),
                xaxis=dict(title="Quantidade de Dígitos"),
                height=420,
                margin=dict(l=40, r=20, t=50, b=40)
            )
            st.plotly_chart(fig_linhas, use_container_width=True)

    with col_comp_tab:
        # Título e legenda superior alinhados à altura do selectbox ao lado
        st.markdown("#### Tabela de acurácia por quantidade de dígitos")
        st.caption(f"Valores percentuais de acerto para: **{comp_sel}**")

        if not df_comp.empty:
            tabela_pivot = (
                df_comp.pivot_table(
                    index="Nome_do_modelo",
                    columns="Digitos",
                    values="Acerto_da_operacao",
                    aggfunc=lambda x: (x.sum() / len(x)) * 100
                )
            )
            tabela_pivot = tabela_pivot.reindex([m for m in MODELOS_GEMINI if m in tabela_pivot.index])
            colunas_ordenadas = [c for c in ORDEM_DIGITOS_NUM if c in tabela_pivot.columns]
            tabela_pivot = tabela_pivot[colunas_ordenadas]

            st.dataframe(
                tabela_pivot.style.format("{:.1f}%")
                .background_gradient(cmap="Blues", vmin=0, vmax=100),
                use_container_width=True,
                height=420
            )

    st.markdown("---")

    # Seção Curva de Decaimento
    st.markdown("### Desempenho dos modelos por operação")
    st.caption("Comparação das operações ao longo dos dígitos (2 a 10) para cada um dos 10 modelos Gemini.")

    # Filtro interativo para selecionar/ocultar operações nas curvas
    col_f_ops, _ = st.columns([1, 1])
    with col_f_ops:
        todas_ops_lista = ["Multiplicação Inteira", "Multiplicação Decimal", "Soma", "Expressões Combinadas"]
        ops_selecionadas = st.multiselect(
            "Selecione as operações para visualizar ou ocultar nas curvas:",
            options=todas_ops_lista,
            default=todas_ops_lista,
            key="sel_ops_visiveis_curvas"
        )

    # Legenda explicativa externa acima do grid com as cores originais
    st.markdown("""
    <div style="display: flex; gap: 24px; flex-wrap: wrap; margin-bottom: 16px; padding: 10px 16px; background-color: #f8fafc; border: 1px solid #e2e8f0; border-radius: 8px; font-size: 0.9rem; font-weight: 600;">
        <div style="display: flex; align-items: center; gap: 8px;"><span style="width: 14px; height: 14px; background-color: #8b5cf6; border-radius: 3px; display: inline-block;"></span> Multiplicação Inteira</div>
        <div style="display: flex; align-items: center; gap: 8px;"><span style="width: 14px; height: 14px; background-color: #f97316; border-radius: 3px; display: inline-block;"></span> Multiplicação Decimal</div>
        <div style="display: flex; align-items: center; gap: 8px;"><span style="width: 14px; height: 14px; background-color: #3b82f6; border-radius: 3px; display: inline-block;"></span> Soma</div>
        <div style="display: flex; align-items: center; gap: 8px;"><span style="width: 14px; height: 14px; background-color: #10b981; border-radius: 3px; display: inline-block;"></span> Expressões Combinadas</div>
    </div>
    """, unsafe_allow_html=True)

    df_todas_op = dfs.get("geral", pd.DataFrame())

    if not df_todas_op.empty and ops_selecionadas:
        df_todas_op_filtradas = df_todas_op[df_todas_op["Tipo_Operacao"].isin(ops_selecionadas)]

        # Linha 1 de modelos (0 a 4)
        cols_dec_l1 = st.columns(5)
        for idx in range(5):
            mod_atual = MODELOS_GEMINI[idx]
            df_mod = df_todas_op_filtradas[df_todas_op_filtradas["Nome_do_modelo"] == mod_atual]
            with cols_dec_l1[idx]:
                if not df_mod.empty:
                    res_dec = (
                        df_mod.groupby(["Tipo_Operacao", "Digitos"])["Acerto_da_operacao"]
                        .agg(Total="count", Acertos="sum")
                        .reset_index()
                    )
                    res_dec["Taxa_Acerto"] = (res_dec["Acertos"] / res_dec["Total"]) * 100
                    # Ordenação estritamente numérica para eliminar ligação entre dígito 2 e 10
                    res_dec["Digitos_Num"] = pd.to_numeric(res_dec["Digitos"], errors="coerce")
                    res_dec = res_dec.sort_values(by=["Tipo_Operacao", "Digitos_Num"])

                    fig_dec = px.line(
                        res_dec,
                        x="Digitos",
                        y="Taxa_Acerto",
                        color="Tipo_Operacao",
                        markers=True,
                        category_orders={
                            "Digitos": ORDEM_DIGITOS_NUM,
                            "Tipo_Operacao": ops_selecionadas
                        },
                        color_discrete_map=CORES_OPERACOES,
                        title=f"<b>{mod_atual}</b>"
                    )
                    fig_dec.update_traces(
                        hovertemplate="<b>%{data.name}</b><br>Dígitos: %{x}<br>Acerto: %{y:.1f}%<extra></extra>"
                    )
                    fig_dec.update_layout(
                        height=240,
                        margin=dict(l=15, r=15, t=35, b=25),
                        yaxis=dict(range=[-5, 105], dtick=50, title=None),
                        xaxis=dict(title=None),
                        showlegend=False
                    )
                    st.plotly_chart(fig_dec, use_container_width=True)
                else:
                    st.info(f"{mod_atual}: Sem dados")

        # Linha 2 de modelos (5 a 9)
        cols_dec_l2 = st.columns(5)
        for idx in range(5, 10):
            mod_atual = MODELOS_GEMINI[idx]
            df_mod = df_todas_op_filtradas[df_todas_op_filtradas["Nome_do_modelo"] == mod_atual]
            with cols_dec_l2[idx - 5]:
                if not df_mod.empty:
                    res_dec = (
                        df_mod.groupby(["Tipo_Operacao", "Digitos"])["Acerto_da_operacao"]
                        .agg(Total="count", Acertos="sum")
                        .reset_index()
                    )
                    res_dec["Taxa_Acerto"] = (res_dec["Acertos"] / res_dec["Total"]) * 100
                    # Ordenação estritamente numérica para eliminar ligação entre dígito 2 e 10
                    res_dec["Digitos_Num"] = pd.to_numeric(res_dec["Digitos"], errors="coerce")
                    res_dec = res_dec.sort_values(by=["Tipo_Operacao", "Digitos_Num"])

                    fig_dec = px.line(
                        res_dec,
                        x="Digitos",
                        y="Taxa_Acerto",
                        color="Tipo_Operacao",
                        markers=True,
                        category_orders={
                            "Digitos": ORDEM_DIGITOS_NUM,
                            "Tipo_Operacao": ops_selecionadas
                        },
                        color_discrete_map=CORES_OPERACOES,
                        title=f"<b>{mod_atual}</b>"
                    )
                    fig_dec.update_traces(
                        hovertemplate="<b>%{data.name}</b><br>Dígitos: %{x}<br>Acerto: %{y:.1f}%<extra></extra>"
                    )
                    fig_dec.update_layout(
                        height=240,
                        margin=dict(l=15, r=15, t=35, b=25),
                        yaxis=dict(range=[-5, 105], dtick=50, title=None),
                        xaxis=dict(title=None),
                        showlegend=False
                    )
                    st.plotly_chart(fig_dec, use_container_width=True)
                else:
                    st.info(f"{mod_atual}: Sem dados")


# =============================================================================
# ABA 3: A INFLUÊNCIA DO RACIOCÍNIO
# =============================================================================
with tab_raciocinio:
    st.markdown("### A Influência do Raciocínio (Tokens de Pensamento)")
    st.caption("Relação entre a Taxa de Acerto (%) e a Média de Tokens de Raciocínio gerados por complexidade de dígitos.")

    # Seletor de quantidade de dígitos: "Todos" por padrão
    col_sel_r, _ = st.columns([1, 1])
    with col_sel_r:
        opcoes_dig_r = ["Todos"] + ORDEM_DIGITOS_NUM
        dig_r_sel = st.selectbox("Selecione a quantidade de dígitos para visualizar:", opcoes_dig_r, index=0, key="sel_dig_raciocinio")

    df_soma_r = dfs.get("soma", pd.DataFrame())
    df_comb_r = dfs.get("combinadas", pd.DataFrame())

    col_r1, col_r2 = st.columns([1, 1])

    # 1. Gráfico de Soma
    with col_r1:
        st.markdown("#### 1. Operações de Soma")
        if not df_soma_r.empty:
            df_soma_filtrado = df_soma_r.copy()
            if dig_r_sel != "Todos":
                df_soma_filtrado = df_soma_filtrado[df_soma_filtrado["Digitos"] == str(dig_r_sel)]

            stats_soma = (
                df_soma_filtrado.groupby(["Nome_do_modelo", "Digitos"])
                .agg(
                    Taxa_Acerto=("Acerto_da_operacao", lambda x: (x.sum() / len(x)) * 100),
                    Media_Reasoning=("reasoning_tokens", "mean")
                )
                .reset_index()
            )
            stats_soma["Digitos_Num"] = pd.to_numeric(stats_soma["Digitos"], errors="coerce")
            stats_soma = stats_soma.sort_values(by=["Nome_do_modelo", "Digitos_Num"])

            if dig_r_sel == "Todos":
                fig_r_soma = px.line(
                    stats_soma,
                    x="Media_Reasoning",
                    y="Taxa_Acerto",
                    color="Nome_do_modelo",
                    markers=True,
                    text="Digitos",
                    category_orders={"Nome_do_modelo": MODELOS_GEMINI},
                    color_discrete_map=CORES_MODELOS_AZUL,
                    labels={
                        "Media_Reasoning": "Média de Tokens de Raciocínio",
                        "Taxa_Acerto": "Taxa de Acerto (%)",
                        "Nome_do_modelo": "Modelo"
                    },
                    title="Soma: Trajetória de Complexidade (Todos os Dígitos)"
                )
                fig_r_soma.update_traces(
                    textposition="top right",
                    marker=dict(size=8),
                    hovertemplate="<b>%{data.name}</b><br>Dígitos: %{text}<br>Tokens Raciocínio: %{x:.1f}<br>Acerto: %{y:.1f}%<extra></extra>"
                )
            else:
                fig_r_soma = px.scatter(
                    stats_soma,
                    x="Media_Reasoning",
                    y="Taxa_Acerto",
                    color="Nome_do_modelo",
                    text="Nome_do_modelo",
                    category_orders={"Nome_do_modelo": MODELOS_GEMINI},
                    color_discrete_map=CORES_MODELOS_AZUL,
                    labels={
                        "Media_Reasoning": "Média de Tokens de Raciocínio",
                        "Taxa_Acerto": "Taxa de Acerto (%)",
                        "Nome_do_modelo": "Modelo"
                    },
                    title=f"Soma: {dig_r_sel} Dígitos"
                )
                fig_r_soma.update_traces(
                    textposition="top center",
                    marker=dict(size=12),
                    hovertemplate="<b>%{text}</b><br>Tokens Raciocínio: %{x:.1f}<br>Acerto: %{y:.1f}%<extra></extra>"
                )

            fig_r_soma.update_layout(
                yaxis=dict(range=[-5, 108], title="Taxa de Acerto (%)"),
                xaxis=dict(title="Média de Tokens de Raciocínio"),
                height=450,
                margin=dict(l=40, r=20, t=50, b=40)
            )
            st.plotly_chart(fig_r_soma, use_container_width=True)

    # 2. Gráfico de Expressões Combinadas
    with col_r2:
        st.markdown("#### 2. Expressões Combinadas a * (b + c)")
        if not df_comb_r.empty:
            df_comb_filtrado = df_comb_r.copy()
            if dig_r_sel != "Todos":
                df_comb_filtrado = df_comb_filtrado[df_comb_filtrado["Digitos"] == str(dig_r_sel)]

            stats_comb = (
                df_comb_filtrado.groupby(["Nome_do_modelo", "Digitos"])
                .agg(
                    Taxa_Acerto=("Acerto_da_operacao", lambda x: (x.sum() / len(x)) * 100),
                    Media_Reasoning=("reasoning_tokens", "mean")
                )
                .reset_index()
            )
            stats_comb["Digitos_Num"] = pd.to_numeric(stats_comb["Digitos"], errors="coerce")
            stats_comb = stats_comb.sort_values(by=["Nome_do_modelo", "Digitos_Num"])

            if dig_r_sel == "Todos":
                fig_r_comb = px.line(
                    stats_comb,
                    x="Media_Reasoning",
                    y="Taxa_Acerto",
                    color="Nome_do_modelo",
                    markers=True,
                    text="Digitos",
                    category_orders={"Nome_do_modelo": MODELOS_GEMINI},
                    color_discrete_map=CORES_MODELOS_AZUL,
                    labels={
                        "Media_Reasoning": "Média de Tokens de Raciocínio",
                        "Taxa_Acerto": "Taxa de Acerto (%)",
                        "Nome_do_modelo": "Modelo"
                    },
                    title="Expressões Combinadas: Trajetória de Complexidade (Todos os Dígitos)"
                )
                fig_r_comb.update_traces(
                    textposition="top right",
                    marker=dict(size=8),
                    hovertemplate="<b>%{data.name}</b><br>Dígitos: %{text}<br>Tokens Raciocínio: %{x:.1f}<br>Acerto: %{y:.1f}%<extra></extra>"
                )
            else:
                fig_r_comb = px.scatter(
                    stats_comb,
                    x="Media_Reasoning",
                    y="Taxa_Acerto",
                    color="Nome_do_modelo",
                    text="Nome_do_modelo",
                    category_orders={"Nome_do_modelo": MODELOS_GEMINI},
                    color_discrete_map=CORES_MODELOS_AZUL,
                    labels={
                        "Media_Reasoning": "Média de Tokens de Raciocínio",
                        "Taxa_Acerto": "Taxa de Acerto (%)",
                        "Nome_do_modelo": "Modelo"
                    },
                    title=f"Expressões Combinadas: {dig_r_sel} Dígitos"
                )
                fig_r_comb.update_traces(
                    textposition="top center",
                    marker=dict(size=12),
                    hovertemplate="<b>%{text}</b><br>Tokens Raciocínio: %{x:.1f}<br>Acerto: %{y:.1f}%<extra></extra>"
                )

            fig_r_comb.update_layout(
                yaxis=dict(range=[-5, 108], title="Taxa de Acerto (%)"),
                xaxis=dict(title="Média de Tokens de Raciocínio"),
                height=450,
                margin=dict(l=40, r=20, t=50, b=40)
            )
            st.plotly_chart(fig_r_comb, use_container_width=True)

# =============================================================================
# ABA 4: COMO OS MODELOS PENSAM
# =============================================================================
with tab_pensam:
    st.markdown("### Investigação Qualitativa: Como os Modelos Pensam")
    st.info("ℹ️ **Nota Metodológica:** Esta visualização qualitativa se restringe às **Expressões Combinadas**, onde os metadados de resumo de raciocínio (*reasoning summary*) foram integralmente capturados via API Batch.")

    st.markdown("""
    > [!NOTE]
    > **Exibição dos Blocos de Pensamento:** O modelo **`gemini-2.5-pro`** é o que disponibiliza os blocos de texto analítico de raciocínio em texto plano legível (disponível para inspeção abaixo). Por padrão de segurança contra destilação, os modelos da geração **Gemini 3** contabilizam os tokens de pensamento em suas métricas numéricas, mas retornam a assinatura interna de raciocínio de forma criptografada (`reasoning.encrypted`).
    """)

    df_comb = dfs.get("combinadas", pd.DataFrame())

    col_sel_p1, col_sel_p2 = st.columns(2)
    with col_sel_p1:
        idx_padrao = MODELOS_GEMINI.index("gemini-2.5-pro") if "gemini-2.5-pro" in MODELOS_GEMINI else 0
        mod_pensam_sel = st.selectbox("Selecione o modelo para inspecionar:", MODELOS_GEMINI, index=idx_padrao, key="sel_mod_pensam")
    with col_sel_p2:
        dig_pensam_sel = st.selectbox("Selecione a quantidade de dígitos:", ORDEM_DIGITOS_NUM, index=0, key="sel_dig_pensam")

    df_amostra = df_comb[(df_comb["Nome_do_modelo"] == mod_pensam_sel) & (df_comb["Digitos"] == str(dig_pensam_sel))]

    if not df_amostra.empty:
        df_sucessos = df_amostra[df_amostra["Acerto_da_operacao"] == True]
        df_falhas = df_amostra[df_amostra["Acerto_da_operacao"] == False]

        col_suc, col_fal = st.columns([1, 1])

        # Coluna da Esquerda: Sucesso
        with col_suc:
            st.markdown("#### ✅ Caso de Sucesso (Acerto)")
            if not df_sucessos.empty:
                opcoes_suc = [f"Amostra #{i+1}: {row['Conta']}" for i, (_, row) in enumerate(df_sucessos.iterrows())]
                idx_suc_sel = st.selectbox("Selecione uma amostra de acerto:", range(len(opcoes_suc)), format_func=lambda x: opcoes_suc[x], key="sel_amostra_suc")
                row_suc = df_sucessos.iloc[idx_suc_sel]

                st.markdown(f"""
                <div class="thought-container-success">
                    <div style="font-size: 0.85rem; font-weight: 700; color: #15803d; text-transform: uppercase;">Métricas do Caso</div>
                    <div style="font-size: 1.1rem; font-weight: 800; color: #166534; margin: 4px 0;">{row_suc['reasoning_tokens']} tokens de raciocínio</div>
                    <hr style="margin: 8px 0; border-color: #bbf7d0;">
                    <div><b>Expressão:</b> <code>{row_suc['Conta']}</code></div>
                    <div><b>Resposta do Modelo:</b> <span style="color: #16a34a; font-weight: bold;">{row_suc['Resultado_do_modelo']}</span></div>
                    <div><b>Gabarito Decimal:</b> <code>{row_suc['Resultado_original']}</code></div>
                    <div style="margin-top: 10px; font-weight: 600; color: #166534;">Linha de Raciocínio (Thinking Process):</div>
                    <div style="background: #ffffff; padding: 10px; border-radius: 6px; font-size: 0.85rem; color: #1e293b; margin-top: 6px; max-height: 250px; overflow-y: auto; border: 1px solid #dcfce7; white-space: pre-wrap;">
{row_suc['resumo_raciocinio'] if row_suc['resumo_raciocinio'] else '(Raciocínio criptografado ou em formato nativo pela API)'}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.warning(f"O modelo {mod_pensam_sel} não obteve acertos para {dig_pensam_sel} dígitos.")

        # Coluna da Direita: Falha
        with col_fal:
            st.markdown("#### ❌ Caso de Falha (Erro)")
            if not df_falhas.empty:
                opcoes_fal = [f"Amostra #{i+1}: {row['Conta']}" for i, (_, row) in enumerate(df_falhas.iterrows())]
                idx_fal_sel = st.selectbox("Selecione uma amostra de erro:", range(len(opcoes_fal)), format_func=lambda x: opcoes_fal[x], key="sel_amostra_fal")
                row_fal = df_falhas.iloc[idx_fal_sel]

                st.markdown(f"""
                <div class="thought-container-error">
                    <div style="font-size: 0.85rem; font-weight: 700; color: #b91c1c; text-transform: uppercase;">Métricas do Caso</div>
                    <div style="font-size: 1.1rem; font-weight: 800; color: #991b1b; margin: 4px 0;">{row_fal['reasoning_tokens']} tokens de raciocínio</div>
                    <hr style="margin: 8px 0; border-color: #fecaca;">
                    <div><b>Expressão:</b> <code>{row_fal['Conta']}</code></div>
                    <div><b>Resposta do Modelo:</b> <span style="color: #dc2626; font-weight: bold;">{row_fal['Resultado_do_modelo']}</span></div>
                    <div><b>Gabarito Decimal:</b> <code>{row_fal['Resultado_original']}</code></div>
                    <div style="margin-top: 10px; font-weight: 600; color: #991b1b;">Linha de Raciocínio (Thinking Process):</div>
                    <div style="background: #ffffff; padding: 10px; border-radius: 6px; font-size: 0.85rem; color: #1e293b; margin-top: 6px; max-height: 250px; overflow-y: auto; border: 1px solid #fee2e2; white-space: pre-wrap;">
{row_fal['resumo_raciocinio'] if row_fal['resumo_raciocinio'] else '(Raciocínio criptografado ou em formato nativo pela API)'}
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.success(f"O modelo {mod_pensam_sel} obteve 100% de acerto para {dig_pensam_sel} dígitos!")
    else:
        st.info("Nenhuma amostra encontrada para esta combinação de modelo e dígitos.")

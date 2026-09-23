"""
Página 2: Resultados
Composta por 4 abas interativas:
1. Acurácia dos modelos (Visão geral e Detalhamento por modelo)
2. Comparativo: desempenhos por complexidade (Lado a lado com tabela e Curva de Decaimento)
3. A influência do Raciocínio (com slider e animação Play)
4. Como os modelos pensam (análise lado a lado sucesso verde / erro vermelho)
"""

import sys
import os
import time
import streamlit as st
import pandas as pd
import altair as alt

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_loader import carregar_todos_dados, ORDEM_DIGITOS_NUM, MODELOS_GEMINI, CORES_OPERACOES
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

    # 1. Gráfico 1: Taxa de acerto por modelo - Nome da Operação
    col_sel1, _ = st.columns([2, 2])
    with col_sel1:
        opcoes_macro = [
            "Visão Geral (Todas as Operações)",
            "Operações de Soma",
            "Multiplicação (Inteiros & Decimais)",
            "Expressões Combinadas a * (b + c)"
        ]
        macro_sel = st.selectbox("Selecione o escopo da visão macro:", opcoes_macro, key="sel_macro_acc")

    # Filtrar dados para a visão macro
    if macro_sel == "Operações de Soma":
        df_macro = dfs.get("soma", pd.DataFrame())
        cor_barra = "#3b82f6"
        nome_op_grafico = "Operações de Soma"
    elif macro_sel == "Multiplicação (Inteiros & Decimais)":
        df_mult = dfs.get("multiplicacao", pd.DataFrame())
        df_dec = dfs.get("decimal", pd.DataFrame())
        df_macro = pd.concat([df_mult, df_dec], ignore_index=True)
        cor_barra = "#8b5cf6"
        nome_op_grafico = "Multiplicação"
    elif macro_sel == "Expressões Combinadas a * (b + c)":
        df_macro = dfs.get("combinadas", pd.DataFrame())
        cor_barra = "#10b981"
        nome_op_grafico = "Expressões Combinadas"
    else:
        df_macro = dfs.get("geral", pd.DataFrame())
        cor_barra = "#0ea5e9"
        nome_op_grafico = "Todas as Operações"

    if not df_macro.empty:
        res_macro = (
            df_macro.groupby("Nome_do_modelo")["Acerto_da_operacao"]
            .agg(Total="count", Acertos="sum")
            .reset_index()
        )
        res_macro["Taxa_Acerto"] = (res_macro["Acertos"] / res_macro["Total"]) * 100
        res_macro = res_macro.sort_values(by="Taxa_Acerto", ascending=True)

        chart_macro = (
            alt.Chart(res_macro)
            .mark_bar(cornerRadiusTopRight=5, cornerRadiusBottomRight=5)
            .encode(
                x=alt.X("Taxa_Acerto:Q", title="Taxa de Acerto (%)", scale=alt.Scale(domain=[0, 100])),
                y=alt.Y("Nome_do_modelo:N", title="Modelo", sort="-x"),
                color=alt.value(cor_barra),
                tooltip=[
                    alt.Tooltip("Nome_do_modelo:N", title="Modelo"),
                    alt.Tooltip("Taxa_Acerto:Q", title="Acurácia (%)", format=".2f"),
                    alt.Tooltip("Acertos:Q", title="Acertos"),
                    alt.Tooltip("Total:Q", title="Total de Testes")
                ]
            )
            .properties(
                title=f"Taxa de acerto por modelo - {nome_op_grafico}",
                height=320
            )
        )

        text_macro = chart_macro.mark_text(
            align="left",
            baseline="middle",
            dx=5,
            fontSize=12,
            fontWeight="bold"
        ).encode(
            text=alt.Text("Taxa_Acerto:Q", format=".1f")
        )

        st.altair_chart(chart_macro + text_macro, use_container_width=True)
    else:
        st.warning("Não há dados disponíveis para a seleção atual.")

    st.divider()

    # 2. Gráfico 2: Detalhamento por modelo
    st.markdown("### Detalhamento por modelo")
    col_d1, col_d2 = st.columns(2)
    with col_d1:
        opcoes_tipo_detalhe = ["Multiplicação (Comparativo Inteiro vs Decimal)", "Soma", "Expressões Combinadas"]
        tipo_detalhe_sel = st.selectbox("Selecione o tipo de operação:", opcoes_tipo_detalhe, key="sel_tipo_det")
    with col_d2:
        modelos_disponiveis = MODELOS_GEMINI
        modelo_detalhe_sel = st.selectbox("Selecione o modelo específico:", modelos_disponiveis, key="sel_mod_det")

    if tipo_detalhe_sel == "Multiplicação (Comparativo Inteiro vs Decimal)":
        df_m = dfs.get("multiplicacao", pd.DataFrame())
        df_d = dfs.get("decimal", pd.DataFrame())
        df_m = df_m[df_m["Nome_do_modelo"] == modelo_detalhe_sel]
        df_d = df_d[df_d["Nome_do_modelo"] == modelo_detalhe_sel]
        df_detalhe = pd.concat([df_m, df_d], ignore_index=True)
        cor_encode = alt.Color("Tipo_Operacao:N", scale=alt.Scale(
            domain=["Multiplicação Inteira", "Multiplicação Decimal"],
            range=["#8b5cf6", "#f97316"]
        ), title="Tipo")
    elif tipo_detalhe_sel == "Soma":
        df_s = dfs.get("soma", pd.DataFrame())
        df_detalhe = df_s[df_s["Nome_do_modelo"] == modelo_detalhe_sel]
        cor_encode = alt.value("#3b82f6")
    else:
        df_c = dfs.get("combinadas", pd.DataFrame())
        df_detalhe = df_c[df_c["Nome_do_modelo"] == modelo_detalhe_sel]
        cor_encode = alt.value("#10b981")

    if not df_detalhe.empty:
        group_cols = ["Digitos"]
        if "Tipo_Operacao" in df_detalhe.columns and tipo_detalhe_sel == "Multiplicação (Comparativo Inteiro vs Decimal)":
            group_cols.append("Tipo_Operacao")

        res_detalhe = (
            df_detalhe.groupby(group_cols)["Acerto_da_operacao"]
            .agg(Total="count", Acertos="sum")
            .reset_index()
        )
        res_detalhe["Taxa_Acerto"] = (res_detalhe["Acertos"] / res_detalhe["Total"]) * 100

        res_detalhe["ordem"] = res_detalhe["Digitos"].apply(
            lambda x: ORDEM_DIGITOS_NUM.index(str(x)) if str(x) in ORDEM_DIGITOS_NUM else 99
        )
        res_detalhe = res_detalhe.sort_values(by=["ordem"])

        chart_detalhe = (
            alt.Chart(res_detalhe)
            .mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4)
            .encode(
                x=alt.X("Taxa_Acerto:Q", title="Taxa de Acerto (%)", scale=alt.Scale(domain=[0, 100])),
                y=alt.Y("Digitos:N", title="Quantidade de dígitos", sort=ORDEM_DIGITOS_NUM),
                color=cor_encode,
                yOffset="Tipo_Operacao:N" if "Tipo_Operacao" in group_cols else alt.value(0),
                tooltip=[
                    alt.Tooltip("Digitos:N", title="Dígitos"),
                    alt.Tooltip("Taxa_Acerto:Q", title="Acerto (%)", format=".1f"),
                    alt.Tooltip("Acertos:Q", title="Acertos"),
                    alt.Tooltip("Total:Q", title="Total de Testes")
                ]
            )
            .properties(
                title=f"Acurácia detalhada: {modelo_detalhe_sel} ({tipo_detalhe_sel})",
                height=340
            )
        )
        st.altair_chart(chart_detalhe, use_container_width=True)
    else:
        st.warning(f"Sem registros de testes para o modelo {modelo_detalhe_sel} nesta categoria.")

# =============================================================================
# ABA 2: COMPARATIVO POR COMPLEXIDADE
# =============================================================================
with tab_complexidade:
    st.markdown("### Desempenho por quantidade de dígitos")

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

    # Dispor Gráfico de Comparativo e Tabela LADO A LADO
    col_comp_graf, col_comp_tab = st.columns([3, 2])

    with col_comp_graf:
        if not df_comp.empty:
            res_comp = (
                df_comp.groupby(["Nome_do_modelo", "Digitos"])["Acerto_da_operacao"]
                .agg(Total="count", Acertos="sum")
                .reset_index()
            )
            res_comp["Taxa_Acerto"] = (res_comp["Acertos"] / res_comp["Total"]) * 100

            chart_linhas = (
                alt.Chart(res_comp)
                .mark_line(point=True)
                .encode(
                    x=alt.X("Digitos:N", title="Quantidade de dígitos", sort=ORDEM_DIGITOS_NUM),
                    y=alt.Y("Taxa_Acerto:Q", title="Taxa de Acerto (%)", scale=alt.Scale(domain=[0, 105])),
                    color=alt.Color("Nome_do_modelo:N", title="Modelo"),
                    tooltip=[
                        alt.Tooltip("Nome_do_modelo:N", title="Modelo"),
                        alt.Tooltip("Digitos:N", title="Dígitos"),
                        alt.Tooltip("Taxa_Acerto:Q", title="Acerto (%)", format=".1f")
                    ]
                )
                .properties(
                    title=f"Comparativo de modelos por complexidade ({comp_sel})",
                    height=380
                )
            )
            st.altair_chart(chart_linhas, use_container_width=True)

    with col_comp_tab:
        st.markdown("#### Tabela de acurácia por quantidade de dígitos")
        if not df_comp.empty:
            tabela_pivot = (
                df_comp.pivot_table(
                    index="Nome_do_modelo",
                    columns="Digitos",
                    values="Acerto_da_operacao",
                    aggfunc=lambda x: (x.sum() / len(x)) * 100
                )
            )
            colunas_ordenadas = [c for c in ORDEM_DIGITOS_NUM if c in tabela_pivot.columns]
            tabela_pivot = tabela_pivot[colunas_ordenadas]
            
            st.dataframe(
                tabela_pivot.style.format("{:.1f}%")
                .background_gradient(cmap="Blues", vmin=0, vmax=100),
                use_container_width=True,
                height=350
            )

    st.divider()

    # Seção Curva de Decaimento posicionada abaixo
    st.markdown("### Desempenho dos modelos por operação")
    
    col_dec_m, _ = st.columns([2, 2])
    with col_dec_m:
        modelo_decaimento_sel = st.selectbox(
            "Selecione o modelo para visualizar a **Curva de Decaimento**:",
            MODELOS_GEMINI,
            key="sel_mod_decaimento"
        )

    df_todas_op = dfs.get("geral", pd.DataFrame())
    df_mod_decaimento = df_todas_op[df_todas_op["Nome_do_modelo"] == modelo_decaimento_sel]

    if not df_mod_decaimento.empty:
        res_decaimento = (
            df_mod_decaimento.groupby(["Tipo_Operacao", "Digitos"])["Acerto_da_operacao"]
            .agg(Total="count", Acertos="sum")
            .reset_index()
        )
        res_decaimento["Taxa_Acerto"] = (res_decaimento["Acertos"] / res_decaimento["Total"]) * 100

        chart_decaimento = (
            alt.Chart(res_decaimento)
            .mark_line(point=True, strokeWidth=2.5)
            .encode(
                x=alt.X("Digitos:N", title="Quantidade de dígitos", sort=ORDEM_DIGITOS_NUM),
                y=alt.Y("Taxa_Acerto:Q", title="Taxa de Acerto (%)", scale=alt.Scale(domain=[-5, 105])),
                color=alt.Color(
                    "Tipo_Operacao:N",
                    scale=alt.Scale(
                        domain=["Multiplicação Inteira", "Multiplicação Decimal", "Soma", "Expressões Combinadas"],
                        range=["#8b5cf6", "#f97316", "#3b82f6", "#10b981"]
                    ),
                    title="Operação"
                ),
                tooltip=[
                    alt.Tooltip("Tipo_Operacao:N", title="Operação"),
                    alt.Tooltip("Digitos:N", title="Dígitos"),
                    alt.Tooltip("Taxa_Acerto:Q", title="Acerto (%)", format=".1f")
                ]
            )
            .properties(
                title=f"Curva de decaimento por modelo: {modelo_decaimento_sel}",
                height=380
            )
        )
        st.altair_chart(chart_decaimento, use_container_width=True)

# =============================================================================
# ABA 3: A INFLUÊNCIA DO RACIOCÍNIO
# =============================================================================
with tab_raciocinio:
    st.markdown("### A Influência do Raciocínio (Tokens de Pensamento)")
    st.markdown(
        "Relação entre a **Taxa de Acerto (%)** e a **Média de Tokens de Raciocínio** consumidos por operação. "
        "Utilize o slider para fixar a quantidade de dígitos ou o botão **▶️ Play** para animar a trajetória de 2 a 10 dígitos."
    )

    df_soma_r = dfs.get("soma", pd.DataFrame())
    df_comb_r = dfs.get("combinadas", pd.DataFrame())

    col_g1, col_g2 = st.columns(2)

    # Gráfico 1: Soma
    with col_g1:
        st.markdown("#### 1. Operações de Soma")
        
        c_sl1, c_pl1 = st.columns([3, 1])
        with c_pl1:
            play_soma = st.button("▶️ Play", key="play_soma")
        with c_sl1:
            digito_soma = st.slider("Quantidade de dígitos (Soma):", min_value=2, max_value=10, value=2, key="slider_soma")

        chart_placeholder_soma = st.empty()

        def render_scatter_soma(val_digito):
            str_dig = str(val_digito)
            df_filtro = df_soma_r[df_soma_r["Digitos"] == str_dig]
            if df_filtro.empty:
                return
            stats_soma = (
                df_filtro.groupby("Nome_do_modelo")
                .agg(
                    Taxa_Acerto=("Acerto_da_operacao", lambda x: (x.sum() / len(x)) * 100),
                    Media_Reasoning=("reasoning_tokens", "mean")
                )
                .reset_index()
            )
            sc_soma = (
                alt.Chart(stats_soma)
                .mark_circle(size=130)
                .encode(
                    x=alt.X("Media_Reasoning:Q", title="Média de Tokens de Raciocínio"),
                    y=alt.Y("Taxa_Acerto:Q", title="Taxa de Acerto (%)", scale=alt.Scale(domain=[-5, 105])),
                    color=alt.Color("Nome_do_modelo:N", title="Modelo"),
                    tooltip=[
                        alt.Tooltip("Nome_do_modelo:N", title="Modelo"),
                        alt.Tooltip("Taxa_Acerto:Q", title="Acerto (%)", format=".1f"),
                        alt.Tooltip("Media_Reasoning:Q", title="Média Reasoning", format=".0f")
                    ]
                )
                .properties(title=f"Soma - Quantidade de dígitos: {str_dig}", height=340)
            )
            chart_placeholder_soma.altair_chart(sc_soma, use_container_width=True)

        if play_soma:
            for d in range(2, 11):
                render_scatter_soma(d)
                time.sleep(0.35)
        else:
            render_scatter_soma(digito_soma)

    # Gráfico 2: Expressões Combinadas
    with col_g2:
        st.markdown("#### 2. Expressões Combinadas a * (b + c)")
        
        c_sl2, c_pl2 = st.columns([3, 1])
        with c_pl2:
            play_comb = st.button("▶️ Play", key="play_comb")
        with c_sl2:
            digito_comb = st.slider("Quantidade de dígitos (Combinadas):", min_value=2, max_value=10, value=2, key="slider_comb")

        chart_placeholder_comb = st.empty()

        def render_scatter_comb(val_digito):
            str_dig = str(val_digito)
            df_filtro = df_comb_r[df_comb_r["Digitos"] == str_dig]
            if df_filtro.empty:
                return
            stats_comb = (
                df_filtro.groupby("Nome_do_modelo")
                .agg(
                    Taxa_Acerto=("Acerto_da_operacao", lambda x: (x.sum() / len(x)) * 100),
                    Media_Reasoning=("reasoning_tokens", "mean")
                )
                .reset_index()
            )
            sc_comb = (
                alt.Chart(stats_comb)
                .mark_circle(size=130)
                .encode(
                    x=alt.X("Media_Reasoning:Q", title="Média de Tokens de Raciocínio"),
                    y=alt.Y("Taxa_Acerto:Q", title="Taxa de Acerto (%)", scale=alt.Scale(domain=[-5, 105])),
                    color=alt.Color("Nome_do_modelo:N", title="Modelo"),
                    tooltip=[
                        alt.Tooltip("Nome_do_modelo:N", title="Modelo"),
                        alt.Tooltip("Taxa_Acerto:Q", title="Acerto (%)", format=".1f"),
                        alt.Tooltip("Media_Reasoning:Q", title="Média Reasoning", format=".0f")
                    ]
                )
                .properties(title=f"Expressões Combinadas - Quantidade de dígitos: {str_dig}", height=340)
            )
            chart_placeholder_comb.altair_chart(sc_comb, use_container_width=True)

        if play_comb:
            for d in range(2, 11):
                render_scatter_comb(d)
                time.sleep(0.35)
        else:
            render_scatter_comb(digito_comb)

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
        # Colocar gemini-2.5-pro com destaque / padrão pois possui textos completos
        modelos_ordenados = ["gemini-2.5-pro"] + [m for m in MODELOS_GEMINI if m != "gemini-2.5-pro"]
        modelo_pensam_sel = st.selectbox("Selecione o modelo Gemini a investigar:", modelos_ordenados, index=0, key="sel_mod_pensam")
    with col_sel_p2:
        digito_pensam_sel = st.selectbox("Selecione a quantidade de dígitos da operação:", ORDEM_DIGITOS_NUM, key="sel_dig_pensam")

    df_subset = df_comb[
        (df_comb["Nome_do_modelo"] == modelo_pensam_sel) &
        (df_comb["Digitos"] == str(digito_pensam_sel))
    ]

    df_sucesso = df_subset[df_subset["Acerto_da_operacao"] == True]
    df_falha = df_subset[df_subset["Acerto_da_operacao"] == False]

    max_exemplos = max(len(df_sucesso), len(df_falha), 1)
    if max_exemplos > 1:
        idx_exemplo = st.slider("Alternar entre amostras disponíveis do conjunto:", min_value=1, max_value=min(max_exemplos, 10), value=1)
        pos = idx_exemplo - 1
    else:
        pos = 0

    col_esq, col_dir = st.columns(2)

    # Coluna Esquerda: Caso de Sucesso
    with col_esq:
        st.markdown("""
        <div class="thought-container-success">
            <div class="thought-header-success">
                ✅ Caso de Sucesso (Resposta Correta)
            </div>
        </div>
        """, unsafe_allow_html=True)

        if not df_sucesso.empty:
            caso_ok = df_sucesso.iloc[pos % len(df_sucesso)]
            tokens_ok = caso_ok.get("reasoning_tokens", 0)
            conta_ok = caso_ok.get("Conta", "")
            resp_ok = caso_ok.get("Resultado_do_modelo", "")
            gab_ok = caso_ok.get("Resultado_original", "")
            pensamento_ok = caso_ok.get("resumo_raciocinio", "")

            st.metric("Total de Tokens de Pensamento", f"{tokens_ok} tokens")
            st.markdown(f"**Operação:** `{conta_ok}`")
            st.markdown(f"**Resposta do Modelo:** `{resp_ok}` | **Gabarito:** `{gab_ok}`")

            st.markdown("**Texto do Resumo de Raciocínio:**")
            if pensamento_ok and pensamento_ok.strip():
                st.markdown(f'<div class="thought-box" style="border-color: #86efac;">{pensamento_ok}</div>', unsafe_allow_html=True)
            else:
                st.caption("O modelo atingiu a resposta correta diretamente na inferência sem emitir bloco de texto explicativo explícito.")
        else:
            st.warning("Nenhum caso de acerto registrado para esta combinação de modelo e dígitos.")

    # Coluna Direita: Caso de Falha
    with col_dir:
        st.markdown("""
        <div class="thought-container-error">
            <div class="thought-header-error">
                ❌ Caso de Falha (Resposta Incorreta)
            </div>
        </div>
        """, unsafe_allow_html=True)

        if not df_falha.empty:
            caso_err = df_falha.iloc[pos % len(df_falha)]
            tokens_err = caso_err.get("reasoning_tokens", 0)
            conta_err = caso_err.get("Conta", "")
            resp_err = caso_err.get("Resultado_do_modelo", "")
            gab_err = caso_err.get("Resultado_original", "")
            pensamento_err = caso_err.get("resumo_raciocinio", "")

            st.metric("Total de Tokens de Pensamento", f"{tokens_err} tokens")
            st.markdown(f"**Operação:** `{conta_err}`")
            st.markdown(f"**Resposta do Modelo:** `{resp_err}` | **Gabarito:** `{gab_err}`")

            st.markdown("**Texto do Resumo de Raciocínio:**")
            if pensamento_err and pensamento_err.strip():
                st.markdown(f'<div class="thought-box" style="border-color: #fca5a5;">{pensamento_err}</div>', unsafe_allow_html=True)
            else:
                st.caption("O modelo errou o cálculo sem emitir bloco de texto explicativo explícito.")
        else:
            st.success("🎉 Nenhuma falha registrada para este modelo e quantidade de dígitos (100% de acerto)!")

import streamlit as st
import pandas as pd
import altair as alt
import os
import datetime

# -----------------------------------------------------------------------------
# CONFIGURAÇÃO DA PÁGINA
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="Dashboard Matemático LLMs | TCC",
    page_icon="🧮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS aprimorada
st.markdown("""
<style>
    .main-header {
        font-size: 2.1rem;
        font-weight: 700;
        color: #0f172a;
        margin-bottom: 0.1rem;
    }
    .sub-header {
        font-size: 1rem;
        color: #64748b;
        margin-bottom: 1.2rem;
    }
    .highlight-badge {
        display: inline-block;
        background-color: #e0f2fe;
        color: #0369a1;
        padding: 3px 8px;
        border-radius: 4px;
        font-weight: 600;
        font-size: 0.85rem;
    }
</style>
""", unsafe_allow_html=True)

ORDEM_DIGITOS = [f"{i} dígitos" for i in range(2, 11)]

# -----------------------------------------------------------------------------
# CARREGAMENTO DOS DADOS (CACHE TTL CURTO PARA ATUALIZAÇÕES EM TEMPO REAL)
# -----------------------------------------------------------------------------
@st.cache_data(ttl=10)
def carregar_dados_experimento():
    dfs = {
        "decimais_openrouter": pd.DataFrame(),
        "decimais_vertex": pd.DataFrame(),
        "inteiros_gemini": pd.DataFrame(),
        "inteiros_openrouter": pd.DataFrame()
    }
    
    # 1. Decimais OpenRouter (Base prioritária atual)
    p_dec_or = "dados/resultados_gemini_decimal_openrouter.csv"
    if os.path.exists(p_dec_or) and os.path.getsize(p_dec_or) > 50:
        try:
            df = pd.read_csv(p_dec_or, dtype=str)
            df["Fonte"] = "OpenRouter (Decimais)"
            df["Tipo_Operacao"] = "Decimal"
            df["Acerto_da_operacao"] = df["Acerto_da_operacao"].astype(str).str.strip().str.lower().isin(["true", "1"])
            if "Acerto_do_formato_de_resposta" in df.columns:
                df["Acerto_do_formato_de_resposta"] = df["Acerto_do_formato_de_resposta"].astype(str).str.strip().str.lower().isin(["true", "1"])
            else:
                df["Acerto_do_formato_de_resposta"] = True
            if "custo_total" in df.columns:
                df["custo_total"] = pd.to_numeric(df["custo_total"], errors="coerce").fillna(0.0)
            else:
                df["custo_total"] = 0.0
            for col in ["Resultado_do_modelo", "Resultado_original_decimal", "Resposta_bruta", "Conta_decimal"]:
                if col in df.columns:
                    df[col] = df[col].fillna("").astype(str)
            dfs["decimais_openrouter"] = df
        except Exception:
            pass

    # 2. Decimais Vertex AI (Execução original)
    p_dec_vtx = "dados/resultados_gemini_decimal.csv"
    if os.path.exists(p_dec_vtx) and os.path.getsize(p_dec_vtx) > 50:
        try:
            df = pd.read_csv(p_dec_vtx, dtype=str)
            df["Fonte"] = "Vertex AI (Decimais)"
            df["Tipo_Operacao"] = "Decimal"
            df["Acerto_da_operacao"] = df["Acerto_da_operacao"].astype(str).str.strip().str.lower().isin(["true", "1"])
            if "Acerto_do_formato_de_resposta" in df.columns:
                df["Acerto_do_formato_de_resposta"] = df["Acerto_do_formato_de_resposta"].astype(str).str.strip().str.lower().isin(["true", "1"])
            else:
                df["Acerto_do_formato_de_resposta"] = True
            if "custo_total" in df.columns:
                df["custo_total"] = pd.to_numeric(df["custo_total"], errors="coerce").fillna(0.0)
            else:
                df["custo_total"] = 0.0
            for col in ["Resultado_do_modelo", "Resultado_original_decimal", "Resposta_bruta", "Conta_decimal"]:
                if col in df.columns:
                    df[col] = df[col].fillna("").astype(str)
            dfs["decimais_vertex"] = df
        except Exception:
            pass

    # 3. Inteiros Gemini (Vertex AI)
    p_int_gem = "dados/resultados_gemini.csv"
    if os.path.exists(p_int_gem) and os.path.getsize(p_int_gem) > 50:
        try:
            df = pd.read_csv(p_int_gem, dtype=str)
            df["Fonte"] = "Vertex AI (Inteiros)"
            df["Tipo_Operacao"] = "Inteiro"
            df["Acerto_da_operacao"] = df["Acerto_da_operacao"].astype(str).str.strip().str.lower().isin(["true", "1"])
            if "Acerto_do_formato_de_resposta" in df.columns:
                df["Acerto_do_formato_de_resposta"] = df["Acerto_do_formato_de_resposta"].astype(str).str.strip().str.lower().isin(["true", "1"])
            else:
                df["Acerto_do_formato_de_resposta"] = True
            if "custo_total" in df.columns:
                df["custo_total"] = pd.to_numeric(df["custo_total"], errors="coerce").fillna(0.0)
            else:
                df["custo_total"] = 0.0
            for col in ["Resultado_do_modelo", "Resultado_original", "Resposta_bruta", "Conta"]:
                if col in df.columns:
                    df[col] = df[col].fillna("").astype(str)
            dfs["inteiros_gemini"] = df
        except Exception:
            pass

    # 4. Inteiros OpenRouter Free
    p_int_or = "dados/resultados_experimento.csv"
    if os.path.exists(p_int_or) and os.path.getsize(p_int_or) > 50:
        try:
            df = pd.read_csv(p_int_or, dtype=str)
            df["Fonte"] = "OpenRouter (Free Inteiros)"
            df["Tipo_Operacao"] = "Inteiro"
            df["Acerto_da_operacao"] = df["Acerto_da_operacao"].astype(str).str.strip().str.lower().isin(["true", "1"])
            if "Acerto_do_formato_de_resposta" in df.columns:
                df["Acerto_do_formato_de_resposta"] = df["Acerto_do_formato_de_resposta"].astype(str).str.strip().str.lower().isin(["true", "1"])
            else:
                df["Acerto_do_formato_de_resposta"] = True
            df["custo_total"] = 0.0
            for col in ["Resultado_do_modelo", "Resultado_original", "Resposta_bruta", "Conta"]:
                if col in df.columns:
                    df[col] = df[col].fillna("").astype(str)
            dfs["inteiros_openrouter"] = df
        except Exception:
            pass

    return dfs

dados_dict = carregar_dados_experimento()
df_dec_or = dados_dict["decimais_openrouter"]
df_dec_vtx = dados_dict["decimais_vertex"]
df_int_gem = dados_dict["inteiros_gemini"]
df_int_or = dados_dict["inteiros_openrouter"]

# -----------------------------------------------------------------------------
# BARRA LATERAL (SIDEBAR): NAVEGAÇÃO E CONTROLES
# -----------------------------------------------------------------------------
with st.sidebar:
    st.image("https://cdn-icons-png.flaticon.com/512/3845/3845868.png", width=60)
    st.title("Painel de Controle")
    st.markdown("Experimento de TCC sobre Capacidade Aritmética de LLMs.")
    
    visao = st.radio(
        "Selecione a Visualização:",
        [
            "🔣 Operações Decimais (OpenRouter)",
            "🔢 Operações Inteiras (Histórico)",
            "⚖️ Comparativo Inteiros vs. Decimais",
            "🌐 Visão Consolidada"
        ],
        index=0
    )
    
    st.markdown("---")
    
    # Status do arquivo de decimais openrouter
    p_dec_or = "dados/resultados_gemini_decimal_openrouter.csv"
    if os.path.exists(p_dec_or):
        n_linhas = len(df_dec_or)
        mod_count = df_dec_or["Nome_do_modelo"].nunique() if n_linhas > 0 else 0
        st.success(f"**OpenRouter Decimais:**\n{n_linhas:,} linhas lidas ({mod_count} modelos)")
    else:
        st.info("Arquivo de decimais ainda não encontrado.")
        
    if st.button("🔄 Atualizar Dados Agora", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# -----------------------------------------------------------------------------
# VISÃO 1: OPERAÇÕES DECIMAIS (OPENROUTER)
# -----------------------------------------------------------------------------
if visao == "🔣 Operações Decimais (OpenRouter)":
    st.markdown('<div class="main-header">🔣 Operações Decimais: Avaliação OpenRouter</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Análise detalhada do desempenho aritmético com casas decimais (Gemini Series via OpenRouter).</div>', unsafe_allow_html=True)
    
    if df_dec_or.empty:
        st.warning("⚠️ O arquivo `dados/resultados_gemini_decimal_openrouter.csv` ainda está vazio ou sendo iniciado. Aguarde algumas requisições e clique em 'Atualizar Dados Agora'.")
        st.stop()
        
    # Opção opcional de comparar com Vertex AI Decimais
    incluir_vtx = False
    if not df_dec_vtx.empty:
        incluir_vtx = st.checkbox("Incluir resultados anteriores do Vertex AI (Decimais) para comparação", value=False)
        
    if incluir_vtx and not df_dec_vtx.empty:
        df_trabalho = pd.concat([df_dec_or, df_dec_vtx], ignore_index=True)
    else:
        df_trabalho = df_dec_or.copy()
        
    # Métricas Principais
    total_ops = len(df_trabalho)
    total_acertos = df_trabalho["Acerto_da_operacao"].sum()
    taxa_acerto = (total_acertos / total_ops) * 100 if total_ops > 0 else 0
    
    taxa_formato = (df_trabalho["Acerto_do_formato_de_resposta"].sum() / total_ops) * 100 if total_ops > 0 else 0
    custo_total = df_trabalho["custo_total"].sum()
    custo_por_acerto = (custo_total / total_acertos) if total_acertos > 0 else 0.0

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("Total de Testes", f"{total_ops:,}")
    c2.metric("Acertos Operação", f"{total_acertos:,}", f"{taxa_acerto:.1f}%")
    c3.metric("Conformidade Formato", f"{taxa_formato:.1f}%")
    c4.metric("Custo Total (BRL)", f"R$ {custo_total:.3f}")
    c5.metric("Custo / Acerto", f"R$ {custo_por_acerto:.4f}")
    
    st.markdown("---")
    
    # Abas analíticas para decimais
    tab_rank, tab_dig, tab_form, tab_custo, tab_erros = st.tabs([
        "🏆 Ranking de Modelos",
        "📈 Desempenho por Dígitos",
        "📝 Conformidade do Formato",
        "💰 Análise de Custos",
        "🔬 Inspeção de Respostas & Erros"
    ])
    
    with tab_rank:
        st.subheader("Taxa de Acerto nas Contas Decimais")
        st.markdown("Percentual de operações matemáticas com casas decimais resolvidas corretamente com correspondência numérica exata.")
        
        df_rank = df_trabalho.groupby(["Nome_do_modelo", "Fonte"]).agg(
            Total=("Acerto_da_operacao", "count"),
            Acertos=("Acerto_da_operacao", "sum"),
            Formato_Correto=("Acerto_do_formato_de_resposta", "sum"),
            Custo_Total=("custo_total", "sum")
        ).reset_index()
        
        df_rank["Taxa_Acerto"] = (df_rank["Acertos"] / df_rank["Total"]) * 100
        df_rank["Taxa_Formato"] = (df_rank["Formato_Correto"] / df_rank["Total"]) * 100
        df_rank = df_rank.sort_values(by="Taxa_Acerto", ascending=False)
        
        grafico_rank = alt.Chart(df_rank).mark_bar(cornerRadiusTopRight=4, cornerRadiusBottomRight=4).encode(
            x=alt.X("Taxa_Acerto:Q", title="Taxa de Acerto (%)", scale=alt.Scale(domain=[0, 100])),
            y=alt.Y("Nome_do_modelo:N", sort="-x", title="Modelo"),
            color=alt.Color("Fonte:N", scale=alt.Scale(range=["#0ea5e9", "#f59e0b"]), legend=alt.Legend(title="Origem")),
            tooltip=[
                "Nome_do_modelo",
                "Fonte",
                alt.Tooltip("Taxa_Acerto:Q", format=".2f", title="Taxa Acerto (%)"),
                alt.Tooltip("Acertos:Q", title="Acertos"),
                alt.Tooltip("Total:Q", title="Total"),
                alt.Tooltip("Custo_Total:Q", format=".4f", title="Custo (R$)")
            ]
        ).properties(height=max(350, len(df_rank) * 35))
        
        st.altair_chart(grafico_rank, use_container_width=True)
        
        # Tabela Detalhada
        st.dataframe(
            df_rank.rename(columns={
                "Nome_do_modelo": "Modelo",
                "Taxa_Acerto": "Acurácia (%)",
                "Taxa_Formato": "Formato Válido (%)",
                "Custo_Total": "Custo Total (R$)"
            }).style.format({
                "Acurácia (%)": "{:.2f}%",
                "Formato Válido (%)": "{:.2f}%",
                "Custo Total (R$)": "R$ {:.4f}"
            }),
            use_container_width=True,
            hide_index=True
        )

    with tab_dig:
        st.subheader("Evolução da Taxa de Acerto por Complexidade (Dígitos)")
        st.markdown("Comportamento dos modelos à medida que a quantidade de dígitos antes e depois da vírgula aumenta (de 2 até 10 dígitos).")
        
        modelos_disp = df_trabalho["Nome_do_modelo"].unique().tolist()
        modelos_sel = st.multiselect(
            "Filtrar modelos para exibir no gráfico de linhas:",
            options=modelos_disp,
            default=modelos_disp[:6] if len(modelos_disp) > 6 else modelos_disp
        )
        
        df_dig = df_trabalho[df_trabalho["Nome_do_modelo"].isin(modelos_sel)] if modelos_sel else df_trabalho
        
        df_dig_grp = df_dig.groupby(["Operacao", "Nome_do_modelo"]).agg(
            Total=("Acerto_da_operacao", "count"),
            Acertos=("Acerto_da_operacao", "sum")
        ).reset_index()
        df_dig_grp["Taxa_Acerto"] = (df_dig_grp["Acertos"] / df_dig_grp["Total"]) * 100
        
        grafico_dig = alt.Chart(df_dig_grp).mark_line(point=True, strokeWidth=2.5).encode(
            x=alt.X("Operacao:N", sort=ORDEM_DIGITOS, title="Complexidade (Qtd. de Dígitos)"),
            y=alt.Y("Taxa_Acerto:Q", title="Taxa de Acerto (%)", scale=alt.Scale(domain=[-2, 102])),
            color=alt.Color("Nome_do_modelo:N", legend=alt.Legend(title="Modelo")),
            tooltip=[
                "Nome_do_modelo",
                "Operacao",
                alt.Tooltip("Taxa_Acerto:Q", format=".1f", title="Taxa Acerto (%)"),
                "Acertos",
                "Total"
            ]
        ).properties(height=450)
        
        st.altair_chart(grafico_dig, use_container_width=True)
        
        # Tabela Pivotada por Dígitos
        st.markdown("##### Tabela Comparativa de Acurácia (%) por Complexidade")
        pivot_dig = df_dig_grp.pivot(index="Nome_do_modelo", columns="Operacao", values="Taxa_Acerto")
        cols_existentes = [c for c in ORDEM_DIGITOS if c in pivot_dig.columns]
        pivot_dig = pivot_dig[cols_existentes]
        st.dataframe(pivot_dig.style.format("{:.1f}%", na_rep="-"), use_container_width=True)

    with tab_form:
        st.subheader("Taxa de Conformidade do Formato de Resposta")
        st.markdown("Mede se o modelo seguiu estritamente o prompt do sistema (retornando apenas o número puro) ou se incluiu frases introdutórias, justificativas ou alucinações.")
        
        df_form = df_trabalho.groupby("Nome_do_modelo").agg(
            Total=("Acerto_do_formato_de_resposta", "count"),
            Formato_OK=("Acerto_do_formato_de_resposta", "sum")
        ).reset_index()
        df_form["Taxa_Formato"] = (df_form["Formato_OK"] / df_form["Total"]) * 100
        df_form = df_form.sort_values(by="Taxa_Formato", ascending=False)
        
        grafico_form = alt.Chart(df_form).mark_bar(color="#6366f1").encode(
            x=alt.X("Taxa_Formato:Q", title="Conformidade do Formato (%)", scale=alt.Scale(domain=[0, 100])),
            y=alt.Y("Nome_do_modelo:N", sort="-x", title="Modelo"),
            tooltip=["Nome_do_modelo", alt.Tooltip("Taxa_Formato:Q", format=".1f", title="Formato OK (%)"), "Formato_OK", "Total"]
        ).properties(height=max(300, len(df_form) * 35))
        
        st.altair_chart(grafico_form, use_container_width=True)

    with tab_custo:
        st.subheader("Consumo Financeiro nas Operações Decimais")
        st.markdown("Avaliação de custo real das chamadas via OpenRouter em Reais (BRL).")
        
        df_custo = df_trabalho.groupby("Nome_do_modelo").agg(
            Custo_Total=("custo_total", "sum"),
            Total_Reqs=("Acerto_da_operacao", "count"),
            Total_Acertos=("Acerto_da_operacao", "sum")
        ).reset_index()
        df_custo["Custo_Medio_Req"] = df_custo["Custo_Total"] / df_custo["Total_Reqs"]
        df_custo["Custo_Por_Acerto"] = df_custo.apply(lambda r: (r["Custo_Total"] / r["Total_Acertos"]) if r["Total_Acertos"] > 0 else 0, axis=1)
        df_custo = df_custo.sort_values(by="Custo_Total", ascending=False)
        
        grafico_custo = alt.Chart(df_custo).mark_bar(color="#10b981").encode(
            x=alt.X("Custo_Total:Q", title="Custo Total Acumulado (R$)"),
            y=alt.Y("Nome_do_modelo:N", sort="-x", title="Modelo"),
            tooltip=[
                "Nome_do_modelo",
                alt.Tooltip("Custo_Total:Q", format=".4f", title="Custo Total (R$)"),
                alt.Tooltip("Custo_Medio_Req:Q", format=".6f", title="Custo/Req (R$)"),
                "Total_Reqs"
            ]
        ).properties(height=max(300, len(df_custo) * 35))
        
        st.altair_chart(grafico_custo, use_container_width=True)
        
        st.dataframe(
            df_custo.rename(columns={
                "Nome_do_modelo": "Modelo",
                "Custo_Total": "Custo Total (R$)",
                "Total_Reqs": "Requisições",
                "Total_Acertos": "Acertos",
                "Custo_Medio_Req": "Custo Médio / Req (R$)",
                "Custo_Por_Acerto": "Custo / Acerto Correto (R$)"
            }).style.format({
                "Custo Total (R$)": "R$ {:.4f}",
                "Custo Médio / Req (R$)": "R$ {:.6f}",
                "Custo / Acerto Correto (R$)": "R$ {:.5f}"
            }),
            use_container_width=True,
            hide_index=True
        )

    with tab_erros:
        st.subheader("Inspeção Qualitativa de Respostas e Erros")
        st.markdown("Permite analisar as alucinações matemáticas, erros de arredondamento e discrepâncias na posição da vírgula decimal.")
        
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            filtro_mod = st.selectbox("Modelo:", ["Todos"] + sorted(df_trabalho["Nome_do_modelo"].unique().tolist()))
        with col_f2:
            filtro_dig = st.selectbox("Dígitos:", ["Todos"] + [d for d in ORDEM_DIGITOS if d in df_trabalho["Operacao"].unique().tolist()])
        with col_f3:
            filtro_status = st.selectbox("Status:", ["Somente Erros", "Somente Acertos", "Todos"])
            
        df_inspec = df_trabalho.copy()
        if filtro_mod != "Todos":
            df_inspec = df_inspec[df_inspec["Nome_do_modelo"] == filtro_mod]
        if filtro_dig != "Todos":
            df_inspec = df_inspec[df_inspec["Operacao"] == filtro_dig]
        if filtro_status == "Somente Erros":
            df_inspec = df_inspec[~df_inspec["Acerto_da_operacao"]]
        elif filtro_status == "Somente Acertos":
            df_inspec = df_inspec[df_inspec["Acerto_da_operacao"]]
            
        cols_mostrar = [
            "Nome_do_modelo", "Operacao", "Conta_decimal", 
            "Resultado_original_decimal", "Resultado_do_modelo", 
            "Acerto_da_operacao", "Resposta_bruta"
        ]
        cols_presentes = [c for c in cols_mostrar if c in df_inspec.columns]
        
        st.write(f"Mostrando **{len(df_inspec)}** registros filtrados:")
        
        # Força exibição literal como texto puro para evitar qualquer arredondamento, truncamento ou notação científica
        config_colunas = {
            "Nome_do_modelo": st.column_config.TextColumn("Modelo"),
            "Operacao": st.column_config.TextColumn("Complexidade"),
            "Conta_decimal": st.column_config.TextColumn("Operação"),
            "Resultado_original_decimal": st.column_config.TextColumn("Gabarito (Original Literal)"),
            "Resultado_do_modelo": st.column_config.TextColumn("Resultado do Modelo (Literal)"),
            "Acerto_da_operacao": st.column_config.CheckboxColumn("Acertou?"),
            "Resposta_bruta": st.column_config.TextColumn("Resposta Bruta Completa")
        }
        
        st.dataframe(
            df_inspec[cols_presentes].head(300),
            column_config=config_colunas,
            use_container_width=True,
            hide_index=True
        )


# -----------------------------------------------------------------------------
# VISÃO 2: OPERAÇÕES INTEIRAS (HISTÓRICO)
# -----------------------------------------------------------------------------
elif visao == "🔢 Operações Inteiras (Histórico)":
    st.markdown('<div class="main-header">🔢 Operações Inteiras: Desempenho Histórico</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Resultados das operações aritméticas originais (inteiros) via Vertex AI e OpenRouter Free.</div>', unsafe_allow_html=True)
    
    df_inteiros = pd.concat([df_int_gem, df_int_or], ignore_index=True)
    
    if df_inteiros.empty:
        st.warning("Nenhum dado de números inteiros encontrado.")
        st.stop()
        
    tot_ops = len(df_inteiros)
    tot_ac = df_inteiros["Acerto_da_operacao"].sum()
    tax_geral = (tot_ac / tot_ops) * 100 if tot_ops > 0 else 0
    cust_tot = df_inteiros["custo_total"].sum()
    
    k1, k2, k3, k4 = st.columns(4)
    k1.metric("Total de Operações Inteiras", f"{tot_ops:,}")
    k2.metric("Acertos Totais", f"{tot_ac:,}")
    k3.metric("Taxa de Acerto Geral", f"{tax_geral:.1f}%")
    k4.metric("Custo Total (Gemini)", f"R$ {cust_tot:.4f}")
    
    st.markdown("---")
    
    t1, t2, t3, t4 = st.tabs([
        "🏆 Ranking de Modelos", 
        "🔍 Análise por Dígitos", 
        "💰 Custos Financeiros",
        "🔬 Inspeção de Respostas & Erros"
    ])
    
    with t1:
        st.subheader("Taxa de Acerto por Modelo (Inteiros)")
        df_grp_int = df_inteiros.groupby(["Nome_do_modelo", "Fonte"]).agg(
            Total=("Acerto_da_operacao", "count"),
            Acertos=("Acerto_da_operacao", "sum")
        ).reset_index()
        df_grp_int["Taxa_Acerto"] = (df_grp_int["Acertos"] / df_grp_int["Total"]) * 100
        df_grp_int = df_grp_int.sort_values(by="Taxa_Acerto", ascending=False)
        
        g_rank_int = alt.Chart(df_grp_int).mark_bar().encode(
            x=alt.X("Taxa_Acerto:Q", title="Taxa de Acerto (%)", scale=alt.Scale(domain=[0, 100])),
            y=alt.Y("Nome_do_modelo:N", sort="-x", title="Modelo"),
            color=alt.Color("Fonte:N", scale=alt.Scale(domain=["OpenRouter (Free Inteiros)", "Vertex AI (Inteiros)"], range=["#3b82f6", "#f97316"])),
            tooltip=["Nome_do_modelo", "Fonte", alt.Tooltip("Taxa_Acerto:Q", format=".1f", title="Acerto (%)"), "Total"]
        ).properties(height=500)
        st.altair_chart(g_rank_int, use_container_width=True)
        
    with t2:
        st.subheader("Desempenho por Complexidade (Dígitos)")
        mods_int = df_inteiros["Nome_do_modelo"].unique().tolist()
        mods_sel = st.multiselect("Filtrar modelos (se vazio, mostra média por Família):", mods_int, default=[])
        
        if mods_sel:
            df_f = df_inteiros[df_inteiros["Nome_do_modelo"].isin(mods_sel)]
            cor_int = "Nome_do_modelo:N"
        else:
            df_f = df_inteiros
            cor_int = "Fonte:N"
            
        df_d_int = df_f.groupby(["Operacao", cor_int.split(":")[0]]).agg(
            Total=("Acerto_da_operacao", "count"),
            Acertos=("Acerto_da_operacao", "sum")
        ).reset_index()
        df_d_int["Taxa_Acerto"] = (df_d_int["Acertos"] / df_d_int["Total"]) * 100
        
        g_lin_int = alt.Chart(df_d_int).mark_line(point=True, strokeWidth=3).encode(
            x=alt.X("Operacao:N", sort=ORDEM_DIGITOS, title="Complexidade"),
            y=alt.Y("Taxa_Acerto:Q", title="Taxa de Acerto (%)", scale=alt.Scale(domain=[0, 100])),
            color=alt.Color(cor_int, title="Legenda"),
            tooltip=[cor_int.split(":")[0], "Operacao", alt.Tooltip("Taxa_Acerto:Q", format=".1f", title="Acerto (%)")]
        ).properties(height=450)
        st.altair_chart(g_lin_int, use_container_width=True)
        
    with t3:
        st.subheader("Custo por Modelo Pago (Vertex AI)")
        df_c_int = df_inteiros[df_inteiros["custo_total"] > 0].groupby("Nome_do_modelo")["custo_total"].sum().reset_index()
        if not df_c_int.empty:
            g_c_int = alt.Chart(df_c_int).mark_bar(color="#2ca02c").encode(
                x=alt.X("custo_total:Q", title="Custo Acumulado (R$)"),
                y=alt.Y("Nome_do_modelo:N", sort="-x", title="Modelo"),
                tooltip=["Nome_do_modelo", alt.Tooltip("custo_total:Q", format=".4f", title="Custo (R$)")]
            ).properties(height=350)
            st.altair_chart(g_c_int, use_container_width=True)
        else:
            st.info("Nenhum custo registrado para esta seleção.")

    with t4:
        st.subheader("Inspeção Qualitativa de Respostas e Erros (Inteiros)")
        st.markdown("Permite verificar os cálculos de números inteiros com representação textual literal exata.")
        col_fi1, col_fi2, col_fi3 = st.columns(3)
        with col_fi1:
            f_mod_i = st.selectbox("Modelo:", ["Todos"] + sorted(df_inteiros["Nome_do_modelo"].unique().tolist()), key="f_mod_int")
        with col_fi2:
            f_dig_i = st.selectbox("Dígitos:", ["Todos"] + [d for d in ORDEM_DIGITOS if d in df_inteiros["Operacao"].unique().tolist()], key="f_dig_int")
        with col_fi3:
            f_sta_i = st.selectbox("Status:", ["Somente Erros", "Somente Acertos", "Todos"], key="f_sta_int")
            
        df_inspec_i = df_inteiros.copy()
        if f_mod_i != "Todos":
            df_inspec_i = df_inspec_i[df_inspec_i["Nome_do_modelo"] == f_mod_i]
        if f_dig_i != "Todos":
            df_inspec_i = df_inspec_i[df_inspec_i["Operacao"] == f_dig_i]
        if f_sta_i == "Somente Erros":
            df_inspec_i = df_inspec_i[~df_inspec_i["Acerto_da_operacao"]]
        elif f_sta_i == "Somente Acertos":
            df_inspec_i = df_inspec_i[df_inspec_i["Acerto_da_operacao"]]
            
        cols_m_i = ["Nome_do_modelo", "Operacao", "Conta", "Resultado_original", "Resultado_do_modelo", "Acerto_da_operacao", "Resposta_bruta"]
        cols_p_i = [c for c in cols_m_i if c in df_inspec_i.columns]
        
        config_c_i = {
            "Nome_do_modelo": st.column_config.TextColumn("Modelo"),
            "Operacao": st.column_config.TextColumn("Complexidade"),
            "Conta": st.column_config.TextColumn("Operação"),
            "Resultado_original": st.column_config.TextColumn("Gabarito (Original Literal)"),
            "Resultado_do_modelo": st.column_config.TextColumn("Resultado do Modelo (Literal)"),
            "Acerto_da_operacao": st.column_config.CheckboxColumn("Acertou?"),
            "Resposta_bruta": st.column_config.TextColumn("Resposta Bruta Completa")
        }
        
        st.write(f"Mostrando **{len(df_inspec_i)}** registros filtrados:")
        st.dataframe(df_inspec_i[cols_p_i].head(300), column_config=config_c_i, use_container_width=True, hide_index=True)


# -----------------------------------------------------------------------------
# VISÃO 3: COMPARATIVO INTEIROS VS. DECIMAIS
# -----------------------------------------------------------------------------
elif visao == "⚖️ Comparativo Inteiros vs. Decimais":
    st.markdown('<div class="main-header">⚖️ Comparativo: Inteiros vs. Decimais</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Investigação direta da hipótese central: como a presença do ponto decimal impacta a acurácia dos modelos.</div>', unsafe_allow_html=True)
    
    # Consolidar decimais (preferência por OpenRouter, mas unindo se desejado)
    df_todos_dec = pd.concat([df_dec_or, df_dec_vtx], ignore_index=True)
    df_todos_int = pd.concat([df_int_gem, df_int_or], ignore_index=True)
    
    if df_todos_dec.empty or df_todos_int.empty:
        st.warning("É necessário ter dados tanto de inteiros quanto de decimais para gerar o comparativo.")
        st.stop()
        
    # Agrupar inteiros
    res_int = df_todos_int.groupby("Nome_do_modelo").agg(
        Total_Int=("Acerto_da_operacao", "count"),
        Acertos_Int=("Acerto_da_operacao", "sum")
    ).reset_index()
    res_int["Taxa_Int"] = (res_int["Acertos_Int"] / res_int["Total_Int"]) * 100

    # Agrupar decimais
    res_dec = df_todos_dec.groupby("Nome_do_modelo").agg(
        Total_Dec=("Acerto_da_operacao", "count"),
        Acertos_Dec=("Acerto_da_operacao", "sum")
    ).reset_index()
    res_dec["Taxa_Dec"] = (res_dec["Acertos_Dec"] / res_dec["Total_Dec"]) * 100

    # Merge dos modelos comuns
    df_comp = pd.merge(res_int, res_dec, on="Nome_do_modelo", how="inner")
    
    if df_comp.empty:
        st.info("Ainda não há modelos avaliados simultaneamente em ambas as bases de dados.")
        st.stop()
        
    df_comp["Delta_Acuracia"] = df_comp["Taxa_Dec"] - df_comp["Taxa_Int"]
    df_comp = df_comp.sort_values(by="Taxa_Dec", ascending=False)
    
    # Métricas comparativas
    queda_media = df_comp["Delta_Acuracia"].mean()
    m_melhor = df_comp.loc[df_comp["Taxa_Dec"].idxmax()]["Nome_do_modelo"]
    m_resiliente = df_comp.loc[df_comp["Delta_Acuracia"].idxmax()]["Nome_do_modelo"]
    
    c1, c2, c3 = st.columns(3)
    c1.metric("Variação Média de Acurácia", f"{queda_media:+.2f} p.p.", help="Diferença percentual média ao migrar de inteiros para decimais.")
    c2.metric("Maior Acurácia em Decimais", m_melhor)
    c3.metric("Maior Resiliência (Menor Queda)", m_resiliente)
    
    st.markdown("---")
    
    # Gráfico de Barras Agrupadas (Inteiros vs Decimais)
    st.subheader("Comparativo Direto de Taxa de Acerto (%)")
    
    # Melt para formato longo do Altair
    df_melt = pd.melt(
        df_comp[["Nome_do_modelo", "Taxa_Int", "Taxa_Dec"]],
        id_vars=["Nome_do_modelo"],
        value_vars=["Taxa_Int", "Taxa_Dec"],
        var_name="Tipo",
        value_name="Taxa_Acerto"
    )
    df_melt["Tipo"] = df_melt["Tipo"].map({"Taxa_Int": "Inteiros", "Taxa_Dec": "Decimais"})
    
    grafico_comp = alt.Chart(df_melt).mark_bar().encode(
        y=alt.Y("Nome_do_modelo:N", title="Modelo", sort="-x"),
        x=alt.X("Taxa_Acerto:Q", title="Taxa de Acerto (%)", scale=alt.Scale(domain=[0, 100])),
        color=alt.Color("Tipo:N", scale=alt.Scale(domain=["Inteiros", "Decimais"], range=["#2563eb", "#10b981"]), legend=alt.Legend(title="Tipo de Operação")),
        yOffset="Tipo:N",
        tooltip=["Nome_do_modelo", "Tipo", alt.Tooltip("Taxa_Acerto:Q", format=".2f", title="Taxa (%)")]
    ).properties(height=max(350, len(df_comp) * 45))
    
    st.altair_chart(grafico_comp, use_container_width=True)
    
    # Tabela com Delta
    st.markdown("##### Tabela Detalhada com Queda de Desempenho")
    st.dataframe(
        df_comp.rename(columns={
            "Nome_do_modelo": "Modelo",
            "Taxa_Int": "Acurácia Inteiros (%)",
            "Taxa_Dec": "Acurácia Decimais (%)",
            "Delta_Acuracia": "Variação (p.p.)",
            "Total_Int": "Testes Inteiros",
            "Total_Dec": "Testes Decimais"
        })[[
            "Modelo", "Acurácia Inteiros (%)", "Acurácia Decimais (%)", "Variação (p.p.)", "Testes Inteiros", "Testes Decimais"
        ]].style.format({
            "Acurácia Inteiros (%)": "{:.2f}%",
            "Acurácia Decimais (%)": "{:.2f}%",
            "Variação (p.p.)": "{:+.2f}%"
        }),
        use_container_width=True,
        hide_index=True
    )
    
    st.markdown("---")
    
    # Comparativo por Dígitos de um Modelo Específico
    st.subheader("Curva de Decaimento por Dígitos: Inteiro vs. Decimal")
    modelo_selecionado = st.selectbox("Escolha um modelo para ver suas duas curvas sobrepostas:", df_comp["Nome_do_modelo"].tolist())
    
    sub_int = df_todos_int[df_todos_int["Nome_do_modelo"] == modelo_selecionado].groupby("Operacao").agg(
        Acertos=("Acerto_da_operacao", "sum"), Total=("Acerto_da_operacao", "count")
    ).reset_index()
    sub_int["Taxa"] = (sub_int["Acertos"] / sub_int["Total"]) * 100
    sub_int["Tipo"] = "Inteiros"
    
    sub_dec = df_todos_dec[df_todos_dec["Nome_do_modelo"] == modelo_selecionado].groupby("Operacao").agg(
        Acertos=("Acerto_da_operacao", "sum"), Total=("Acerto_da_operacao", "count")
    ).reset_index()
    sub_dec["Taxa"] = (sub_dec["Acertos"] / sub_dec["Total"]) * 100
    sub_dec["Tipo"] = "Decimais"
    
    df_curvas = pd.concat([sub_int, sub_dec], ignore_index=True)
    
    g_curvas = alt.Chart(df_curvas).mark_line(point=True, strokeWidth=3).encode(
        x=alt.X("Operacao:N", sort=ORDEM_DIGITOS, title="Complexidade da Operação"),
        y=alt.Y("Taxa:Q", title="Taxa de Acerto (%)", scale=alt.Scale(domain=[-2, 102])),
        color=alt.Color("Tipo:N", scale=alt.Scale(domain=["Inteiros", "Decimais"], range=["#2563eb", "#10b981"])),
        tooltip=["Tipo", "Operacao", alt.Tooltip("Taxa:Q", format=".1f", title="Acurácia (%)")]
    ).properties(height=400)
    
    st.altair_chart(g_curvas, use_container_width=True)


# -----------------------------------------------------------------------------
# VISÃO 4: VISÃO CONSOLIDADA
# -----------------------------------------------------------------------------
elif visao == "🌐 Visão Consolidada":
    st.markdown('<div class="main-header">🌐 Visão Consolidada de Todo o Experimento</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Panorama geral unificando todas as rodadas: Inteiros, Decimais, Vertex AI e OpenRouter.</div>', unsafe_allow_html=True)
    
    todos_dfs = [df for df in dados_dict.values() if not df.empty]
    if not todos_dfs:
        st.warning("Nenhum dado carregado.")
        st.stop()
        
    df_global = pd.concat(todos_dfs, ignore_index=True)
    
    tot_ops_g = len(df_global)
    tot_ac_g = df_global["Acerto_da_operacao"].sum()
    taxa_g = (tot_ac_g / tot_ops_g) * 100 if tot_ops_g > 0 else 0
    custo_g = df_global["custo_total"].sum()
    modelos_g = df_global["Nome_do_modelo"].nunique()
    
    col1, col2, col3, col4, col5 = st.columns(5)
    col1.metric("Total de Operações", f"{tot_ops_g:,}")
    col2.metric("Acertos Totais", f"{tot_ac_g:,}")
    col3.metric("Acurácia Geral", f"{taxa_g:.1f}%")
    col4.metric("Modelos Testados", f"{modelos_g}")
    col5.metric("Custo Total Consolidado", f"R$ {custo_g:.2f}")
    
    st.markdown("---")
    st.subheader("Distribuição das Operações por Base de Dados e Tipo")
    
    df_fontes = df_global.groupby(["Fonte", "Tipo_Operacao"]).agg(
        Testes=("Acerto_da_operacao", "count"),
        Acertos=("Acerto_da_operacao", "sum"),
        Custo=("custo_total", "sum")
    ).reset_index()
    df_fontes["Acuracia"] = (df_fontes["Acertos"] / df_fontes["Testes"]) * 100
    
    st.dataframe(
        df_fontes.rename(columns={
            "Fonte": "Base / Origem",
            "Tipo_Operacao": "Tipo de Conta",
            "Testes": "Qtd. Operações",
            "Acertos": "Total Acertos",
            "Acuracia": "Acurácia (%)",
            "Custo": "Custo Total (R$)"
        }).style.format({
            "Acurácia (%)": "{:.2f}%",
            "Custo Total (R$)": "R$ {:.4f}"
        }),
        use_container_width=True,
        hide_index=True
    )

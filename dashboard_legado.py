import streamlit as st
import pandas as pd
import altair as alt
import os
import json
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
        "soma_openrouter": pd.DataFrame(),
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

    # 2. Operações de Soma (OpenRouter Batch API)
    candidatos_soma = [
        "dados/resultados_gemini_soma_openrouter.csv",
        "gemini/openrouter/operacoes_soma/resultados_gemini_soma_openrouter.csv"
    ]
    for p_soma in candidatos_soma:
        if os.path.exists(p_soma) and os.path.getsize(p_soma) > 50:
            try:
                df = pd.read_csv(p_soma, dtype=str)
                df["Fonte"] = "OpenRouter (Soma)"
                df["Tipo_Operacao"] = "Soma"
                
                # Normalização de nomes de colunas
                if "Acerto da operacao" in df.columns and "Acerto_da_operacao" not in df.columns:
                    df["Acerto_da_operacao"] = df["Acerto da operacao"]
                if "Acerto do formato de resposta" in df.columns and "Acerto_do_formato_de_resposta" not in df.columns:
                    df["Acerto_do_formato_de_resposta"] = df["Acerto do formato de resposta"]
                if "Nome do modelo" in df.columns and "Nome_do_modelo" not in df.columns:
                    df["Nome_do_modelo"] = df["Nome do modelo"]
                if "Custo total" in df.columns and "custo_total" not in df.columns:
                    df["custo_total"] = df["Custo total"]
                
                df["Acerto_da_operacao"] = df["Acerto_da_operacao"].astype(str).str.strip().str.lower().isin(["true", "1"])
                if "Acerto_do_formato_de_resposta" in df.columns:
                    df["Acerto_do_formato_de_resposta"] = df["Acerto_do_formato_de_resposta"].astype(str).str.strip().str.lower().isin(["true", "1"])
                else:
                    df["Acerto_do_formato_de_resposta"] = True
                
                if "custo_total" in df.columns:
                    df["custo_total"] = pd.to_numeric(df["custo_total"], errors="coerce").fillna(0.0)
                else:
                    df["custo_total"] = 0.0
                    
                # Extração e normalização de tokens de raciocínio
                if "Quantidade de reasoning tokens gerados" in df.columns:
                    df["reasoning_tokens"] = pd.to_numeric(df["Quantidade de reasoning tokens gerados"], errors="coerce").fillna(0)
                elif "reasoning_tokens" in df.columns:
                    df["reasoning_tokens"] = pd.to_numeric(df["reasoning_tokens"], errors="coerce").fillna(0)
                else:
                    df["reasoning_tokens"] = 0

                for c_custo in ["Custo de input tokens", "Custo de output tokens", "Custo de reasoning tokens"]:
                    if c_custo in df.columns:
                        df[c_custo] = pd.to_numeric(df[c_custo], errors="coerce").fillna(0.0)

                for col in ["Resultado_do_modelo", "Resultado bruto do modelo", "Resultado original", "Resposta_bruta", "Conta"]:
                    if col in df.columns:
                        df[col] = df[col].fillna("").astype(str)
                        
                dfs["soma_openrouter"] = df
                break
            except Exception:
                pass

    # 3. Decimais Vertex AI (Execução histórica)
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

    # 4. Inteiros Gemini (Vertex AI)
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

    # 5. Inteiros OpenRouter Free
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
df_soma_or = dados_dict["soma_openrouter"]
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
            "➕ Operações de Soma (OpenRouter)",
            "🔢 Operações Inteiras (Histórico)",
            "⚖️ Comparativo: Inteiros, Decimais e Soma",
            "🌐 Visão Consolidada"
        ],
        index=0
    )
    
    st.markdown("---")
    
    # Status dos arquivos
    p_dec_or = "dados/resultados_gemini_decimal_openrouter.csv"
    if os.path.exists(p_dec_or):
        n_linhas_dec = len(df_dec_or)
        mod_count_dec = df_dec_or["Nome_do_modelo"].nunique() if n_linhas_dec > 0 else 0
        st.success(f"**OpenRouter Decimais:**\n{n_linhas_dec:,} linhas lidas ({mod_count_dec} modelos)")
    else:
        st.info("Arquivo de decimais ainda não encontrado.")
        
    caminho_ctrl_soma = "gemini/openrouter/operacoes_soma/controle_jobs_batch.json"
    if not df_soma_or.empty:
        n_linhas_soma = len(df_soma_or)
        mod_count_soma = df_soma_or["Nome_do_modelo"].nunique()
        st.success(f"**OpenRouter Soma:**\n{n_linhas_soma:,} linhas processadas ({mod_count_soma} modelos)")
    elif os.path.exists(caminho_ctrl_soma):
        st.warning("**OpenRouter Soma:**\nLotes submetidos na Batch API (aguardando conclusão)")
    else:
        st.info("OpenRouter Soma: aguardando envio.")

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
        
    # Foco exclusivo na base OpenRouter (Vertex AI removido conforme Plano de Implementação 2)
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
        
        df_rank = df_trabalho.groupby("Nome_do_modelo").agg(
            Total=("Acerto_da_operacao", "count"),
            Acertos=("Acerto_da_operacao", "sum"),
            Formato_Correto=("Acerto_do_formato_de_resposta", "sum"),
            Custo_Total=("custo_total", "sum")
        ).reset_index()
        
        df_rank["Taxa_Acerto"] = (df_rank["Acertos"] / df_rank["Total"]) * 100
        df_rank["Taxa_Formato"] = (df_rank["Formato_Correto"] / df_rank["Total"]) * 100
        df_rank = df_rank.sort_values(by="Taxa_Acerto", ascending=False)
        
        grafico_rank = alt.Chart(df_rank).mark_bar(color="#0ea5e9", cornerRadiusTopRight=4, cornerRadiusBottomRight=4).encode(
            x=alt.X("Taxa_Acerto:Q", title="Taxa de Acerto (%)", scale=alt.Scale(domain=[0, 100])),
            y=alt.Y("Nome_do_modelo:N", sort="-x", title="Modelo"),
            tooltip=[
                "Nome_do_modelo",
                alt.Tooltip("Taxa_Acerto:Q", format=".2f", title="Taxa Acerto (%)"),
                alt.Tooltip("Acertos:Q", title="Acertos"),
                alt.Tooltip("Total:Q", title="Total"),
                alt.Tooltip("Custo_Total:Q", format=".4f", title="Custo (R$)")
            ]
        ).properties(height=max(350, len(df_rank) * 35))
        
        st.altair_chart(grafico_rank, use_container_width=True)
        
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
        st.markdown("Comportamento dos modelos à medida que a quantidade de dígitos aumenta (de 2 até 10 dígitos).")
        
        modelos_disp = sorted(df_trabalho["Nome_do_modelo"].unique().tolist())
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
        
        st.markdown("##### Tabela Comparativa de Acurácia (%) por Complexidade")
        pivot_dig = df_dig_grp.pivot(index="Nome_do_modelo", columns="Operacao", values="Taxa_Acerto")
        cols_existentes = [c for c in ORDEM_DIGITOS if c in pivot_dig.columns]
        pivot_dig = pivot_dig[cols_existentes]
        st.dataframe(pivot_dig.style.format("{:.1f}%", na_rep="-"), use_container_width=True)

    with tab_form:
        st.subheader("Taxa de Conformidade do Formato de Resposta")
        st.markdown("Mede se o modelo seguiu estritamente o prompt do sistema (retornando apenas o número puro).")
        
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
        st.markdown("Permite analisar alucinações matemáticas e erros de arredondamento.")
        
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
# VISÃO 2: OPERAÇÕES DE SOMA (OPENROUTER BATCH API)
# -----------------------------------------------------------------------------
elif visao == "➕ Operações de Soma (OpenRouter)":
    st.markdown('<div class="main-header">➕ Operações de Soma: Avaliação via Batch API</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Análise detalhada do desempenho aritmético na operação de adição pura (Gemini Series via OpenRouter Batch API).</div>', unsafe_allow_html=True)
    
    caminho_ctrl_soma = "gemini/openrouter/operacoes_soma/controle_jobs_batch.json"
    
    if df_soma_or.empty:
        if os.path.exists(caminho_ctrl_soma):
            st.info("⏳ **Lotes em Processamento na Batch API da OpenRouter**")
            st.markdown("Os lotes de operações de soma foram submetidos com sucesso e estão sendo processados de forma assíncrona pela OpenRouter.")
            
            try:
                with open(caminho_ctrl_soma, "r", encoding="utf-8") as fc:
                    jobs_ctrl = json.load(fc)
                
                linhas_status = []
                for mod, jinfo in jobs_ctrl.items():
                    linhas_status.append({
                        "Modelo": mod,
                        "Batch ID": jinfo.get("batch_id"),
                        "Total Requisições": jinfo.get("total_requests", 450),
                        "Status Atual": jinfo.get("status", "in_progress"),
                        "Data Envio": jinfo.get("timestamp_envio", "")[:19].replace("T", " ")
                    })
                st.dataframe(pd.DataFrame(linhas_status), use_container_width=True, hide_index=True)
                
                st.markdown("""
                > **💡 Próximo Passo:**  
                > Quando a OpenRouter concluir o processamento dos lotes, execute o comando abaixo no terminal para baixar as respostas brutas e consolidar a base final:  
                > ```powershell
                > cd gemini/openrouter/operacoes_soma
                > python salvar_resultados.py
                > ```
                """)
            except Exception as e:
                st.error(f"Erro ao ler arquivo de controle: {e}")
        else:
            st.warning("⚠️ Os lotes de soma ainda não foram enviados ou a base de dados tratada não foi encontrada.")
            st.markdown("Execute `python enviar_chamadas.py --executar` dentro de `gemini/openrouter/operacoes_soma/` para iniciar os lotes.")
        st.stop()
        
    df_trabalho_s = df_soma_or.copy()
    
    # Métricas Principais
    total_ops_s = len(df_trabalho_s)
    total_acertos_s = df_trabalho_s["Acerto_da_operacao"].sum()
    taxa_acerto_s = (total_acertos_s / total_ops_s) * 100 if total_ops_s > 0 else 0
    taxa_formato_s = (df_trabalho_s["Acerto_do_formato_de_resposta"].sum() / total_ops_s) * 100 if total_ops_s > 0 else 0
    custo_total_s = df_trabalho_s["custo_total"].sum()
    media_reasoning_s = df_trabalho_s["reasoning_tokens"].mean() if "reasoning_tokens" in df_trabalho_s.columns else 0.0

    cs1, cs2, cs3, cs4, cs5 = st.columns(5)
    cs1.metric("Total de Testes (Soma)", f"{total_ops_s:,}")
    cs2.metric("Acertos Operação", f"{total_acertos_s:,}", f"{taxa_acerto_s:.1f}%")
    cs3.metric("Conformidade Formato", f"{taxa_formato_s:.1f}%")
    cs4.metric("Custo Total (BRL)", f"R$ {custo_total_s:.3f}")
    cs5.metric("Média Tokens Raciocínio", f"{media_reasoning_s:.1f}")
    
    st.markdown("---")
    
    # Abas analíticas da Soma
    tab_s_rank, tab_s_dig, tab_s_disp, tab_s_form, tab_s_custo, tab_s_erros = st.tabs([
        "🏆 Ranking de Modelos",
        "📈 Desempenho por Dígitos",
        "🎯 Dispersão: Acerto vs. Raciocínio",
        "📝 Conformidade do Formato",
        "💰 Análise de Custos",
        "🔬 Inspeção de Respostas & Erros"
    ])
    
    with tab_s_rank:
        st.subheader("Taxa de Acerto nas Operações de Soma")
        st.markdown("Ranking de acurácia matemática nas contas de adição pura de 2 a 10 dígitos.")
        
        df_rank_s = df_trabalho_s.groupby("Nome_do_modelo").agg(
            Total=("Acerto_da_operacao", "count"),
            Acertos=("Acerto_da_operacao", "sum"),
            Formato_OK=("Acerto_do_formato_de_resposta", "sum"),
            Custo_Total=("custo_total", "sum")
        ).reset_index()
        df_rank_s["Taxa_Acerto"] = (df_rank_s["Acertos"] / df_rank_s["Total"]) * 100
        df_rank_s = df_rank_s.sort_values(by="Taxa_Acerto", ascending=False)
        
        g_rank_s = alt.Chart(df_rank_s).mark_bar(color="#8b5cf6", cornerRadiusTopRight=4, cornerRadiusBottomRight=4).encode(
            x=alt.X("Taxa_Acerto:Q", title="Taxa de Acerto (%)", scale=alt.Scale(domain=[0, 100])),
            y=alt.Y("Nome_do_modelo:N", sort="-x", title="Modelo"),
            tooltip=[
                "Nome_do_modelo",
                alt.Tooltip("Taxa_Acerto:Q", format=".2f", title="Acurácia (%)"),
                alt.Tooltip("Acertos:Q", title="Acertos"),
                alt.Tooltip("Total:Q", title="Total"),
                alt.Tooltip("Custo_Total:Q", format=".4f", title="Custo (R$)")
            ]
        ).properties(height=max(350, len(df_rank_s) * 35))
        st.altair_chart(g_rank_s, use_container_width=True)
        
        st.dataframe(
            df_rank_s.rename(columns={
                "Nome_do_modelo": "Modelo",
                "Taxa_Acerto": "Acurácia (%)",
                "Formato_OK": "Formato Válido (Qtd)",
                "Custo_Total": "Custo Total (R$)"
            }).style.format({
                "Acurácia (%)": "{:.2f}%",
                "Custo Total (R$)": "R$ {:.4f}"
            }),
            use_container_width=True,
            hide_index=True
        )

    with tab_s_dig:
        st.subheader("Evolução da Taxa de Acerto por Complexidade de Dígitos (Soma)")
        st.markdown("Comportamento da acurácia de soma à medida que os números crescem de 2 a 10 dígitos.")
        
        mod_disp_s = sorted(df_trabalho_s["Nome_do_modelo"].unique().tolist())
        mod_sel_s = st.multiselect("Filtrar modelos:", options=mod_disp_s, default=mod_disp_s[:6] if len(mod_disp_s) > 6 else mod_disp_s, key="sel_mod_soma")
        
        df_d_s = df_trabalho_s[df_trabalho_s["Nome_do_modelo"].isin(mod_sel_s)] if mod_sel_s else df_trabalho_s
        df_d_grp_s = df_d_s.groupby(["Operacao", "Nome_do_modelo"]).agg(
            Total=("Acerto_da_operacao", "count"),
            Acertos=("Acerto_da_operacao", "sum")
        ).reset_index()
        df_d_grp_s["Taxa_Acerto"] = (df_d_grp_s["Acertos"] / df_d_grp_s["Total"]) * 100
        
        g_dig_s = alt.Chart(df_d_grp_s).mark_line(point=True, strokeWidth=2.5).encode(
            x=alt.X("Operacao:N", sort=ORDEM_DIGITOS, title="Complexidade (Qtd. de Dígitos)"),
            y=alt.Y("Taxa_Acerto:Q", title="Taxa de Acerto (%)", scale=alt.Scale(domain=[-2, 102])),
            color=alt.Color("Nome_do_modelo:N", legend=alt.Legend(title="Modelo")),
            tooltip=["Nome_do_modelo", "Operacao", alt.Tooltip("Taxa_Acerto:Q", format=".1f", title="Acerto (%)")]
        ).properties(height=450)
        st.altair_chart(g_dig_s, use_container_width=True)

    with tab_s_disp:
        st.subheader("🎯 Dispersão: Proporção de Acerto vs. Quantidade de Tokens de Raciocínio")
        st.markdown("Análise da hipótese de raciocínio estendido: modelos que gastam mais tokens de raciocínio (thinking tokens) obtêm maior proporção de acerto na soma?")
        
        df_disp = df_trabalho_s.groupby("Nome_do_modelo").agg(
            Acuracia=("Acerto_da_operacao", lambda s: s.mean() * 100),
            Media_Reasoning=("reasoning_tokens", "mean"),
            Total_Reasoning=("reasoning_tokens", "sum"),
            Total_Operacoes=("Acerto_da_operacao", "count")
        ).reset_index()
        
        g_disp = alt.Chart(df_disp).mark_circle(size=140).encode(
            x=alt.X("Media_Reasoning:Q", title="Média de Tokens de Raciocínio por Operação"),
            y=alt.Y("Acuracia:Q", title="Taxa de Acerto (%)", scale=alt.Scale(domain=[-2, 102])),
            color=alt.Color("Nome_do_modelo:N", legend=alt.Legend(title="Modelo")),
            tooltip=[
                "Nome_do_modelo",
                alt.Tooltip("Acuracia:Q", format=".2f", title="Acurácia (%)"),
                alt.Tooltip("Media_Reasoning:Q", format=".1f", title="Média Reasoning Tokens"),
                alt.Tooltip("Total_Reasoning:Q", format=",.0f", title="Total Reasoning Tokens"),
                "Total_Operacoes"
            ]
        ).properties(height=420)
        
        st.altair_chart(g_disp, use_container_width=True)
        
        st.dataframe(
            df_disp.rename(columns={
                "Nome_do_modelo": "Modelo",
                "Acuracia": "Acurácia (%)",
                "Media_Reasoning": "Média Reasoning Tokens",
                "Total_Reasoning": "Total Reasoning Tokens",
                "Total_Operacoes": "Operações"
            }).style.format({
                "Acurácia (%)": "{:.2f}%",
                "Média Reasoning Tokens": "{:.1f}",
                "Total Reasoning Tokens": "{:,.0f}"
            }),
            use_container_width=True,
            hide_index=True
        )

    with tab_s_form:
        st.subheader("Conformidade de Formato nas Operações de Soma")
        st.markdown("Verificação se o modelo retornou estritamente o número solicitado.")
        df_f_s = df_trabalho_s.groupby("Nome_do_modelo").agg(
            Total=("Acerto_do_formato_de_resposta", "count"),
            Formato_OK=("Acerto_do_formato_de_resposta", "sum")
        ).reset_index()
        df_f_s["Taxa_Formato"] = (df_f_s["Formato_OK"] / df_f_s["Total"]) * 100
        df_f_s = df_f_s.sort_values(by="Taxa_Formato", ascending=False)
        
        g_form_s = alt.Chart(df_f_s).mark_bar(color="#6366f1").encode(
            x=alt.X("Taxa_Formato:Q", title="Conformidade do Formato (%)", scale=alt.Scale(domain=[0, 100])),
            y=alt.Y("Nome_do_modelo:N", sort="-x", title="Modelo"),
            tooltip=["Nome_do_modelo", alt.Tooltip("Taxa_Formato:Q", format=".1f", title="Formato OK (%)"), "Total"]
        ).properties(height=max(300, len(df_f_s) * 35))
        st.altair_chart(g_form_s, use_container_width=True)

    with tab_s_custo:
        st.subheader("Custos Financeiros Detalhados (Batch API Soma)")
        st.markdown("Custos apurados considerando a tarifa da Batch API com 50% de desconto.")
        
        cols_custo_grp = {"custo_total": "sum", "Acerto_da_operacao": ["count", "sum"]}
        for c in ["Custo de input tokens", "Custo de output tokens", "Custo de reasoning tokens"]:
            if c in df_trabalho_s.columns:
                cols_custo_grp[c] = "sum"
                
        df_c_s = df_trabalho_s.groupby("Nome_do_modelo").agg(
            Custo_Total=("custo_total", "sum"),
            Total_Reqs=("Acerto_da_operacao", "count"),
            Total_Acertos=("Acerto_da_operacao", "sum")
        ).reset_index()
        df_c_s = df_c_s.sort_values(by="Custo_Total", ascending=False)
        
        g_c_s = alt.Chart(df_c_s).mark_bar(color="#10b981").encode(
            x=alt.X("Custo_Total:Q", title="Custo Total Acumulado (R$)"),
            y=alt.Y("Nome_do_modelo:N", sort="-x", title="Modelo"),
            tooltip=["Nome_do_modelo", alt.Tooltip("Custo_Total:Q", format=".4f", title="Custo (R$)"), "Total_Reqs"]
        ).properties(height=max(300, len(df_c_s) * 35))
        st.altair_chart(g_c_s, use_container_width=True)

    with tab_s_erros:
        st.subheader("Inspeção Qualitativa de Erros e Respostas Brutas (Soma)")
        col_s1, col_s2, col_s3 = st.columns(3)
        with col_s1:
            f_s_mod = st.selectbox("Modelo:", ["Todos"] + sorted(df_trabalho_s["Nome_do_modelo"].unique().tolist()), key="f_soma_mod")
        with col_s2:
            f_s_dig = st.selectbox("Dígitos:", ["Todos"] + [d for d in ORDEM_DIGITOS if d in df_trabalho_s["Operacao"].unique().tolist()], key="f_soma_dig")
        with col_s3:
            f_s_sta = st.selectbox("Status:", ["Somente Erros", "Somente Acertos", "Todos"], key="f_soma_sta")
            
        df_inspec_s = df_trabalho_s.copy()
        if f_s_mod != "Todos":
            df_inspec_s = df_inspec_s[df_inspec_s["Nome_do_modelo"] == f_s_mod]
        if f_s_dig != "Todos":
            df_inspec_s = df_inspec_s[df_inspec_s["Operacao"] == f_s_dig]
        if f_s_sta == "Somente Erros":
            df_inspec_s = df_inspec_s[~df_inspec_s["Acerto_da_operacao"]]
        elif f_s_sta == "Somente Acertos":
            df_inspec_s = df_inspec_s[df_inspec_s["Acerto_da_operacao"]]
            
        cols_mostrar_s = ["Nome_do_modelo", "Operacao", "Conta", "Resultado original", "Resultado_do_modelo", "Acerto_da_operacao", "Resposta_bruta"]
        cols_presentes_s = [c for c in cols_mostrar_s if c in df_inspec_s.columns]
        
        st.write(f"Mostrando **{len(df_inspec_s)}** registros filtrados:")
        st.dataframe(df_inspec_s[cols_presentes_s].head(300), use_container_width=True, hide_index=True)


# -----------------------------------------------------------------------------
# VISÃO 3: OPERAÇÕES INTEIRAS (HISTÓRICO)
# -----------------------------------------------------------------------------
elif visao == "🔢 Operações Inteiras (Histórico)":
    st.markdown('<div class="main-header">🔢 Operações Inteiras: Desempenho Histórico</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Resultados das operações aritméticas originais de multiplicação de inteiros via Vertex AI e OpenRouter Free.</div>', unsafe_allow_html=True)
    
    df_inteiros = pd.concat([df_int_gem, df_int_or], ignore_index=True)
    
    if df_inteiros.empty:
        st.warning("Nenhum dado de números inteiros encontrado.")
        st.stop()
        
    tot_ops = len(df_inteiros)
    tot_ac = df_inteiros["Acerto_da_operacao"].sum()
    taxa_ac = (tot_ac / tot_ops) * 100 if tot_ops > 0 else 0
    tot_custo = df_inteiros["custo_total"].sum()
    
    ci1, ci2, ci3, ci4 = st.columns(4)
    ci1.metric("Total de Testes (Inteiros)", f"{tot_ops:,}")
    ci2.metric("Acertos Totais", f"{tot_ac:,}")
    ci3.metric("Taxa Global de Acerto", f"{taxa_ac:.1f}%")
    ci4.metric("Custo Total (BRL)", f"R$ {tot_custo:.2f}")
    
    st.markdown("---")
    
    t1, t2, t3, t4 = st.tabs(["🏆 Ranking", "📈 Curva por Dígitos", "💰 Custos Vertex", "🔬 Inspeção de Erros"])
    
    with t1:
        st.subheader("Acurácia Global por Modelo (Inteiros)")
        df_r_int = df_inteiros.groupby(["Nome_do_modelo", "Fonte"]).agg(
            Total=("Acerto_da_operacao", "count"),
            Acertos=("Acerto_da_operacao", "sum")
        ).reset_index()
        df_r_int["Taxa_Acerto"] = (df_r_int["Acertos"] / df_r_int["Total"]) * 100
        df_r_int = df_r_int.sort_values(by="Taxa_Acerto", ascending=False)
        
        g_r_int = alt.Chart(df_r_int).mark_bar().encode(
            x=alt.X("Taxa_Acerto:Q", title="Taxa de Acerto (%)", scale=alt.Scale(domain=[0, 100])),
            y=alt.Y("Nome_do_modelo:N", sort="-x", title="Modelo"),
            color=alt.Color("Fonte:N", legend=alt.Legend(title="Origem")),
            tooltip=["Nome_do_modelo", "Fonte", alt.Tooltip("Taxa_Acerto:Q", format=".2f", title="Taxa (%)"), "Total"]
        ).properties(height=max(400, len(df_r_int) * 25))
        st.altair_chart(g_r_int, use_container_width=True)
        
    with t2:
        st.subheader("Decaimento da Acurácia por Complexidade (Dígitos)")
        cor_int = "Nome_do_modelo:N"
        df_d_int = df_inteiros.groupby(["Operacao", cor_int.split(":")[0]]).agg(
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
            
        cols_p_i = [c for c in ["Nome_do_modelo", "Operacao", "Conta", "Resultado_original", "Resultado_do_modelo", "Acerto_da_operacao", "Resposta_bruta"] if c in df_inspec_i.columns]
        st.dataframe(df_inspec_i[cols_p_i].head(300), use_container_width=True, hide_index=True)


# -----------------------------------------------------------------------------
# VISÃO 4: COMPARATIVO: INTEIROS, DECIMAIS E SOMA
# -----------------------------------------------------------------------------
elif visao == "⚖️ Comparativo: Inteiros, Decimais e Soma":
    st.markdown('<div class="main-header">⚖️ Comparativo Tripartite: Inteiros vs. Decimais vs. Soma</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Investigação da hipótese central: como a adição de casas decimais e a mudança de operação (multiplicação vs. soma) afetam o raciocínio matemático dos LLMs.</div>', unsafe_allow_html=True)
    
    df_todos_dec = pd.concat([df_dec_or, df_dec_vtx], ignore_index=True)
    df_todos_int = pd.concat([df_int_gem, df_int_or], ignore_index=True)
    
    if df_todos_dec.empty or df_todos_int.empty:
        st.warning("É necessário ter dados de inteiros e decimais para gerar o comparativo.")
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

    df_comp = pd.merge(res_int, res_dec, on="Nome_do_modelo", how="inner")
    
    tem_soma = not df_soma_or.empty
    if tem_soma:
        res_soma = df_soma_or.groupby("Nome_do_modelo").agg(
            Total_Soma=("Acerto_da_operacao", "count"),
            Acertos_Soma=("Acerto_da_operacao", "sum")
        ).reset_index()
        res_soma["Taxa_Soma"] = (res_soma["Acertos_Soma"] / res_soma["Total_Soma"]) * 100
        df_comp = pd.merge(df_comp, res_soma, on="Nome_do_modelo", how="left")
    else:
        st.info("ℹ️ Os dados de soma serão incorporados a este comparativo assim que os lotes da Batch API forem concluídos.")
        
    if df_comp.empty:
        st.info("Ainda não há modelos avaliados simultaneamente nas bases disponíveis.")
        st.stop()
        
    df_comp["Delta_Dec_vs_Int"] = df_comp["Taxa_Dec"] - df_comp["Taxa_Int"]
    if tem_soma and "Taxa_Soma" in df_comp.columns:
        df_comp["Delta_Soma_vs_Int"] = df_comp["Taxa_Soma"] - df_comp["Taxa_Int"]
        df_comp = df_comp.sort_values(by="Taxa_Soma", ascending=False)
    else:
        df_comp = df_comp.sort_values(by="Taxa_Dec", ascending=False)
        
    # Métricas comparativas
    c1, c2, c3 = st.columns(3)
    c1.metric("Variação Média (Decimais vs Inteiros)", f"{df_comp['Delta_Dec_vs_Int'].mean():+.2f} p.p.")
    if tem_soma and "Delta_Soma_vs_Int" in df_comp.columns:
        c2.metric("Variação Média (Soma vs Inteiros)", f"{df_comp['Delta_Soma_vs_Int'].dropna().mean():+.2f} p.p.")
        c3.metric("Maior Acurácia em Soma", df_comp.loc[df_comp["Taxa_Soma"].idxmax()]["Nome_do_modelo"] if not df_comp["Taxa_Soma"].isna().all() else "-")
    else:
        c2.metric("Maior Acurácia em Decimais", df_comp.loc[df_comp["Taxa_Dec"].idxmax()]["Nome_do_modelo"])
        c3.metric("Maior Resiliência (Decimais)", df_comp.loc[df_comp["Delta_Dec_vs_Int"].idxmax()]["Nome_do_modelo"])
        
    st.markdown("---")
    
    # Gráfico de Barras Comparativo
    st.subheader("Comparativo de Taxa de Acerto (%) por Operação")
    
    value_vars = ["Taxa_Int", "Taxa_Dec"]
    mapa_tipos = {"Taxa_Int": "Inteiros (Multiplicação)", "Taxa_Dec": "Decimais (Multiplicação)"}
    cores_domain = ["Inteiros (Multiplicação)", "Decimais (Multiplicação)"]
    cores_range = ["#2563eb", "#10b981"]
    
    if tem_soma and "Taxa_Soma" in df_comp.columns:
        value_vars.append("Taxa_Soma")
        mapa_tipos["Taxa_Soma"] = "Soma (Adição)"
        cores_domain.append("Soma (Adição)")
        cores_range.append("#8b5cf6")
        
    df_melt = pd.melt(
        df_comp[["Nome_do_modelo"] + value_vars],
        id_vars=["Nome_do_modelo"],
        value_vars=value_vars,
        var_name="Tipo",
        value_name="Taxa_Acerto"
    )
    df_melt["Tipo"] = df_melt["Tipo"].map(mapa_tipos)
    df_melt = df_melt.dropna(subset=["Taxa_Acerto"])
    
    grafico_comp = alt.Chart(df_melt).mark_bar().encode(
        y=alt.Y("Nome_do_modelo:N", title="Modelo", sort="-x"),
        x=alt.X("Taxa_Acerto:Q", title="Taxa de Acerto (%)", scale=alt.Scale(domain=[0, 100])),
        color=alt.Color("Tipo:N", scale=alt.Scale(domain=cores_domain, range=cores_range), legend=alt.Legend(title="Tipo de Operação")),
        yOffset="Tipo:N",
        tooltip=["Nome_do_modelo", "Tipo", alt.Tooltip("Taxa_Acerto:Q", format=".2f", title="Taxa (%)")]
    ).properties(height=max(350, len(df_comp) * 45))
    st.altair_chart(grafico_comp, use_container_width=True)
    
    # Tabela detalhada
    st.markdown("##### Tabela Detalhada com Desempenho e Variações")
    cols_tabela = ["Nome_do_modelo", "Taxa_Int", "Taxa_Dec", "Delta_Dec_vs_Int"]
    nomes_cols = {
        "Nome_do_modelo": "Modelo",
        "Taxa_Int": "Inteiros (%)",
        "Taxa_Dec": "Decimais (%)",
        "Delta_Dec_vs_Int": "Δ Decimais (p.p.)"
    }
    format_cols = {
        "Inteiros (%)": "{:.2f}%",
        "Decimais (%)": "{:.2f}%",
        "Δ Decimais (p.p.)": "{:+.2f}%"
    }
    
    if tem_soma and "Taxa_Soma" in df_comp.columns:
        cols_tabela.extend(["Taxa_Soma", "Delta_Soma_vs_Int"])
        nomes_cols["Taxa_Soma"] = "Soma (%)"
        nomes_cols["Delta_Soma_vs_Int"] = "Δ Soma (p.p.)"
        format_cols["Soma (%)"] = "{:.2f}%"
        format_cols["Δ Soma (p.p.)"] = "{:+.2f}%"
        
    df_show_tabela = df_comp[cols_tabela].rename(columns=nomes_cols)
    st.dataframe(df_show_tabela.style.format(format_cols, na_rep="-"), use_container_width=True, hide_index=True)
    
    st.markdown("---")
    
    # Curvas de Decaimento Sobrepostas
    st.subheader("Curvas de Decaimento por Dígitos Sobrepostas")
    modelo_selecionado = st.selectbox("Escolha um modelo para ver suas curvas sobrepostas:", df_comp["Nome_do_modelo"].tolist())
    
    curvas_list = []
    
    sub_int = df_todos_int[df_todos_int["Nome_do_modelo"] == modelo_selecionado].groupby("Operacao").agg(
        Acertos=("Acerto_da_operacao", "sum"), Total=("Acerto_da_operacao", "count")
    ).reset_index()
    sub_int["Taxa"] = (sub_int["Acertos"] / sub_int["Total"]) * 100
    sub_int["Tipo"] = "Inteiros (Multiplicação)"
    curvas_list.append(sub_int)
    
    sub_dec = df_todos_dec[df_todos_dec["Nome_do_modelo"] == modelo_selecionado].groupby("Operacao").agg(
        Acertos=("Acerto_da_operacao", "sum"), Total=("Acerto_da_operacao", "count")
    ).reset_index()
    sub_dec["Taxa"] = (sub_dec["Acertos"] / sub_dec["Total"]) * 100
    sub_dec["Tipo"] = "Decimais (Multiplicação)"
    curvas_list.append(sub_dec)
    
    if tem_soma:
        sub_soma = df_soma_or[df_soma_or["Nome_do_modelo"] == modelo_selecionado].groupby("Operacao").agg(
            Acertos=("Acerto_da_operacao", "sum"), Total=("Acerto_da_operacao", "count")
        ).reset_index()
        if not sub_soma.empty:
            sub_soma["Taxa"] = (sub_soma["Acertos"] / sub_soma["Total"]) * 100
            sub_soma["Tipo"] = "Soma (Adição)"
            curvas_list.append(sub_soma)
            
    df_curvas = pd.concat(curvas_list, ignore_index=True)
    
    g_curvas = alt.Chart(df_curvas).mark_line(point=True, strokeWidth=3).encode(
        x=alt.X("Operacao:N", sort=ORDEM_DIGITOS, title="Complexidade da Operação"),
        y=alt.Y("Taxa:Q", title="Taxa de Acerto (%)", scale=alt.Scale(domain=[-2, 102])),
        color=alt.Color("Tipo:N", scale=alt.Scale(domain=cores_domain, range=cores_range)),
        tooltip=["Tipo", "Operacao", alt.Tooltip("Taxa:Q", format=".1f", title="Acurácia (%)")]
    ).properties(height=400)
    st.altair_chart(g_curvas, use_container_width=True)


# -----------------------------------------------------------------------------
# VISÃO 5: VISÃO CONSOLIDADA
# -----------------------------------------------------------------------------
elif visao == "🌐 Visão Consolidada":
    st.markdown('<div class="main-header">🌐 Visão Consolidada de Todo o Experimento</div>', unsafe_allow_html=True)
    st.markdown('<div class="sub-header">Panorama geral unificando todas as rodadas: Inteiros, Decimais, Soma, Vertex AI e OpenRouter.</div>', unsafe_allow_html=True)
    
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

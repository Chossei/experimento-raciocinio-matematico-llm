import streamlit as st
import pandas as pd
import altair as alt
import os

st.set_page_config(page_title="Dashboard Matemático LLMs", layout="wide", page_icon="🧮")

st.title("📊 Raciocínio Matemático nos LLMs")
st.markdown("Visualização interativa das taxas de acerto e consumo financeiro dos modelos.")

@st.cache_data
def carregar_dados():
    df_experimento = pd.DataFrame()
    df_gemini = pd.DataFrame()
    
    # Tenta ler do diretório dados/ local (útil para uso local e se hospedado no mesmo repositório)
    if os.path.exists("dados/resultados_experimento.csv"):
        df_experimento = pd.read_csv("dados/resultados_experimento.csv")
        df_experimento["Familia"] = "OpenRouter (Free)"
        
    if os.path.exists("dados/resultados_gemini.csv"):
        df_gemini = pd.read_csv("dados/resultados_gemini.csv")
        df_gemini["Familia"] = "Vertex AI (Gemini)"
        
    if df_experimento.empty and df_gemini.empty:
        return pd.DataFrame()
        
    df_total = pd.concat([df_experimento, df_gemini], ignore_index=True)
    return df_total

df = carregar_dados()

if df.empty:
    st.warning("Nenhum dado encontrado na pasta 'dados/'. Aguarde os scripts terminarem e atualize a página.")
    st.stop()

# Garantir tipos corretos
df["Acerto_da_operacao"] = df["Acerto_da_operacao"].astype(bool)
if "custo_total" not in df.columns:
    df["custo_total"] = 0.0
df["custo_total"] = pd.to_numeric(df["custo_total"], errors="coerce").fillna(0.0)

# ================================
# MÉTRICAS GLOBAIS
# ================================
st.header("Resumo Global")
col1, col2, col3, col4 = st.columns(4)

total_ops = len(df)
total_acertos = df["Acerto_da_operacao"].sum()
taxa_geral = (total_acertos / total_ops) * 100 if total_ops > 0 else 0
custo_total = df["custo_total"].sum()

col1.metric("Total de Operações Avaliadas", total_ops)
col2.metric("Acertos Totais", total_acertos)
col3.metric("Taxa de Acerto Geral", f"{taxa_geral:.1f}%")
col4.metric("Custo Total Acumulado", f"R$ {custo_total:.4f}")

st.markdown("---")

# ================================
# ABAS DE ANÁLISE
# ================================
aba1, aba2, aba3 = st.tabs(["🏆 Ranking de Modelos", "🔍 Análise por Dígitos", "💰 Análise Financeira (Gemini)"])

with aba1:
    st.subheader("Taxa de Acerto por Modelo")
    st.markdown("Comparativo do desempenho global de todos os modelos cadastrados.")
    
    df_agrupado = df.groupby(["Nome_do_modelo", "Familia"]).agg(
        Total=("Acerto_da_operacao", "count"),
        Acertos=("Acerto_da_operacao", "sum")
    ).reset_index()
    
    df_agrupado["Taxa_Acerto"] = (df_agrupado["Acertos"] / df_agrupado["Total"]) * 100
    df_agrupado = df_agrupado.sort_values(by="Taxa_Acerto", ascending=False)
    
    grafico_ranking = alt.Chart(df_agrupado).mark_bar().encode(
        x=alt.X("Taxa_Acerto:Q", title="Taxa de Acerto (%)", scale=alt.Scale(domain=[0, 100])),
        y=alt.Y("Nome_do_modelo:N", sort="-x", title="Modelo"),
        color=alt.Color("Familia:N", legend=alt.Legend(title="Família/API"), scale=alt.Scale(domain=["OpenRouter (Free)", "Vertex AI (Gemini)"], range=["#1f77b4", "#ff7f0e"])),
        tooltip=["Nome_do_modelo", "Familia", alt.Tooltip("Taxa_Acerto:Q", format=".1f", title="Acerto (%)"), "Total"]
    ).properties(height=500)
    
    st.altair_chart(grafico_ranking, use_container_width=True)


with aba2:
    st.subheader("Desempenho por Complexidade (Qtd de Dígitos)")
    st.markdown("Veja como os modelos sofrem (ou não) conforme a conta matemática cresce.")
    
    # Filtro
    modelos_disponiveis = df["Nome_do_modelo"].unique().tolist()
    
    col_filtro, _ = st.columns([2, 1])
    with col_filtro:
        modelos_selecionados = st.multiselect(
            "Selecione modelos específicos para comparar (se vazio, mostra a média entre as Famílias):",
            options=modelos_disponiveis,
            default=[]
        )
    
    if modelos_selecionados:
        df_filtrado = df[df["Nome_do_modelo"].isin(modelos_selecionados)]
        cor = "Nome_do_modelo:N"
    else:
        df_filtrado = df
        cor = "Familia:N"
    
    # Agrupar
    df_digitos = df_filtrado.groupby(["Operacao", cor.split(":")[0]]).agg(
        Total=("Acerto_da_operacao", "count"),
        Acertos=("Acerto_da_operacao", "sum")
    ).reset_index()
    
    df_digitos["Taxa_Acerto"] = (df_digitos["Acertos"] / df_digitos["Total"]) * 100
    
    grafico_linhas = alt.Chart(df_digitos).mark_line(point=True, strokeWidth=3).encode(
        x=alt.X("Operacao:N", title="Complexidade da Conta", sort=["2 dígitos", "3 dígitos", "4 dígitos", "5 dígitos", "6 dígitos"]),
        y=alt.Y("Taxa_Acerto:Q", title="Taxa de Acerto (%)", scale=alt.Scale(domain=[0, 100])),
        color=alt.Color(cor, title="Legenda"),
        tooltip=[cor.split(":")[0], "Operacao", alt.Tooltip("Taxa_Acerto:Q", format=".1f", title="Acerto (%)"), "Total"]
    ).properties(height=450)
    
    st.altair_chart(grafico_linhas, use_container_width=True)

with aba3:
    st.subheader("Custo Total por Modelo Pago")
    st.markdown("Modelos gratuitos (OpenRouter:free) são desconsiderados deste gráfico.")
    
    if custo_total > 0:
        df_custo = df[df["Familia"] == "Vertex AI (Gemini)"].groupby("Nome_do_modelo")["custo_total"].sum().reset_index()
        df_custo = df_custo[df_custo["custo_total"] > 0].sort_values(by="custo_total", ascending=False)
        
        grafico_custo = alt.Chart(df_custo).mark_bar(color="#2ca02c").encode(
            x=alt.X("custo_total:Q", title="Custo Acumulado (BRL)"),
            y=alt.Y("Nome_do_modelo:N", sort="-x", title="Modelo (Gemini)"),
            tooltip=["Nome_do_modelo", alt.Tooltip("custo_total:Q", format=".4f", title="Custo (R$)")]
        ).properties(height=350)
        
        st.altair_chart(grafico_custo, use_container_width=True)
    else:
        st.info("Ainda não há dados financeiros capturados nos CSVs, ou o gasto foi literalmente zero até agora.")

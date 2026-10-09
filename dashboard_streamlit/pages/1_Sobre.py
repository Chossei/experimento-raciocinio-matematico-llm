"""
Página 1: Sobre o Experimento
Apresenta o storytelling completo: Introdução, Metodologia, Resultados Esperados e Métricas Globais.
"""

import sys
import os
import streamlit as st
import pandas as pd

# Adicionar pasta raiz do dashboard ao path para imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from utils.data_loader import carregar_todos_dados, obter_estatisticas_globais, MODELOS_GEMINI, CORES_MODELOS_AZUL
from utils.styles import aplicar_estilos_globais

aplicar_estilos_globais()

# -----------------------------------------------------------------------------
# CABEÇALHO DA PÁGINA
# -----------------------------------------------------------------------------
st.markdown('<div class="dash-title">📖 Sobre o Experimento</div>', unsafe_allow_html=True)
st.markdown(
    '<div class="dash-subtitle">'
    'Investigação da capacidade de raciocínio matemático, precisão aritmética e conformidade do formato de resposta em LLMs da família Google Gemini.'
    '</div>',
    unsafe_allow_html=True
)

# -----------------------------------------------------------------------------
# CARREGAMENTO DE DADOS E MÉTRICAS GLOBAIS
# -----------------------------------------------------------------------------
dfs = carregar_todos_dados()
stats = obter_estatisticas_globais(dfs)

col_top1, col_top2, col_top3 = st.columns([1, 1, 1])

with col_top1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Custo Total Acumulado</div>
        <div class="metric-value">${stats['custo_total_usd']:.2f} USD</div>
        <div class="metric-sub">OpenRouter & Vertex AI</div>
    </div>
    """, unsafe_allow_html=True)

with col_top2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Acurácia Global</div>
        <div class="metric-value">{stats['taxa_acerto_global']:.1f}%</div>
        <div class="metric-sub">Taxa média de acerto</div>
    </div>
    """, unsafe_allow_html=True)

with col_top3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Conformidade de Formato</div>
        <div class="metric-value">{stats['conformidade_global']:.1f}%</div>
        <div class="metric-sub">Respostas puramente numéricas</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# SEÇÃO: MODELOS DA FAMÍLIA GEMINI SELECIONADOS (COM CARD INTEGRADO)
# -----------------------------------------------------------------------------
st.markdown("### 🤖 Modelos da Família Gemini Avaliados")
st.markdown(
    f"Foram avaliados longitudinalmente os **{stats['modelos_testados']} modelos** oficiais da família Google Gemini, ordenados da geração anterior até a mais recente:"
)

cols_mod = st.columns(5)
for idx, modelo in enumerate(MODELOS_GEMINI):
    col_atual = cols_mod[idx % 5]
    cor_borda = CORES_MODELOS_AZUL.get(modelo, "#3b82f6")
    with col_atual:
        st.markdown(
            f'<div style="background-color: #f8fafc; border: 1.5px solid {cor_borda}; border-radius: 8px; padding: 8px; text-align: center; margin-bottom: 10px; font-weight: 600; font-size: 0.85rem; color: #0f172a;">'
            f'🔹 {modelo}'
            f'</div>',
            unsafe_allow_html=True
        )

st.markdown("<br>", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# CORPO DO STORYTELLING (INTRODUÇÃO, METODOLOGIA, RESULTADOS)
# -----------------------------------------------------------------------------
tab_intro, tab_metodo, tab_esperado = st.tabs([
    "🎯 Introdução & Hipótese",
    "⚙️ Metodologia & Operações",
    "📈 Resultados Esperados"
])

with tab_intro:
    col_ctx, col_hip = st.columns([1, 1])

    with col_ctx:
        st.markdown("### 📌 Contextualização do Experimento")
        st.markdown(
            'O experimento “Raciocínio Matemático nos LLMs” foi delineado no âmbito de Trabalho de Conclusão de Curso (TCC) de Átila Prudente, denominado "Engenharia de IA: Teoria e Aplicações", com o objetivo fundamental de analisar a capacidade analítica e aritmética dos modelos de inteligência artificial generativa em diferentes níveis de complexidade numérica.'
        )
        st.markdown(
            'Embora os LLMs alcancem desempenhos expressivos em benchmarks de linguagem natural e geração de código, tarefas determinísticas, como a execução de cálculos aritméticos em grande escala, revelam limitações na representação posicional e no planejamento cognitivo dos modelos.'
        )

    with col_hip:
        st.markdown("### 🎯 Hipótese")
        st.info(
            "A acurácia matemática dos LLMs decai, de forma não linear, com o crescimento da quantidade de dígitos (complexidade numérica), sendo mais degradada em expressões combinadas de operadores simples (juntando adições e multiplicações) e em multiplicações decimais do que em adições inteiras. Em complemento, a ativação de tokens de raciocínio atua como um compensador de acurácia, atenuando essa curva de decaimento."
        )


with tab_metodo:
    st.markdown("### Estrutura Metodológica")

    col_m1, col_m2 = st.columns(2)

    with col_m1:
        st.markdown("#### 1. Geração Controlada de Dados")
        st.markdown(f"""
        - **Total de Testes:** Foram avaliadas **{stats['total_testes']:,} inferências** no total através dos 10 modelos Gemini.
        - **Reprodutibilidade:** Os operandos foram sintetizados através de gerador pseudoaleatório baseado em NumPy fixando a semente `seed=123`.
        - **Estratificação por Dígitos:** Foram gerados operandos variando rigorosamente de **2 a 10 dígitos**.
        - **Volume Amostral:** 50 operações para cada quantidade de dígitos em cada tipo de teste.
        - **Precisão Arbitrária:** Os gabaritos numéricos de referência foram apurados com a biblioteca nativa `decimal.Decimal` com precisão de 100 dígitos, eliminando qualquer distorção de arredondamento por `float64`.
        """)

        st.markdown("#### 2. Engenharia de Prompt Estrita")
        st.markdown("""
        Para eliminar vieses na formulação, utilizou-se uma instrução invariável com comando de restrição de formato:
        ```text
        Sua tarefa é resolver uma operação matemática. 
        Responda a pergunta a seguir e retorne o resultado somente em 
        formato de número, sem unidades ou caracteres especiais.

        [Expressão Aritmética]
        ```
        """)

    with col_m2:
        st.markdown("#### 3. Tipos de Operações Testadas")
        st.markdown("""
        1. **Multiplicação inteira:** `a * b`
        2. **Multiplicação decimal:** `(a/10) * (b/10)`
        3. **Soma inteira:** `a + b`
        4. **Expressões combinadas:** `a * (b + c)`
        """)

        st.markdown("#### 4. Arquitetura de Inferência")
        st.markdown("""
        - **OpenRouter Batch API:** Execução massiva e assíncrona com redução de 50% nos custos.
        - **Inferência flexível:** controle das janelas de RPM (Requisições por Minuto) e RPD (Requisições por Dia).
        - **Budget de Raciocínio (Thinking Effort):** Configurado no nível mínimo permitido (`effort: none`, `minimal` ou `low`) para avaliar o raciocínio intrínseco dos modelos no estado base.
        """)

with tab_esperado:
    st.markdown("### O que se espera encontrar no dashboard?")

    st.markdown("""
    - **1. Curva de Decaimento por Complexidade:** O ponto exato de inflexão onde cada modelo começa a falhar na resolução de cálculos extensos.
    - **2. Discrepância Inteiro vs Decimal:** Avaliar se a mera inserção de ponto decimal desestabiliza a atenção dos LLMs em comparação à multiplicação inteira equivalente.
    - **3. Precedência de Operadores em Expressões Combinadas:** Avaliar se o cálculo composto `a * (b + c)` amplifica os erros por propagação da soma preliminar na multiplicação final.
    - **4. Impacto dos Tokens de Raciocínio:** Verificar a correlação entre a quantidade de tokens de raciocínio gerados e a preservação da acurácia em dígitos elevados.
    - **5. Qualidade do Pensamento (Inspeção de Raciocínio):** Comparação qualitativa lado a lado entre o raciocínio de um modelo quando obtém acerto versus quando comete um erro.
    - **6. Custos Financeiros:** Despesas em Dólar (USD) por modelo e por complexidade numérica.
    """)

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #64748b; font-size: 0.85rem;">
    Experimento Acadêmico de Raciocínio Matemático nos LLMs • Trabalho de Conclusão de Curso (TCC) • 2026
</div>
""", unsafe_allow_html=True)

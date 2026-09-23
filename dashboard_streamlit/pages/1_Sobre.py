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
from utils.data_loader import carregar_todos_dados, obter_estatisticas_globais, MODELOS_GEMINI
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

col1, col2, col3, col4 = st.columns(4)

with col1:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Total de Testes</div>
        <div class="metric-value">{stats['total_testes']:,}</div>
        <div class="metric-sub">Requisições avaliadas</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Custo Total Acumulado</div>
        <div class="metric-value">R$ {stats['custo_total_brl']:.2f}</div>
        <div class="metric-sub">~${stats['custo_total_usd']:.2f} USD (Câmbio 5.15)</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Modelos Avaliados</div>
        <div class="metric-value">{stats['modelos_testados']}</div>
        <div class="metric-sub">Família Google Gemini</div>
    </div>
    """, unsafe_allow_html=True)

with col4:
    st.markdown(f"""
    <div class="metric-card">
        <div class="metric-label">Conformidade de Formato</div>
        <div class="metric-value">{stats['conformidade_global']:.1f}%</div>
        <div class="metric-sub">Respostas puramente numéricas</div>
    </div>
    """, unsafe_allow_html=True)

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
    st.markdown("### Contextualização do Experimento")
    st.markdown(
        'O experimento “Raciocínio Matemático nos LLMs” foi delineado no âmbito de Trabalho de Conclusão de Curso (TCC) de Átila Prudente, denominado "Engenharia de IA: Teoria e Aplicações", com o objetivo fundamental de analisar a capacidade analítica e aritmética dos modelos de inteligência artificial generativa em diferentes níveis de complexidade numérica.'
    )
    st.markdown(
        'Embora os LLMs alcancem bons desempenhos em benchmarks de linguagem natural e geração de código, tarefas determinísticas, como a execução de cálculos aritméticos em grande escala, podem revelar limitações de representação posicional e do planejamento das cadeias de pensamento dos modelos.'
    )

    st.markdown("#### Hipótese")
    st.info(
        "A acurácia matemática dos LLMs decai, de forma não linear, com o crescimento da quantidade de dígitos (complexidade numérica), sendo mais degrada em expressões combinadas de operadores simples (juntando adições e multiplicações) e em multiplicações decimais do que em adições inteiras. Em complemento, a ativação de tokens de raciocínio pode atuar como um compensador de acurácia, reduzindo essa curva de decaimento."
    )

    st.markdown("#### Modelos da Família Gemini Selecionados")
    st.markdown(
        "Para garantir uma análise longitudinal e comparativa entre diferentes gerações e portes de modelos, foram avaliadas 10 variantes da família **Google Gemini**:"
    )
    
    cols_mod = st.columns(5)
    for idx, modelo in enumerate(MODELOS_GEMINI):
        col_atual = cols_mod[idx % 5]
        with col_atual:
            st.markdown(f'<span class="badge-pill badge-blue" style="margin-bottom: 8px; width: 100%; justify-content: center;">{modelo}</span>', unsafe_allow_html=True)

with tab_metodo:
    st.markdown("### Estrutura Metodológica")

    col_m1, col_m2 = st.columns(2)

    with col_m1:
        st.markdown("#### 1. Geração Controlada de Dados")
        st.markdown("""
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
        - **Inferência flexível:** controle das janelas de RPM (Requisições por Minuto) e RPD (Requisições por Dia) com redução de 50% nos custos.
        - **Budget de Raciocínio (Thinking Effort):** Configurado no nível mínimo permitido (`effort: none`, `minimal` ou `low`) para avaliar o raciocínio intrínseco dos modelos no estado base.
        """)

with tab_esperado:
    st.markdown("### O que se espera encontrar no dashboard?")

    st.markdown("""
    - **1. Curva de Decaimento por Complexidade:** O ponto exato de inflexão onde cada modelo começa a errar.
    - **2. Discrepância Inteiro vs Decimal:** Avaliar se a mera inserção de vírgula flutuante/ponto decimal desestabiliza a capacidade de atenção dos LLMs em comparação à multiplicação inteira equivalente.
    - **3. Precedência de Operadores em Expressões Combinadas:** Avaliar se o cálculo composto `a * (b + c)` amplifica os erros por propagação da soma preliminar na multiplicação final.
    - **4. Impacto dos Tokens de Raciocínio:** Verificar se existe associação entre a acurácia obtida e os tokens de pensamentos gerados.
    - **5. Qualidade do Pensamento (Tokens de Raciocínio):** Comparação qualitativa lado a lado entre a linha de raciocínio de um modelo quando ele atinge a resposta correta versus quando ele comete um erro de cálculo.
    - **6. Custos financeiros:** Custo em Reais (BRL) por operação.
    """)

st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #64748b; font-size: 0.85rem;">
    Experimento Acadêmico de Raciocínio Matemático nos LLMs • Trabalho de Conclusão de Curso (TCC) • 2026
</div>
""", unsafe_allow_html=True)

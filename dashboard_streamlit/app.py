"""
Ponto de Entrada Principal do Novo Dashboard Streamlit Multipáginas.
Configura roteamento de páginas e navegação unificada.
"""

import os
import sys

# Garantir que o diretório raiz esteja no topo do sys.path para resolução consistente de módulos
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

import streamlit as st

st.set_page_config(
    page_title="Raciocínio Matemático nos LLMs | TCC",
    page_icon="🧮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Caminho absoluto para a pasta de páginas
pages_dir = os.path.join(BASE_DIR, "pages")

# Configuração da navegação moderna Streamlit
pg = st.navigation([
    st.Page(
        os.path.join(pages_dir, "1_Sobre.py"),
        title="Sobre o Experimento",
        icon="📖",
        default=True
    ),
    st.Page(
        os.path.join(pages_dir, "2_Resultados.py"),
        title="Resultados",
        icon="📊"
    ),
    st.Page(
        os.path.join(pages_dir, "3_Custos_Formatos_Erros.py"),
        title="Custos, Formatos e Erros",
        icon="💰"
    )
])

pg.run()

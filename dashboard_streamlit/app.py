"""
Ponto de Entrada Principal do Novo Dashboard Streamlit Multipáginas.
Configura roteamento de páginas e navegação unificada.
"""

import os
import streamlit as st

st.set_page_config(
    page_title="Raciocínio Matemático nos LLMs | TCC",
    page_icon="🧮",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Caminho absoluto para a pasta de páginas
base_dir = os.path.dirname(os.path.abspath(__file__))
pages_dir = os.path.join(base_dir, "pages")

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

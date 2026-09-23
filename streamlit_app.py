"""
Ponto de Entrada Principal para Deploy no Streamlit Community Cloud (streamlit_app.py).
Executa o novo Dashboard Multipáginas localizado em dashboard_streamlit/app.py.
"""

import os
import sys

# Garante inclusão do diretório do dashboard no PYTHONPATH
base_dir = os.path.dirname(os.path.abspath(__file__))
dash_dir = os.path.join(base_dir, "dashboard_streamlit")
if dash_dir not in sys.path:
    sys.path.insert(0, dash_dir)

# Execução direta do app.py do dashboard_streamlit
import runpy
caminho_app = os.path.join(dash_dir, "app.py")
runpy.run_path(caminho_app, run_name="__main__")

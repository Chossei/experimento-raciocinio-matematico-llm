"""
Ponto de Entrada Principal para Deploy no Streamlit Community Cloud (dashboard.py).
Executa o novo Dashboard Multipáginas localizado em dashboard_streamlit/app.py.
Garante compatibilidade total caso o deploy no Streamlit Cloud aponte para dashboard.py.
"""

import os
import sys

base_dir = os.path.dirname(os.path.abspath(__file__))
dash_dir = os.path.join(base_dir, "dashboard_streamlit")
if dash_dir not in sys.path:
    sys.path.insert(0, dash_dir)

import runpy
caminho_app = os.path.join(dash_dir, "app.py")
runpy.run_path(caminho_app, run_name="__main__")

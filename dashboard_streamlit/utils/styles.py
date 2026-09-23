"""
Módulo de Estilos e Design System para o Dashboard Streamlit.
Fornece CSS customizado, tema moderno, cards de métricas e estilos destacados.
"""

import streamlit as st

def aplicar_estilos_globais():
    """Aplica folha de estilos personalizada com estética moderna e polida."""
    st.markdown("""
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        }

        /* Títulos principais e subtítulos */
        .dash-title {
            font-size: 2.2rem;
            font-weight: 800;
            color: #0f172a;
            margin-bottom: 0.2rem;
            letter-spacing: -0.02em;
        }
        .dash-subtitle {
            font-size: 1.05rem;
            color: #64748b;
            margin-bottom: 1.5rem;
            line-height: 1.5;
        }

        /* Cards de Métricas em Destaque */
        .metric-card {
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            border: 1px solid #e2e8f0;
            border-radius: 12px;
            padding: 1.2rem;
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.05), 0 2px 4px -2px rgba(0, 0, 0, 0.05);
            transition: transform 0.2s ease, box-shadow 0.2s ease;
        }
        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08);
        }
        .metric-label {
            font-size: 0.85rem;
            font-weight: 600;
            color: #64748b;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 0.3rem;
        }
        .metric-value {
            font-size: 1.9rem;
            font-weight: 800;
            color: #0f172a;
            letter-spacing: -0.02em;
        }
        .metric-sub {
            font-size: 0.8rem;
            color: #94a3b8;
            margin-top: 0.2rem;
        }

        /* Badges de Destaque */
        .badge-pill {
            display: inline-flex;
            align-items: center;
            padding: 0.25rem 0.75rem;
            border-radius: 9999px;
            font-size: 0.8rem;
            font-weight: 600;
        }
        .badge-blue {
            background-color: #eff6ff;
            color: #1d4ed8;
            border: 1px solid #bfdbfe;
        }
        .badge-green {
            background-color: #ecfdf5;
            color: #047857;
            border: 1px solid #a7f3d0;
        }
        .badge-amber {
            background-color: #fffbeb;
            color: #b45309;
            border: 1px solid #fde68a;
        }

        /* Seção "Como os modelos pensam" - Destaque Sucesso e Falha */
        .thought-container-success {
            background-color: #f0fdf4;
            border: 2px solid #22c55e;
            border-radius: 12px;
            padding: 1.2rem;
            margin-top: 0.8rem;
        }
        .thought-container-error {
            background-color: #fef2f2;
            border: 2px solid #ef4444;
            border-radius: 12px;
            padding: 1.2rem;
            margin-top: 0.8rem;
        }
        .thought-header-success {
            color: #15803d;
            font-weight: 700;
            font-size: 1.15rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 0.6rem;
        }
        .thought-header-error {
            color: #b91c1c;
            font-weight: 700;
            font-size: 1.15rem;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            margin-bottom: 0.6rem;
        }
        .thought-box {
            background-color: #ffffff;
            border: 1px solid #e2e8f0;
            border-radius: 8px;
            padding: 1rem;
            font-family: monospace;
            font-size: 0.85rem;
            max-height: 420px;
            overflow-y: auto;
            white-space: pre-wrap;
            line-height: 1.6;
        }

        /* Tabs aprimoradas */
        .stTabs [data-baseweb="tab-list"] {
            gap: 8px;
        }
        .stTabs [data-baseweb="tab"] {
            border-radius: 8px;
            padding: 8px 16px;
            font-weight: 600;
            font-size: 0.95rem;
        }

        /* Alerta discreto */
        .info-box {
            background-color: #f8fafc;
            border-left: 4px solid #3b82f6;
            padding: 0.8rem 1.2rem;
            border-radius: 0 8px 8px 0;
            margin-bottom: 1.2rem;
            font-size: 0.9rem;
            color: #334155;
        }
    </style>
    """, unsafe_allow_html=True)

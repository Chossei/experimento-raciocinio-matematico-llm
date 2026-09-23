"""
Módulo de Carregamento e Tratamento Unificado de Dados para o Dashboard Streamlit.
Focado exclusivamente nos 10 modelos da família Gemini.
"""

import os
import re
import pandas as pd
import streamlit as st

ORDEM_DIGITOS = [f"{i} dígitos" for i in range(2, 11)]
ORDEM_DIGITOS_NUM = [str(i) for i in range(2, 11)]

MODELOS_GEMINI = [
    "gemini-3.8-flash",
    "gemini-3.7-flash",
    "gemini-3.6-flash",
    "gemini-3.5-flash",
    "gemini-3.5-flash-lite",
    "gemini-3.1-flash-lite",
    "gemini-3.1-pro-preview",
    "gemini-3-flash-preview",
    "gemini-2.5-pro",
    "gemini-2.5-flash"
]

CORES_OPERACOES = {
    "Multiplicação Inteira": "#8b5cf6",     # Roxo
    "Multiplicação Decimal": "#f97316",     # Laranja
    "Soma": "#3b82f6",                      # Azul
    "Expressões Combinadas": "#10b981"      # Verde esmeralda
}

def obter_caminho_dados():
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_dir, "dados")

@st.cache_data(ttl=60)
def carregar_todos_dados():
    """Carrega e padroniza os 4 conjuntos de dados de resultados."""
    dados_dir = obter_caminho_dados()
    dfs = {}

    # 1. Multiplicação Inteira
    p_mult = os.path.join(dados_dir, "resultados_multiplicacao.csv")
    if os.path.exists(p_mult):
        df_mult = pd.read_csv(p_mult, dtype=str)
        df_mult["Tipo_Operacao"] = "Multiplicação Inteira"
        dfs["multiplicacao"] = normalizar_dataframe(df_mult, tipo="multiplicacao")
    else:
        dfs["multiplicacao"] = pd.DataFrame()

    # 2. Multiplicação Decimal
    p_dec = os.path.join(dados_dir, "resultados_decimal.csv")
    if os.path.exists(p_dec):
        df_dec = pd.read_csv(p_dec, dtype=str)
        df_dec["Tipo_Operacao"] = "Multiplicação Decimal"
        dfs["decimal"] = normalizar_dataframe(df_dec, tipo="decimal")
    else:
        dfs["decimal"] = pd.DataFrame()

    # 3. Operações de Soma
    p_soma = os.path.join(dados_dir, "resultados_soma.csv")
    if os.path.exists(p_soma):
        df_soma = pd.read_csv(p_soma, dtype=str)
        df_soma["Tipo_Operacao"] = "Soma"
        dfs["soma"] = normalizar_dataframe(df_soma, tipo="soma")
    else:
        dfs["soma"] = pd.DataFrame()

    # 4. Expressões Combinadas
    p_comb = os.path.join(dados_dir, "resultados_combinadas.csv")
    if os.path.exists(p_comb):
        df_comb = pd.read_csv(p_comb, dtype=str)
        df_comb["Tipo_Operacao"] = "Expressões Combinadas"
        dfs["combinadas"] = normalizar_dataframe(df_comb, tipo="combinadas")
    else:
        dfs["combinadas"] = pd.DataFrame()

    # Dataframe unificado com todas as operações
    lista_dfs = [df for df in dfs.values() if not df.empty]
    if lista_dfs:
        dfs["geral"] = pd.concat(lista_dfs, ignore_index=True)
    else:
        dfs["geral"] = pd.DataFrame()

    return dfs

def normalizar_dataframe(df, tipo):
    """Uniformiza os nomes de colunas e tipos de dados essenciais, evitando duplicatas de colunas."""
    df = df.loc[:, ~df.columns.duplicated()].copy()

    mapeamento_colunas = [
        ("Nome do modelo", "Nome_do_modelo"),
        ("nome do modelo", "Nome_do_modelo"),
        ("quantidade de digitos", "Operacao"),
        ("Quantidade de digitos", "Operacao"),
        ("tipo", "Operacao"),
        ("resultado bruto do modelo", "Resposta_bruta"),
        ("resultado tratado do modelo", "Resultado_do_modelo"),
        ("resultado da operacao", "Resultado_original"),
        ("Resultado_original_decimal", "Resultado_original"),
        ("resultado original", "Resultado_original"),
        ("Acerto da operacao", "Acerto_da_operacao"),
        ("acerto da operacao", "Acerto_da_operacao"),
        ("Acerto do formato de resposta", "Acerto_do_formato_de_resposta"),
        ("acerto do formato de resposta", "Acerto_do_formato_de_resposta"),
        ("conta", "Conta"),
        ("Conta_decimal", "Conta"),
        ("custo total", "custo_total"),
        ("Custo total", "custo_total"),
        ("custo de input tokens", "custo_input"),
        ("custo de output tokens", "custo_output"),
        ("quantidade de reasoning tokens gerados", "reasoning_tokens"),
        ("Quantidade de reasoning tokens gerados", "reasoning_tokens"),
        ("resumo do raciocinio", "resumo_raciocinio")
    ]

    for origem, destino in mapeamento_colunas:
        if origem in df.columns:
            if destino in df.columns and origem != destino:
                mask_vazio = df[destino].isna() | (df[destino].astype(str).str.strip() == "")
                df.loc[mask_vazio, destino] = df.loc[mask_vazio, origem]
                df = df.drop(columns=[origem])
            elif destino not in df.columns:
                df = df.rename(columns={origem: destino})

    df = df.loc[:, ~df.columns.duplicated()].copy()

    # Filtrar estritamente modelos Gemini
    if "Nome_do_modelo" in df.columns:
        df = df[df["Nome_do_modelo"].isin(MODELOS_GEMINI)].copy()

    # Normalizar booleanos
    if "Acerto_da_operacao" in df.columns:
        df["Acerto_da_operacao"] = df["Acerto_da_operacao"].astype(str).str.strip().str.lower().isin(["true", "1"])
    else:
        df["Acerto_da_operacao"] = False

    if "Acerto_do_formato_de_resposta" in df.columns:
        df["Acerto_do_formato_de_resposta"] = df["Acerto_do_formato_de_resposta"].astype(str).str.strip().str.lower().isin(["true", "1"])
    else:
        df["Acerto_do_formato_de_resposta"] = True

    # Normalizar custos
    if "custo_total" in df.columns:
        df["custo_total"] = pd.to_numeric(df["custo_total"], errors="coerce").fillna(0.0)
    else:
        df["custo_total"] = 0.0

    # Normalizar reasoning tokens
    if "reasoning_tokens" in df.columns:
        df["reasoning_tokens"] = pd.to_numeric(df["reasoning_tokens"], errors="coerce").fillna(0).astype(int)
    else:
        df["reasoning_tokens"] = 0

    # Normalizar coluna Operacao (padronizar formato 'X dígitos') e criar coluna Digitos (somente número)
    if "Operacao" in df.columns:
        df["Operacao"] = df["Operacao"].astype(str).apply(padronizar_digitos)
        df["Digitos"] = df["Operacao"].apply(extrair_apenas_digito)
    else:
        df["Operacao"] = "2 dígitos"
        df["Digitos"] = "2"

    # Preencher colunas ausentes comuns
    for col in ["Resposta_bruta", "Resultado_do_modelo", "Resultado_original", "Conta", "resumo_raciocinio"]:
        if col not in df.columns:
            df[col] = ""
        else:
            df[col] = df[col].fillna("").astype(str)

    return df

def padronizar_digitos(val):
    if not val:
        return "2 dígitos"
    v = str(val).strip()
    match = re.search(r'\d+', v)
    if match:
        num = match.group()
        return f"{num} dígitos"
    return v

def extrair_apenas_digito(val):
    if not val:
        return "2"
    v = str(val).strip()
    match = re.search(r'\d+', v)
    if match:
        return match.group()
    return v

def obter_estatisticas_globais(dfs):
    """Calcula estatísticas de alto nível para exibição na página Sobre."""
    df_geral = dfs.get("geral", pd.DataFrame())
    if df_geral.empty:
        return {
            "total_testes": 0,
            "custo_total_brl": 0.0,
            "custo_total_usd": 0.0,
            "taxa_acerto_global": 0.0,
            "conformidade_global": 0.0,
            "modelos_testados": len(MODELOS_GEMINI)
        }

    total_testes = len(df_geral)
    custo_total_brl = df_geral["custo_total"].sum()
    custo_total_usd = custo_total_brl / 5.15 if custo_total_brl > 0 else 0.0
    taxa_acerto_global = (df_geral["Acerto_da_operacao"].mean() * 100) if total_testes > 0 else 0.0
    conformidade_global = (df_geral["Acerto_do_formato_de_resposta"].mean() * 100) if total_testes > 0 else 0.0

    return {
        "total_testes": total_testes,
        "custo_total_brl": custo_total_brl,
        "custo_total_usd": custo_total_usd,
        "taxa_acerto_global": taxa_acerto_global,
        "conformidade_global": conformidade_global,
        "modelos_testados": df_geral["Nome_do_modelo"].nunique()
    }

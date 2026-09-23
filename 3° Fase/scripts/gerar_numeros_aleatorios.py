"""Script Central de Geração de Números Aleatórios e Operações Matemáticas

Conforme 'Plano de Implementação - FINAL.md' (Item 1 / Quadro 1):
Gera e salva dataframes padronizados em 'operacoes/operacoes_(tipo da operacao).csv':
1. Somas inteiras: a + b
2. Multiplicações inteiras: a * b
3. Expressões combinadas: a * (b + c)
"""

import os
import argparse
import numpy as np
import pandas as pd
from decimal import Decimal

PASTA_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
PASTA_RAIZ = os.path.dirname(PASTA_SCRIPTS)
PASTA_OPERACOES = os.path.join(PASTA_RAIZ, "operacoes")
os.makedirs(PASTA_OPERACOES, exist_ok=True)

def gerar_operacoes_soma(seed=123):
    np.random.seed(seed)
    dados = []
    for digitos in range(2, 11):
        low_val = 10**(digitos - 1)
        high_val = 10**digitos
        tipo_str = f"{digitos} dígitos"
        for _ in range(50):
            a = int(np.random.randint(low=low_val, high=high_val, dtype=np.int64))
            b = int(np.random.randint(low=low_val, high=high_val, dtype=np.int64))
            resultado_dec = Decimal(str(a)) + Decimal(str(b))
            conta_str = f"{a}+{b} = ?"
            dados.append({
                "num_a": a,
                "num_b": b,
                "conta": conta_str,
                "resultado da operacao": str(resultado_dec),
                "quantidade de digitos": tipo_str
            })
    df = pd.DataFrame(dados)
    caminho = os.path.join(PASTA_OPERACOES, "operacoes_soma.csv")
    df.to_csv(caminho, index=False)
    print(f"[Soma] Salvo em: {caminho} ({len(df)} linhas)")
    return df

def gerar_operacoes_multiplicacao(seed=123):
    np.random.seed(seed)
    dados = []
    for digitos in range(2, 11):
        low_val = 10**(digitos - 1)
        high_val = 10**digitos
        tipo_str = f"{digitos} dígitos"
        for _ in range(50):
            a = int(np.random.randint(low=low_val, high=high_val, dtype=np.int64))
            b = int(np.random.randint(low=low_val, high=high_val, dtype=np.int64))
            resultado_dec = Decimal(str(a)) * Decimal(str(b))
            conta_str = f"{a} * {b} = ?"
            dados.append({
                "num_a": a,
                "num_b": b,
                "conta": conta_str,
                "resultado da operacao": str(resultado_dec),
                "quantidade de digitos": tipo_str
            })
    df = pd.DataFrame(dados)
    caminho = os.path.join(PASTA_OPERACOES, "operacoes_multiplicacao.csv")
    df.to_csv(caminho, index=False)
    print(f"[Multiplicação] Salvo em: {caminho} ({len(df)} linhas)")
    return df

def gerar_operacoes_combinadas(seed=123):
    np.random.seed(seed)
    dados = []
    for digitos in range(2, 11):
        low_val = 10**(digitos - 1)
        high_val = 10**digitos
        tipo_str = f"{digitos} dígitos"
        for _ in range(50):
            a = int(np.random.randint(low=low_val, high=high_val, dtype=np.int64))
            b = int(np.random.randint(low=low_val, high=high_val, dtype=np.int64))
            c = int(np.random.randint(low=low_val, high=high_val, dtype=np.int64))
            resultado_dec = Decimal(str(a)) * (Decimal(str(b)) + Decimal(str(c)))
            conta_str = f"{a} * ({b} + {c}) = ?"
            dados.append({
                "num_a": a,
                "num_b": b,
                "num_c": c,
                "conta": conta_str,
                "resultado da operacao": str(resultado_dec),
                "quantidade de digitos": tipo_str
            })
    df = pd.DataFrame(dados)
    caminho = os.path.join(PASTA_OPERACOES, "operacoes_combinadas.csv")
    df.to_csv(caminho, index=False)
    print(f"[Combinadas] Salvo em: {caminho} ({len(df)} linhas)")
    return df

def main():
    parser = argparse.ArgumentParser(description="Geração de operações matemáticas com NumPy (Seed 123)")
    parser.add_argument("--tipo", choices=["todos", "soma", "multiplicacao", "combinadas"], default="combinadas",
                        help="Tipo de operação a ser gerada (padrão: combinadas)")
    args = parser.parse_args()

    if args.tipo in ["todos", "soma"]:
        gerar_operacoes_soma()
    if args.tipo in ["todos", "multiplicacao"]:
        gerar_operacoes_multiplicacao()
    if args.tipo in ["todos", "combinadas"]:
        gerar_operacoes_combinadas()

if __name__ == "__main__":
    main()

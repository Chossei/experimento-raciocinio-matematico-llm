"""Módulo Gerador de Operações - 3° Experimento: Expressões Combinadas a * (b + c)

Conforme estabelecido em 'Plano de Implementação - FINAL.md':
- Gera 50 números aleatórios 'a', 50 'b' e 50 'c' por quantidade de dígitos (2 a 10 dígitos)
- Semente fixa: 123 (numpy)
- Expressão: a * (b + c)
- Total: 9 complexidades * 50 = 450 operações
- Salvamento em 'operacoes/operacoes_combinadas.csv' com colunas do Quadro 1.
"""

import os
import numpy as np
import pandas as pd
from decimal import Decimal

def gerar_operacoes_combinadas():
    # Fixar semente para reprodutibilidade estrita
    np.random.seed(123)
    
    dados = []
    
    for digitos in range(2, 11):
        low_val = 10**(digitos - 1)
        high_val = 10**digitos
        tipo_str = f"{digitos} dígitos"
        
        for _ in range(50):
            a = int(np.random.randint(low=low_val, high=high_val, dtype=np.int64))
            b = int(np.random.randint(low=low_val, high=high_val, dtype=np.int64))
            c = int(np.random.randint(low=low_val, high=high_val, dtype=np.int64))
            
            # Cálculo matemático com a biblioteca Decimal (precisão infinita, sem overflow de int64/float64)
            a_dec = Decimal(str(a))
            b_dec = Decimal(str(b))
            c_dec = Decimal(str(c))
            resultado_dec = a_dec * (b_dec + c_dec)
            
            # Formato da conta: a * (b + c) = ?
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
    
    pasta_script = os.path.dirname(os.path.abspath(__file__))
    pasta_raiz_fase3 = os.path.dirname(os.path.dirname(pasta_script))
    caminho_csv = os.path.join(pasta_raiz_fase3, "operacoes", "operacoes_combinadas.csv")
    
    os.makedirs(os.path.dirname(caminho_csv), exist_ok=True)
    df.to_csv(caminho_csv, index=False)
    print(f"Arquivo gerado com sucesso: {caminho_csv} ({len(df)} operacoes)")
    
    return df

if __name__ == "__main__":
    gerar_operacoes_combinadas()

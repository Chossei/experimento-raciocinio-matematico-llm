import os
import numpy as np
import pandas as pd

def gerar_operacoes_soma():
    """Gera 50 operações de soma por quantidade de dígitos (2 a 10 dígitos)

    com reprodutibilidade garantida por numpy seed 123.
    Total: 9 complexidades * 50 = 450 operações.
    """
    np.random.seed(123)
    dados = []

    for digitos in range(2, 11):
        low_val = 10**(digitos - 1)
        high_val = 10**digitos
        tipo_str = f"{digitos} dígitos"

        for _ in range(50):
            a = np.random.randint(low=low_val, high=high_val, dtype=np.int64)
            b = np.random.randint(low=low_val, high=high_val, dtype=np.int64)
            resultado = int(a) + int(b)
            conta_str = f"{a}+{b} = ?"

            dados.append({
                'num_a': a,
                'num_b': b,
                'string': conta_str,
                'Conta': conta_str,
                'resultado': resultado,
                'Resultado_original': resultado,
                'tipo': tipo_str,
                'Operacao': tipo_str
            })

    df = pd.DataFrame(dados)

    # Pastas de destino
    pastas_destino = [
        'dados',
        'gemini/openrouter/operacoes_soma',
        'github_repo/dados',
        'github_repo/gemini/openrouter/operacoes_soma'
    ]

    for pasta in pastas_destino:
        os.makedirs(pasta, exist_ok=True)
        caminho_csv = os.path.join(pasta, 'operacoes_soma.csv')
        df.to_csv(caminho_csv, index=False)
        print(f"Salvo: {caminho_csv} ({len(df)} linhas)")

    return df

if __name__ == '__main__':
    gerar_operacoes_soma()

import os
import re
import asyncio
import pandas as pd
import numpy as np
import openai
from openai import AsyncOpenAI
from dotenv import load_dotenv
import time

# Carrega as variáveis de ambiente
load_dotenv('chave.env')

# Obter todas as chaves disponíveis
CHAVES_API = []
for k, v in os.environ.items():
    if k.startswith("OPEN_ROUTER_API_KEY") and v.strip():
        CHAVES_API.append(v.strip())

if not CHAVES_API:
    raise ValueError("Nenhuma chave OPEN_ROUTER_API_KEY encontrada no arquivo chave.env.")

indice_chave_atual = 0

def get_client():
    return AsyncOpenAI(
        base_url='https://openrouter.ai/api/v1',
        api_key=CHAVES_API[indice_chave_atual]
    )

client = get_client()

def alternar_chave():
    global indice_chave_atual, client
    if indice_chave_atual < len(CHAVES_API) - 1:
        indice_chave_atual += 1
        client = get_client()
        print(f"\n[Aviso] Alternando para a chave da API {indice_chave_atual + 1}...")
        return True
    return False

# Lista de modelos gratuitos
modelos_gratuitos = [
    'dots-3-note-preview:free', 'liquid/lfm-2.5-2.6b:free',
    'nvidia/nemotron-3.5-lightning:free', 'thinkingmachines/inkling-small:free',
    'poolside/laguna-s-2.1:free', 'thinkingmachines/inkling:free',
    'poolside/laguna-xs-2.1:free', 'cohere/north-mini-code:free',
    'z-ai/glm-5.2:free', 'nvidia/nemotron-3.5-content-safety:free',
    'nvidia/nemotron-3-ultra-550b-a55b:free', 'minimax/minimax-m3:free',
    'nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free',
    'google/gemma-4-26b-a4b-it:free', 'google/gemma-4-31b-it:free',
    'minimax/minimax-m2.7:free', 'nvidia/nemotron-3-super-120b-a12b:free'
]

# Caminhos dos arquivos
DADOS_DIR = 'dados'
ARQUIVO_OPERACOES = os.path.join(DADOS_DIR, 'operacoes.csv')
ARQUIVO_RESULTADOS = os.path.join(DADOS_DIR, 'resultados_experimento.csv')

# Limites
TAMANHO_LOTE = 20 # Para fazer backup e respeitar os 20 RPM do OpenRouter

def gerar_operacoes():
    """Gera as operações matemáticas caso a base de dados ainda não exista."""
    print("Gerando base de operações matemáticas...")
    np.random.seed(123)
    dados_experimento = []
    
    # Gera de 2 a 6 dígitos
    for digitos in range(2, 7):
        low_val = 10**(digitos - 1)
        high_val = 10**digitos
        tipo_str = f"{digitos} dígitos"
        
        for i in range(100):
            a = np.random.randint(low=low_val, high=high_val)
            b = np.random.randint(low=low_val, high=high_val)
            resultado = int(a * b) # Evita tipos numpy longos
            
            dados_experimento.append({
                'num_a': a,
                'num_b': b,
                'Conta': f'{a}x{b} = ?',
                'Resultado_original': resultado,
                'Operacao': tipo_str
            })
            
    df = pd.DataFrame(dados_experimento)
    df.to_csv(ARQUIVO_OPERACOES, index=False)
    print(f"Total de {len(df)} operações geradas e salvas em {ARQUIVO_OPERACOES}.")
    return df

def extrair_numero(texto):
    """Extrai apenas os dígitos numéricos da resposta do modelo usando Regex."""
    # Encontra números. Pode conter sinal de menos caso tente responder negativos, mas aqui é só multiplicar positivos.
    padrao = re.compile(r'\d+')
    numeros = padrao.findall(texto)
    if numeros:
        # Junta tudo, ex: caso responda 1 234 567
        return int("".join(numeros))
    return None

async def realizar_chamada(modelo, conta_dict):
    """Realiza uma chamada para um único modelo avaliando uma única conta."""
    prompt_geral = f"""
    Sua tarefa é resolver operações matemáticas.
    Responda a pergunta a seguir e retorne o resultado SOMENTE em formato de número, sem unidades ou caracteres especiais.
    {conta_dict['Conta']}
    """
    
    try:
        resposta = await client.chat.completions.create(
            model=modelo,
            messages=[{'role': 'user', 'content': prompt_geral}]
        )
        texto_resposta = resposta.choices[0].message.content
        
        # Análise
        valor_extraido = extrair_numero(texto_resposta)
        acerto_formato = True
        
        # Se contiver letras ou outros caracteres não numéricos (exceto whitespace), errou formato
        if re.search(r'[a-zA-Z]', texto_resposta):
            acerto_formato = False
            
        acerto_operacao = (valor_extraido == conta_dict['Resultado_original'])
        
        return {
            'Nome_do_modelo': modelo,
            'Operacao': conta_dict['Operacao'],
            'Resultado_do_modelo': valor_extraido,
            'Resposta_bruta': texto_resposta,
            'Resultado_original': conta_dict['Resultado_original'],
            'Acerto_da_operacao': acerto_operacao,
            'Acerto_do_formato_de_resposta': acerto_formato,
            'Conta': conta_dict['Conta']
        }
    except openai.RateLimitError as e:
        print(f"Rate Limit (429) atingido na chave atual ao testar {modelo}.")
        return {"status": "rate_limit", "modelo": modelo, "conta_dict": conta_dict}
    except openai.APIStatusError as e:
        if e.status_code in [402, 403]:
            # Erros comuns de falta de crédito
            print(f"Erro {e.status_code} na chave atual ao testar {modelo} (possivelmente sem saldo).")
            return {"status": "rate_limit", "modelo": modelo, "conta_dict": conta_dict}
        else:
            print(f"Erro na API com o modelo {modelo}: {e}")
            return None
    except Exception as e:
        print(f"Erro com o modelo {modelo}: {e}")
        return None

async def main():
    if not os.path.exists(DADOS_DIR):
        os.makedirs(DADOS_DIR)
        
    # Carrega ou gera operações
    if os.path.exists(ARQUIVO_OPERACOES):
        df_operacoes = pd.read_csv(ARQUIVO_OPERACOES)
    else:
        df_operacoes = gerar_operacoes()

    # Carrega resultados existentes (backup)
    if os.path.exists(ARQUIVO_RESULTADOS):
        df_resultados = pd.read_csv(ARQUIVO_RESULTADOS)
    else:
        # Cria dataframe vazio com as colunas esperadas
        colunas = [
            'Nome_do_modelo', 'Operacao', 'Resultado_do_modelo', 'Resposta_bruta',
            'Resultado_original', 'Acerto_da_operacao', 'Acerto_do_formato_de_resposta', 'Conta'
        ]
        df_resultados = pd.DataFrame(columns=colunas)

    # Identifica as combinações (modelo, conta) que já foram feitas
    concluidos = set()
    if not df_resultados.empty:
        for _, row in df_resultados.iterrows():
            chave = f"{row['Nome_do_modelo']}||{row['Conta']}"
            concluidos.add(chave)

    # Lista de tarefas pendentes (Agrupando por contas e depois modelos)
    pendencias = []
    for _, row in df_operacoes.iterrows():
        for modelo in modelos_gratuitos:
            chave = f"{modelo}||{row['Conta']}"
            if chave not in concluidos:
                pendencias.append((modelo, row.to_dict()))

    print(f"Total de operações pendentes: {len(pendencias)}")
    if len(pendencias) == 0:
        print("Experimento concluído! Nenhuma operação pendente.")
        return

    requisicoes_feitas = 0
    resultados_novos = []

    # Processa pendências
    while pendencias:
        lote_atual = pendencias[:TAMANHO_LOTE]
        pendencias = pendencias[TAMANHO_LOTE:]
        
        print(f"Processando lote de {len(lote_atual)} requisições... (Requisitadas até agora nesta sessão: {requisicoes_feitas})")
        
        tarefas = [realizar_chamada(modelo, conta) for modelo, conta in lote_atual]
        respostas = await asyncio.gather(*tarefas)
        
        teve_rate_limit = False
        
        for res in respostas:
            if res is not None:
                if isinstance(res, dict) and res.get("status") == "rate_limit":
                    teve_rate_limit = True
                    # Devolve para o INÍCIO da fila
                    pendencias.insert(0, (res["modelo"], res["conta_dict"]))
                else:
                    resultados_novos.append(res)
                    requisicoes_feitas += 1
        
        # Salva o backup
        if resultados_novos:
            novo_df = pd.DataFrame(resultados_novos)
            if os.path.exists(ARQUIVO_RESULTADOS):
                # Anexa ao existente
                df_salvo = pd.read_csv(ARQUIVO_RESULTADOS)
                df_salvo = pd.concat([df_salvo, novo_df], ignore_index=True)
                df_salvo.to_csv(ARQUIVO_RESULTADOS, index=False)
            else:
                novo_df.to_csv(ARQUIVO_RESULTADOS, index=False)
            
            # Limpa para a próxima iteração
            resultados_novos = []
            print(f"Backup salvo com sucesso.")
            
        if teve_rate_limit:
            # Se a chave atingiu limite de saldo/requisição, tenta a próxima
            if not alternar_chave():
                print("Todas as chaves atingiram o Rate Limit ou acabaram os créditos. Encerrando o script por hoje.")
                break
        elif pendencias:
            print("Aguardando 90 segundos para garantir a reinicialização do Rate Limit do OpenRouter (20 RPM)...")
            await asyncio.sleep(90)

if __name__ == '__main__':
    asyncio.run(main())

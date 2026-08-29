import os
import re
import asyncio
import pandas as pd
import numpy as np
import openai
from openai import AsyncOpenAI
from dotenv import load_dotenv
import time
import logging
from datetime import datetime

# ==========================================
# CONFIGURAÇÃO DE LOGS
# ==========================================
if not os.path.exists('logs'):
    os.makedirs('logs')

data_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = os.path.join('logs', f'execucao_{data_hora}.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logging.info("=== Iniciando Pipeline de Experimento Matemático ===")

# ==========================================
# VARIÁVEIS DE AMBIENTE E CHAVES
# ==========================================
load_dotenv('chave.env')

CHAVES_API = []
for k, v in os.environ.items():
    if k.startswith("OPEN_ROUTER_API_KEY") and v.strip():
        CHAVES_API.append(v.strip())

if not CHAVES_API:
    logging.error("Nenhuma chave OPEN_ROUTER_API_KEY encontrada no arquivo chave.env.")
    raise ValueError("Nenhuma chave OPEN_ROUTER_API_KEY encontrada no arquivo chave.env.")

indice_chave_atual = 0
logging.info(f"Total de {len(CHAVES_API)} chave(s) carregada(s).")

def get_client():
    return AsyncOpenAI(
        base_url='https://openrouter.ai/api/v1',
        api_key=CHAVES_API[indice_chave_atual],
        max_retries=0
    )

client = get_client()

def alternar_chave():
    global indice_chave_atual, client
    if indice_chave_atual < len(CHAVES_API) - 1:
        indice_chave_atual += 1
        client = get_client()
        logging.warning(f"Alternando para a chave da API {indice_chave_atual + 1}...")
        return True
    return False

# ==========================================
# CONFIGURAÇÕES DO EXPERIMENTO
# ==========================================
modelos_gratuitos = [
    'dots-3-note-preview:free', 'liquid/lfm-2.5-2.6b:free',
    'nvidia/nemotron-3.5-lightning:free', 
    # 'thinkingmachines/inkling-small:free', - apenas para harnesses agenticos
    'poolside/laguna-s-2.1:free', 
    # 'thinkingmachines/inkling:free', - apenas para harnesses agenticos
    'poolside/laguna-xs-2.1:free', 'cohere/north-mini-code:free',
    'z-ai/glm-5.2:free',
    # 'nvidia/nemotron-3.5-content-safety:free', - não faz operações matemáticas. retorna "safety" ou "unsafety", modelo com fine tuning para essa tarefa específica.
    'nvidia/nemotron-3-ultra-550b-a55b:free', 
    # 'minimax/minimax-m3:free', - modelo descontinuado
    'nvidia/nemotron-3-nano-omni-30b-a3b-reasoning:free',
    'google/gemma-4-26b-a4b-it:free', 'google/gemma-4-31b-it:free',
    'minimax/minimax-m2.7:free', 'nvidia/nemotron-3-super-120b-a12b:free'
]

DADOS_DIR = 'dados'
ARQUIVO_OPERACOES = os.path.join(DADOS_DIR, 'operacoes.csv')
ARQUIVO_RESULTADOS = os.path.join(DADOS_DIR, 'resultados_experimento.csv')

TAMANHO_LOTE = 20 # Para fazer backup e respeitar os 20 RPM do OpenRouter

# ==========================================
# FUNÇÕES DE APOIO
# ==========================================
def gerar_operacoes():
    logging.info("Gerando base de operações matemáticas...")
    np.random.seed(123)
    dados_experimento = []
    
    # Expandido para testar até 8 dígitos
    for digitos in range(2, 9):
        low_val = 10**(digitos - 1)
        high_val = 10**digitos
        tipo_str = f"{digitos} dígitos"
        
        for i in range(100):
            a = np.random.randint(low=low_val, high=high_val, dtype=np.int64)
            b = np.random.randint(low=low_val, high=high_val, dtype=np.int64)
            # Convertendo para int nativo do Python ANTES de multiplicar para evitar o limite de 64 bits do numpy
            resultado = int(a) * int(b)
            
            dados_experimento.append({
                'num_a': a,
                'num_b': b,
                'Conta': f'{a}x{b} = ?',
                'Resultado_original': resultado,
                'Operacao': tipo_str
            })
            
    df = pd.DataFrame(dados_experimento)
    df.to_csv(ARQUIVO_OPERACOES, index=False)
    logging.info(f"Total de {len(df)} operações geradas e salvas em {ARQUIVO_OPERACOES}.")
    return df

def extrair_numero(texto):
    padrao = re.compile(r'\d+')
    numeros = padrao.findall(texto)
    if numeros:
        return int("".join(numeros))
    return None

# ==========================================
# CHAMADA ASSÍNCRONA
# ==========================================
async def realizar_chamada(modelo, conta_dict):
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
        
        if not hasattr(resposta, 'choices') or not resposta.choices:
            logging.error(f"O modelo {modelo} retornou uma resposta vazia (NoneType).")
            return None
            
        texto_resposta = resposta.choices[0].message.content
        valor_extraido = extrair_numero(texto_resposta)
        acerto_formato = True
        
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
        msg = getattr(e, 'message', str(e))
        logging.warning(f"Rate Limit (429) no modelo {modelo}. Detalhes: {msg}")
        if 'temporarily rate-limited upstream' in msg.lower() or 'upstream_429' in msg.lower():
            return {"status": "rate_limit_congelar", "modelo": modelo, "conta_dict": conta_dict}
        elif 'free-models-per-day' in msg.lower() or 'daily' in msg.lower():
            return {"status": "rate_limit_diario", "modelo": modelo, "conta_dict": conta_dict}
        else:
            return {"status": "rate_limit_temporario", "modelo": modelo, "conta_dict": conta_dict}
    except openai.APIStatusError as e:
        if e.status_code == 402:
            logging.warning(f"Erro {e.status_code} na chave atual ao testar {modelo} (Sem saldo).")
            return {"status": "rate_limit", "modelo": modelo, "conta_dict": conta_dict}
        elif e.status_code == 403:
            # 403 não é rate limit de chave, mas sim bloqueio específico do modelo
            logging.error(f"Erro 403 ao testar {modelo} (Acesso bloqueado ou proibido pelo provider). O modelo será ignorado.")
            return None
        else:
            logging.error(f"Erro na API com o modelo {modelo}: {e.status_code} - {e.message}")
            return None
    except Exception as e:
        logging.error(f"Erro inesperado com o modelo {modelo}: {e}")
        return None

# ==========================================
# FLUXO PRINCIPAL
# ==========================================
async def main():
    if not os.path.exists(DADOS_DIR):
        os.makedirs(DADOS_DIR)
        
    if os.path.exists(ARQUIVO_OPERACOES):
        df_operacoes = pd.read_csv(ARQUIVO_OPERACOES)
    else:
        df_operacoes = gerar_operacoes()

    if os.path.exists(ARQUIVO_RESULTADOS):
        df_resultados = pd.read_csv(ARQUIVO_RESULTADOS)
    else:
        colunas = [
            'Nome_do_modelo', 'Operacao', 'Resultado_do_modelo', 'Resposta_bruta',
            'Resultado_original', 'Acerto_da_operacao', 'Acerto_do_formato_de_resposta', 'Conta'
        ]
        df_resultados = pd.DataFrame(columns=colunas)

    concluidos = set()
    if not df_resultados.empty:
        for _, row in df_resultados.iterrows():
            chave = f"{row['Nome_do_modelo']}||{row['Conta']}"
            concluidos.add(chave)

    pendencias = []
    for _, row in df_operacoes.iterrows():
        for modelo in modelos_gratuitos:
            chave = f"{modelo}||{row['Conta']}"
            if chave not in concluidos:
                pendencias.append((modelo, row.to_dict()))

    logging.info(f"Total de operações pendentes na fila: {len(pendencias)}")
    if len(pendencias) == 0:
        logging.info("Experimento concluído! Nenhuma operação pendente.")
        return

    requisicoes_feitas = 0
    resultados_novos = []
    
    # Dicionário para gerenciar modelos bloqueados no upstream (modelo: timestamp_liberacao)
    modelos_congelados = {}
    
    # Semáforo para limitar a concorrência a 5 requisições simultâneas
    semaforo = asyncio.Semaphore(5)

    while pendencias:
        agora = time.time()
        
        # Descongelar modelos que já passaram do tempo
        modelos_descongelar = [m for m, t in modelos_congelados.items() if agora >= t]
        for m in modelos_descongelar:
            del modelos_congelados[m]
            logging.info(f"O modelo {m} saiu da geladeira (5 min expiraram). Voltando para a fila de testes.")
            
        lote_atual = []
        pendencias_restantes = []
        
        for p in pendencias:
            modelo = p[0]
            if modelo not in modelos_congelados and len(lote_atual) < TAMANHO_LOTE:
                lote_atual.append(p)
            else:
                pendencias_restantes.append(p)
                
        pendencias = pendencias_restantes
        
        if not lote_atual:
            logging.info("Fila vazia ou todos os modelos restantes estão congelados. Aguardando 10 segundos...")
            await asyncio.sleep(10)
            continue
            
        logging.info(f"Processando lote de {len(lote_atual)} requisições... (Requisitadas nesta sessão: {requisicoes_feitas})")
        
        async def tarefa_com_semaforo(m, c):
            async with semaforo:
                return await realizar_chamada(m, c)
                
        tarefas = [tarefa_com_semaforo(modelo, conta) for modelo, conta in lote_atual]
        respostas = await asyncio.gather(*tarefas)
        
        teve_rate_limit = False
        
        for res in respostas:
            if res is not None:
                status = res.get("status") if isinstance(res, dict) else None
                if status in ["rate_limit", "rate_limit_diario"]:
                    teve_rate_limit = True
                    pendencias.insert(0, (res["modelo"], res["conta_dict"]))
                elif status == "rate_limit_congelar":
                    if res["modelo"] not in modelos_congelados:
                        modelos_congelados[res["modelo"]] = time.time() + 300  # Congela por 5 minutos
                        logging.warning(f"Congelando o modelo {res['modelo']} por 5 minutos devido a erro de Upstream Rate Limit.")
                    pendencias.append((res["modelo"], res["conta_dict"]))
                elif status == "rate_limit_temporario":
                    # Reenfileira no final para tentar novamente mais tarde sem trocar a chave
                    pendencias.append((res["modelo"], res["conta_dict"]))
                else:
                    resultados_novos.append(res)
                    requisicoes_feitas += 1
        
        if resultados_novos:
            novo_df = pd.DataFrame(resultados_novos)
            if os.path.exists(ARQUIVO_RESULTADOS):
                df_salvo = pd.read_csv(ARQUIVO_RESULTADOS)
                df_salvo = pd.concat([df_salvo, novo_df], ignore_index=True)
                df_salvo.to_csv(ARQUIVO_RESULTADOS, index=False)
            else:
                novo_df.to_csv(ARQUIVO_RESULTADOS, index=False)
            
            resultados_novos = []
            logging.info("Backup salvo com sucesso no arquivo CSV.")
            
        if teve_rate_limit:
            if not alternar_chave():
                logging.error("Todas as chaves atingiram o Rate Limit ou acabaram os créditos. Encerrando por hoje.")
                break
        elif pendencias:
            logging.info("Aguardando 90 segundos para a reinicialização do Rate Limit (20 RPM)...")
            await asyncio.sleep(90)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.warning("Script interrompido manualmente pelo usuário (KeyboardInterrupt).")

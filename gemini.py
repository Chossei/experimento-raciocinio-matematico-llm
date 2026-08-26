import os
import re
import json
import asyncio
import pandas as pd
import numpy as np
from dotenv import load_dotenv
import time
import logging
from datetime import datetime

from google.oauth2 import service_account
import vertexai
from vertexai.generative_models import GenerativeModel
from google.api_core.exceptions import ResourceExhausted, ServiceUnavailable, InternalServerError

# ==========================================
# CONFIGURAÇÃO DE LOGS
# ==========================================
if not os.path.exists('logs_gemini'):
    os.makedirs('logs_gemini')

data_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = os.path.join('logs_gemini', f'execucao_gemini_{data_hora}.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logging.info("=== Iniciando Pipeline de Experimento Matemático (Gemini Vertex AI) ===")

# ==========================================
# VARIÁVEIS DE AMBIENTE E AUTENTICAÇÃO
# ==========================================
# Carregando variáveis de ambiente
load_dotenv('chave.env')

# A chave GEMINI_API_KEY no .env é um JSON de Service Account
gemini_api_key_str = os.environ.get("GEMINI_API_KEY", "")
if not gemini_api_key_str:
    # Fallback caso o dotenv não carregue multiline com formato customizado
    with open('chave.env', 'r', encoding='utf-8') as f:
        content = f.read()
        if "GEMINI_API_KEY =" in content:
            gemini_api_key_str = content.split("GEMINI_API_KEY =")[1].strip()
            if gemini_api_key_str.startswith('"') and gemini_api_key_str.endswith('"'):
                gemini_api_key_str = gemini_api_key_str[1:-1]
            elif gemini_api_key_str.startswith("'") and gemini_api_key_str.endswith("'"):
                gemini_api_key_str = gemini_api_key_str[1:-1]

try:
    creds_dict = json.loads(gemini_api_key_str)
    credentials = service_account.Credentials.from_service_account_info(creds_dict)
    
    # Inicializa o Vertex AI
    project_id = creds_dict.get("project_id", "plataformas-aula-ufba")
    vertexai.init(project=project_id, location="us-central1", credentials=credentials)
    logging.info(f"Vertex AI inicializado com sucesso para o projeto: {project_id} | Região: us-central1")
except Exception as e:
    logging.error(f"Erro ao carregar credenciais do Vertex AI a partir do chave.env: {e}")
    raise ValueError("Falha na autenticação. Verifique o formato do JSON em GEMINI_API_KEY no chave.env.")

# ==========================================
# CONFIGURAÇÕES DO EXPERIMENTO (DADOS DA API)
# ==========================================
# Taxa de câmbio (Agosto de 2026): 1 USD = ~R$ 5,15
taxa_cambio = 5.15

# Preços baseados na API do Google AI Studio / Vertex AI (Nível Padrão, em dólares)
dados_api = [
    {"modelo": "gemini-3.7-flash", "input_usd" : 0.75, "output_usd": 3.75, 'RPM':'1000', 'RPD':'10000'},
    {"modelo": "gemini-3.6-flash", "input_usd": 0.75, "output_usd": 3.75, 'RPM':'1000', 'RPD':'10000'},
    {"modelo": "gemini-3.5-flash", "input_usd": 1.50, "output_usd": 9.00, 'RPM':'1000', 'RPD':'10000'},
    {"modelo": "gemini-3.5-flash-lite", "input_usd": 0.30, "output_usd": 2.50, 'RPM':'4000', 'RPD':'150000'},
    {"modelo": "gemini-3.1-flash-lite", "input_usd": 0.25, "output_usd": 1.50, 'RPM':'4000', 'RPD':'150000'},
    {"modelo": "gemini-3.1-pro-preview", "input_usd": 2.00, "output_usd": 12.00, 'RPM':'25', 'RPD':'250'},
    {"modelo": "gemini-3-flash-preview", "input_usd": 0.50, "output_usd": 3.00, 'RPM':'1000', 'RPD':'10000'},
    {"modelo": "gemini-2.5-pro", "input_usd": 1.25, "output_usd": 10.00, 'RPM':'150', 'RPD': '1000'},
    {"modelo": "gemini-2.5-flash", "input_usd": 0.30, "output_usd": 2.50, 'RPM':'1000', 'RPD':'10000'}
]

# Semáforos por modelo, baseados nas RPMs estipuladas
semaforos_por_modelo = {}
for d in dados_api:
    rpm = int(d['RPM'])
    if rpm <= 25:
        # Modelo mais restritivo (25 rpm)
        semaforos_por_modelo[d['modelo']] = asyncio.Semaphore(5)
    elif rpm <= 150:
        # Modelo intermediário (150 rpm)
        semaforos_por_modelo[d['modelo']] = asyncio.Semaphore(30)
    else:
        # Modelos com RPM alto (1000 a 4000 rpm)
        semaforos_por_modelo[d['modelo']] = asyncio.Semaphore(100)

DADOS_DIR = 'dados'
ARQUIVO_OPERACOES = os.path.join(DADOS_DIR, 'operacoes.csv')
ARQUIVO_RESULTADOS = os.path.join(DADOS_DIR, 'resultados_gemini.csv')

# Lote ampliado porque as RPMs gerais da Vertex suportam
TAMANHO_LOTE = 100 

# ==========================================
# FUNÇÕES DE APOIO
# ==========================================
def extrair_numero(texto):
    padrao = re.compile(r'\d+')
    numeros = padrao.findall(texto)
    if numeros:
        return int("".join(numeros))
    return None

def calcular_custo(modelo_nome, input_tokens, output_tokens):
    for d in dados_api:
        if d['modelo'] == modelo_nome:
            # Para modelos gratuitos ou em que o custo é vazio, mantemos vazio
            if not d.get('input_usd') or not d.get('output_usd'):
                return ""
            try:
                in_usd = float(d['input_usd'])
                out_usd = float(d['output_usd'])
                custo_usd = (input_tokens * in_usd / 1_000_000) + (output_tokens * out_usd / 1_000_000)
                custo_brl = custo_usd * taxa_cambio
                return round(custo_brl, 6)
            except ValueError:
                return ""
    return ""

# ==========================================
# CHAMADA ASSÍNCRONA
# ==========================================
async def realizar_chamada(modelo_nome, conta_dict):
    prompt_geral = f"""
    Sua tarefa é resolver operações matemáticas.
    Responda a pergunta a seguir e retorne o resultado SOMENTE em formato de número, sem unidades ou caracteres especiais.
    {conta_dict['Conta']}
    """
    
    try:
        model = GenerativeModel(modelo_nome)
        
        # Vertex AI faz as chamadas automaticamente. Retries são gerenciados pela lib interna,
        # mas as exceções maiores (Quota) chegam até nós.
        resposta = await model.generate_content_async(prompt_geral)
        
        if not resposta or not resposta.text:
            logging.error(f"O modelo {modelo_nome} retornou uma resposta vazia.")
            return None
            
        texto_resposta = resposta.text
        valor_extraido = extrair_numero(texto_resposta)
        acerto_formato = not bool(re.search(r'[a-zA-Z]', texto_resposta))
        acerto_operacao = (valor_extraido == conta_dict['Resultado_original'])
        
        # Extrair contagem de tokens do Usage Metadata
        input_tokens = 0
        output_tokens = 0
        if hasattr(resposta, 'usage_metadata') and resposta.usage_metadata is not None:
            input_tokens = getattr(resposta.usage_metadata, 'prompt_token_count', 0)
            output_tokens = getattr(resposta.usage_metadata, 'candidates_token_count', 0)
            
        custo_total = calcular_custo(modelo_nome, input_tokens, output_tokens)
        
        return {
            'Nome_do_modelo': modelo_nome,
            'Operacao': conta_dict['Operacao'],
            'Resultado_do_modelo': valor_extraido,
            'Resposta_bruta': texto_resposta,
            'Resultado_original': conta_dict['Resultado_original'],
            'Acerto_da_operacao': acerto_operacao,
            'Acerto_do_formato_de_resposta': acerto_formato,
            'Conta': conta_dict['Conta'],
            'custo_total': custo_total
        }
        
    except ResourceExhausted as e: 
        # Código 429 Quota Exceeded (Pode ser RPM ou RPD)
        msg = str(e)
        logging.warning(f"Rate Limit (429) no modelo {modelo_nome}. Detalhes: {msg}")
        
        if 'per day' in msg.lower() or 'daily' in msg.lower():
            return {"status": "rate_limit_diario", "modelo": modelo_nome, "conta_dict": conta_dict}
        else:
            return {"status": "rate_limit_congelar", "modelo": modelo_nome, "conta_dict": conta_dict}
            
    except (ServiceUnavailable, InternalServerError) as e:
        # Erro de Upstream do Vertex (Indisponível no momento)
        logging.warning(f"Erro upstream 5xx para {modelo_nome}: {e}")
        return {"status": "rate_limit_congelar", "modelo": modelo_nome, "conta_dict": conta_dict}
        
    except Exception as e:
        # Como ValueError de modelo não encontrado
        logging.error(f"Erro inesperado com o modelo {modelo_nome}: {e}")
        # Retornamos None para o script simplesmente ignorar essa operação para esse modelo com erro fatal
        return None

# ==========================================
# FLUXO PRINCIPAL
# ==========================================
async def main():
    if not os.path.exists(DADOS_DIR):
        os.makedirs(DADOS_DIR)
        
    if not os.path.exists(ARQUIVO_OPERACOES):
        logging.error(f"Arquivo de operações não encontrado: {ARQUIVO_OPERACOES}. Execute o outro script para gerar as contas primeiro.")
        return
        
    df_operacoes = pd.read_csv(ARQUIVO_OPERACOES)

    if os.path.exists(ARQUIVO_RESULTADOS):
        df_resultados = pd.read_csv(ARQUIVO_RESULTADOS)
    else:
        colunas = [
            'Nome_do_modelo', 'Operacao', 'Resultado_do_modelo', 'Resposta_bruta',
            'Resultado_original', 'Acerto_da_operacao', 'Acerto_do_formato_de_resposta', 'Conta', 'custo_total'
        ]
        df_resultados = pd.DataFrame(columns=colunas)

    concluidos = set()
    if not df_resultados.empty:
        for _, row in df_resultados.iterrows():
            chave = f"{row['Nome_do_modelo']}||{row['Conta']}"
            concluidos.add(chave)

    pendencias = []
    # Usaremos os modelos definidos no dados_api
    modelos_lista = [d['modelo'] for d in dados_api]
    
    # Set para bloquear modelos que esgotaram limite diário
    modelos_esgotados_hoje = set()
    
    for _, row in df_operacoes.iterrows():
        for modelo in modelos_lista:
            chave = f"{modelo}||{row['Conta']}"
            if chave not in concluidos:
                pendencias.append((modelo, row.to_dict()))

    logging.info(f"Total de operações pendentes na fila Gemini: {len(pendencias)}")
    if len(pendencias) == 0:
        logging.info("Experimento concluído! Nenhuma operação pendente.")
        return

    requisicoes_feitas = 0
    resultados_novos = []
    
    # Dicionário da "Geladeira"
    modelos_congelados = {}

    while pendencias:
        agora = time.time()
        
        # Descongelar
        modelos_descongelar = [m for m, t in modelos_congelados.items() if agora >= t]
        for m in modelos_descongelar:
            del modelos_congelados[m]
            logging.info(f"O modelo {m} saiu da geladeira. Voltando para a fila de testes.")
            
        lote_atual = []
        pendencias_restantes = []
        
        for p in pendencias:
            modelo = p[0]
            if modelo in modelos_esgotados_hoje:
                continue
                
            if modelo not in modelos_congelados and len(lote_atual) < TAMANHO_LOTE:
                lote_atual.append(p)
            else:
                pendencias_restantes.append(p)
                
        pendencias = pendencias_restantes
        
        if not lote_atual:
            if not pendencias:
                logging.info("Todas as tarefas pendentes pertencem a modelos esgotados por hoje. Encerrando.")
                break
            logging.info("Fila vazia ou modelos congelados. Aguardando 10 segundos...")
            await asyncio.sleep(10)
            continue
            
        logging.info(f"Processando lote de {len(lote_atual)} requisições Vertex AI... (Requisitadas nesta sessão: {requisicoes_feitas})")
        
        async def tarefa_com_semaforo(m, c):
            async with semaforos_por_modelo[m]:
                return await realizar_chamada(m, c)
                
        tarefas = [tarefa_com_semaforo(modelo, conta) for modelo, conta in lote_atual]
        respostas = await asyncio.gather(*tarefas)
        
        for res in respostas:
            if res is not None:
                status = res.get("status") if isinstance(res, dict) else None
                if status == "rate_limit_diario":
                    modelos_esgotados_hoje.add(res["modelo"])
                    logging.error(f"Modelo {res['modelo']} esgotou a cota diária (RPD). Pausando até amanhã.")
                    pendencias.insert(0, (res["modelo"], res["conta_dict"]))
                elif status == "rate_limit_congelar":
                    if res["modelo"] not in modelos_congelados:
                        # Congela por 60 segundos (1 minuto) para resets de RPM
                        modelos_congelados[res["modelo"]] = time.time() + 60
                        logging.warning(f"Congelando {res['modelo']} por 1 minuto devido a Rate Limit/RPM.")
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
            
        await asyncio.sleep(2)

if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.warning("Script interrompido manualmente pelo usuário (KeyboardInterrupt).")

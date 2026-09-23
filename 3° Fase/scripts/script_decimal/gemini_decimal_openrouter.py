import os
import re
import time
import json
import asyncio
import argparse
import logging
from datetime import datetime
from decimal import Decimal, InvalidOperation, getcontext
import pandas as pd
from dotenv import load_dotenv
from openai import AsyncOpenAI
import openai

# Configuração de precisão arbitrária para comparações numéricas
getcontext().prec = 100

# ==========================================
# CONFIGURAÇÃO DE LOGS E DIRETÓRIOS
# ==========================================
PASTA_OPENROUTER = os.path.dirname(os.path.abspath(__file__))
PASTA_GEMINI = os.path.dirname(PASTA_OPENROUTER)
PASTA_RAIZ = os.path.dirname(PASTA_GEMINI)
LOGS_DIR = os.path.join(PASTA_OPENROUTER, 'logs')
if not os.path.exists(LOGS_DIR):
    os.makedirs(LOGS_DIR)

data_hora = datetime.now().strftime("%Y%m%d_%H%M%S")
log_filename = os.path.join(LOGS_DIR, f'openrouter_decimais_{data_hora}.log')

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_filename, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

logging.info("=== Iniciando Inferência Decimal para Gemini via OpenRouter ===")

# ==========================================
# AUTENTICAÇÃO E CHAVE OPENROUTER
# ==========================================
def carregar_openrouter_key(env_path):
    """Carrega a chave OPEN_ROUTER_API_KEY_2 de forma robusta."""
    load_dotenv(env_path)
    chave = os.environ.get("OPEN_ROUTER_API_KEY_2", "")
    if chave and chave.strip():
        return chave.strip().strip('"').strip("'")

    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8', errors='ignore') as f:
            for linha in f:
                linha_limpa = linha.strip()
                if linha_limpa.startswith("OPEN_ROUTER_API_KEY_2"):
                    partes = linha_limpa.split("=", 1)
                    if len(partes) == 2:
                        return partes[1].strip().strip('"').strip("'")
    return ""

env_path = os.path.join(PASTA_RAIZ, 'chave.env')
api_key = carregar_openrouter_key(env_path)

if not api_key:
    logging.error("A chave OPEN_ROUTER_API_KEY_2 não foi encontrada em chave.env!")
    raise ValueError("Chave OPEN_ROUTER_API_KEY_2 não encontrada no arquivo chave.env.")

client = AsyncOpenAI(
    base_url='https://openrouter.ai/api/v1',
    api_key=api_key,
    max_retries=0,
    default_headers={
        "HTTP-Referer": "https://tcc-experimento.ufba.br",
        "X-Title": "Experimento TCC Raciocinio Matematico LLMs"
    }
)

logging.info("Cliente AsyncOpenAI configurado com sucesso para o OpenRouter.")

# ==========================================
# CONFIGURAÇÕES DO EXPERIMENTO
# ==========================================
# Taxa de câmbio (Agosto de 2026): 1 USD = ~R$ 5,15
taxa_cambio = 5.15

# Tabela de modelos Gemini e custos por 1 milhão de tokens
dados_api = [
    {"modelo": "gemini-3.8-flash", "input_usd": 0.75, "output_usd": 3.75, "rpm": 1000, "rpd": 10000},
    {"modelo": "gemini-3.7-flash", "input_usd": 0.75, "output_usd": 3.75, "rpm": 250, "rpd": 10000},
    {"modelo": "gemini-3.6-flash", "input_usd": 0.75, "output_usd": 3.75, "rpm": 1000, "rpd": 10000},
    {"modelo": "gemini-3.5-flash", "input_usd": 1.50, "output_usd": 9.00, "rpm": 1000, "rpd": 10000},
    {"modelo": "gemini-3.5-flash-lite", "input_usd": 0.30, "output_usd": 2.50, "rpm": 4000, "rpd": 150000},
    {"modelo": "gemini-3.1-flash-lite", "input_usd": 0.25, "output_usd": 1.50, "rpm": 4000, "rpd": 150000},
    {"modelo": "gemini-3.1-pro-preview", "input_usd": 2.00, "output_usd": 12.00, "rpm": 25, "rpd": 1000},
    {"modelo": "gemini-3-flash-preview", "input_usd": 0.50, "output_usd": 3.00, "rpm": 1000, "rpd": 10000},
    {"modelo": "gemini-2.5-pro", "input_usd": 1.25, "output_usd": 10.00, "rpm": 150, "rpd": 1000},
    {"modelo": "gemini-2.5-flash", "input_usd": 0.30, "output_usd": 2.50, "rpm": 1000, "rpd": 10000}
]

modelos_lista = [d["modelo"] for d in dados_api]

DADOS_DIR = os.path.join(PASTA_RAIZ, 'dados')
ARQUIVO_OPERACOES = os.path.join(DADOS_DIR, 'operacoes.csv')
ARQUIVO_RESULTADOS_OR = os.path.join(DADOS_DIR, 'resultados_gemini_decimal_openrouter.csv')

# ==========================================
# FUNÇÕES DE APOIO E COMPARAÇÃO DECIMAL
# ==========================================
def extrair_numero_decimal(texto):
    """Extrai um número decimal (com ponto) da resposta do modelo."""
    if not texto:
        return None
    texto_limpo = texto.strip()
    padrao = re.compile(r'-?\d+\.?\d*')
    match = padrao.search(texto_limpo)
    if match:
        return match.group()
    return None

def comparar_decimais(valor_extraido, valor_esperado):
    """Compara dois valores decimais lidando com zeros à direita (ex: '5.490' == '5.49').

    1. Primeiro verifica se as strings são idênticas.
    2. Se diferentes, converte ambos para Decimal (com precisão de 100 dígitos)
       e compara a equivalência numérica exata, sem introduzir imprecisões de float.
    """
    if valor_extraido is None or valor_esperado is None:
        return False
    val_ext = str(valor_extraido).strip()
    val_esp = str(valor_esperado).strip()

    if val_ext == val_esp:
        return True

    try:
        return Decimal(val_ext) == Decimal(val_esp)
    except (InvalidOperation, ValueError):
        return False

def obter_rpm(modelo_nome):
    """Retorna o RPM (requests per minute) do modelo."""
    for d in dados_api:
        if d['modelo'] == modelo_nome:
            return d.get('rpm', 60)
    return 60

def calcular_custo(modelo_nome, input_tokens, output_tokens):
    """Calcula o custo total em Reais (BRL) baseado nos tokens utilizados."""
    for d in dados_api:
        if d['modelo'] == modelo_nome:
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

def obter_config_reasoning(modelo_nome):
    """Retorna a configuração de esforço mínimo para deixar os modelos no 'pelo' (sem raciocínio/thinking)."""
    # Modelos onde o raciocínio é opcional (podem desligar 100% com effort: none)
    if any(x in modelo_nome for x in ['2.5-flash', '3.1-flash-lite', '3-flash-preview']):
        return {'effort': 'none'}
    # Modelos que aceitam minimal
    elif any(x in modelo_nome for x in ['3.6-flash', '3.5-flash', '3.5-flash-lite']):
        return {'effort': 'minimal'}
    # Modelos onde a API da Google/OpenRouter exige raciocínio obrigatório (mínimo permitido é 'low')
    # Inclui: gemini-3.8-flash, gemini-3.7-flash, gemini-3.1-pro-preview e gemini-2.5-pro
    else:
        return {'effort': 'low'}

# ==========================================
# BUFFER INCREMENTAL PARA BACKUP A CADA 10 REQUISIÇÕES
# ==========================================
class BufferResultados:
    """Gerencia o salvamento no CSV a cada 10 requisições bem sucedidas."""
    def __init__(self, arquivo_csv, tamanho_flush=10):
        self.arquivo_csv = arquivo_csv
        self.tamanho_flush = tamanho_flush
        self.buffer = []
        self.lock = asyncio.Lock()
        self.total_salvo = 0

    async def adicionar(self, resultado):
        async with self.lock:
            self.buffer.append(resultado)
            if len(self.buffer) >= self.tamanho_flush:
                await self._flush_locked()

    async def flush(self):
        async with self.lock:
            if self.buffer:
                await self._flush_locked()

    async def _flush_locked(self):
        if not self.buffer:
            return
        df = pd.DataFrame(self.buffer)
        arquivo_existe = os.path.exists(self.arquivo_csv)
        df.to_csv(self.arquivo_csv, mode='a', header=not arquivo_existe, index=False)
        self.total_salvo += len(self.buffer)
        logging.info(f"💾 Backup realizado: {len(self.buffer)} resultados salvos no CSV (Total acumulado: {self.total_salvo}).")
        self.buffer.clear()

# ==========================================
# INFERÊNCIA ASSÍNCRONA VIA OPENROUTER
# ==========================================
async def processar_requisicao(semaforo, buffer_resultados, modelo, req_info):
    """Executa a requisição assíncrona para o modelo via OpenRouter com retentativas."""
    async with semaforo:
        prompt = (
            "Sua tarefa é resolver operações matemáticas.\n"
            "Responda a pergunta a seguir e retorne o resultado "
            "SOMENTE em formato de número decimal, sem unidades ou caracteres especiais.\n"
            f"{req_info['conta_decimal']}"
        )

        modelo_openrouter = f"google/{modelo}" if not modelo.startswith("google/") else modelo
        config_reasoning = obter_config_reasoning(modelo)
        tentativas = 0
        max_tentativas = 5
        espera_base = 5  # segundos

        while tentativas < max_tentativas:
            try:
                resposta = await client.chat.completions.create(
                    model=modelo_openrouter,
                    messages=[{"role": "user", "content": prompt}],
                    temperature=0.0,
                    max_tokens=1000,
                    extra_body={"reasoning": config_reasoning}
                )

                if not hasattr(resposta, 'choices') or not resposta.choices:
                    logging.error(f"Resposta vazia de {modelo} para {req_info['conta_decimal']}")
                    return None

                texto_resposta = resposta.choices[0].message.content or ""
                valor_extraido = extrair_numero_decimal(texto_resposta)
                acerto_formato = not bool(re.search(r'[a-zA-Z]', texto_resposta))

                resultado_esperado = str(req_info["resultado_original_decimal"])
                acerto_operacao = comparar_decimais(valor_extraido, resultado_esperado)

                # Extração de tokens e custo
                input_tokens = 0
                output_tokens = 0
                if resposta.usage:
                    input_tokens = resposta.usage.prompt_tokens or 0
                    output_tokens = resposta.usage.completion_tokens or 0

                custo_total = calcular_custo(modelo, input_tokens, output_tokens)

                resultado = {
                    'Nome_do_modelo': modelo,
                    'Operacao': req_info["operacao"],
                    'Resultado_do_modelo': valor_extraido,
                    'Resposta_bruta': texto_resposta,
                    'Resultado_original_decimal': resultado_esperado,
                    'Acerto_da_operacao': acerto_operacao,
                    'Acerto_do_formato_de_resposta': acerto_formato,
                    'Conta_decimal': req_info["conta_decimal"],
                    'custo_total': custo_total
                }

                # Salva no buffer que descarrega no CSV a cada 10 requisições
                await buffer_resultados.adicionar(resultado)
                return resultado

            except openai.RateLimitError as e:
                tentativas += 1
                espera = espera_base * (2 ** (tentativas - 1))
                logging.warning(
                    f"Rate limit (429) no modelo {modelo} ({req_info['conta_decimal']}). "
                    f"Tentativa {tentativas}/{max_tentativas}. Aguardando {espera}s..."
                )
                await asyncio.sleep(espera)
            except openai.APIStatusError as e:
                tentativas += 1
                if e.status_code == 429:
                    espera = espera_base * (2 ** (tentativas - 1))
                    logging.warning(
                        f"Rate limit (HTTP 429) no modelo {modelo}. "
                        f"Tentativa {tentativas}/{max_tentativas}. Aguardando {espera}s..."
                    )
                    await asyncio.sleep(espera)
                elif e.status_code == 402:
                    # 402 pode ser causado por reserva temporária de saldo das requisições em voo.
                    # Aguarda requisições paralelas finalizarem para liberar a reserva de créditos.
                    espera = espera_base * (2 ** (tentativas - 1))
                    logging.warning(
                        f"Alerta 402 (Reserva de saldo temporária) no OpenRouter para {modelo}. "
                        f"Aguardando liberação de requisições em voo por {espera}s... (Tentativa {tentativas}/{max_tentativas})"
                    )
                    await asyncio.sleep(espera)
                else:
                    logging.error(f"Erro {e.status_code} na API OpenRouter para {modelo}: {e.message}")
                    if tentativas < max_tentativas:
                        await asyncio.sleep(espera_base)
            except Exception as e:
                tentativas += 1
                logging.error(f"Erro inesperado com {modelo} ({req_info['conta_decimal']}): {e}")
                if tentativas < max_tentativas:
                    await asyncio.sleep(espera_base)

        logging.error(f"Falha definitiva para {req_info['conta_decimal']} com {modelo} após {max_tentativas} tentativas.")
        return None

async def processar_modelo(buffer_resultados, modelo, requisicoes):
    """Processa todas as requisições de um modelo respeitando rigorosamente seu RPM."""
    rpm = obter_rpm(modelo)
    # Limita concorrência ativa para evitar esgotamento de reserva de crédito e burst limits no OpenRouter (mínimo de 2 requisições paralelas)
    concorrencia = min(15, max(2, int(rpm * 0.05)))
    semaforo = asyncio.Semaphore(concorrencia)

    logging.info(f"Processando {len(requisicoes)} requisições para {modelo} (RPM: {rpm}, concorrência: {concorrencia})...")

    resultados = []
    lote_tamanho = rpm
    total_lotes = (len(requisicoes) + lote_tamanho - 1) // lote_tamanho

    for i in range(0, len(requisicoes), lote_tamanho):
        lote = requisicoes[i:i + lote_tamanho]
        num_lote = (i // lote_tamanho) + 1
        logging.info(f"  [{modelo}] Lote {num_lote}/{total_lotes} ({len(lote)} requisições)...")

        inicio_lote = time.monotonic()

        tarefas = [
            processar_requisicao(semaforo, buffer_resultados, modelo, req)
            for req in lote
        ]
        resultados_lote = await asyncio.gather(*tarefas)

        validos = [r for r in resultados_lote if r is not None]
        resultados.extend(validos)

        # Força gravação de quaisquer retornos pendentes deste lote
        await buffer_resultados.flush()

        # Respeitar a janela móvel de 1 minuto por RPM
        if i + lote_tamanho < len(requisicoes):
            decorrido = time.monotonic() - inicio_lote
            tempo_restante = 60.0 - decorrido
            if tempo_restante > 0:
                logging.info(f"  [{modelo}] Lote processado em {decorrido:.1f}s. Aguardando {tempo_restante:.1f}s para respeitar o RPM ({rpm})...")
                await asyncio.sleep(tempo_restante)
            else:
                logging.info(f"  [{modelo}] Lote processado em {decorrido:.1f}s (>= 60s). Prosseguindo imediatamente.")

    return resultados

# ==========================================
# FLUXO PRINCIPAL
# ==========================================
async def main_async(modelo_selecionado=None, limite_requisicoes=None):
    if not os.path.exists(DADOS_DIR):
        os.makedirs(DADOS_DIR)

    if not os.path.exists(ARQUIVO_OPERACOES):
        logging.error(f"Arquivo de operações não encontrado: {ARQUIVO_OPERACOES}")
        return

    # Leitura com Resultado_original_decimal como str para preservar precisão máxima
    df_operacoes = pd.read_csv(ARQUIVO_OPERACOES, dtype={'Resultado_original_decimal': str})

    if 'Conta_decimal' not in df_operacoes.columns:
        logging.error("A coluna 'Conta_decimal' não existe no arquivo de operações.")
        return

    # Buffer com backup incremental a cada 10 requisições
    buffer_resultados = BufferResultados(ARQUIVO_RESULTADOS_OR, tamanho_flush=10)

    # Identificar operações já concluídas no arquivo de resultados
    concluidos = set()
    if os.path.exists(ARQUIVO_RESULTADOS_OR):
        df_resultados = pd.read_csv(ARQUIVO_RESULTADOS_OR)
        for _, row in df_resultados.iterrows():
            chave = f"{row['Nome_do_modelo']}||{row['Conta_decimal']}"
            concluidos.add(chave)
        logging.info(f"Retomando experimento: {len(concluidos)} operações já registradas no CSV.")

    # Modelos a serem executados
    modelos_a_executar = [modelo_selecionado] if modelo_selecionado else modelos_lista

    pendencias_por_modelo = {m: [] for m in modelos_a_executar}

    for _, row in df_operacoes.iterrows():
        for modelo in modelos_a_executar:
            chave = f"{modelo}||{row['Conta_decimal']}"
            if chave not in concluidos:
                pendencias_por_modelo[modelo].append({
                    "chave": chave,
                    "conta_decimal": row['Conta_decimal'],
                    "operacao": row['tipo'],
                    "resultado_original_decimal": str(row['Resultado_original_decimal'])
                })

    # Aplicar limite se fornecido (útil para testes de homologação)
    if limite_requisicoes is not None:
        for m in modelos_a_executar:
            pendencias_por_modelo[m] = pendencias_por_modelo[m][:limite_requisicoes]

    total_pendentes = sum(len(v) for v in pendencias_por_modelo.values())
    if total_pendentes == 0:
        logging.info("Todas as operações decimais já foram processadas para os modelos selecionados. Nada a fazer.")
        return

    logging.info(f"Total de requisições pendentes: {total_pendentes}")

    total_processados = 0
    for modelo in modelos_a_executar:
        reqs = pendencias_por_modelo[modelo]
        if not reqs:
            logging.info(f"Modelo {modelo} já possui todas as operações concluídas. Pulando.")
            continue

        resultados = await processar_modelo(buffer_resultados, modelo, reqs)
        acertos = sum(1 for r in resultados if r['Acerto_da_operacao'])
        total = len(resultados)
        taxa = (acertos / total * 100) if total > 0 else 0
        total_processados += total

        logging.info(f"[{modelo}] Concluído: {acertos}/{total} acertos ({taxa:.1f}%)")

    # Garante que qualquer resíduo do buffer seja gravado no disco
    await buffer_resultados.flush()
    logging.info(f"\n=== Inferência OpenRouter (Decimais) concluída! Total processado: {total_processados} ===")

def main():
    parser = argparse.ArgumentParser(description="Experimento Decimal para Gemini via OpenRouter")
    parser.add_argument("--modelo", type=str, default=None, help="Nome do modelo específico a rodar (ex: gemini-3.8-flash)")
    parser.add_argument("--limite", type=int, default=None, help="Limite de operações para teste rápido")
    args = parser.parse_args()

    asyncio.run(main_async(modelo_selecionado=args.modelo, limite_requisicoes=args.limite))

if __name__ == '__main__':
    main()

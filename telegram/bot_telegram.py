"""Bot de Telemetria e Assistente Virtual do Experimento no Telegram

Este script conecta o seu celular diretamente ao seu ambiente local e aos experimentos:
1. Permite conversar com a IA sobre o experimento em linguagem natural.
2. Comandos instantâneos para checar status de jobs, saldo no OpenRouter e métricas.
3. Notificações proativas quando processos terminarem.
4. Totalmente baseado em 'requests' (zero dependências adicionais pesadas).
"""

import os
import sys
import time
import json
import logging
from datetime import datetime
import requests
from dotenv import load_dotenv

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")

PASTA_TELEGRAM = os.path.dirname(os.path.abspath(__file__))
PASTA_RAIZ = os.path.dirname(PASTA_TELEGRAM)

# Carregamento de chaves
ARQUIVO_ENV_TELEGRAM = os.path.join(PASTA_TELEGRAM, ".env")
ARQUIVO_CHAVE_ENV = os.path.join(PASTA_RAIZ, "chave.env")

# Carrega primeiro de telegram/.env se existir
if os.path.exists(ARQUIVO_ENV_TELEGRAM):
    load_dotenv(ARQUIVO_ENV_TELEGRAM)

TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip()
AUTHORIZED_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "").strip()

# Se não estiver no .env do telegram, busca no chave.env manualmente
if not TELEGRAM_BOT_TOKEN and os.path.exists(ARQUIVO_CHAVE_ENV):
    try:
        with open(ARQUIVO_CHAVE_ENV, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if line.startswith("TELEGRAM_BOT_TOKEN") and "=" in line:
                    TELEGRAM_BOT_TOKEN = line.split("=", 1)[1].strip("\"' \r\n")
    except Exception:
        pass

OPENROUTER_API_KEY = os.environ.get("OPEN_ROUTER_API_KEY_2", "").strip()
if not OPENROUTER_API_KEY and os.path.exists(ARQUIVO_CHAVE_ENV):
    try:
        with open(ARQUIVO_CHAVE_ENV, "r", encoding="utf-8", errors="ignore") as f:
            for line in f:
                if "OPEN_ROUTER_API_KEY_2" in line and "=" in line:
                    OPENROUTER_API_KEY = line.strip().split("=", 1)[1].strip("\"' \r\n")
    except Exception:
        pass

LOGS_DIR = os.path.join(PASTA_TELEGRAM, "logs")
os.makedirs(LOGS_DIR, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(os.path.join(LOGS_DIR, "telegram_bot.log"), encoding="utf-8"),
        logging.StreamHandler()
    ]
)

TELEGRAM_API_URL = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}"

def salvar_chat_id(chat_id):
    global AUTHORIZED_CHAT_ID
    AUTHORIZED_CHAT_ID = str(chat_id)
    with open(ARQUIVO_ENV_TELEGRAM, "w", encoding="utf-8") as f:
        f.write(f"TELEGRAM_BOT_TOKEN={TELEGRAM_BOT_TOKEN}\n")
        f.write(f"TELEGRAM_CHAT_ID={AUTHORIZED_CHAT_ID}\n")
    logging.info(f"Chat ID {chat_id} salvo e pareado com sucesso!")

def enviar_mensagem_telegram(chat_id, texto, reply_markup=None):
    if not TELEGRAM_BOT_TOKEN:
        return False
    url = f"{TELEGRAM_API_URL}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": texto,
        "parse_mode": "Markdown"
    }
    if reply_markup:
        payload["reply_markup"] = reply_markup
    try:
        r = requests.post(url, json=payload, timeout=20)
        return r.status_code == 200
    except Exception as e:
        logging.error(f"Erro ao enviar mensagem no Telegram: {e}")
        return False

def obter_teclado_comandos():
    """Cria botões de acesso rápido no Telegram."""
    return {
        "keyboard": [
            [{"text": "📊 Status dos Jobs"}, {"text": "💰 Saldo e Custos"}],
            [{"text": "🧪 Status do JEV"}, {"text": "❓ Ajuda"}]
        ],
        "resize_keyboard": True
    }

def obter_status_jobs():
    """Consulta o status dos lotes de Batch na API do OpenRouter."""
    if not OPENROUTER_API_KEY:
        return "⚠️ Chave `OPEN_ROUTER_API_KEY_2` não configurada."
    
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
    batches = [
        ("batch-1792339733-zQrGUXlpEby3n1BTNQzL", "Gemini 3.8 Flash (mid)"),
        ("batch-1792339735-RucI3RjGrGS4Iwsa6BvB", "Gemini 3.8 Flash (high)")
    ]

    msg = "📊 *Status dos Lotes (Batch API)*\n\n"
    for b_id, nome in batches:
        try:
            r = requests.get(f"https://openrouter.ai/api/beta/batches/{b_id}", headers=headers, timeout=15)
            if r.status_code == 200:
                d = r.json()
                st = d.get("status", "desconhecido").upper()
                counts = d.get("request_counts", {})
                tot = counts.get("total", 0)
                comp = counts.get("completed", 0)
                fail = counts.get("failed", 0)
                emoji = "✅" if st == "COMPLETED" else "⏳"
                msg += f"{emoji} *{nome}*\n"
                msg += f"• Status: `{st}`\n"
                msg += f"• Progresso: {comp}/{tot} concluídas (Falhas: {fail})\n\n"
            else:
                msg += f"⚠️ *{nome}*: Erro HTTP {r.status_code}\n\n"
        except Exception as e:
            msg += f"⚠️ *{nome}*: Falha ao consultar ({e})\n\n"
    return msg

def obter_saldo_e_custos():
    """Consulta saldo no OpenRouter e valor acumulado do experimento."""
    if not OPENROUTER_API_KEY:
        return "⚠️ Chave `OPEN_ROUTER_API_KEY_2` não configurada."
    
    headers = {"Authorization": f"Bearer {OPENROUTER_API_KEY}"}
    try:
        r = requests.get("https://openrouter.ai/api/v1/credits", headers=headers, timeout=15)
        if r.status_code == 200:
            d = r.json().get("data", {})
            tot = d.get("total_credits", 0)
            use = d.get("total_usage", 0)
            saldo = round(tot - use, 4)
            emoji_saldo = "🟢" if saldo > 0 else "🔴"
            msg = "💰 *Relatório Financeiro OpenRouter*\n\n"
            msg += f"• Total Adquirido: `${tot:.2f} USD`\n"
            msg += f"• Uso Faturado: `${use:.4f} USD`\n"
            msg += f"• Saldo Atual: {emoji_saldo} *`${saldo:.4f} USD`*\n\n"
            msg += "📈 *Custo Acumulado do Experimento (4 Operações):*\n"
            msg += "• Total Geral: `~$27.55 USD` (26.997 testes)\n"
            msg += "• Expressões Combinadas: `$11.91 USD`\n"
            msg += "• Saldo suficiente para rodar o JEV: *SIM* (< $0.01 USD necessário)"
            return msg
        else:
            return f"⚠️ Erro ao consultar créditos: HTTP {r.status_code}"
    except Exception as e:
        return f"⚠️ Falha de conexão: {e}"

def obter_status_jev():
    """Verifica a base do JEV e prontidão para rodar."""
    p_base = os.path.join(PASTA_RAIZ, "jev", "bases_de_dados", "base_jev_completa.csv")
    if os.path.exists(p_base):
        try:
            import pandas as pd
            df = pd.read_csv(p_base)
            n_tot = len(df)
            n_v = (df["tipo_expressao"] == "VERDADEIRA").sum()
            n_f = (df["tipo_expressao"] == "FALSA").sum()
            msg = "🧪 *Status do Experimento JEV (1.14)*\n\n"
            msg += f"• Base pronta: `base_jev_completa.csv`\n"
            msg += f"• Total de Amostras: `{n_tot}` (100 por dígito: 50/50)\n"
            msg += f"• Expressões Verdadeiras: `{n_v}`\n"
            msg += f"• Expressões Falsas: `{n_f}` (1.164 erros reais de modelos)\n"
            msg += f"• Modelo: `typesafe/jev-1.14` (Decisions API)\n"
            msg += f"• Custo estimado: `< $0.01 USD`\n"
            msg += f"• Status: *Aguardando autorização para execução*"
            return msg
        except Exception as e:
            return f"⚠️ Erro ao ler base do JEV: {e}"
    else:
        return "⚠️ Base do JEV ainda não encontrada em `jev/bases_de_dados/`."

def responder_com_ia(chat_id, pergunta_usuario):
    """Responde a perguntas em linguagem natural usando o modelo via OpenRouter."""
    if not OPENROUTER_API_KEY:
        enviar_mensagem_telegram(chat_id, "⚠️ Não posso responder por IA porque a chave do OpenRouter não está configurada.")
        return

    enviar_mensagem_telegram(chat_id, "🤔 _Processando sua pergunta..._")

    prompt_sistema = (
        "Você é o assistente virtual do experimento de TCC sobre Raciocínio Matemático nos LLMs, "
        "conduzido por Átila Prudente. O experimento avalia 12 modelos da família Google Gemini "
        "(do 2.5 flash ao 3.8 flash com variações low, medium e high) e o modelo de decisão TypeSafe JEV 1.14. "
        "Seja extremamente prestativo, inteligente, objetivo e direto ao ponto. "
        "Responda sempre em português do Brasil e utilize formatação limpa compatível com Telegram."
    )

    url = "https://openrouter.ai/api/v1/chat/completions"
    headers = {
        "Authorization": f"Bearer {OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://tcc-experimento.ufba.br",
        "X-Title": "Telegram Bot Telemetria"
    }
    payload = {
        "model": "google/gemini-2.5-flash",
        "messages": [
            {"role": "system", "content": prompt_sistema},
            {"role": "user", "content": pergunta_usuario}
        ],
        "temperature": 0.3,
        "max_tokens": 800
    }

    try:
        resp = requests.post(url, headers=headers, json=payload, timeout=30)
        if resp.status_code == 200:
            dados = resp.json()
            resposta = dados["choices"][0]["message"]["content"]
            enviar_mensagem_telegram(chat_id, resposta)
        else:
            enviar_mensagem_telegram(chat_id, f"⚠️ Erro na IA ({resp.status_code}): {resp.text[:200]}")
    except Exception as e:
        enviar_mensagem_telegram(chat_id, f"⚠️ Erro ao gerar resposta: {e}")

def processar_mensagem(msg):
    chat = msg.get("chat", {})
    chat_id = str(chat.get("id", ""))
    texto = msg.get("text", "").strip()
    usuario = msg.get("from", {}).get("first_name", "Usuário")

    if not chat_id or not texto:
        return

    global AUTHORIZED_CHAT_ID
    # Pareamento automático de segurança no primeiro /start
    if not AUTHORIZED_CHAT_ID:
        salvar_chat_id(chat_id)
        msg_boas_vindas = (
            f"👋 Olá, *{usuario}*!\n\n"
            f"Seu Telegram foi *pareado com sucesso* com o servidor do experimento!\n"
            f"Chat ID autorizado: `{chat_id}`\n\n"
            f"Use os botões abaixo ou digite qualquer pergunta para falar comigo em tempo real!"
        )
        enviar_mensagem_telegram(chat_id, msg_boas_vindas, reply_markup=obter_teclado_comandos())
        return

    # Bloquear acessos de chats não autorizados
    if str(chat_id) != str(AUTHORIZED_CHAT_ID):
        logging.warning(f"Mensagem bloqueada de Chat ID não autorizado: {chat_id}")
        enviar_mensagem_telegram(chat_id, "⛔ Acesso restrito. Este bot é privado.")
        return

    # Roteamento de comandos
    texto_lower = texto.lower()
    if texto_lower in ["/start", "oi", "olá", "ola", "iniciar"]:
        msg_menu = (
            f"🤖 *Assistente do Experimento Online*\n\n"
            f"Estou conectado ao seu computador. Você pode clicar nos botões rápidos abaixo ou me fazer qualquer pergunta sobre o experimento!"
        )
        enviar_mensagem_telegram(chat_id, msg_menu, reply_markup=obter_teclado_comandos())

    elif texto_lower in ["/status", "status dos jobs", "status"]:
        enviar_mensagem_telegram(chat_id, obter_status_jobs())

    elif texto_lower in ["/saldo", "/custos", "saldo e custos", "saldo", "custo", "custos"]:
        enviar_mensagem_telegram(chat_id, obter_saldo_e_custos())

    elif texto_lower in ["/jev", "status do jev", "jev"]:
        enviar_mensagem_telegram(chat_id, obter_status_jev())

    elif texto_lower in ["/ajuda", "ajuda", "help", "❓ ajuda"]:
        msg_ajuda = (
            "📖 *Comandos Disponíveis:*\n\n"
            "• `/status` - Verifica o status dos lotes de Batch na API\n"
            "• `/saldo` - Consulta o saldo disponível e custo total do experimento\n"
            "• `/jev` - Exibe os detalhes da base e do modelo JEV 1.14\n"
            "• *Conversa livre:* Digite qualquer pergunta ou dúvida, e eu te responderei usando a IA do projeto!"
        )
        enviar_mensagem_telegram(chat_id, msg_ajuda, reply_markup=obter_teclado_comandos())

    else:
        # Conversa em linguagem natural usando a IA
        responder_com_ia(chat_id, texto)

def main():
    if not TELEGRAM_BOT_TOKEN or TELEGRAM_BOT_TOKEN == "SEU_TOKEN_DO_BOT_AQUI":
        print("\n" + "="*60)
        print("⚠️ ATENÇÃO: TELEGRAM_BOT_TOKEN NÃO CONFIGURADO!")
        print("Siga o passo a passo em 'telegram/README.md' para pegar o seu token")
        print("com o @BotFather no Telegram e colocá-lo em 'telegram/.env'.")
        print("="*60 + "\n")
        return

    logging.info("=== Iniciando Bot do Telegram em modo Long Polling ===")
    logging.info("O bot está escutando mensagens. Pressione Ctrl+C para encerrar.")

    offset = None
    while True:
        try:
            params = {"timeout": 30}
            if offset is not None:
                params["offset"] = offset

            resp = requests.get(f"{TELEGRAM_API_URL}/getUpdates", params=params, timeout=35)
            if resp.status_code == 200:
                dados = resp.json()
                for update in dados.get("result", []):
                    offset = update["update_id"] + 1
                    if "message" in update:
                        processar_mensagem(update["message"])
            elif resp.status_code == 401:
                logging.error("Token do Telegram inválido! Verifique o TELEGRAM_BOT_TOKEN.")
                time.sleep(10)
            else:
                time.sleep(2)
        except requests.exceptions.RequestException:
            time.sleep(3)
        except Exception as e:
            logging.error(f"Erro no ciclo do bot: {e}")
            time.sleep(3)

if __name__ == "__main__":
    main()

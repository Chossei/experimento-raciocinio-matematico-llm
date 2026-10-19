"""Ponte de Automação entre o Telegram e o Antigravity IDE

Este módulo:
1. Recebe a mensagem do usuário vinda do Telegram.
2. Clica na caixa de texto do Antigravity IDE na tela do computador.
3. Cola a mensagem e pressiona [ENTER].
4. Monitora o arquivo de log interno do Antigravity (transcript.jsonl) em tempo real.
5. Captura a resposta textual completa do agente e a retorna para ser enviada de volta no Telegram.
"""

import os
import sys
import time
import json
import glob
import logging
import ctypes
import pyautogui
import pyperclip

# Desativa o FAILSAFE para evitar travamentos quando o mouse estiver em cantos ou posições virtuais
pyautogui.FAILSAFE = False
pyautogui.PAUSE = 0.05

user32 = ctypes.windll.user32

PASTA_TELEGRAM = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_CONFIG_POSICAO = os.path.join(PASTA_TELEGRAM, "config_posicao.json")

def obter_arquivo_transcript_ativo():
    """Localiza o arquivo transcript.jsonl da conversa atualmente ativa."""
    padrao = os.path.expanduser(r"~/.gemini/antigravity-ide/brain/*/.system_generated/logs/transcript.jsonl")
    arquivos = glob.glob(padrao)
    if not arquivos:
        return None
    # Retorna o arquivo modificado mais recentemente
    return max(arquivos, key=os.path.getmtime)

def obter_posicao_chat():
    """Carrega as coordenadas salvas pelo calibrador ou calcula um ponto padrão."""
    if os.path.exists(ARQUIVO_CONFIG_POSICAO):
        try:
            with open(ARQUIVO_CONFIG_POSICAO, "r", encoding="utf-8") as f:
                d = json.load(f)
                return d.get("chat_x"), d.get("chat_y")
        except Exception as e:
            logging.error(f"Erro ao ler config_posicao.json: {e}")

    # Ponto padrão na resolução atual (barra inferior direita onde fica o chat do IDE)
    sw, sh = pyautogui.size()
    return int(sw * 0.75), int(sh * 0.93)

def obter_ultimo_step(caminho_transcript):
    """Lê o último step_index registrado no transcript."""
    if not caminho_transcript or not os.path.exists(caminho_transcript):
        return 0, None
    try:
        with open(caminho_transcript, "r", encoding="utf-8", errors="ignore") as f:
            linhas = f.readlines()
        if not linhas:
            return 0, None
        ultimo_obj = json.loads(linhas[-1])
        return ultimo_obj.get("step_index", 0), ultimo_obj
    except Exception as e:
        logging.error(f"Erro ao ler transcript: {e}")
        return 0, None

def clicar_na_coordenada(x, y):
    """Clica na tela utilizando PyAutoGUI e fallback nativo Win32."""
    try:
        user32.SetCursorPos(int(x), int(y))
        time.sleep(0.05)
        user32.mouse_event(0x0002, 0, 0, 0, 0) # MOUSEEVENTF_LEFTDOWN
        time.sleep(0.05)
        user32.mouse_event(0x0004, 0, 0, 0, 0) # MOUSEEVENTF_LEFTUP
    except Exception as e:
        logging.warning(f"Aviso no clique win32: {e}")

    try:
        pyautogui.click(x, y)
    except Exception as e:
        logging.warning(f"Aviso no clique pyautogui: {e}")

def injetar_texto_no_antigravity(texto):
    """Copia a mensagem, clica na caixa de texto, cola e aperta Enter."""
    chat_x, chat_y = obter_posicao_chat()
    logging.info(f"Clicando na coordenada do chat: ({chat_x}, {chat_y})")

    # 1. Copia o texto para a área de transferência primeiro
    pyperclip.copy(texto)
    time.sleep(0.1)

    # 2. Clica na caixa de texto do Antigravity
    clicar_na_coordenada(chat_x, chat_y)
    time.sleep(0.2)

    # 3. Cola o texto (Ctrl + V)
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.2)

    # 4. Envia Enter
    pyautogui.press("enter")
    time.sleep(0.1)
    logging.info("Texto injetado e [ENTER] pressionado com sucesso!")

def extrair_solicitacao_permissao(obj):
    """Verifica se o passo do transcript é uma pergunta (ask_question) ou pedido de autorização."""
    if not isinstance(obj, dict):
        return None
    
    tipo = obj.get("type", "")
    tool_calls = obj.get("tool_calls", [])
    if isinstance(tool_calls, list):
        for tc in tool_calls:
            if isinstance(tc, dict) and tc.get("name") == "ask_question":
                args = tc.get("args", {})
                if isinstance(args, str):
                    try:
                        args = json.loads(args)
                    except Exception:
                        args = {}
                questions = args.get("questions", [])
                msg = "🔔 *O Antigravity está solicitando sua confirmação / escolha:*\n\n"
                for q in questions:
                    msg += f"❓ *{q.get('question', '')}*\n"
                    for op in q.get("options", []):
                        msg += f"• `{op}`\n"
                msg += "\n👉 *Envie sua resposta ou clique em '✅ Permitir / Sim' no Telegram para autorizar!*"
                return msg
            
            if tc.get("status") in ["CONFIRMATION_REQUEST", "WAITING_APPROVAL", "PENDING_APPROVAL"]:
                nome = tc.get("name", "ação")
                return f"🔔 *O Antigravity está solicitando permissão para executar `{nome}`!*\n\n👉 *Envie 'sim' ou toque em '✅ Permitir / Sim' para autorizar.*"

    if tipo in ["CONFIRMATION_REQUEST", "PERMISSION_REQUEST"]:
        return "🔔 *O Antigravity está solicitando permissão na tela do computador.*\n\n👉 *Envie 'sim' ou toque em '✅ Permitir / Sim' para autorizar.*"

    return None

def executar_comando_antigravity(mensagem_usuario, callback_status=None, timeout_segundos=900):
    """Executa o ciclo completo:
    1. Injeta o prompt no IDE
    2. Monitora o transcript até a resposta final ou pedido de autorização
    3. Retorna o texto de resposta
    """
    transcript_path = obter_arquivo_transcript_ativo()
    if not transcript_path:
        return "⚠️ Não foi possível localizar o arquivo de sessão do Antigravity IDE no disco."

    step_inicial, _ = obter_ultimo_step(transcript_path)
    logging.info(f"Iniciando ciclo. Step inicial no transcript: {step_inicial}")

    # Injeta a mensagem na interface
    injetar_texto_no_antigravity(mensagem_usuario)

    if callback_status:
        callback_status("📥 _Mensagem enviada ao Antigravity IDE! Aguardando o agente processar..._")

    inicio = time.time()
    ultimo_status_notificado = ""
    ultimo_tamanho_linhas = 0

    while time.time() - inicio < timeout_segundos:
        time.sleep(1.5)
        try:
            with open(transcript_path, "r", encoding="utf-8", errors="ignore") as f:
                linhas = f.readlines()

            if len(linhas) == ultimo_tamanho_linhas:
                continue
            ultimo_tamanho_linhas = len(linhas)

            # Analisa as novas linhas a partir do final
            for l in reversed(linhas):
                try:
                    d = json.loads(l)
                except Exception:
                    continue

                idx = d.get("step_index", 0)
                if idx <= step_inicial:
                    break

                # Notifica se o agente estiver executando comandos
                tipo = d.get("type", "")
                if callback_status:
                    if tipo == "RUN_COMMAND" and ultimo_status_notificado != "terminal":
                        callback_status("⚙️ _O agente está executando comandos no computador..._")
                        ultimo_status_notificado = "terminal"
                    elif tipo in ["REPLACE_FILE_CONTENT", "WRITE_TO_FILE"] and ultimo_status_notificado != "edit":
                        callback_status("📝 _O agente está editando arquivos do projeto..._")
                        ultimo_status_notificado = "edit"

                # Verifica se há pedido de permissão / pergunta interativa
                msg_perm = extrair_solicitacao_permissao(d)
                if msg_perm:
                    logging.info(f"Solicitação de permissão capturada no step {idx}!")
                    return msg_perm

                # Verifica se é a resposta final do agente (PLANNER_RESPONSE com conteúdo e sem ferramentas)
                if d.get("source") == "MODEL" and d.get("type") == "PLANNER_RESPONSE":
                    content = d.get("content")
                    tool_calls = d.get("tool_calls")
                    status = d.get("status", "")
                    if content and not tool_calls and status == "DONE":
                        logging.info(f"Resposta final do agente capturada no step {idx}!")
                        return content
        except Exception as e:
            logging.error(f"Erro durante leitura do transcript: {e}")

    return "⚠️ Tempo limite excedido (mais de 15 minutos). O agente pode ainda estar processando uma tarefa longa ou aguardando resposta manual."

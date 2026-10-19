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
import pyautogui
import pyperclip

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

def injetar_texto_no_antigravity(texto):
    """Clica na caixa de texto, cola a mensagem e aperta Enter."""
    chat_x, chat_y = obter_posicao_chat()
    
    # Salva posição original do mouse para restaurar depois
    orig_x, orig_y = pyautogui.position()

    logging.info(f"Clicando na coordenada do chat: ({chat_x}, {chat_y})")
    pyautogui.click(chat_x, chat_y)
    time.sleep(0.15)

    # Copia o texto para o clipboard garantindo caracteres especiais e UTF-8
    pyperclip.copy(texto)
    time.sleep(0.1)

    # Cola (Ctrl+V) e dá Enter
    pyautogui.hotkey("ctrl", "v")
    time.sleep(0.15)
    pyautogui.press("enter")
    time.sleep(0.1)

    # Restaura o cursor
    pyautogui.moveTo(orig_x, orig_y)

def executar_comando_antigravity(mensagem_usuario, callback_status=None, timeout_segundos=600):
    """Executa o ciclo completo:
    1. Injeta o prompt no IDE
    2. Monitora o transcript até a resposta final
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
        callback_status("📥 _Mensagem injetada no Antigravity IDE! Aguardando o agente processar..._")

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

                # Notifica progresso se o agente estiver executando comandos
                tipo = d.get("type", "")
                if callback_status:
                    if tipo == "RUN_COMMAND" and ultimo_status_notificado != "terminal":
                        callback_status("⚙️ _O agente está executando comandos no computador..._")
                        ultimo_status_notificado = "terminal"
                    elif tipo in ["REPLACE_FILE_CONTENT", "WRITE_TO_FILE"] and ultimo_status_notificado != "edit":
                        callback_status("📝 _O agente está editando arquivos do projeto..._")
                        ultimo_status_notificado = "edit"

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

    return "⚠️ Tempo limite excedido (timeout). O agente pode ainda estar processando ou ocorreu um travamento."

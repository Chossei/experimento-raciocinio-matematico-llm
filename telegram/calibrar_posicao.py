"""Script de Calibração da Caixa de Texto do Antigravity IDE

Este script ajuda você a capturar a coordenada exata (X, Y) da caixa de texto
onde você digita suas mensagens no Antigravity IDE.
"""

import os
import sys
import time
import json

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")

try:
    import pyautogui
except ImportError:
    print("⚠️ pyautogui não encontrado. Instalando...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pyautogui", "pyperclip"])
    import pyautogui

PASTA_TELEGRAM = os.path.dirname(os.path.abspath(__file__))
ARQUIVO_CONFIG = os.path.join(PASTA_TELEGRAM, "config_posicao.json")

def main():
    print("\n" + "="*65)
    print("   🎯 CALIBRAÇÃO DA CAIXA DE TEXTO DO ANTIGRAVITY IDE")
    print("="*65)
    print("\nINSTRUÇÕES:")
    print("1. Assim que a contagem começar, posicione o cursor do mouse")
    print("   EXATAMENTE em cima da caixa de texto do Antigravity onde você digita.")
    print("2. Não clique, apenas mantenha o mouse parado lá até o fim da contagem.\n")
    
    input("Pressione [ENTER] no teclado para iniciar a contagem de 5 segundos...")
    print()

    for i in range(5, 0, -1):
        print(f"⏳ Capturando posição em {i} segundo(s)... Mantenha o mouse sobre o chat!")
        time.sleep(1)

    x, y = pyautogui.position()
    print(f"\n✅ POSIÇÃO CAPTURADA COM SUCESSO:")
    print(f"   X: {x} pixels")
    print(f"   Y: {y} pixels")

    config = {
        "chat_x": x,
        "chat_y": y,
        "screen_width": pyautogui.size().width,
        "screen_height": pyautogui.size().height,
        "data_calibracao": time.strftime("%Y-%m-%d %H:%M:%S")
    }

    with open(ARQUIVO_CONFIG, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=2, ensure_ascii=False)

    print(f"\n💾 Coordenadas salvas em '{ARQUIVO_CONFIG}'!")
    print("Agora o bot do Telegram sabe exatamente onde clicar para colar suas mensagens.\n")
    print("="*65 + "\n")

if __name__ == "__main__":
    main()

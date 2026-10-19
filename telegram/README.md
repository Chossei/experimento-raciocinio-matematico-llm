# 🤖 Assistente Virtual do Experimento via Telegram

Este módulo permite que você converse com o assistente do seu experimento em tempo real pelo seu smartphone (via aplicativo do Telegram) e consulte métricas, status de execuções de Batch e saldo da conta OpenRouter.

---

## 🚀 Passo a Passo para Ativação (Menos de 2 minutos)

### 1. Criar o seu Bot no Telegram (Gratuito)
1. Abra o aplicativo do **Telegram** no celular ou no computador.
2. Na barra de pesquisa, procure por: `@BotFather` (ele tem um selo azul de verificado).
3. Inicie a conversa e envie o comando:
   ```text
   /newbot
   ```
4. O BotFather vai pedir um **nome** para o seu bot (ex: `Experimento LLM Bot`).
5. Em seguida, vai pedir um **username** que termine obrigatoriamente com `bot` (ex: `meu_experimento_atila_bot`).
6. O BotFather vai te responder com uma mensagem contendo o seu **HTTP API Token**, no formato:
   ```text
   7123456789:AAFlq... (uma sequência longa de letras e números)
   ```
   *Copie essa chave.*

---

### 2. Configurar o Token no Projeto
Crie um arquivo chamado `.env` dentro da pasta `telegram/` (ou abra o arquivo `chave.env` na raiz do projeto) e adicione a linha:

```env
TELEGRAM_BOT_TOKEN=SEU_TOKEN_COPIADO_AQUI
```

*(Substitua `SEU_TOKEN_COPIADO_AQUI` pelo token real que o BotFather gerou).*

---

### 3. Iniciar o Bot no Computador
Você pode iniciar de duas formas:

- **Opção 1 (Mais fácil):** Dê um duplo clique no arquivo `iniciar_bot.bat` dentro da pasta `telegram/`.
- **Opção 2 (Via terminal PowerShell):**
  ```powershell
  & "C:\Users\choss\AppData\Local\Programs\Python\Python312\python.exe" telegram/bot_telegram.py
  ```

O terminal exibirá:
```text
=== Iniciando Bot do Telegram em modo Long Polling ===
O bot está escutando mensagens...
```

---

### 4. Parear com o seu Celular
1. No seu Telegram, abra a conversa com o bot que você acabou de criar.
2. Clique em **Iniciar** ou envie `/start`.
3. O bot reconhecerá seu usuário automaticamente, salvará seu `Chat ID` para segurança (impedindo que outras pessoas acessem) e exibirá os botões interativos no teclado do celular!

---

## 📱 Funcionalidades Disponíveis

| Botão / Comando | O que faz? |
| :--- | :--- |
| **📊 Status dos Jobs** (`/status`) | Consulta a API do OpenRouter e exibe o progresso dos lotes de Batch (ex: Gemini 3.8 Flash mid e high). |
| **💰 Saldo e Custos** (`/saldo`) | Mostra saldo restante em dólares e custo total acumulado do experimento. |
| **🧪 Status do JEV** (`/jev`) | Informa sobre o dataset do JEV (3.600 amostras 50/50) e prontidão. |
| **❓ Ajuda** (`/ajuda`) | Exibe o guia rápido de comandos. |
| **💬 Conversa Livre (IA)** | Envie qualquer pergunta em português sobre o experimento, hipóteses, modelos ou dados, e a IA responderá diretamente pelo chat! |

---

## 🔒 Segurança
- O bot utiliza **emparelhamento automático**: na primeira vez que você der `/start`, ele memoriza o seu `TELEGRAM_CHAT_ID`.
- Qualquer outra pessoa que tentar enviar mensagens ao seu bot receberá uma mensagem de "Acesso restrito".

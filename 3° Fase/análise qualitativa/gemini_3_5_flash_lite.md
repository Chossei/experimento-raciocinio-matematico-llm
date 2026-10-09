# Análise Qualitativa de Raciocínio: Gemini 3.5 Flash Lite

**Modelo:** `google/gemini-3.5-flash-lite`  
**Configuração de Reasoning:** `effort: "minimal"`  
**Taxa Global de Acerto em Expressões Combinadas:** 12,9% (58 acertos / 392 erros)  
**Padrão Cognitivo Geral:** O Gemini 3.5 Flash Lite representa o caso extremo de modelo enxuto e hiper-econômico. Sob o parâmetro de esforço `"minimal"`, o modelo quase não consome tokens de pensamento ocultos (média próxima de 0 tokens). Sem um espaço de rascunho mental (*scratchpad*), o modelo tenta resolver expressões aritméticas compostas em uma **única passagem direta (*single-pass forward inference*)**, o que funciona com maestria em 2 dígitos (100% de acerto), mas colapsa catastrófica e imediatamente a partir de 3 dígitos (apenas 14% de acerto) e atinge 0% absoluto de 5 a 10 dígitos.

---

## 1. Amostras de Acerto (5 Casos Analisados)

### Amostra 1 (2 Dígitos) - Memorização Paramétrica Pura
* **Expressão:** `71 * (84 + 75) = ?`
* **Gabarito Real:** `11289`
* **Resposta do Modelo:** `11289`
* **Tokens de Raciocínio Gerados:** 0 tokens
* **Fluxo Cognitivo Deduzido:**
  - `84 + 75 = 159`
  - `71 * 159 = 11289`
* **Diagnóstico da Eficácia:** A operação envolve números pequenos cuja composição posicional cabe diretamente nos pesos da camada de atenção feed-forward, sem necessidade de decomposição sequencial em múltiplos passos.

---

### Amostra 2 (2 Dígitos) - Fatoração com Múltiplo de 10
* **Expressão:** `20 * (32 + 87) = ?`
* **Gabarito Real:** `2380`
* **Resposta do Modelo:** `2380`
* **Tokens de Raciocínio Gerados:** 0 tokens
* **Fluxo Cognitivo Deduzido:**
  - `32 + 87 = 119`
  - `20 * 119 = 2 * 119 * 10 = 238 * 10 = 2380`
* **Diagnóstico da Eficácia:** A presença do multiplicador `20` permitiu ao modelo duplicar `119` e acrescentar zero, uma transformação trivial para modelos leves.

---

### Amostra 3 (2 Dígitos) - Adição Fechada em Dezena Redonda
* **Expressão:** `63 * (14 + 40) = ?`
* **Gabarito Real:** `3402`
* **Resposta do Modelo:** `3402`
* **Tokens de Raciocínio Gerados:** 0 tokens
* **Fluxo Cognitivo Deduzido:**
  - `14 + 40 = 54`
  - `63 * 54 = 3402`
* **Diagnóstico da Eficácia:** Números pequenos sem complexidade de vai-um encadeado. Resolução direta em 1 token gerado.

---

### Amostra 4 (3 Dígitos) - Caso Raro com Múltiplo de 5 e Soma Limpa
* **Expressão:** `325 * (779 + 320) = ?`
* **Gabarito Real:** `357175`
* **Resposta do Modelo:** `357175`
* **Tokens de Raciocínio Gerados:** 0 tokens
* **Fluxo Cognitivo Deduzido:**
  - `779 + 320 = 1099` (quase `1100`)
  - `325 * (1100 - 1) = 325 * 1100 - 325 = 357500 - 325 = 357175`
* **Diagnóstico da Eficácia:** O acerto fortuito se deu pela estrutura do termo `1099`, que permitiu ao modelo aplicar implicitamente o atalho `325 * 11` seguido da subtração de 325.

---

### Amostra 5 (4 Dígitos) - O Único Acerto de 4 Dígitos em 50 Testes
* **Expressão:** `2100 * (7085 + 3917) = ?`
* **Gabarito Real:** `23104200`
* **Resposta do Modelo:** `23104200`
* **Tokens de Raciocínio Gerados:** 0 tokens
* **Fluxo Cognitivo Deduzido:**
  - `7085 + 3917 = 11002`
  - `2100 * 11002 = 21 * 11002 * 100 = (231042) * 100 = 23104200`
* **Diagnóstico da Eficácia:** Uma anomalia estatística explicada pela estrutura dos operandos: `2100` termina em `00` e a soma resulta em `11002` (com dois zeros centrais). Multiplicar `21 * 11002` é uma operação quase livre de carry interno (`21 * 11 = 231` e `21 * 2 = 42`).

---

## 2. Amostras de Erro (5 Casos Analisados)

### Amostra 1 (3 Dígitos) - Início da Falha por Falta de Scratchpad
* **Expressão:** `173 * (674 + 807) = ?`
* **Gabarito Real:** `256213`
* **Resposta do Modelo:** `254711` *(Diferença: -1.502)*
* **Tokens de Raciocínio Gerados:** 0 tokens
* **Diagnóstico da Falha:** A soma interna é `674 + 807 = 1481`. Sem tokens de reflexão, o modelo aproxima `173 * 1500 ≈ 259500`, prevê `254711` como um número plausível no espaço latente. A ordem de grandeza está correta (~250 mil), mas a precisão aritmética se perde nos 3 últimos dígitos.

---

### Amostra 2 (4 Dígitos) - Alucinação Heurística em 8 Algarismos
* **Expressão:** `8249 * (9801 + 7621) = ?`
* **Gabarito Real:** `143714078`
* **Resposta do Modelo:** `143896562` *(Diferença: +182.484)*
* **Tokens de Raciocínio Gerados:** 0 tokens
* **Diagnóstico da Falha:** `9801 + 7621 = 17422`. O produto real é `143.714.078`. O modelo retornou `143.896.562`. Ele acertou perfeitamente os primeiros três dígitos (`143...`), demonstrando intuição sobre a magnitude, mas errou todas as 5 casas inferiores por ausência de acumulação vertical de parcelas.

---

### Amostra 3 (5 Dígitos) - Desvio de Milhões por Interpolação
* **Expressão:** `32776 * (63648 + 22871) = ?`
* **Gabarito Real:** `2835746744`
* **Resposta do Modelo:** `2840919408` *(Diferença: +5.172.664)*
* **Tokens de Raciocínio Gerados:** 0 tokens
* **Diagnóstico da Falha:** A soma é `86519`. `32776 * 86519` tem como estimativa inicial `32,7k * 86,5k ≈ 2,835 bilhões`. O modelo produziu `2,840 bilhões`. O desvio relativo é de apenas 0,18%, mas em aritmética exata é um erro completo. O modelo se comporta como uma calculadora de baixa precisão de ponto flutuante.

---

### Amostra 4 (6 Dígitos) - Perda Total de Rastreamento de Carry
* **Expressão:** `174273 * (466488 + 334134) = ?`
* **Gabarito Real:** `139526797806`
* **Resposta do Modelo:** `138977232232` *(Diferença: -549.565.574)*
* **Tokens de Raciocínio Gerados:** 0 tokens
* **Diagnóstico da Falha:** O produto de 6 por 6 dígitos exige 36 multiplicações elementares e dezenas de carries. Sem reasoning ativo, a probabilidade de um modelo com arquitetura Lite acertar 36 produtos simultâneos em um passe forward é estatisticamente nula.

---

### Amostra 5 (7 Dígitos) - Alucinação de 14 Casas Decimais
* **Expressão:** `4203095 * (2347485 + 5019498) = ?`
* **Gabarito Real:** `30964129412385`
* **Resposta do Modelo:** `30985162464735` *(Diferença: +21.033.052.350)*
* **Tokens de Raciocínio Gerados:** 0 tokens
* **Diagnóstico da Falha:** O modelo acerta a primeira dezena de trilhões (`309...`) e os últimos dois dígitos (`...85` vs `...35` errando por pouco), mas todos os 8 dígitos centrais são ruído estocástico decorrente da incapacidade de reter estados matemáticos transitórios sem tokens de reflexão.

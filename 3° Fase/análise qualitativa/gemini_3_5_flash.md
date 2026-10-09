# Análise Qualitativa de Raciocínio: Gemini 3.5 Flash

**Modelo:** `google/gemini-3.5-flash`  
**Configuração de Reasoning:** `effort: "minimal"`  
**Taxa Global de Acerto em Expressões Combinadas:** 44,9% (202 acertos / 248 erros)  
**Padrão Cognitivo Geral:** O Gemini 3.5 Flash exibe um comportamento de alta combatividade algorítmica: mesmo com esforço "minimal", ele aloca agressivamente tokens de raciocínio (média de 602 tokens em acertos e 963 tokens em erros). Ele domina com facilidade operações de 2 a 4 dígitos. Porém, sob alta carga aritmética (5 a 8 dígitos), ele sofre de uma patologia cognitiva característica: **vazamento de rascunho (*scratchpad leakage*)**. Em vez de sintetizar o número final, o modelo transborda os produtos parciais da sua cadeia de pensamento diretamente para o texto final, gerando números concatenados anômalos.

---

## 1. Amostras de Acerto (5 Casos Analisados)

### Amostra 1 (2 Dígitos) - Condução Eficiente de Adição e Multiplicação
* **Expressão:** `86 * (86 + 35) = ?`
* **Gabarito Real:** `10406`
* **Resposta do Modelo:** `10406`
* **Tokens de Raciocínio Gerados:** 333 tokens
* **Fluxo Cognitivo:**
  1. Soma dos parênteses: `86 + 35 = 121`.
  2. Multiplicação: `86 * 121 = 86 * (100 + 20 + 1)`.
  3. `8600 + 1720 + 86 = 10406`.
* **Diagnóstico da Eficácia:** Uso canônico da base 10 com verificação em apenas 333 tokens.

---

### Amostra 2 (3 Dígitos) - Alta Precisão com Três Parcelas
* **Expressão:** `493 * (307 + 351) = ?`
* **Gabarito Real:** `324394`
* **Resposta do Modelo:** `324394`
* **Tokens de Raciocínio Gerados:** 606 tokens
* **Fluxo Cognitivo:**
  1. Soma: `307 + 351 = 658`.
  2. `493 * 658`: decompõe `493` como `(500 - 7)`.
  3. `500 * 658 = 329000`.
  4. `7 * 658 = 4606`.
  5. Subtração: `329000 - 4606 = 324394`.
* **Diagnóstico da Eficácia:** Estratégia de atalho cognitivo (`500 - 7`) altamente inteligente, transformando uma multiplicação demorada de 3x3 dígitos em uma multiplicação trivial por 500 seguida de subtração rápida.

---

### Amostra 3 (4 Dígitos) - Expansão Polinomial Exata
* **Expressão:** `8424 * (9281 + 3625) = ?`
* **Gabarito Real:** `108720144`
* **Resposta do Modelo:** `108720144`
* **Tokens de Raciocínio Gerados:** 837 tokens
* **Fluxo Cognitivo:**
  1. `9281 + 3625 = 12906`.
  2. `8424 * 12906`:
     - `8000 * 12906 = 103248000`
     - `400 * 12906 = 5162400`
     - `20 * 12906 = 258120`
     - `4 * 12906 = 51624`
  3. Soma dos 4 termos parciais acumulada sem nenhum erro de transporte: `108720144`.
* **Diagnóstico da Eficácia:** Raciocínio disciplinado de 837 tokens garantindo que cada um dos 4 produtos intermediários mantivesse alinhamento de base.

---

### Amostra 4 (5 Dígitos) - Resolução no Início da Zona Crítica
* **Expressão:** `82635 * (10713 + 50078) = ?`
* **Gabarito Real:** `5023464285`
* **Resposta do Modelo:** `5023464285`
* **Tokens de Raciocínio Gerados:** 737 tokens
* **Fluxo Cognitivo:**
  1. `10713 + 50078 = 60791`.
  2. `82635 * 60791`.
  3. Graças à presença do zero intermediário em `60791` (`60000 + 700 + 90 + 1`), a multiplicação é reduzida a 4 passos em vez de 5, permitindo fechar os 10 dígitos com precisão.
* **Diagnóstico da Eficácia:** A presença de zeros em potências intermediárias reduz a carga de trabalho de raciocínio abaixo do limiar de saturação do 3.5 Flash.

---

### Amostra 5 (6 Dígitos) - Sucesso em 12 Casas Decimais
* **Expressão:** `201869 * (690329 + 894646) = ?`
* **Gabarito Real:** `319957318275`
* **Resposta do Modelo:** `319957318275`
* **Tokens de Raciocínio Gerados:** 960 tokens (limite de saturação do modelo)
* **Fluxo Cognitivo:**
  1. `690329 + 894646 = 1584975`.
  2. Multiplicação de 6 dígitos por 7 dígitos executada no topo da capacidade de reasoning (960 tokens).
  3. O modelo executou a soma dos produtos de `200000`, `1000`, `800`, `60`, `9` contra `1584975`, convergindo com sucesso para `319957318275`.
* **Diagnóstico da Eficácia:** Acerto raro e impressionante que demonstra que o modelo é capaz de alcançar precisão em 12 casas quando todas as verificações parciais se alinham sem colapso de contexto.

---

## 2. Amostras de Erro (5 Casos Analisados)

### Amostra 1 (4 Dígitos) - Vazamento Catastrófico de Produtos Intermediários
* **Expressão:** `9626 * (3483 + 7857) = ?`
* **Gabarito Real:** `109158840`
* **Resposta do Modelo:** `40900010206000068040226` (23 algarismos)
* **Tokens de Raciocínio Gerados:** 956 tokens
* **Diagnóstico da Falha:** `3483 + 7857 = 11340`. Ao multiplicar `9626 * 11340`, o modelo calculou mentalmente os produtos parciais, mas a camada de decodificação sofreu colapso e imprimiu os buffers de cálculo concatenados (`409000... 1020600... 6804...`) como se fossem uma única string numérica. Erro severo de violação de integridade representacional.

---

### Amostra 2 (5 Dígitos) - Transbordamento de Potências de 10
* **Expressão:** `82837 * (80771 + 66413) = ?`
* **Gabarito Real:** `12192281008` (11 algarismos)
* **Resposta do Modelo:** `81177472000012192281008` (23 algarismos)
* **Tokens de Raciocínio Gerados:** 961 tokens
* **Diagnóstico da Falha:** Repare com atenção no final da resposta do modelo: `...12192281008`! O modelo **acertou o resultado exato da conta com perfeição milimétrica**, mas antes de emiti-lo, imprimiu o produto parcial da primeira parcela de milhares (`811774720000`), concatenando ambos na mesma resposta! O reasoning encontrou o valor certo, mas falhou em descartar o rascunho anterior.

---

### Amostra 3 (6 Dígitos) - Concatenação do Multiplicador na Saída
* **Expressão:** `870247 * (323783 + 601647) = ?`
* **Gabarito Real:** `805352681210`
* **Resposta do Modelo:** `5352681210870247`
* **Tokens de Raciocínio Gerados:** 961 tokens
* **Diagnóstico da Falha:** A resposta do modelo contém os dígitos finais corretos da resposta (`5352681210`) seguidos da colagem imediata do próprio multiplicador original (`870247`)! Novamente, uma falha de descarregamento de memória do reasoning sobre a camada de resposta.

---

### Amostra 4 (7 Dígitos) - Truncamento de Dígitos por Esgotamento
* **Expressão:** `4046978 * (6287737 + 7534361) = ?`
* **Gabarito Real:** `55937726519844` (14 algarismos)
* **Resposta do Modelo:** `559334519844` (12 algarismos)
* **Tokens de Raciocínio Gerados:** 958 tokens
* **Diagnóstico da Falha:** O modelo acertou o prefixo (`5593...`) e o sufixo (`...519844`), mas "engoliu" dois dígitos no meio durante a conversão do buffer de atenção, encurtando o resultado de 14 para 12 casas.

---

### Amostra 5 (8 Dígitos) - Degradação em Repetição Estocástica (`...11111...`)
* **Expressão:** `86664194 * (84567779 + 18108971) = ?`
* **Gabarito Real:** `8898397781289500`
* **Resposta do Modelo:** `8898398111111500`
* **Tokens de Raciocínio Gerados:** 958 tokens
* **Diagnóstico da Falha:** O modelo acertou a magnitude inicial (`889839...`) e os zeros finais (`...500`), mas ao se deparar com a complexidade de 8x8 colunas no limite de 958 tokens, o mecanismo de atenção entrou em loop de probabilidade e gerou uma sequência de repetição de algarismos 1 (`...8111111500`), um sinal clássico de colapso de certeza estatística do LLM.

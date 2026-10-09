# Análise Qualitativa de Raciocínio: Gemini 3.1 Pro Preview

**Modelo:** `google/gemini-3.1-pro-preview`  
**Configuração de Reasoning:** `effort: "low"`  
**Taxa Global de Acerto em Expressões Combinadas:** 60,9% (274 acertos / 176 erros)  
**Padrão Cognitivo Geral:** O Gemini 3.1 Pro Preview é o modelo de maior profundidade computacional da pesquisa. Seu raciocínio não é meramente conversacional: ele opera como um calculador algorítmico matricial. Ele mantém altíssima estabilidade de carry até 6 e 7 dígitos. Quando erra, os erros não são alucinações caóticas, mas **desvios potencias exatos** (como `-1.000`, `-2.400` ou `+2.000.000`), decorrentes de falhas microscópicas na soma de colunas de produtos parciais.

---

## 1. Amostras de Acerto (5 Casos Analisados)

### Amostra 1 (2 Dígitos) - Execução Instantânea
* **Expressão:** `76 * (94 + 57) = ?`
* **Gabarito Real:** `11476`
* **Resposta do Modelo:** `11476`
* **Tokens de Raciocínio Gerados:** 350 tokens
* **Reconstituição do Fluxo Cognitivo:**
  1. *Subexpressão Interna:* Avalia `94 + 57`. Faz `90 + 50 = 140`; `4 + 7 = 11`; resultado `151`.
  2. *Multiplicação Direta:* `76 * 151`. Decompõe `151` como `150 + 1`.
  3. *Cálculo:* `76 * 150 = 76 * 100 + 76 * 50 = 7600 + 3800 = 11400`.
  4. *Termo Residual:* `11400 + 76 * 1 = 11476`.
  5. *Validação:* Formato de saída restrito a número inteiro.
* **Diagnóstico da Eficácia:** Uso eficiente de decomposição (`150 + 1`). Resolução limpa em apenas 350 tokens sem desperdício de contexto.

---

### Amostra 2 (3 Dígitos) - Alinhamento Aritmético Perfeito
* **Expressão:** `483 * (208 + 673) = ?`
* **Gabarito Real:** `425523`
* **Resposta do Modelo:** `425523`
* **Tokens de Raciocínio Gerados:** 503 tokens
* **Reconstituição do Fluxo Cognitivo:**
  1. *Subexpressão Interna:* `208 + 673 = 881`.
  2. *Estratégia de Multiplicação:* `483 * 881`.
  3. *Decomposição em Potências:*
     - `483 * 800 = 386400`
     - `483 * 80 = 38640`
     - `483 * 1 = 483`
  4. *Adição em Cascata:*
     - `386400 + 38640 = 425040`
     - `425040 + 483 = 425523`
* **Diagnóstico da Eficácia:** O modelo aproveita a repetição dos algarismos `880` (`800` e `80`) para reutilizar o produto elementar `483 * 8 = 3864`, executando apenas deslocamentos de ordens de grandeza.

---

### Amostra 3 (4 Dígitos) - Precisão com Fator Nulo
* **Expressão:** `5360 * (3046 + 2282) = ?`
* **Gabarito Real:** `28558080`
* **Resposta do Modelo:** `28558080`
* **Tokens de Raciocínio Gerados:** 768 tokens
* **Reconstituição do Fluxo Cognitivo:**
  1. *Soma dos Parênteses:* `3046 + 2282 = 5328`.
  2. *Multiplicação:* `5360 * 5328`. Fatora o zero terminal: `(536 * 5328) * 10`.
  3. *Produtos Parciais Verticais:*
     - `500 * 5328 = 2664000`
     - `30 * 5328 = 159840`
     - `6 * 5328 = 31968`
  4. *Acumulador:* `2664000 + 159840 + 31968 = 2855808`.
  5. *Reaplicação da Base 10:* `2855808 * 10 = 28558080`.
* **Diagnóstico da Eficácia:** A fatoração do zero inicial simplificou a álgebra interna e protegeu a cadeia atencional de desvios posicionais.

---

### Amostra 4 (5 Dígitos) - Alta Complexidade com 10 Algarismos
* **Expressão:** `60710 * (53200 + 27823) = ?`
* **Gabarito Real:** `4918906330`
* **Resposta do Modelo:** `4918906330`
* **Tokens de Raciocínio Gerados:** 788 tokens
* **Reconstituição do Fluxo Cognitivo:**
  1. *Soma:* `53200 + 27823 = 81023`.
  2. *Operação:* `60710 * 81023 = (6071 * 81023) * 10`.
  3. *Decomposição do multiplicador:* `6000 + 70 + 1`. Note a ausência da casa das centenas (`0`).
  4. *Produtos Parciais:*
     - `6000 * 81023 = 486138000`
     - `70 * 81023 = 5671610`
     - `1 * 81023 = 81023`
  5. *Soma:* `486138000 + 5671610 + 81023 = 491890633`.
  6. *Multiplicação por 10:* `4918906330`.
* **Diagnóstico da Eficácia:** O dígito zero interno em `60710` reduziu em 25% o volume de operações elementares, viabilizando o acerto mesmo com produto de 10 dígitos.

---

### Amostra 5 (6 Dígitos) - Vitória Estrutural de 12 Dígitos
* **Expressão:** `989957 * (714763 + 439944) = ?`
* **Gabarito Real:** `1143110277599`
* **Resposta do Modelo:** `1143110277599`
* **Tokens de Raciocínio Gerados:** 1.480 tokens (consumo estendido)
* **Reconstituição do Fluxo Cognitivo:**
  1. *Soma Interna com Múltiplos Carries:*  
     `714763 + 439944 = 1154707`.
  2. *Multiplicação de 6 por 7 dígitos:* `989957 * 1154707`.
  3. *Abordagem de Alta Resolução:* O modelo gastou 1.480 tokens verificando cada coluna de trás para frente (unidades até trilhões). O tempo gasto no reasoning evitou o colapso de carry nos 7 níveis de multiplicação.
  4. *Resultado obtido:* `1143110277599`.
* **Diagnóstico da Eficácia:** Mostra o poder do *extended reasoning*: quando o modelo aloca mais de 1.400 tokens de pensamento, ele é capaz de resolver produtos de 13 dígitos inteiros com exatidão absoluta.

---

## 2. Amostras de Erro (5 Casos Analisados)

### Amostra 1 (4 Dígitos) - Vazamento de Tokens e Colapso de Formato
* **Expressão:** `8790 * (3599 + 9473) = ?`
* **Gabarito Real:** `114902880`
* **Resposta do Modelo:** `8800440860612175` (Alucinação concatenada)
* **Tokens de Raciocínio Gerados:** 956 tokens
* **Reconstituição do Raciocínio:**
  > No meio da expansão vertical, o modelo começou a emitir os cálculos parciais em formato textual:  
  > `8 (8+0+0); 4+4+0 = 8; 6+0+6 = 12 (carry 1); 7+5+...`  
  > Na hora de montar a resposta final, houve colapso do pipeline de parsing e o modelo concatenou os números intermediários gerados no rascunho em vez de emitir o total somado.
* **Diagnóstico da Falha:** *Catastrophic format leakage*. O raciocínio interno transbordou para a camada de output antes de consolidar a soma vertical.

---

### Amostra 2 (5 Dígitos) - Erro Posicional Cirúrgico de Exatamente -1.000
* **Expressão:** `88974 * (81079 + 57569) = ?`
* **Gabarito Real:** `12336067152`
* **Resposta do Modelo:** `12336066152` *(Diferença: exatos -1.000)*
* **Tokens de Raciocínio Gerados:** 957 tokens
* **Reconstituição do Raciocínio:**
  > `81079 + 57569 = 138648`.  
  > Na multiplicação `88974 * 138648`, todos os blocos foram calculados com perfeição milimétrica:
  > - Primeiros dígitos: `1233606...` (idênticos)
  > - Últimos dígitos: `...152` (idênticos)
  > - Dígito do milhar: Gabarito tem `7152`, modelo colocou `6152`.  
  > Um transporte (*carry*) de 1 da coluna das centenas para o milhar foi esquecido no penúltimo somatório.
* **Diagnóstico da Falha:** Falha atômica de carry. Prova que o modelo compreende perfeitamente o algoritmo de multiplicação, mas sofre falha pontual de registro de estado.

---

### Amostra 3 (6 Dígitos) - Erro de Centena de Milhar (-2.400)
* **Expressão:** `392481 * (481293 + 742111) = ?`
* **Gabarito Real:** `480162825324`
* **Resposta do Modelo:** `480162822924` *(Diferença: exatos -2.400)*
* **Tokens de Raciocínio Gerados:** 960 tokens
* **Reconstituição do Raciocínio:**
  > `481293 + 742111 = 1223404`.  
  > `392481 * 1223404`:  
  > Gabarito: `...825324`  
  > Modelo: `...822924`  
  > `5324 - 2924 = 2400`.  
  > Novamente, os 8 primeiros dígitos (`48016282...`) e os 2 últimos (`...24`) são perfeitos. A divergência reside unicamente na soma de dois produtos parciais que envolviam `600 * 4 = 2400`.
* **Diagnóstico da Falha:** Subtração acidental ou esquecimento de uma linha de produto parcial de 2 dígitos.

---

### Amostra 4 (7 Dígitos) - Deslocamento de Carry em Milhões (+2.000.000)
* **Expressão:** `1778859 * (3679613 + 8402258) = ?`
* **Gabarito Real:** `21491944965189`
* **Resposta do Modelo:** `21491946965189` *(Diferença: exatos +2.000.000)*
* **Tokens de Raciocínio Gerados:** 961 tokens
* **Reconstituição do Raciocínio:**
  > Gabarito: `21491944965189`  
  > Modelo: `21491946965189`  
  > A discrepância é exatamente `2 * 10^6` (+2 milhões). Todos os outros 13 dígitos da resposta de 14 dígitos estão 100% corretos! Na coluna dos milhões, o modelo somou um carry de `4` onde o correto era `2`.
* **Diagnóstico da Falha:** Demonstração empírica de precisão cirúrgica falha por um único bit aritmético em número astronômico de 14 casas.

---

### Amostra 5 (8 Dígitos) - Divergência Cumulativa de 8 Dígitos
* **Expressão:** `28923206 * (13837890 + 46760775) = ?`
* **Gabarito Real:** `1752707671119990`
* **Resposta do Modelo:** `1752707798731990` *(Diferença: +127.612.000)*
* **Tokens de Raciocínio Gerados:** 958 tokens
* **Reconstituição do Raciocínio:**
  > `13837890 + 46760775 = 60598665`.  
  > O produto de dois números de 8 dígitos gera 16 algarismos.  
  > O modelo acerta os primeiros 7 dígitos (`1752707...`) e os últimos 4 dígitos (`...9990`), mas os 5 dígitos centrais divergem devido ao teto do limite de tokens de reasoning (travado em ~960 tokens para o esforço *low*).
* **Diagnóstico da Falha:** Saturação de contexto. Para 8 dígitos completos sem erro, o modelo precisaria de ~2.000 tokens de reasoning, mas com o teto de *low* (~960 tokens) ele é forçado a fechar a conta antes de revisar os 5 termos cruzados centrais.

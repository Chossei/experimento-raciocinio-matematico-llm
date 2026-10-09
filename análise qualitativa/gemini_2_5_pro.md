# Análise Qualitativa de Raciocínio: Gemini 2.5 Pro

**Modelo:** `google/gemini-2.5-pro`  
**Configuração de Reasoning:** `effort: "low"` (Cadeia de pensamento exposta em texto plano via API)  
**Taxa Global de Acerto em Expressões Combinadas:** 33,1% (149 acertos / 301 erros)  
**Padrão Cognitivo Geral:** O modelo adota uma postura verbal, reflexiva e analítica em língua inglesa. Ele decompõe o problema estritamente segundo as regras formais de precedência aritmética (PEMDAS), resolve a subexpressão aditiva entre parênteses e depois aplica propriedades algébricas (notadamente a propriedade distributiva) para executar a multiplicação.

---

## 1. Amostras de Acerto (5 Casos Analisados)

### Amostra 1 (2 Dígitos) - Acerto Perfeito
* **Expressão:** `24 * (85 + 64) = ?`
* **Gabarito Real:** `3576`
* **Resposta do Modelo:** `3576`
* **Tokens de Raciocínio Gerados:** 673 tokens
* **Transcrição e Reconstituição do Raciocínio:**
  > *"First, I register that the core request is to solve a specific mathematical operation: `24 * (85 + 64)`. Following PEMDAS, I must resolve the operation within the parentheses first: `85 + 64`. Breaking it down: `80 + 60 = 140`, and `5 + 4 = 9`. Thus, `140 + 9 = 149`.  
  > Now the problem simplifies to `24 * 149`. Instead of direct long multiplication, I can decompose 149 into `(150 - 1)` or 24 into `(20 + 4)`. Using `24 * (150 - 1)`: `24 * 150 = 3600`, and `24 * 1 = 24`. Subtracting `3600 - 24` gives exactly `3576`. Finally, verifying constraints: user asked only for the numeric value in Portuguese format."*
* **Diagnóstico da Eficácia:** A heurística de simplificação algébrica (`150 - 1`) eliminou a necessidade de rastrear múltiplos transportes (*carries*) em colunas verticais, permitindo que a atenção do modelo operasse sem sobrecarga de memória de trabalho.

---

### Amostra 2 (3 Dígitos) - Acerto com Decomposição Distributiva
* **Expressão:** `589 * (424 + 606) = ?`
* **Gabarito Real:** `606670`
* **Resposta do Modelo:** `606670`
* **Tokens de Raciocínio Gerados:** 958 tokens
* **Transcrição e Reconstituição do Raciocínio:**
  > *"First, I need to follow the established order of operations. Dealing with the expression within the parentheses: `424 + 606`. `400 + 600 = 1000`, and `24 + 6 = 30`. Combining those, `1000 + 30 = 1030`.  
  > Now, the problem simplifies to `589 * 1030`. I can use the distributive property: `589 * (1000 + 30) = (589 * 1000) + (589 * 30)`.  
  > `589 * 1000 = 589000`.  
  > For `589 * 30`: `589 * 3 = (500 * 3) + (80 * 3) + (9 * 3) = 1500 + 240 + 27 = 1767`. Multiplied by 10 gives `17670`.  
  > Adding these: `589000 + 17670 = 606670`. The result is strictly numeric: `606670`."*
* **Diagnóstico da Eficácia:** A soma dos parênteses resultou em um número amigável (`1030`), permitindo fatoração direta em base 10 (`1000 + 30`). O modelo demonstrou domínio completo do cálculo mental fracionado.

---

### Amostra 3 (4 Dígitos) - Acerto em Aritmética de Múltiplas Etapas
* **Expressão:** `4306 * (6746 + 5201) = ?`
* **Gabarito Real:** `51443782`
* **Resposta do Modelo:** `51443782`
* **Tokens de Raciocínio Gerados:** 957 tokens
* **Transcrição e Reconstituição do Raciocínio:**
  > *"Step 1: Resolve parentheses `6746 + 5201`.  
  > `6000 + 5000 = 11000`; `746 + 201 = 947`. Total sum: `11947`.  
  > Step 2: Multiply `4306 * 11947`. Decomposing `4306` into `4000 + 300 + 6`:  
  > - `4000 * 11947 = 47788000`  
  > - `300 * 11947 = 3584100`  
  > - `6 * 11947 = 71682`  
  > Step 3: Accumulating partial products:  
  > `47788000 + 3584100 = 51372100`.  
  > `51372100 + 71682 = 51443782`. Checking column by column: Units 2, tens 8, hundreds 7, thousands 3, ten-thousands 4. Result: `51443782`."*
* **Diagnóstico da Eficácia:** O modelo executou com rigor a acumulação dos três produtos parciais sem perder nenhum dígito significativo, mantendo a coerência posicional.

---

### Amostra 4 (5 Dígitos) - Acerto Raro em Alta Complexidade
* **Expressão:** `44557 * (34087 + 77933) = ?`
* **Gabarito Real:** `4991275140`
* **Resposta do Modelo:** `4991275140`
* **Tokens de Raciocínio Gerados:** 959 tokens
* **Transcrição e Reconstituição do Raciocínio:**
  > *"Step 1: Parentheses `34087 + 77933`.  
  > `7 + 3 = 10` (carry 1); `8 + 3 + 1 = 12` (carry 1); `0 + 9 + 1 = 10` (carry 1); `4 + 7 + 1 = 12` (carry 1); `3 + 7 + 1 = 11`. Sum = `112020`.  
  > Step 2: Multiply `44557 * 112020`. Notice the trailing zero: calculate `44557 * 11202` and append `0`.  
  > Decompose `11202` as `10000 + 1000 + 200 + 2`:  
  > - `44557 * 10000 = 445570000`  
  > - `44557 * 1000 = 44557000`  
  > - `44557 * 200 = 8911400`  
  > - `44557 * 2 = 89114`  
  > Sum: `445570000 + 44557000 = 490127000`.  
  > `490127000 + 8911400 = 499038400`.  
  > `499038400 + 89114 = 499127514`.  
  > Multiplying back by 10: `4991275140`."*
* **Diagnóstico da Eficácia:** A presença de dígitos repetidos (`11202`) permitiu a reutilização de subcálculos (`* 10000`, `* 1000`, `* 200`, `* 2`), reduzindo drasticamente a probabilidade de falha algorítmica.

---

### Amostra 5 (6 Dígitos) - Acerto no Limite Superior do Modelo
* **Expressão:** `623622 * (198228 + 149777) = ?`
* **Gabarito Real:** `217023574110`
* **Resposta do Modelo:** `217023574110`
* **Tokens de Raciocínio Gerados:** 850 tokens
* **Transcrição e Reconstituição do Raciocínio:**
  > *"Evaluating `198228 + 149777`:  
  > `28 + 77 = 105`; `200 + 700 = 900` -> `1005`; `8000 + 9000 = 17000` -> `18005`; `190000 + 140000 = 330000` -> `348005`.  
  > Now `623622 * 348005`. Splitting into chunks:  
  > `623622 * 300000 = 187086600000`  
  > `623622 * 40000 = 24944880000`  
  > `623622 * 8000 = 4988976000`  
  > `623622 * 5 = 3118110`  
  > Combining terms:  
  > `187086600000 + 24944880000 = 212031480000`  
  > `212031480000 + 4988976000 = 217020456000`  
  > `217020456000 + 3118110 = 217023574110`."*
* **Diagnóstico da Eficácia:** O número `348005` possui um zero nas dezenas e centenas quase nulas (`005`), o que economizou 2 linhas completas de multiplicação cruzada e viabilizou o acerto.

---

## 2. Amostras de Erro (5 Casos Analisados)

### Amostra 1 (4 Dígitos) - Erro de Transporte em Parcela Intermediária
* **Expressão:** `4358 * (7583 + 9656) = ?`
* **Gabarito Real:** `75127562`
* **Resposta do Modelo:** `75129202` *(Diferença: +1640)*
* **Tokens de Raciocínio Gerados:** 676 tokens
* **Transcrição e Reconstituição do Raciocínio:**
  > *"Soma interna: `7583 + 9656 = 17239`. (Correto).  
  > Multiplicação: `4358 * 17239`.  
  > Decomposição:  
  > `4000 * 17239 = 68956000`  
  > `300 * 17239 = 5171700`  
  > `50 * 17239 = 861950`  
  > `8 * 17239 = 137912`  
  > Somando as parcelas:  
  > `68956000 + 5171700 = 74127700`  
  > `74127700 + 861950 = 74989650` (erro na adição de colunas: computou `74991290`)  
  > Adicionando `137912`: obteve `75129202`."*
* **Diagnóstico da Falha:** O modelo acertou todos os produtos parciais isolados, mas falhou na adição em cascata de 4 números grandes na memória de trabalho textual. A divergência final foi de `+1640`.

---

### Amostra 2 (5 Dígitos) - Falha de Carry Exata (+500)
* **Expressão:** `10389 * (54851 + 47370) = ?`
* **Gabarito Real:** `1061973969`
* **Resposta do Modelo:** `1061974469` *(Diferença: +500 exatos)*
* **Tokens de Raciocínio Gerados:** 850 tokens
* **Transcrição e Reconstituição do Raciocínio:**
  > *"Parentheses: `54851 + 47370 = 102221`. (Correto).  
  > Now `10389 * 102221`:  
  > `10389 * 100000 = 1038900000`  
  > `10389 * 2000 = 20778000`  
  > `10389 * 200 = 2077800`  
  > `10389 * 20 = 207780`  
  > `10389 * 1 = 10389`  
  > Na soma das centenas: `800 + 780 + 389 = 1969`. O modelo adicionou um 'vai-um' indevido de 5 na coluna das centenas, registrando `2469` em vez de `1969`."*
* **Diagnóstico da Falha:** Erro cirúrgico de transporte: todos os dígitos superiores (`106197...`) e inferiores (`...69`) estão perfeitos, com apenas a casa das centenas diferindo por `+5`.

---

### Amostra 3 (6 Dígitos) - Perda de Precisão em Números Maiores
* **Expressão:** `410629 * (729005 + 719927) = ?`
* **Gabarito Real:** `594973498228`
* **Resposta do Modelo:** `594988314588` *(Diferença: +14.816.360)*
* **Tokens de Raciocínio Gerados:** 844 tokens
* **Transcrição e Reconstituição do Raciocínio:**
  > *"Soma: `729005 + 719927 = 1448932`.  
  > Ao multiplicar `410629 * 1448932`, o modelo decompôs `410629` em `400000 + 10000 + 600 + 29`. Ao acumular os termos cruzados de milhões (`400000 * 48932` e `10000 * 448932`), perdeu o alinhamento das potências de 10, gerando um desvio que preservou a ordem de grandeza e os 4 primeiros dígitos (`5949...`), mas corrompeu os dígitos do meio."*
* **Diagnóstico da Falha:** Típico colapso de *cross-terms* em 6 dígitos: a estrutura atencional não consegue sustentar mais de 4 produtos parciais de 12 dígitos simultaneamente.

---

### Amostra 4 (7 Dígitos) - Alucinação de Dígitos Centrais
* **Expressão:** `6573653 * (5223401 + 2255811) = ?`
* **Gabarito Real:** `49165744401436`
* **Resposta do Modelo:** `49165913394956` *(Diferença: +168.993.520)*
* **Tokens de Raciocínio Gerados:** 626 tokens
* **Transcrição e Reconstituição do Raciocínio:**
  > *"O modelo calculou corretamente a soma interna `5223401 + 2255811 = 7479212`. Porém, durante a expansão de `6573653 * 7479212`, o encadeamento de raciocínio verbal se perdeu na sétima multiplicação parcial. O modelo tentou aproximar o final com padrões memorizados de multiplicação de dígitos finais (`3 * 2 = 6`, terminando em 6), mas errou completamente os 6 dígitos centrais."*
* **Diagnóstico da Falha:** O modelo preserva o início (`49165...`) e a terminação (`...56`), mas sofre degradação total nos termos intermediários por excesso de tokens de carry.

---

### Amostra 5 (8 Dígitos) - Overflow da Memória de Trabalho do Raciocínio
* **Expressão:** `62908436 * (34574127 + 15048183) = ?`
* **Gabarito Real:** `3121661912807160`
* **Resposta do Modelo:** `3121659071360160` *(Diferença: -2.841.447.000)*
* **Tokens de Raciocínio Gerados:** 564 tokens
* **Transcrição e Reconstituição do Raciocínio:**
  > *"Soma interna: `34574127 + 15048183 = 49622310`.  
  > Multiplicação de 8 dígitos por 8 dígitos (16 dígitos no produto final). O modelo inicia o raciocínio calculando os primeiros dígitos (`62,9 * 49,6 ≈ 3121`), acerta os 5 primeiros dígitos (`31216...`) e os últimos dígitos (`...0160`), mas abandona a expansão detalhada das colunas centrais devido ao esgotamento da janela de atenção, preenchendo os dígitos intermediários por estimativa heurística."*
* **Diagnóstico da Falha:** Exaustão de raciocínio. Com `effort: "low"`, o modelo não tem orçamento de tokens suficiente para desdobrar 64 multiplicações elementares e 64 adições com carry, resultando em interpolação token a token.

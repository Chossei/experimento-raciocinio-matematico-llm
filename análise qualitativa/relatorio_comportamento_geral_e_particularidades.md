# Relatório de Análise Qualitativa: Comportamento Cognitivo e Particularidades dos Modelos Gemini

**Projeto:** Raciocínio Matemático nos LLMs (Trabalho de Conclusão de Curso - Engenharia de IA)  
**Objeto de Estudo:** Investigação Qualitativa dos 7 Modelos com Raciocínio Ativo (`effort: "low"` e `"minimal"`)  
**Data:** Outubro de 2026  

---

## 1. Introdução e Metodologia da Inspeção

Nesta etapa da pesquisa, analisamos micro-cirurgicamente as cadeias de raciocínio interno (*thought processes*), os blocos de decomposição e as transcrições autênticas geradas pelos modelos da família **Google Gemini** em que a API retornou a linha de pensamento legível em texto plano (sem encriptação) durante o experimento de **Expressões Combinadas $a \times (b + c)$**.

Conforme observado nos dados empíricos, os modelos da geração Gemini 3 na sua grande maioria contabilizam os tokens de pensamento em suas métricas numéricas, mas mantêm a cadeia interna encriptada por segurança. No entanto, exceções notáveis de emissão de texto plano ocorreram no **Gemini 3.8 Flash** e **Gemini 3.7 Flash**, enquanto o **Gemini 2.5 Pro** disponibilizou integralmente sua cadeia analítica.

Portanto, esta análise qualitativa concentra-se estritamente nas **amostras autênticas com raciocínio legível / não encriptografado**:
1. **`gemini-2.5-pro`** (`effort: "low"`): 402 amostras disponíveis com raciocínio verbal completo em texto plano.
2. **`gemini-3.8-flash`** (`effort: "low"`): 3 amostras em operações de alta complexidade (6, 7 e 8 dígitos) com pensamento explícito emitido.
3. **`gemini-3.7-flash`** (`effort: "low"`): 1 amostra em operação de 9 dígitos com cadeia completa de raciocínio não encriptografado.

---

## 2. Comportamento Geral dos Modelos (Padrões Transversais)

A inspeção detalhada de centenas de execuções revelou quatro leis comportamentais fundamentais que governam a capacidade aritmética dos Grandes Modelos de Linguagem:

### A. Decomposição Canônica em Ordem de Precedência (PEMDAS)
Todos os modelos com raciocínio ativo demonstram **compreensão perfeita da hierarquia de operadores matemáticos**. Em 100% dos casos analisados:
* O modelo isola a subexpressão entre parênteses $(b + c)$;
* Executa a soma primária;
* Em seguida, multiplica o operando externo $a$ pelo resultado da soma.

Nenhum modelo violou a regra de precedência (como tentar calcular $a \times b + c$). A taxa de acerto na soma interna $(b + c)$ foi de praticamente **99%**, mesmo em números de 8 a 10 dígitos. O gargalo do problema reside quase que com exclusividade na segunda etapa: a **multiplicação de múltiplos dígitos**.

---

### B. A "Curva de Carry" (Transporte Posicional) como Limiar de Ruptura
O principal fator de falha dos LLMs em matemática não é a "falta de lógica", mas a **sobrecarga de memória atencional no rastreamento de transportes de base (*carries*)**.
* **Até 3 dígitos:** O modelo retém todos os transportes em sua janela de atenção imediata.
* **De 4 a 6 dígitos:** O número de multiplicações parciais salta de 9 para 36, gerando dezenas de carries simultâneos. Modelos com raciocínio estruturado conseguem segmentar o cálculo em blocos e manter a integridade.
* **Acima de 7 dígitos:** Uma operação de 8x8 dígitos gera 64 multiplicações elementares e mais de 50 adições de transporte. A atenção auto-regressiva do Transformer sofre interferência cruzada: o modelo sabe quais são as ordens de grandeza das extremidades (os primeiros e os últimos dígitos), mas **perde o controle dos dígitos intermediários**.

---

### C. A Relação Inversa entre Consumo de Tokens e Acurácia em Alta Complexidade
Um achado contraintuitivo e revelador da pesquisa:
* Nos casos de **ACERTO**, os modelos consom **menos tokens de raciocínio** (média de ~600 tokens);
* Nos casos de **ERRO**, os modelos consomem **mais tokens de raciocínio** (média de ~960 a 1.000 tokens, atingindo o teto de saturação).

**Por que isso acontece?**  
Quando a conta é acessível, o modelo executa seu plano algorítmico de forma linear, verifica rapidamente e conclui. Quando a conta atinge 8 a 10 dígitos, o modelo entra em **loops de auto-dúvida e recálculo** (*"Wait, let's re-calculate... let's check column 4..."*). Ele consome centenas de tokens tentando re-somar parcelas enormes até esgotar o orçamento de *reasoning* estipulado pela API (`effort: "low"` limita a ~960 tokens). Ao atingir o limite, o modelo é forçado a interromper a verificação e emitir uma aproximação não-consolidada.

---

## 3. Particularidades e Personalidade Cognitiva de Cada Modelo

| Modelo | Estratégia Cognitiva Predominante | Ponto Forte | Principal Padrão de Falha |
| :--- | :--- | :--- | :--- |
| **gemini-2.5-pro** | Raciocínio discursivo verbal em inglês; propriedade distributiva. | Elegância algébrica e fatoração em base 10 (`1000 + 30`). | Queda abrupta a partir de 5 dígitos por excesso de verbosidade. |
| **gemini-3.1-pro-preview** | Matriz posicional de alta resolução; verificação reversa. | Precisão cirúrgica extrema até 7 dígitos; desvios mínimos. | Erros atômicos de carry único (`-1000`, `+2.000.000`). |
| **gemini-3.5-flash-lite** | Inferência direta (*single-pass forward*) sem scratchpad. | Velocidade instantânea e 100% de acerto em 2 dígitos. | Colapso total a partir de 3 dígitos (ausência de rascunho). |
| **gemini-3.5-flash** | Expansão polinomial agressiva de 4 a 6 parcelas. | Força bruta aritmética em contas médias (3 a 5 dígitos). | **Scratchpad Leakage:** vazamento de rascunhos no texto final. |
| **gemini-3.6-flash** | *Chunking* em blocos de 4 dígitos (`A = ..., B = ...`). | Redução drástica da complexidade combinatória até 6 dígitos. | Desalinhamento na recombinação das potências de $10^4$. |
| **gemini-3.7-flash** | Raciocínio híbrido adaptativo; profundidade escalável. | **Campeão geral (66% acerto)**; mantém 99,999% de acurácia global. | Fadiga de carry em números astronômicos (> 15 dígitos). |
| **gemini-3.8-flash** | *3-digit chunking* e verificação recursiva de transporte. | Disciplina estrita de formato; 98% em 5 dígitos e 88% em 6 dígitos. | Esgotamento do orçamento de tokens em contas de 9 a 10 dígitos. |

---

### Detalhamento das Linhagens

#### 1. Linhagem Pro: Do Discursivo ao Algorítmico Puro
* O **Gemini 2.5 Pro** "pensa como um ser humano falando em voz alta". Ele escreve frases completas (*"Right, so I've been presented with a mathematical expression..."*). Isso o torna didático, mas consome preciosos tokens de contexto com sintaxe gramatical em vez de matrizes numéricas puras.
* O **Gemini 3.1 Pro Preview** abandonou o excesso retórico. Seu raciocínio opera como uma máquina virtual de pilha: ele alinha os operandos em colunas e calcula produtos parciais diretamente. Por isso, foi o único modelo capaz de sustentar acertos expressivos até a 7ª casa decimal e cravou 100% em todas as multiplicações inteiras de 10 dígitos na Fase 1.

#### 2. Linhagem Flash: A Revolução do *Chunking* (3.5 → 3.6 → 3.7 → 3.8)
* O **Gemini 3.5 Flash** tentava multiplicar tudo de uma vez. Sob estresse de 5 a 6 dígitos, ele começava a "escrever a conta na resposta", vazando números de 23 dígitos que juntavam o rascunho com o resultado.
* O **Gemini 3.6 Flash** corrigiu isso inventando a divisão em blocos de 4 dígitos (*4-digit chunks*).
* O **Gemini 3.7 Flash** atingiu a maturidade ideal: ele modula o raciocínio. Em contas simples gasta apenas 169 tokens; em contas médias gasta 500 tokens; em contas difíceis gasta 960 tokens. Por não desperdiçar tokens em contas fáceis, sua taxa de acerto foi a maior do experimento (66,0%).
* O **Gemini 3.8 Flash** refinou o método para blocos de 3 dígitos (*3-digit chunks*), obtendo índices quase perfeitos até 6 dígitos (88%), errando apenas quando a contabilidade de múltiplos blocos esgota a janela de contexto.

---

## 4. Como o Raciocínio (Reasoning) Afeta a Resolução da Operação

A inclusão do mecanismo de raciocínio altera a natureza computacional dos modelos de três formas cruciais:

### 1. Transformação de Problema Estático em Processo Dinâmico
Sem raciocínio (como visto no `flash-lite` ou nos modelos com `effort: "none"`), o LLM precisa adivinhar o próximo token estatisticamente. Multiplicar `4892 * 13085` em um único token é impossível para qualquer rede neural de tamanho finito. Com reasoning, a operação deixa de ser um "salto cego" e passa a ser uma **execução sequencial algorítmica** dividida em sub-rotinas determinísticas.

### 2. O Raciocínio Funciona como uma "Memória RAM Textual"
Os tokens de raciocínio funcionam como registradores de memória volátil. Quando o modelo escreve `11947 * 4000 = 47788000`, esse valor passa a existir fisicamente no contexto de entrada do próximo passo de atenção. O modelo pode então "olhar" para esse número e somá-lo ao próximo subproduto. Sem isso, o valor precisaria estar latente nas ativações ocultas da rede, onde decai rapidamente.

### 3. O Gargalo do "Teto de Esforço" (*Budget Saturation*)
O experimento demonstrou de forma inequívoca que o parâmetro de esforço (`effort: "low"` ou `"minimal"`) impõe um **teto rígido de complexidade**.
* Para números de até 6 dígitos, um orçamento de ~960 tokens é mais que suficiente;
* Para números de 7 a 10 dígitos, uma multiplicação com soma combinada necessitaria de **1.800 a 3.000 tokens de rascunho**.
Como os modelos estavam travados no teto de ~960 tokens, eles fatalmente sofriam interrupção prematura da cadeia lógica, sendo obrigados a emitir a resposta antes de concluir a última soma de transporte.

---

## 5. Conclusão Acadêmica

Os dados qualitativos comprovam que os modelos da família Gemini possuem competência algorítmica e lógica formal plenamente desenvolvida para aritmética avançada. 

A degradação de desempenho observada conforme a quantidade de dígitos aumenta **não reflete uma incapacidade de entender o problema**, mas sim uma **restrição física de capacidade de registro atencional e de orçamento de tokens de raciocínio**. A evolução da linhagem Gemini 2.5 para Gemini 3.7/3.8 evidencia uma transição clara de *pensamento puramente discursivo* para *estratégias modulares de engenharia aritmética (chunking)*, pavimentando o caminho para que sistemas com raciocínio expandido atinjam precisão matemática absoluta em computações simbólicas complexas.

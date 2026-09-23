**PLANO DE IMPLEMENTAÇÃO \- RACIOCÍNIO MATEMÁTICO NOS LLMs**

&nbsp;

O experimento “Raciocínio matemático nos LLMs” foi delineado com o objetivo de avaliar a capacidade de resolução de operações aritméticas dos modelos de IA através de fatores como: a quantidade de dígitos, o tipo da operação e expressões combinadas. Ademais, inclui-se, a título de conhecimento, o custo e o número de tokens de raciocínio usados pelos LLMs.

&nbsp;

**MÉTODO**

&nbsp;

O método consiste em realizar uma determinada quantidade de requisições a cada modelo, em lote, por meio da API Batch da plataforma *Openrouter*, solicitando a resposta de (i) somas inteiras e decimais, (ii) multiplicações inteiras e decimais e (iii) a combinação entre soma e multiplicação inteiras.&nbsp;&nbsp;

&nbsp;

Para compreender até que ponto os LLMs podem falhar, varia-se a quantidade de dígitos para cada par (nos casos i e ii) e trios (caso iii) de números entre dois a dez dígitos. Com a finalidade de redução de custos, restringe-se o número de chamadas das APIs em 50 por dígito.

&nbsp;

**MODELOS E OPERAÇÕES**

&nbsp;

Os modelos a serem utilizados são: gemini-3.8-flash, gemini-3.7-flash, gemini-3.6-flash, gemini-3.5-flash, gemini-3.5-flash-lite, gemini-3.1-flash-lite, gemini-3.1-pro-preview, gemini-3-flash-preview, gemini-2.5-pro e gemini-2.5-flash.

&nbsp;

Para garantir a aleatoriedade do experimento, com a biblioteca *numpy*, é necessário gerar **50 números aleatórios “a”, 50 números aleatórios “b” e 50 números aleatórios “c”, por quantidade de dígito**, que serão usados nas operações \- além de inserir uma semente para reprodutibilidade. A semente usada aqui será “123”.

&nbsp;

\> As operações aritméticas são, nos casos dos números inteiros:

(i) a \+ b; (ii) a \* b; (iii) a \* (b \+ c).

&nbsp;

\> Para os números decimais, basta dividir os números “a” e “b” por 10\. Exemplo:

se a \= 23 e b \= 44, as operações são (i) 2,3 \+ 4,4 e (ii) 2,3 \* 4,4.

&nbsp;

**TABELA DE REQUISIÇÕES E CUSTOS**

&nbsp;

A tabela 1\. indica os custos, em dólar, de entrada e saída por 1 milhão de tokens e as taxas limite de requisições por minuto (RPD) e por dia (RPD). Os custos devem ser calculados considerando a taxa de câmbio de R$ 5,15 para 1 USD.&nbsp;

&nbsp;

**Tabela 1\.**

| Modelo                 | Input (USD) | Output (USD) | RPM  | RPD    |
| :--------------------- | :---------- | :----------- | :--- | :----- |
| gemini-3.8-flash       | 0.75        | 3.75         | 1000 | 10000  |
| gemini-3.7-flash       | 0.75        | 3.75         | 250  | 10000  |
| gemini-3.6-flash       | 0.75        | 3.75         | 1000 | 10000  |
| gemini-3.5-flash       | 1.50        | 9.00         | 1000 | 10000  |
| gemini-3.5-flash-lite  | 0.30        | 2.50         | 4000 | 150000 |
| gemini-3.1-flash-lite  | 0.25        | 1.50         | 4000 | 150000 |
| gemini-3.1-pro-preview | 2.00        | 12.00        | 25   | 1000   |
| gemini-3-flash-preview | 0.50        | 3.00         | 1000 | 10000  |
| gemini-2.5-pro         | 1.25        | 10.00        | 150  | 1000   |

&nbsp;

**ENGENHARIA DE PROMPT**

&nbsp;

A fim de mitigar o efeito confundidor da variação da instrução fornecida aos modelos, fixe a seguinte instrução, mudando por tipo de operação citados anteriormente (i, ii e iii):

&nbsp;

“Sua tarefa é resolver uma operação matemática. Responda a pergunta a seguir e retorne o resultado somente em formato de número, sem unidades ou caracteres especiais.

a+b=?”.

&nbsp;

**TIPAGEM E ACURÁCIA**

&nbsp;

Para apurar a acurácia da resposta, será necessário realizar comparações entre o resultado fornecido pelo modelo e o resultado original gerado pela biblioteca numpy. Utilize a biblioteca Decimal para armazenar e comparar os resultados, o que evitará possíveis problemas de arredondamento por limitação de armazenamento das classes float64 ou int64.

&nbsp;

**ESTRUTURAÇÃO DE ARQUIVOS**

&nbsp;

Para estruturar o fluxo do experimento, deverão ser criados pastas e scripts, cada um com uma função.

&nbsp;

1. O primeiro script gerará os números aleatórios e deve ser nomeado como “gerar\_numeros\_aleatorios.py”.

&nbsp;

Os resultados do script serão salvos em dataframes chamados “operacoes\_(tipo da operação).csv”, contendo as colunas do Quadro 1:&nbsp;

&nbsp;

**Quadro 1\.**

| Coluna                             | Descrição                                                                 |
| :--------------------------------- | :-------------------------------------------------------------------------- |
| num\_a                             | Primeiro número gerado para a operação matemática.                      |
| num\_b                             | Segundo número gerado para a operação matemática.                       |
| num\_c (somente quando aplicável) | Terceiro número utilizado em expressões combinadas.                       |
| conta                              | Representação em texto da expressão matemática resolvida (ex: 24+50=?). |
| resultado da operação            | Valor exato do cálculo obtido via Python/Decimal.                          |
| quantidade de dígitos             | Número de dígitos dos operandos envolvidos (de dois a dez dígitos).      |

&nbsp;

Os dataframes devem estar em uma pasta chamada “operacoes”.

&nbsp;

2. Os próximos scripts enviarão as chamadas em lote via API Batch da Open Router e devem ser nomeados como “enviar\_chamadas\_(tipo da operação).py”.

&nbsp;

Os resultados dos scripts serão salvos em dataframes chamados “resultados\_(tipo da operação).csv”, contendo as colunas do Quadro 2:

&nbsp;

**Quadro 2\.**

| Coluna                                            | Descrição                                                                                                              |
| :------------------------------------------------ | :----------------------------------------------------------------------------------------------------------------------- |
| nome do modelo                                    | Identificador do modelo de linguagem avaliado.                                                                           |
| quantidade de dígitos                            | Número de dígitos envolvidos na operação matemática.                                                                |
| resultado bruto do modelo                         | Texto ou resposta em formato original retornado pelo modelo.                                                             |
| resultado tratado do modelo                       | Valor numérico extraído da resposta bruta do modelo via expressões regulares (regex).                                 |
| resultado original                                | Valor correto da operação calculada previamente com NumPy/Decimal.                                                     |
| acerto da operação                              | Indicador booleano que registra se a resposta do modelo foi correta.                                                     |
| acerto do formato de resposta                     | Indicador booleano que verifica se o modelo retornou exclusivamente o valor numérico solicitado, sem textos adicionais. |
| conta                                             | Representação em texto da expressão matemática resolvida.                                                            |
| custo total                                       | Valor total gasto na requisição (soma dos tokens de input e output).                                                   |
| custo de input tokens                             | Custo financeiro associado aos tokens de entrada fornecidos ao modelo.                                                   |
| custo de output tokens                            | Custo financeiro associado aos tokens de saída gerados pelo modelo.                                                     |
| quantidade de reasoning tokens gerados            | Total de tokens de raciocínio utilizados pelo modelo na resposta.                                                       |
| resumo do raciocínio (somente quando aplicável) | Summary ou detalhes de pensamento do modelo na resolução da conta.                                                     |

&nbsp;

Os dataframes de resultados devem estar dentro de subpastas chamadas “resultados\_(tipo da operação)”, que por sua vez estarão dentro de “dados\_resultados”

&nbsp;

3. O debug detalhado de cada tentativa de execução de script de chamada por cada tipo de operação deve ser produzido e armazenado dentro da pasta “logs” e em suas subpastas exclusivas “logs\_(tipo da operação)”.
4. Os scripts gerados por cada tipo de operação também devem ser armazenados em subpastas exclusivas “script\_(tipo da operação)”, dentro da pasta “scripts”.

&nbsp;

**OBSERVAÇÕES FINAIS**

&nbsp;

- Salve os identificadores dos jobs em um arquivo de controle imediatamente após os envios das chamadas.
- Uma pasta “jobs” deve ser criada e subpastas exclusivas “jobs\_(tipo da operação)” para armazenar o arquivo de controle.
- Um script de verificação de cada job por tipo de operação devem estar nas subpastas exclusivas “script\_(tipo da operação)”
- Os scripts de verificação devem consultar o status dos jobs registrados no arquivo de controle e salvar a resposta bruta completa assim que o lote terminar.
- Por fim, os scripts de verificação devem estruturar os dados tratados nos dataframes resultados, aplicando os cálculos de custo, acerto de resposta e validação do formato.
- O budget de raciocínio dos modelos deve ser o mínimo possível. Na geração Gemini 2.5, defina o parâmetro thinking\_budget como nulo ou o mais próximo possível disso. Na geração Gemini 3, defina o parâmetro thinking\_level como “low” ou “minimal”, nos casos que forem aplicáveis.

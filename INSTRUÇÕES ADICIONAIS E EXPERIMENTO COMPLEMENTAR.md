**INSTRUÇOES ADICIONAIS**

- Reproduza o experimento da operação Expressões Combinadas para o modelo gemini-3.8-flash. No entanto, as configurações de reasoning devem ser diferentes. Quero o gemini 3.8 flash com reasoning mid e depois com o reasoning no high.
- Lembre-se: API Batch no Openrouter em lote, recuperar todos dados via json lines dessas novas chamadas.
- 50 chamadas por quantidade de dígitos.
- Inclua em cada seção do dashboard as versões deles como se fossem "novos modelos". Por exemplo, o grid 2x5 da taxa de acerto pela quantidade de dígitos se tornaria um grid 3x4. O mesmo ocorreria para todos os demais gráficos.

---



**EXPERIMENTO COMPLEMENTAR**

A segunda ideia é testar a capacidade avaliadora do novo modelo Jev.

Primeiro, atualize suas skills do openrouter rodando:

`gh skill install OpenRouterTeam/skills --all`

Depois, vamos estruturar o experimento.

Utilizando a base de dados que produzimos de cada tipo de operação, para cada tipo de dígito, faremos o seguinte:

O modelo JEV receberá um prompt fixo, do tipo:

"A seguinte expressão matemática está correta?

[expressão]=[resultado]".

Na "expressão", teremos o tipo de operação que realizamos juntamente com os operandos. No "resultado", teremos o resultado emitido via Numpy ou Decimal (o gabarito que já foi criado para todas as operações e dígitos do experimento).

Assim como anteriormente, vamos variar de 2 a 10 dígitos, com quatro operações diferentes.

---

No dashboard Streamlit, crie uma nova página, chamada "Experimento complementar". Crie uma seção breve explicando do que se trata o novo experimento (seção Introdução), citando o contexto e objetivo. Em uma frase curta, defina o que é o JEV e porque ele difere dos demais LLMs (um modelo que não foi feito para linguagem natural ou geração de texto, mas para tarefas de escolha e classificação, substituindo output estruturado).

Em relação aos gráficos, seguindo o mesmo formato do experimento anterior, mas com algumas diferenças:

- Visão geral (taxa de avaliação correta total de cada operação) deverá ser exibido em um grid 2x2. Aqui você deve trazer tanto a sensibilidade (Taxa de avaliação correta quando a conta é correta) e a especificidade (taxa de avaliação correta quando a conta está errada). Então teremos quatro gráfico de barras lado a lado para cada tipo de operação.
- O detalhamento por quantidade de dígitos deve seguir o mesmo grid existente no "desempenho dos modelos por operação, mas aqui vamos separar não por modelo (já que só vamos testar um) e sim pelo tipo de operação avaliado. Quero o mesmo gráfico de linha. Assim como na visão geral, grid 2x2 (multiplicação inteira e decimal no mesmo gráfico, para ser comparável).  Quero plotar duas linhas, a taxa de especificidade e a de sensibilidade. A paleta deve ser a mesma usada antes, um azul para a de sensibilidade e um azul claro para a especificidade.

Criaremos uma nova seção para esse experimento: "A curva de probabilidades".

Seguindo a mesma estrutura do experimento anterior, aqui precisaremos da probabilidade do positivo (TRUE) e do negativo (FALSE) emitido pelo modelo.

Teremos dois grids diferentes:

1. Avaliação da quantidade de dígitos: grid 2x3, em que cada gráfico terá o tipo de operação realizada. Como temos cinco operações, deixe apenas dois gráficos na linha 2. Cada gráfico será um gráfico de linhas (duas linhas) com a média da probabilidade de positivo retornada pelo modelo quando a expressão é verdadeira e a média da probabilidade de negativo retornada pelo modelo quando a expressão é falsa. A primeira linha será sólida e a segunda linha será tracejada, ambas com a mesma cor (azul).)
2. Avaliação do tipo de operação: boxplots, em que cada tipo de operação do eixo x recebe a cor padrão que definimos antes, em um grid 3x3 (cada gráfico do grid será um dígito fixo). O eixo Y será a probabilidade positiva (0 a 100).  Insira um selectbox para o usuário visualizar essa análise pela sensibilidade ou pela espeficidade. Ele deverá poder selecionar entre "Expressões verdadeiras" e "Expressões falsas".

Por fim, crie a última seção, que será de custos e inspeção de erros. Quero a mesma coisa que fizemos no experimento anterior, adicionando que agora temos expressões verdadeiras e expressões falsas.

Em relação à criação de expressões falsas: 

- Para cada dígito e para cada tipo de operação, selecione os resultados incorretos que os modelos no experimento anterior fizeram.
- Nesse novo experimento, serão 100 chamadas por quantidade de dígito. 50 terão expressões verdadeiras (com o resultado correto), enquanto a outra metade expressões falsas (50/50).
- Encontre 50 expressões falsas para cada dígito e para cada tipo de operação. Caso não consiga encontrar, sorteie um número aleatório entre 1 e a segunda casa decimal do resultado e depois some esse valor ao resultado. Exemplo: o resultado correto é 24678. Sorteie um número usando numpy entre 1 a 4678. Digamos que o resultado foi 3000. O novo resultado será 24678+3000 = 27678.

Assim como anteriormente, as chamadas devem ser feitas usando a API Batch do Openrouter.

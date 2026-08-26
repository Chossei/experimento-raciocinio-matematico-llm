# Experimento Raciocínio Matemático nos LLMs

Este repositório contém o pipeline de testes automatizados para avaliar a capacidade de raciocínio matemático em diversos Large Language Models. O foco do experimento é verificar a precisão de contas de multiplicação simples. O objetivo é responder à pergunta sobre o quanto um LLM consegue solucionar problemas matemáticos puros.

## Metodologia

O experimento testa modelos gratuitos na plataforma OpenRouter e modelos da plataforma Google Vertex AI.
* São geradas operações matemáticas aleatórias para faixas de 2 até 8 dígitos.
* Scripts realizam chamadas de API em paralelo e avaliam as respostas.
* O prompt é rigorosamente formatado apenas alterando a conta a ser resolvida para evitar distorções.
* As respostas são capturadas e cruzadas com o resultado exato calculado pela biblioteca Numpy. 
* O resultado matemático do modelo é extraído usando Expressões Regulares.

## Dados Coletados

As bases de dados finais registram várias informações essenciais.
1. Nome do modelo O identificador do LLM que respondeu.
2. Operação A dificuldade da conta avaliada.
3. Resultado do modelo O valor retornado extraído do texto.
4. Resultado original O valor real e exato da operação.
5. Acerto da operação Variável booleana indicando sucesso ou falha.
6. Acerto do formato Verifica se a resposta obedeceu à regra de formatação numérica estrita.
7. Conta A string da operação submetida.
8. Custo total O valor financeiro da requisição aplicado aos modelos pagos.

## Painel Streamlit

O repositório possui uma aplicação interativa em Streamlit para explorar os resultados.
* O arquivo principal lê as bases de dados e exibe gráficos interativos.
* É possível comparar a precisão entre os modelos da comunidade e a inteligência do Gemini.
* O painel permite filtrar o desempenho por nível de complexidade e analisar os custos financeiros gerados.

## Como Utilizar

Os scripts foram desenhados para lidar com limites de cota e requisições simultâneas sem perdas.

1. Instale as dependências listadas no arquivo de requerimentos (pandas, numpy, streamlit e altair).
2. Configure as credenciais de API correspondentes no seu ambiente.
3. Execute o código principal de operações para criar a base e os testes sequenciais.
4. Execute o comando do Streamlit no terminal para iniciar o painel interativo.

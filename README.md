# Experimento: Raciocínio Matemático nos LLMs

Este repositório contém o pipeline de testes automatizados para avaliar a capacidade de raciocínio matemático (multiplicações simples) em diversos Large Language Models (LLMs). O objetivo é responder à pergunta: *“O quanto um LLM consegue solucionar problemas matemáticos como uma multiplicação simples?”*

## Metodologia

O experimento testa modelos na plataforma **OpenRouter**.
- São geradas 100 operações matemáticas aleatórias para cada faixa de dígitos: de 2 a 6 dígitos (ex: 2 dígitos = xx vezes xx).
- Um script realiza chamadas de API em paralelo e avalia as respostas.
- O prompt é rigorosamente formatado, apenas alterando a conta a ser resolvida, para evitar ruídos.
- As respostas são capturadas e cruzadas com o resultado exato (calculado via Numpy). O resultado do modelo é extraído via Expressão Regular (Regex).

## Dados Coletados

A base de dados final registra as seguintes colunas:
1. **Nome do modelo**: Qual LLM respondeu.
2. **Operação**: A dificuldade da conta (ex: 2 dígitos, 3 dígitos).
3. **Resultado do modelo**: O valor que o LLM retornou (extraído de texto para int).
4. **Resultado original**: O valor real e exato da operação.
5. **Acerto da operação**: Variável booleana (`True`/`False`), comparando os dois valores.
6. **Acerto do formato**: Verifica se a resposta obedeceu à regra imposta (responder somente com números).
7. **Conta**: A string da operação submetida.

## Como Utilizar

O script foi preparado para lidar com os limites rígidos das contas gratuitas no OpenRouter (50 requisições diárias / 20 RPM). Ao rodar, ele cria (ou atualiza) as bases e salva localmente, parando automaticamente ao atingir o limite.

1. Instale os requerimentos (`pandas`, `numpy`, `openai`, `python-dotenv`).
2. Crie um arquivo `chave.env` e insira: `OPEN_ROUTER_API_KEY=sua_chave_aqui`
3. Execute o script `pipeline_experimento.py`.

# Experimento Complementar: JEV (TypeSafe Decision Model)

## 1. Visão Geral e Objetivo
O objetivo deste experimento complementar é testar a capacidade avaliadora do modelo de decisão **JEV** (`typesafe/jev-1.14` via OpenRouter Decisions API).

Diferente de Large Language Models (LLMs) tradicionais, que foram projetados para geração de texto em linguagem natural, o **JEV** é um modelo de decisão (System One) especializado em tarefas de classificação, escolha e validação direta de proposições, retornando **probabilidades calibradas** (entre 0.0 e 1.0) em vez de gerar texto livre.

## 2. Estrutura de Diretórios
```text
jev/
├── bases_de_dados/
│   ├── base_jev_completa.csv                 # 3.600 amostras (4 operações x 9 dígitos x 100 amostras: 50/50)
│   ├── base_jev_soma.csv                     # 900 amostras de Soma (450 V / 450 F)
│   ├── base_jev_multiplicacao_inteira.csv    # 900 amostras de Multiplicação Inteira (450 V / 450 F)
│   ├── base_jev_multiplicacao_decimal.csv    # 900 amostras de Multiplicação Decimal (450 V / 450 F)
│   └── base_jev_expressoes_combinadas.csv   # 900 amostras de Expressões Combinadas (450 V / 450 F)
├── scripts/
│   ├── gerar_base_jev.py                     # Script reprodutível de geração da base
│   ├── executar_experimento_jev.py           # Script de execução via OpenRouter Decisions API
│   └── processar_resultados_jev.py           # Cálculo de sensibilidade, especificidade e métricas
├── resultados/
│   ├── respostas_brutas_jev.jsonl            # Backup bruto de todas as respostas da API
│   ├── resultados_jev.csv                    # Base tabular final com probabilidades e predições
│   └── metricas_jev_consolidadas.csv         # Resumo estatístico por operação e dígito
└── logs/
    └── geracao_base_jev.log                  # Log da geração da base de dados
```

## 3. Metodologia de Amostragem da Base de Dados
Para cada uma das 4 operações matemáticas (Soma, Multiplicação Inteira, Multiplicação Decimal e Expressões Combinadas) ao longo de 9 níveis de complexidade (2 a 10 dígitos), foram geradas **100 amostras** equilibradas (50/50):
- **50 Expressões Verdadeiras:** Com o resultado exato emitido via precisão arbitrária (`Decimal`).
- **50 Expressões Falsas:**
  1. Primeiro, busca resultados incorretos reais que os LLMs cometeram nos experimentos anteriores para aquela conta específica (foram capturados 1.164 erros reais de modelos).
  2. Quando não há erro real disponível (ex.: somas simples de poucos dígitos), aplica-se a perturbação estrita: sorteia-se um número aleatório entre 1 e a segunda casa decimal do resultado e soma-se ao gabarito.

### Formato do Prompt Fixo
```text
A seguinte expressão matemática está correta?

[expressão] = [resultado]
```

## 4. Como Executar o Experimento

### Modo Simulação (Dry-Run - sem gastar créditos)
Para validar o pipeline de execução e geração de resultados:
```powershell
python "jev/scripts/executar_experimento_jev.py" --dry-run
```

### Teste Piloto (ex: 5 amostras)
```powershell
python "jev/scripts/executar_experimento_jev.py" --limite 5
```

### Execução Completa (3.600 amostras)
```powershell
python "jev/scripts/executar_experimento_jev.py"
```

### Processamento e Consolidação das Métricas
Após a execução, consolide as métricas estatísticas:
```powershell
python "jev/scripts/processar_resultados_jev.py"
```

## 5. Métricas Analisadas no Dashboard
- **Sensibilidade (True Positive Rate):** Taxa de avaliação correta quando a conta é verdadeira ($TP / (TP + FN)$).
- **Especificidade (True Negative Rate):** Taxa de avaliação correta quando a conta é falsa ($TN / (TN + FP)$).
- **Acurácia Global:** Taxa total de acerto da classificação ($ (TP + TN) / Total $).
- **Curva de Probabilidades:** Média da probabilidade de positivo quando a expressão é verdadeira vs. média da probabilidade de negativo quando a expressão é falsa.

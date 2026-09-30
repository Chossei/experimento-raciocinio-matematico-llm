# Relatório Executivo de Custos do Experimento

**Projeto:** Raciocínio Matemático nos LLMs (Trabalho de Conclusão de Curso - Engenharia de IA)  
**Autor:** Átila Prudente  
**Data de Consolidação:** 30 de Setembro de 2026  
**Infraestrutura:** Google Cloud Vertex AI & OpenRouter API  

---

## 1. Resumo Executivo Financeiro

O experimento utilizou uma arquitetura híbrida de execução ao longo de suas três fases:
1. **Google Cloud Vertex AI (1ª Fase):** Execução síncrona das operações de *Multiplicação Inteira* com `thinking_budget=0` (sem cadeias ocultas de raciocínio).
2. **OpenRouter API (2ª e 3ª Fases):** Execução das operações de *Multiplicação Decimal*, *Soma* e *Expressões Combinadas* utilizando endpoints diretos e a **Batch API** com 50% de desconto.

### Indicadores Globais Reais Faturados
* **Total em Créditos Adquiridos (OpenRouter):** `$30,00 USD`
* **Total Efetivamente Faturado na Conta (OpenRouter):** `$23,53 USD`
* **Saldo Remanescente em Conta (OpenRouter):** `$6,47 USD`
* **Total Efetivamente Faturado no Google Cloud (Vertex AI):** `$0,74 USD` (8.100 requisições de Multiplicação Inteira)
* **Custo Efetivo Direto das 25.777 Operações Consolidadas:** **`$22,16 USD`**
* **Custo Total Global (Operações + Pré-testes de Calibração):** **`~$24,27 USD`**

---

## 2. Decomposição de Custos por Operação e Provedor

| Operação | Plataforma / Provedor | Modo de Execução | Volume Amostral | Custo Efetivo (USD) | Percentual (%) |
| :--- | :---: | :---: | :---: | :---: | :---: |
| **Multiplicação Inteira** | **Google Cloud Vertex AI** | Síncrono (`thinking_budget=0`) | 8.100 reqs | **$0,7355 USD** | 3,3% |
| **Multiplicação Decimal** | **OpenRouter API** | Síncrono / Flex | 8.677 reqs | **$9,8217 USD** | 44,3% |
| **Soma** | **OpenRouter API** | Batch API (50% de desconto) | 4.500 reqs | **$3,7219 USD** | 16,8% |
| **Expressões Combinadas** | **OpenRouter API** | Batch API (50% de desconto) | 4.500 reqs | **$7,8762 USD** | 35,6% |
| **SUBTOTAL DO EXPERIMENTO** | — | — | **25.777 reqs** | **`$22,1553 USD`** | **100,0%** |
| *Chamadas de Debug e Validação* | OpenRouter API | Testes e validações | ~500 reqs | **$2,1147 USD** | — |
| **FATURAMENTO TOTAL INTEGRADO** | **Vertex AI + OpenRouter** | **Híbrido** | **~26.300 reqs** | **`$24,2700 USD`** | — |

---

## 3. Tabela Consolidada por Modelo Gemini (em USD)

| Modelo Gemini | Mult. Inteira *(Vertex AI)* | Mult. Decimal *(OpenRouter)* | Soma *(Batch OR)* | Combinadas *(Batch OR)* | Total por Modelo (USD) | Participação (%) |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **gemini-3.1-pro-preview** | $0,1896 | $2,9040 | $0,9390 | $2,3975 | **$6,4301** | 29,0% |
| **gemini-3.8-flash** | $0,0000* | $3,9490 | $0,2643 | $0,6760 | **$4,8893** | 22,1% |
| **gemini-2.5-pro** | $0,1160 | $1,0810 | $1,1215 | $1,7366 | **$4,0553** | 18,3% |
| **gemini-3.5-flash** | $0,1427 | $0,1659 | $0,7879 | $1,6869 | **$2,7835** | 12,6% |
| **gemini-3.7-flash** | $0,0762 | $1,4757 | $0,2365 | $0,6360 | **$2,4244** | 10,9% |
| **gemini-3.6-flash** | $0,0762 | $0,0734 | $0,3440 | $0,6957 | **$1,1893** | 5,4% |
| **gemini-3-flash-preview** | $0,0476 | $0,0713 | $0,0098 | $0,0148 | **$0,1435** | 0,6% |
| **gemini-3.5-flash-lite** | $0,0347 | $0,0364 | $0,0069 | $0,0108 | **$0,0890** | 0,4% |
| **gemini-2.5-flash** | $0,0286 | $0,0384 | $0,0069 | $0,0144 | **$0,0883** | 0,4% |
| **gemini-3.1-flash-lite** | $0,0238 | $0,0264 | $0,0049 | $0,0074 | **$0,0626** | 0,3% |
| **TOTAL GERAL** | **$0,7355** | **$9,8217** | **$3,7219** | **$7,8762** | **`$22,1553 USD`** | **100,0%** |

*\*Nota: O `gemini-3.8-flash` foi anunciado pela Google posteriormente às rodadas no Vertex AI, tendo sido incorporado a partir da fase decimal na OpenRouter.*

---

## 4. Análise de Eficiência Financeira e Alocação de Recursos

### A. Concentração na Classe Pro e Raciocínio (Thinking)
* Apenas três modelos (**`gemini-3.1-pro-preview`**, **`gemini-3.8-flash`** e **`gemini-2.5-pro`**) foram responsáveis por **`$15,37 USD` (69,4%)** de todos os gastos da pesquisa.
* A razão para essa disparidade não foi o volume de requisições (que foi estritamente homogêneo), mas sim:
  1. O preço de tabela por milhão de tokens de saída nestes modelos ($10 a $12 USD/M tokens).
  2. A geração compulsória de cadeias longas de tokens de raciocínio (*thought chains*) em números extensos (7 a 10 dígitos).

### B. Hiper-eficiência da Linha Flash-Lite
* Os modelos econômicos da família (**`gemini-3.1-flash-lite`**, **`gemini-2.5-flash`** e **`gemini-3.5-flash-lite`**) demonstraram custo quase desprezível:
  * Juntos, executaram mais de **7.500 inferências completas** somando apenas **`$0,24 USD`** de despesa total.

### C. Economia Proporcionada pela Batch API
* A migração para a Batch API da OpenRouter nas fases de Soma e Combinadas garantiu 50% de desconto institucional:
  * Custo total apurado via Batch: **`$11,60 USD`**
  * Custo se tivesse sido executado de modo síncrono: **`$23,20 USD`**
  * **Economia direta gerada:** **`$11,60 USD`**

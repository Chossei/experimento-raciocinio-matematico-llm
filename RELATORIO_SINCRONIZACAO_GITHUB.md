# 📋 Relatório de Alterações e Guia de Sincronização com o GitHub

> **Data de Atualização:** 08 de Setembro de 2026  
> **Projeto:** Experimento TCC - Raciocínio Matemático nos LLMs  
> **Finalidade:** Servir como guia definitivo para o próximo agente / desenvolvedor sincronizar todas as modificações, implementações e arquivos novos criados na máquina local para o repositório oficial no GitHub.

---

## 📌 1. Visão Geral do Que Foi Feito

Neste ciclo de trabalho, expandimos o experimento de capacidade aritmética de LLMs para avaliar operações com **números decimais (ponto flutuante)** utilizando a família de modelos **Google Gemini via OpenRouter**. 

As principais frentes de trabalho foram:
1. **Inclusão do novo modelo `gemini-3.8-flash`**: Adicionado à lista de modelos, limites de taxa (RPM/RPD) e matriz de custos em todos os scripts do projeto.
2. **Criação do módulo e script OpenRouter (`gemini/openrouter/gemini_decimal_openrouter.py`)**:
   - Desenvolvido especificamente para consumir a chave `OPEN_ROUTER_API_KEY_2` de `chave.env`.
   - Implementado buffer incremental com flush em disco a cada 10 requisições para evitar perda de dados.
   - Implementada lógica de comparação decimal exata (`decimal.Decimal` com precisão de 100 dígitos) resolvendo equivalências como `19.6` vs `19.60`.
3. **Resolução dos Gargalos Operacionais e Financeiros do OpenRouter**:
   - **Diagnóstico e Correção do Erro HTTP 402**: Descoberto que a OpenRouter faz uma reserva preventiva de créditos baseada no `max_tokens` (`concorrência × max_tokens × preço_output`). Sem definir `max_tokens`, 40 requisições simultâneas reservavam até $9.83 de saldo, bloqueando a execução mesmo com $6.00 de crédito livre. A solução foi limitar `max_tokens=1000` e concorrência para 15 workers.
   - **Otimização de Tokens de Raciocínio (Thinking)**: No Vertex AI original, o raciocínio estava desativado (`thinking_budget=0`). Na OpenRouter, os modelos vinham com `effort: "medium"`, gerando até 9.000 tokens de raciocínio ocultos por conta simples e inflando o custo em mais de 100x. Ajustamos o parâmetro para deixar os modelos "no pelo":
     - `effort: "none"` para `2.5-flash`, `3.1-flash-lite` e `3-flash-preview`.
     - `effort: "minimal"` para `3.6-flash`, `3.5-flash` e `3.5-flash-lite`.
     - `effort: "low"` para `3.8-flash`, `3.7-flash` e `3.1-pro-preview` (onde a Google não permite desativar 100%).
   - O custo caiu de R$ 0,035 por operação para frações de centavo (R$ 0,0003 por operação).
4. **Reformulação do Dashboard Streamlit (`dashboard.py`)**:
   - Adicionadas visualizações dedicadas e separadas para operações decimais baseadas em `dados/resultados_gemini_decimal_openrouter.csv`.
   - Implementado cache inteligente com TTL curto (`@st.cache_data(ttl=10)`) e botão de atualização em tempo real para acompanhar a execução do script.
   - Adicionadas abas de:
     - 🏆 **Ranking de Modelos** (Acurácia global em decimais).
     - 📈 **Desempenho por Complexidade (2 a 10 dígitos)**.
     - 📝 **Conformidade do Formato** (Avaliação se o modelo seguiu o prompt e retornou apenas o número).
     - 💰 **Consumo Financeiro** (Custo total em BRL e custo por acerto).
     - 🔬 **Inspeção de Respostas & Erros** (Tabela filtrável para análise de alucinações decimais).
     - ⚖️ **Comparativo Inteiros vs. Decimais** (Análise direta da hipótese central do TCC: variação percentual de desempenho ao adicionar casas decimais).
     - 🌐 **Visão Consolidada** (Unificação de todos os testes históricos e atuais).

---

## 📁 2. Mapeamento de Arquivos (Modificados e Novos)

| Arquivo | Status | Descrição da Modificação |
| :--- | :---: | :--- |
| `gemini/openrouter/gemini_decimal_openrouter.py` | **NOVO** | Script assíncrono para inferência de operações decimais via OpenRouter, com buffer a cada 10 requisições, controle de thinking e comparação com `Decimal`. |
| `dados/resultados_gemini_decimal_openrouter.csv` | **NOVO** | Base de dados gerada incrementalmente contendo os resultados das operações decimais via OpenRouter. |
| `dashboard.py` | **MODIFICADO** | Painel Streamlit totalmente refatorado com 4 visões, incluindo aba isolada para decimais, comparativo e inspeção de erros. |
| `gemini/gemini.py` | **MODIFICADO** | Adicionado modelo `gemini-3.8-flash` (RPM 1000, RPD 10000, Input $0.75, Output $3.75). |
| `gemini/gemini_decimal.py` | **MODIFICADO** | Adicionado modelo `gemini-3.8-flash` na matriz de modelos decimais. |
| `gemini/gemini_flexivel.py` | **MODIFICADO** | Adicionado `gemini-3.8-flash` com 50% de desconto de cota flexível ($0.375 / $1.875). |
| `gemini/gemini_decimal_flexivel.py` | **MODIFICADO** | Adicionado `gemini-3.8-flash` com desconto flexível para decimais. |
| `gemini/verificador_batch.py` | **MODIFICADO** | Adicionado `gemini-3.8-flash` na lista de checagem do Batch Prediction. |
| `github_repo/` | **SINCRONIZADO LOCALMENTE** | A pasta de espelho `github_repo/` já recebeu cópias idênticas de `gemini_decimal_openrouter.py`, `dashboard.py`, `gemini.py`, `gemini_decimal.py`, etc. |

---

## ⚙️ 3. Detalhamento Técnico das Implementações

### 3.1. Tratamento de Precisão Decimal (`decimal.Decimal`)
Nas operações com decimais (como `5.6 x 3.5 = 19.6`), modelos frequentemente retornam `19.6` enquanto a planilha de referência pode conter `19.60`, ou vice-versa.
Uma comparação ingênua de strings (`"19.6" == "19.60"`) resultaria em falso negativo. Por outro lado, converter para `float` comum de ponto flutuante em Python causa problemas clássicos de arredondamento binário IEEE 754 (como `0.1 + 0.2 != 0.3`).

**Solução implementada em `comparar_decimais`:**
```python
from decimal import Decimal, InvalidOperation, getcontext
getcontext().prec = 100

def comparar_decimais(valor_extraido, valor_esperado):
    if valor_extraido is None or valor_esperado is None:
        return False
    val_ext = str(valor_extraido).strip()
    val_esp = str(valor_esperado).strip()

    if val_ext == val_esp:
        return True

    try:
        return Decimal(val_ext) == Decimal(val_esp)
    except (InvalidOperation, ValueError):
        return False
```

### 3.2. Mecanismo de Backup Incremental (`BufferResultados`)
Para evitar perdas de dados em execuções longas caso ocorra interrupção de rede ou queda do terminal:
- Uma classe assíncrona thread-safe `BufferResultados` armazena as respostas em memória.
- A cada 10 requisições bem-sucedidas (`tamanho_flush=10`), o buffer realiza `df.to_csv(..., mode='a')` no disco.
- Ao final de cada lote de modelo, um `.flush()` forçado garante que 100% dos dados parciais estejam persistidos.

### 3.3. Configuração de Raciocínio (Desligando Thinking / "No Pelo")
A Google introduziu raciocínio embutido (thinking) nos modelos Gemini 2.5 e 3.x. No OpenRouter, o padrão (`medium`) consome milhares de tokens extras. Para padronizar os experimentos aritméticos puros (zero-shot sem raciocínio extenso) e reduzir custos:
```python
def obter_config_reasoning(modelo_nome):
    # Modelos onde o raciocínio pode ser 100% desligado
    if any(x in modelo_nome for x in ['2.5-flash', '3.1-flash-lite', '3-flash-preview']):
        return {'effort': 'none'}
    # Modelos que aceitam minimal
    elif any(x in modelo_nome for x in ['3.6-flash', '3.5-flash', '3.5-flash-lite']):
        return {'effort': 'minimal'}
    # Modelos onde o raciocínio é obrigatório pelo endpoint da Google/OpenRouter
    # Inclui: gemini-3.8-flash, gemini-3.7-flash, gemini-3.1-pro-preview e gemini-2.5-pro
    else:
        return {'effort': 'low'}
```

> [!NOTE]
> **Comportamento do Gemini 2.5 Pro:**
> Foi testado diretamente no endpoint da OpenRouter se o `gemini-2.5-pro` aceitava `effort: "none"`. A API retornou **Erro 400**:
> `Error 400: Reasoning is mandatory for this endpoint and cannot be disabled.`
> Por isso, para o **Gemini 2.5 Pro**, a configuração adotada é estritamente **`effort: "low"`**, que comprime os tokens de raciocínio para o piso mínimo absoluto da Google (~60 tokens em vez de milhares), evitando o Erro 400 e mantendo o custo em centavos.

---

## 🚀 4. Guia Passo a Passo para o Próximo Agente Sincronizar com o GitHub

Como a máquina atual é corporativa e não possui o executável do `git` configurado no `PATH` (nem permissões de MCP para execução externa de git), o próximo agente ou o desenvolvedor que tiver acesso ao terminal com Git deve seguir estes passos:

### Passo 1: Verificar se os arquivos estão espelhados em `github_repo/`
Todos os arquivos alterados e criados na pasta raiz do projeto já possuem cópias na pasta `github_repo/`:
- `github_repo/dashboard.py`
- `github_repo/gemini/openrouter/gemini_decimal_openrouter.py`
- `github_repo/gemini/gemini.py`
- `github_repo/gemini/gemini_decimal.py`
- `github_repo/gemini/verificador_batch.py`

Se a execução de `dados/resultados_gemini_decimal_openrouter.csv` já tiver terminado, copie o CSV final para `github_repo/dados/`:
```powershell
Copy-Item "dados\resultados_gemini_decimal_openrouter.csv" "github_repo\dados\resultados_gemini_decimal_openrouter.csv" -Force
```

### Passo 2: Atenção aos Arquivos Sensíveis (.gitignore)
Certifique-se de que nenhum arquivo contendo credenciais seja commitado:
- ❌ `chave.env` (contém a chave da API OpenRouter)
- ❌ `temp_creds.json` / `vertex_chave.json` (contêm credenciais do Google Cloud Vertex AI)

O arquivo `.gitignore` do repositório já está configurado para bloquear:
```gitignore
*.env
chave.env
.env
__pycache__/
*.pyc
logs/
logs_gemini/
```

### Passo 3: Executar os Comandos Git
Navegue até a pasta `github_repo/` (ou inicialize onde estiver o repositório clonado) e rode:

```bash
cd github_repo

# 1. Verificar o status dos arquivos alterados e novos
git status

# 2. Adicionar os novos scripts, dashboard e documentação
git add gemini/openrouter/gemini_decimal_openrouter.py
git add gemini/gemini.py gemini/gemini_decimal.py gemini/verificador_batch.py
git add dashboard.py
git add RELATORIO_SINCRONIZACAO_GITHUB.md

# 3. Adicionar a base de dados (se for desejado commitar o CSV no repositório)
git add dados/resultados_gemini_decimal_openrouter.csv

# 4. Criar o commit explicativo
git commit -m "feat(gemini-decimal): adiciona gemini-3.8-flash, pipeline openrouter decimal com controle de thinking e novo dashboard com analise separada"

# 5. Enviar para a branch principal
git push origin main
```

---

## 📊 5. Como Executar o Novo Dashboard

Para abrir o dashboard com os gráficos separados de decimais, execute no terminal:

```bash
streamlit run dashboard.py
```

O dashboard disponibilizará imediatamente no menu lateral:
- **🔣 Operações Decimais (OpenRouter)**: Focado na base nova com 5 sub-abas analíticas.
- **🔢 Operações Inteiras (Histórico)**: Visão histórica dos dados de inteiros (OpenRouter Free e Vertex AI).
- **⚖️ Comparativo Inteiros vs. Decimais**: Gráficos agrupados e curva de decaimento por complexidade de dígitos.
- **🌐 Visão Consolidada**: Estatísticas unificadas de todo o projeto do TCC.

---

## 📈 6. Status Final Consolidado da Base Decimal (8.677 / 9.000 Concluídas - 96,4%)

A base de dados `dados/resultados_gemini_decimal_openrouter.csv` foi salva com 8.677 operações processadas:

| Modelo | Testes Realizados | Total Gabarito | Taxa de Acerto (%) | Custo Total (R$) | Custo Total (USD) | Status |
| :--- | :---: | :---: | :---: | :---: | :---: | :---: |
| **`gemini-3.8-flash`** | 900 | 900 | **89.78%** | R$ 20,34 | $3,95 USD | ✅ 100% Concluído |
| **`gemini-3.1-pro-preview`** | 580 | 900 | **85.00%** | R$ 14,96 | $2,90 USD | ⏸️ 64,4% Concluído |
| **`gemini-3.7-flash`** | 899 | 900 | **70.52%** | R$ 7,60 | $1,48 USD | ✅ 99,9% Concluído |
| **`gemini-3.5-flash`** | 900 | 900 | **43.00%** | R$ 0,85 | $0,17 USD | ✅ 100% Concluído |
| **`gemini-3.6-flash`** | 900 | 900 | **40.00%** | R$ 0,38 | $0,07 USD | ✅ 100% Concluído |
| **`gemini-3-flash-preview`** | 900 | 900 | **32.22%** | R$ 0,37 | $0,07 USD | ✅ 100% Concluído |
| **`gemini-3.1-flash-lite`** | 900 | 900 | **29.56%** | R$ 0,14 | $0,03 USD | ✅ 100% Concluído |
| **`gemini-3.5-flash-lite`** | 900 | 900 | **27.78%** | R$ 0,19 | $0,04 USD | ✅ 100% Concluído |
| **`gemini-2.5-pro`** | 898 | 900 | **27.06%** | R$ 5,57 | $1,08 USD | ✅ 99,8% Concluído |
| **`gemini-2.5-flash`** | 900 | 900 | **19.00%** | R$ 0,20 | $0,04 USD | ✅ 100% Concluído |
| **TOTAL GERAL** | **8.677** | **9.000** | **44.97%** | **R$ 50,58** | **$9,82 USD** | **96,4% Total** |

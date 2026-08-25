# Estrutura de Paralelismo do Experimento Matemático

Este documento descreve detalhadamente a arquitetura de concorrência e paralelismo implementada no script `pipeline_experimento.py`. O objetivo desta arquitetura é extrair o máximo de velocidade possível da API do OpenRouter respeitando as estritas limitações de contas gratuitas.

## 1. O Problema (O "Gargalo" Sequencial)
Se o script fosse construído de forma sequencial, ele enviaria a **Conta X** para o **Modelo A**, aguardaria a resposta (3 a 5 segundos), e só então enviaria a mesma **Conta X** para o **Modelo B**.
Como a nossa lista contém cerca de 18 modelos, testar uma única operação matemática levaria cerca de **1 minuto e meio**. Para 8.000 operações, o tempo de execução passaria dos dias ou semanas.

## 2. A Solução Assíncrona (`asyncio` e `HTTPX`)
Para resolver isso, utilizamos a biblioteca nativa `asyncio` em conjunto com o cliente `AsyncOpenAI`. 
A lógica inverte o processo:
1. O script pega 1 operação matemática.
2. Ele constrói uma "Fila de Tarefas" (Tasks) empacotando essa mesma operação para os **18 modelos simultaneamente**.
3. A função `asyncio.gather(*tarefas)` "chuta" todas as 18 requisições para a rede ao mesmo tempo.
4. Conforme os modelos terminam de pensar, o script capta a resposta, no mesmo tempo que levaria para processar 1 única resposta (3 a 5 segundos no total).

## 3. O Problema da Rajada (Burst Limit)
No OpenRouter, especialmente para modelos do tier "Free" (como o Google Gemma ou os Nemotron da Nvidia), não existe apenas o Rate Limit diário, mas também o limite de **Concorrência/Rajada**. 
Atirar 18 requisições exatamente no mesmo milissegundo aciona o mecanismo de defesa do provedor, que retorna o erro **HTTP 429 (Too Many Requests)** quase que instantaneamente para a maioria delas, recusando as conexões.

## 4. O "Semáforo" (Semaphore) como Balanceador
Para continuar usufruindo da velocidade extrema do paralelismo sem irritar os servidores, implementamos o **Padrão Semaphore** (Semáforo).

```python
semaforo = asyncio.Semaphore(5)

async def tarefa_com_semaforo(m, c):
    async with semaforo:
        return await realizar_chamada(m, c)
```

**Como funciona na prática:**
1. Quando o `asyncio.gather` tenta atirar as 18 requisições para a internet, o Semáforo atua como um pedágio.
2. Ele libera apenas as **5 primeiras** requisições e trava as outras 13 em espera local.
3. No exato milissegundo em que o 1º modelo responde (ou falha), a vaga é liberada e o 6º modelo é disparado imediatamente.
4. O processo flui de forma contínua: nunca há mais do que 5 conexões abertas com a rede externa, mas o script também nunca fica ocioso esperando ativamente, mantendo um pipeline contínuo e extremamente veloz.

### Benefícios:
- **Resiliência:** A taxa de falsos-positivos por limite de requisições cai drasticamente.
- **Velocidade Contínua:** Mantemos o paralelismo sem as penalidades do método *fire-and-forget* (atirar e esquecer).
- **Compatibilidade:** Funciona perfeitamente bem com as contas "Free" do OpenRouter.

## 5. Falhas 403 vs 429
Nesta mesma estrutura, o controle de fallback está instruído a:
- **Ignorar 403 (Forbidden):** Acontece se um modelo sair do ar ou sofrer bloqueio geográfico. Não interfere na chave atual, e a vaga do semáforo é devolvida instantaneamente.
- **Acionar Fallback (429 e 402):** Se um erro 429 ou 402 vier (indicando falta de saldo de fato), o lote inteiro é pausado e a chave global rotacionada, e as requisições devolvidas para a fila.

---
*Gerado para referência e manutenções futuras.*

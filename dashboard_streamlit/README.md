# 🧮 Avaliação do Raciocínio Matemático nos Modelos Google Gemini

Dashboard analítico e interativo desenvolvido em **Streamlit** para o Trabalho de Conclusão de Curso (TCC) de **Átila Prudente**.

O projeto investiga a capacidade de raciocínio formal, os limites da atenção posicional e os custos operacionais de **10 modelos da família Google Gemini** submetidos a operações de complexidade numérica crescente (de 2 a 10 dígitos).

---

## 📌 Escopo do Experimento
- **25.777 inferências avaliadas** via API Batch do OpenRouter.
- **4 Categorias de Operações**:
  - Multiplicação Inteira: $a \cdot b$
  - Multiplicação Decimal: $\left(\frac{a}{10}\right) \cdot \left(\frac{b}{10}\right)$
  - Adição Inteira: $a + b$
  - Expressões Combinadas: $a \cdot (b + c)$
- **Precisão Arbitrária**: Gabarito computado com 100 dígitos de precisão exata (`decimal.Decimal`).
- **Análise de Raciocínio**: Inspeção de cadeias de pensamento (*Thinking Tokens* e processos cognitivos).

---

## 🚀 Estrutura do Dashboard Multipáginas
1. **📖 Sobre o Experimento**: Storytelling acadêmico, hipótese, metodologia de geração pseudoaleatória (`seed=123`) e KPIs macro.
2. **📊 Resultados**:
   - Acurácia macro e granular por complexidade.
   - Curvas de decaimento por modelo e matriz comparativa.
   - Análise de dispersão (Tokens de Raciocínio vs Taxa de Acerto) com animação interativa.
   - Como os Modelos Pensam: Comparativo paralelo de casos de acerto vs erro com cadeias de raciocínio.
3. **💰 Custos, Formatos e Erros**: Custos financeiros acumulados, conformidade estrita de formatação numérica e inspeção de erros com busca em tempo real.

---

## 🛠️ Execução Local

```bash
# Clone o repositório
git clone https://github.com/Chossei/dashboard-raciocinio-llm.git
cd dashboard-raciocinio-llm

# Instale os requisitos
pip install -r requirements.txt

# Inicie o Streamlit
streamlit run streamlit_app.py
```

# Geração automática de atividades educacionais com leiautes explicáveis

Código, conjunto de dados e artefatos de avaliação da dissertação de mestrado de
**Matheus Lisboa Oliveira dos Santos** (PPGCC / UFCG).

O trabalho investiga se um modelo de linguagem ajustado por *fine-tuning* com atividades de
**adição** para o 2º ano do Ensino Fundamental é capaz de gerar atividades completas — enunciado,
descrição dos elementos visuais e organização espacial em HTML/CSS — pedagogicamente adequadas, e
se esse conhecimento se transfere para subtração, multiplicação e divisão.

---

## Mapa do repositório

### O que sustenta os resultados da dissertação

| Diretório | Conteúdo |
|---|---|
| `experimento3-final/` | Construção do conjunto de dados final e ajuste fino do modelo reportado |
| `experimento4-voluntarios/` | Avaliação com seis especialistas e todas as análises estatísticas |

### Material histórico (não reproduz resultados publicados)

Mantido como registro da evolução do trabalho. **Não use estes diretórios como referência para os
números da dissertação.**

| Diretório | Conteúdo |
|---|---|
| `dataset-generation/` | Experimentos iniciais de geração de exemplos |
| `experimento1/` | Tentativas com PDF/ODT e *fine-tuning* de LLaMA 2 |
| `experimento2/` | LLaMA 2, LLaMA 3 e GPT-3.5 (`ft:gpt-3.5-turbo-0125:ufcg::BTEw6z95`); base própria com **620** exemplos |
| `gpt-generated-questions/` | Prompts e saídas de modelos **sem** ajuste fino (DeepSeek V3.2, Gemini 3, GPT-5.2, GPT-3.5, Kimi K2), usados no apêndice comparativo |

---

## Conjunto de dados

Construído manualmente para este trabalho, em HTML/CSS, a partir de atividades de livros didáticos
do 2º ano (ver *Licenciamento e origem do material*, ao final).

```
experimento3-final/handmade_html_dataset/english/
├── train/     615 arquivos .html  →  614 exemplos de treino (base.html é ignorado pelo código)
├── test/       16 arquivos .html  →  partição reservada, nunca usada no treino
└── presentation/
experimento3-final/data/train_gpt.jsonl   614 exemplos — arquivo efetivamente enviado à OpenAI
```

**614 é o número correto de exemplos de treino.** O `train_gpt.jsonl` não termina em quebra de
linha, então `wc -l` devolve 613; conte objetos JSON, não linhas.

### A partição de teste

As 16 atividades de `test/` foram reservadas desde o início e constituem o **grupo de controle**
da avaliação com especialistas. A disjunção em relação ao treino foi verificada por dois critérios
independentes — **zero nomes** e **zero hashes MD5** em comum:

```bash
cd experimento3-final/handmade_html_dataset/english
comm -12 <(ls train/*.html | xargs -n1 basename | sort -u) \
         <(find test -name '*.html' | xargs -n1 basename | sort -u) | wc -l   # 0
comm -12 <(md5sum train/*.html | awk '{print $1}' | sort -u) \
         <(find test -name '*.html' -exec md5sum {} \; | awk '{print $1}' | sort -u) | wc -l   # 0
```

> ⚠️ **`test/group-addition/` e `test/group-subtraction/` não indicam o conteúdo das atividades.**
> Os nomes referem-se aos **dois grupos de avaliadores** (oito atividades para cada). As dezesseis
> são de adição e contagem; **nenhuma é de subtração**.

### Idioma

Todos os 614 exemplos de treino têm `language: en`. As atividades submetidas aos especialistas
foram geradas com `language: pt-br` — um valor de parâmetro que **não aparece no treino**. Isso é
discutido na dissertação como explicação para as falhas de idioma observadas.

---

## Modelo final

```
ft:gpt-4.1-2025-04-14:ufcg::CikEQZns
```

Base `gpt-4.1-2025-04-14`, ajustado na plataforma da OpenAI com:

| Hiperparâmetro | Valor |
|---|---|
| Épocas | **4** |
| Tamanho do lote | 20 |
| Multiplicador da taxa de aprendizado | 6 |

O número de épocas é verificável na curva de treinamento publicada na dissertação: ela vai até o
**passo 123** e, com 614 exemplos em lotes de 20, cada época corresponde a ⌈614/20⌉ = 31 passos.
Quatro épocas produzem 124 passos; cinco produziriam 155.

> ⚠️ A célula de hiperparâmetros de `01-finetuning-gpt-41.ipynb` mostra `EPOCHS = 5`, e as células
> finais referenciam o modelo GPT-3.5 do `experimento2`. São **resíduos de uma execução de teste
> posterior**, preservados para não descaracterizar o registro histórico. O notebook traz uma nota
> explicativa no ponto exato. A configuração válida é a da tabela acima.

---

## Avaliação com especialistas

Seis voluntários licenciados em Matemática avaliaram 24 atividades cada, em um instrumento de
10 perguntas em escala Likert de 5 pontos.

```
experimento4-voluntarios/evaluations/<avaliador>/<operação>/<id_atividade>/
├── form.csv          10 respostas
├── parameters.json   parâmetros de geração (temperature = "N/A" ⇒ atividade de livro)
└── example.png       captura da atividade como apresentada ao avaliador
```

Os avaliadores são identificados por pseudônimo: **`A1`–`A3`** compõem o Grupo A e
**`B1`–`B3`** o Grupo B. Cada grupo avaliou 24 das 48 atividades; as 16 atividades de livro
foram divididas entre os dois grupos, e por isso aparecem em ambos.

- **48 atividades únicas** — 32 geradas (4 operações × 2 temperaturas × 4 tipos de tarefa) e 16 de livro
- **3 avaliações por atividade** → 144 registros → **1.440 respostas**, sem dados faltantes
- `random.seed(42)` fixado na geração do conjunto avaliado

---

## Reprodução

### Roda sem custo e sem credenciais

**`experimento4-voluntarios/evaluation_statistics.ipynb`** reproduz, a partir dos `form.csv`
brutos, **todas as tabelas estatísticas da dissertação**:

| Análise | Onde |
|---|---|
| Estatísticas descritivas | *Estatísticas descritivas* |
| Alpha de Cronbach | *Alpha de Cronbach* |
| ICC entre avaliadores | *ICC — Concordância entre avaliadores* |
| Q2 — Mann-Whitney livro × modelo (com Holm) | *Mann-Whitney* |
| Q3 — Kruskal-Wallis entre operações (com Holm) | *Kruskal-Wallis* |
| Q4 — tendência central por temperatura | *Impacto da temperatura* |
| Q4 — dispersão (Fligner-Killeen, Brown-Forsythe) | *Q4 pela via da DISPERSÃO* |
| Correlação de Spearman entre perguntas (gera o PNG publicado) | *Correlação entre perguntas* |
| Composição do conjunto de treinamento | *Distribuição das categorias…* |
| Desempenho por tipo de tarefa | *Desempenho das atividades geradas por tipo de tarefa* |
| Q5 — proporções de P7 com IC de Wilson e testes de Fisher | *Proporção de avaliações positivas em P7* |

```bash
cd experimento4-voluntarios
jupyter nbconvert --to notebook --execute --inplace evaluation_statistics.ipynb
```

As figuras de distribuição Likert publicadas na dissertação são geradas por um script à parte,
que lê os mesmos `form.csv` brutos:

```bash
cd experimento4-voluntarios
python3 gerar_figuras_dissertacao.py
```

Dependências: `pandas`, `numpy`, `scipy`, `statsmodels`, `pingouin`, `scikit-posthocs`,
`seaborn`, `matplotlib >= 3.10.9`.

> O `matplotlib` precisa ser 3.10.9 ou superior: versões anteriores entram em recursão infinita em
> Python 3.12+ ao copiar objetos `Path`, quebrando qualquer gráfico.

### NÃO roda sem credenciais — e tem custo real

| Notebook | Por quê |
|---|---|
| `experimento3-final/01-finetuning-gpt-41.ipynb` | **Cria um job de ajuste fino real** na OpenAI. O treinamento reportado custou cerca de US$ 95. |
| `experimento3-final/02-generate-dataset-evaluation-persons.ipynb` | Chama a API de geração e usa Selenium para renderizar as atividades. |

Ambos requerem `OPENAI_API_KEY` em um arquivo `.env` (não versionado). **Não os execute para
conferir números** — os resultados publicados já estão salvos nas saídas das células.

---

## Licenciamento e origem do material

O repositório reúne materiais de naturezas distintas, sob licenças diferentes:

| Conteúdo | Licença |
|---|---|
| Código (notebooks, scripts) | **MIT** — ver `LICENSE` |
| Base de atividades, gerações e dados de avaliação | **CC BY-NC-SA 4.0** — ver `LICENSE-DADOS` |

As atividades da base foram **reconstruídas manualmente em HTML/CSS** para esta pesquisa,
tomando como referência livros didáticos de Matemática do 2º ano (Ápis/Ática, Caderno do
Futuro/IBEP, Bons Amigos/FTD). Os direitos das obras originais permanecem com seus autores e
editoras; nenhuma imagem delas é reproduzida aqui. Os detalhes estão em `LICENSE-DADOS`.

Os dados de avaliação envolvem participantes de pesquisa, sob aprovação do Comitê de Ética
(CAAE 88802224.3.0000.5182), e estão pseudonimizados. A reidentificação é vedada.

## Citação

Este repositório acompanha a dissertação de mestrado em Ciência da Computação da Universidade
Federal de Campina Grande. Consulte o texto para a descrição completa da metodologia, das questões
de pesquisa e das limitações do estudo.

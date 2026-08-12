#!/usr/bin/env python3
"""Gera as figuras de distribuição Likert publicadas na dissertação.

Substitui as versões anteriores por três motivos:

1. A paleta era vermelho-verde, com o ponto neutro em branco. O branco sobre
   fundo claro praticamente desaparecia, e vermelho-verde é o par mais comum de
   confusão para daltonismo. A paleta atual é laranja -> cinza -> azul, validada
   com separação ΔE 15,2 (protanopia) e 18,7 (visão normal) entre pares
   adjacentes.

2. As figuras por operação mostravam "Proporção de respostas" com apenas três
   observações por barra, o que sugere uma precisão inexistente. Passam a
   mostrar contagens, com o n declarado.

3. O boxplot por pergunta/assunto/modelo/temperatura reunia nove séries e, por
   ser boxplot de escala ordinal de cinco pontos com n pequeno, produzia caixas
   que cobriam de 1 a 5 em quase todas as perguntas -- contradizendo visualmente
   a afirmação de que as medianas se concentram entre 4 e 5. Foi substituído por
   barras divergentes (Likert empilhado), forma adequada a dados ordinais.

Uso:  python3 gerar_figuras_dissertacao.py [diretorio_de_saida]
"""
import csv, json, glob, os, sys
from collections import defaultdict

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import Patch

BASE = os.path.dirname(os.path.abspath(__file__))
SAIDA = sys.argv[1] if len(sys.argv) > 1 else os.path.join(BASE, "artifacts")

# Paleta divergente laranja -> cinza -> azul (validada para daltonismo).
CORES = {1: "#A63603", 2: "#FD8D3C", 3: "#D9D9D9", 4: "#6BAED6", 5: "#08519C"}
ROTULOS = {1: "1", 2: "2", 3: "3", 4: "4", 5: "5"}
OPERACOES = ["adição", "subtração", "multiplicação", "divisão"]
PERGUNTAS = [f"P{i}" for i in range(1, 11)]

plt.rcParams.update({
    "font.size": 9, "axes.titlesize": 10, "axes.labelsize": 9,
    "figure.facecolor": "white", "axes.facecolor": "white",
    "axes.edgecolor": "#666666", "axes.linewidth": 0.6,
    "xtick.color": "#333333", "ytick.color": "#333333",
})


def carregar():
    """Lê os form.csv brutos e devolve uma lista de registros."""
    regs = []
    for form in glob.glob(os.path.join(BASE, "evaluations", "*", "*", "*", "form.csv")):
        d = os.path.dirname(form)
        params = json.load(open(os.path.join(d, "parameters.json"), encoding="utf-8"))
        notas = [int(r[1]) for r in list(csv.reader(open(form, newline="", encoding="utf-8")))[1:]]
        regs.append({
            "operacao": d.split(os.sep)[-2],
            "tarefa": params["task"],
            "temperatura": params["temperature"],
            "livro": params["temperature"] == "N/A",
            "notas": notas,
        })
    return regs


def barras_divergentes(ax, contagens, titulo, n_por_barra, percentual=False):
    """Likert empilhado divergente: neutro centrado em zero.

    Cada barra é uma pergunta. As notas 1-2 crescem para a esquerda, 4-5 para a
    direita, e o neutro (3) fica metade de cada lado -- convenção que permite
    comparar visualmente o balanço entre discordância e concordância.

    `percentual=True` normaliza cada barra pelo total. Use quando os grupos
    comparados tiverem tamanhos diferentes: com contagens e eixo compartilhado,
    o grupo menor parece pior apenas por ser menor.
    """
    ys = range(len(PERGUNTAS))
    for i, p in enumerate(PERGUNTAS):
        c = contagens[p]
        if percentual:
            tot = sum(c.values()) or 1
            c = {k: 100 * v / tot for k, v in c.items()}
            c = defaultdict(int, c)
        # lado negativo: parte do centro para a esquerda
        esq = -c[3] / 2
        for nota in (2, 1):
            ax.barh(i, -c[nota], left=esq, color=CORES[nota],
                    edgecolor="white", linewidth=1.2, height=0.72)
            esq -= c[nota]
        # neutro, a cavalo sobre o zero
        ax.barh(i, c[3], left=-c[3] / 2, color=CORES[3],
                edgecolor="white", linewidth=1.2, height=0.72)
        # lado positivo
        dir_ = c[3] / 2
        for nota in (4, 5):
            ax.barh(i, c[nota], left=dir_, color=CORES[nota],
                    edgecolor="white", linewidth=1.2, height=0.72)
            dir_ += c[nota]

    ax.axvline(0, color="#444444", linewidth=0.8, zorder=3)
    ax.set_yticks(list(ys))
    ax.set_yticklabels(PERGUNTAS)
    ax.invert_yaxis()
    ax.set_title(f"{titulo}  (n = {n_por_barra} por pergunta)", pad=6)
    ax.grid(axis="x", linestyle=":", alpha=0.35, zorder=0)
    ax.set_axisbelow(True)
    for lado in ("top", "right", "left"):
        ax.spines[lado].set_visible(False)


def legenda(fig):
    fig.legend(handles=[Patch(facecolor=CORES[k], edgecolor="white", label=ROTULOS[k])
                        for k in (1, 2, 3, 4, 5)],
               title="Escala Likert", loc="lower center", ncol=5,
               frameon=False, bbox_to_anchor=(0.5, -0.01))


def contar(regs, filtro):
    """Conta respostas por pergunta e nota, para os registros que passam no filtro."""
    cont = {p: defaultdict(int) for p in PERGUNTAS}
    n = 0
    for r in regs:
        if not filtro(r):
            continue
        n += 1
        for i, nota in enumerate(r["notas"]):
            cont[PERGUNTAS[i]][nota] += 1
    return cont, n


def figura_por_operacao(regs):
    """Substitui o antigo boxplot de nove séries."""
    fig, axes = plt.subplots(2, 2, figsize=(11, 6.5), sharex=True)
    for ax, op in zip(axes.flat, OPERACOES):
        cont, n = contar(regs, lambda r, op=op: r["operacao"] == op and not r["livro"])
        barras_divergentes(ax, cont, op.capitalize(), n)
    for ax in axes[1]:
        ax.set_xlabel("Número de avaliações")
    legenda(fig)
    fig.tight_layout(rect=[0, 0.06, 1, 1])
    destino = os.path.join(SAIDA, "likert_divergente_por_operacao.png")
    fig.savefig(destino, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  {destino}")


def figura_modelo_vs_livro(regs):
    """Comparação direta entre atividades geradas e extraídas de livros."""
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), sharex=True)
    for ax, (rot, filt) in zip(axes, [
            ("Atividades geradas pelo modelo", lambda r: not r["livro"]),
            ("Atividades extraídas de livros", lambda r: r["livro"])]):
        cont, n = contar(regs, filt)
        # percentual: os grupos têm tamanhos diferentes (96 x 48 avaliações)
        barras_divergentes(ax, cont, rot, n, percentual=True)
        ax.set_xlabel("Percentual das avaliações")
    legenda(fig)
    fig.tight_layout(rect=[0, 0.09, 1, 1])
    destino = os.path.join(SAIDA, "likert_divergente_modelo_vs_livro.png")
    fig.savefig(destino, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  {destino}")


def figura_temperatura(regs):
    """Mantém a comparação entre temperaturas, base da Q4."""
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.2), sharex=True)
    for ax, t in zip(axes, [0.5, 0.7]):
        cont, n = contar(regs, lambda r, t=t: not r["livro"] and r["temperatura"] == t)
        barras_divergentes(ax, cont, f"Temperatura $T = {str(t).replace('.', ',')}$", n)
        ax.set_xlabel("Número de avaliações")
    legenda(fig)
    fig.tight_layout(rect=[0, 0.09, 1, 1])
    destino = os.path.join(SAIDA, "likert_divergente_por_temperatura.png")
    fig.savefig(destino, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  {destino}")


TAREFAS_PT = {
    "observe image, write answer": "Observar imagem e escrever resposta",
    "observe image, draw answer": "Observar imagem e desenhar resposta",
    "observe images, write answer": "Observar imagens e escrever resposta",
    "observe images, link objects": "Observar imagens e relacionar objetos",
}


def figura_detalhada_por_operacao(regs, op):
    """Detalhe por tipo de tarefa e temperatura, para uma operação.

    Substitui as figuras que mostravam "Proporção de respostas" com n = 3: aqui
    o eixo é contagem e o n aparece no título de cada painel, deixando explícito
    que cada célula reúne uma atividade avaliada por três especialistas.
    """
    tarefas = sorted(TAREFAS_PT)
    fig, axes = plt.subplots(len(tarefas), 2, figsize=(11, 2.1 * len(tarefas)),
                             sharex=True)
    for lin, tarefa in enumerate(tarefas):
        for col, temp in enumerate([0.5, 0.7]):
            ax = axes[lin][col]
            cont, n = contar(regs, lambda r, t=tarefa, tp=temp, o=op:
                             not r["livro"] and r["operacao"] == o
                             and r["tarefa"] == t and r["temperatura"] == tp)
            rot = f"{TAREFAS_PT[tarefa]} · $T={str(temp).replace('.', ',')}$"
            barras_divergentes(ax, cont, rot, n)
            ax.tick_params(labelsize=7)
            ax.title.set_size(8)
    for ax in axes[-1]:
        ax.set_xlabel("Número de avaliações")
    legenda(fig)
    fig.suptitle(f"Distribuição das respostas Likert — {op.capitalize()}", y=1.0)
    fig.tight_layout(rect=[0, 0.045, 1, 0.985])
    destino = os.path.join(SAIDA, f"likert_divergente_detalhe_{op}.png")
    fig.savefig(destino, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"  {destino}")


if __name__ == "__main__":
    os.makedirs(SAIDA, exist_ok=True)
    regs = carregar()
    assert len(regs) == 144, f"esperava 144 registros, li {len(regs)}"
    print(f"{len(regs)} registros · {sum(len(r['notas']) for r in regs)} respostas")
    print("figuras geradas:")
    figura_por_operacao(regs)
    figura_modelo_vs_livro(regs)
    figura_temperatura(regs)
    for op in OPERACOES:
        figura_detalhada_por_operacao(regs, op)

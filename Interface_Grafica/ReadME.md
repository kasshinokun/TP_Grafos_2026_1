# Interface Gráfica — Projeto Delta v4c

## Visão Geral

Esta pasta reúne as interfaces gráficas desenvolvidas individualmente por cada programador da equipe para o **Projeto Delta v4c** — sistema de análise de redes sociais do GitHub usando Teoria dos Grafos. Cada membro escolheu livremente o framework e a abordagem de interface, resultando em três implementações distintas e complementares.

---

## Estrutura da Pasta

```
Interface_Grafica/
├── Daniel/
│   └── main_gui.py              # Interface CTK — painel de controle sequencial
│
├── Gabriel/
│   ├── gui_ctk0.py              # CTK Rev A — versão base
│   ├── gui_ctk1a.py             # CTK Rev B — máscara de tokens
│   ├── gui_ctk1b.py             # CTK Rev A+ — melhorias UI/UX
│   ├── gui_ctk1c.py             # CTK Rev B — multitela + grafos
│   ├── gui_ctk1c2.py            # CTK Rev B — spinner e temas
│   ├── gui_ctk1d.py             # CTK Rev C — sem dependências de grafos
│   ├── gui_ctk1d2.py            # CTK Rev H — versão final CTK ✅
│   ├── gui_pyqt6_1a.py          # PyQt6 Rev A — conversão base
│   ├── gui_pyqt6_1b.py          # PyQt6 Rev A+ — ofuscação de logs
│   ├── gui_pyqt6_1c.py          # PyQt6 Rev D — estabilização
│   ├── gui_pyqt6_1d.py          # PyQt6 Rev E — QR via buffer
│   └── gui_pyqt6_1d2.py         # PyQt6 Rev E — versão final PyQt6 ✅
│
└── Paulo/
    ├── app.py                   # Interface web Streamlit
    └── lib/                     # Bibliotecas JS bundled (Vis.js, Tom Select)
```

---

## Comparativo das Abordagens

| | **Daniel** | **Gabriel** | **Paulo** |
|---|---|---|---|
| **Framework** | CustomTkinter | CustomTkinter / PyQt6 | Streamlit |
| **Tipo** | Desktop | Desktop | Web (navegador) |
| **Foco principal** | Pipeline de análise de grafos | Mineração GitHub + visualização | Dashboard completo + algoritmos |
| **Visualização de grafos** | Log textual | Leitor GEXF embutido | PyVis interativo (arrastar/zoom) |
| **Algoritmos** | Centralidade de grau | — | BFS, DFS, Dijkstra, SCC, Topológica |
| **Métricas** | Top 5 centralidade | — | PageRank, Betweenness, Comunidades... |
| **Exportação** | GEPHI (`.gexf`) | Leitura de `.gexf` | GEPHI (`.gexf`) |
| **Mineração GitHub** | Indireta (via lapidador) | Direta (orquestrador híbrido) | Via CSV upload |
| **Arquitetura** | Monolítica | Monolítica + threads | EDA (Event-Driven Architecture) |
| **Instalação** | `pip install customtkinter` | `pip install customtkinter` ou `PyQt6` | `pip install streamlit pyvis pandas` |

---

## Como Executar Cada Interface

### Daniel
```bash
pip install customtkinter
python Daniel/main_gui.py
```

### Gabriel (versões recomendadas)
```bash
# CustomTkinter
pip install customtkinter pillow pyzbar qrcode
python Gabriel/gui_ctk1d2.py

# PyQt6
pip install PyQt6 pillow pyzbar qrcode
python Gabriel/gui_pyqt6_1d2.py
```

### Paulo
```bash
pip install streamlit pandas pyvis
streamlit run Paulo/app.py
```

---

## Contexto do Projeto

Todos os módulos de interface dependem do **motor de grafos compartilhado** do projeto Delta v4c(Nome Interno). Certifique-se de executar cada interface a partir da raiz do projeto para que as importações funcionem corretamente:

```
projeto_delta/
├── graph_engine/       ← usado por Daniel
├── grafo/              ← usado por Paulo
├── orchestrator_hibrido_alpha0e.py  ← usado por Gabriel
├── main_rebuild.py     ← lapidador (Gabriel e Daniel)
├── grafos_runner.py    ← runner de grafos (Gabriel)
└── Interface_Grafica/
    ├── Daniel/
    ├── Gabriel/
    └── Paulo/
```

---

## READMEs Individuais

Cada subpasta possui seu próprio README detalhado:

- [`Daniel/README.md`](Daniel/README.md)
- [`Gabriel/README.md`](Gabriel/README.md)
- [`Paulo/README.md`](Paulo/README.md)

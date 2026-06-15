# Interface Gráfica — Gabriel

## Descrição

Conjunto de interfaces gráficas para o **Projeto Delta v4c** — sistema de mineração híbrida de dados do GitHub com pós-processamento (lapidador) e integração de grafos. Gabriel desenvolveu versões paralelas usando dois frameworks distintos (**CustomTkinter** e **PyQt6**), com múltiplas revisões evolutivas documentadas.

---

## Estrutura dos Arquivos

### Série CustomTkinter (`gui_ctk*.py`)

| Arquivo | Revisão | Destaques |
|---|---|---|
| `gui_ctk0.py` | REV A | Versão inicial: checkbox "Rodar Lapidador", botão pós-processar, testes unitários via subprocess, integração `grafos_runner` |
| `gui_ctk1a.py` | REV B | Tokens com máscara por padrão (alternância Mostrar/Esconder) |
| `gui_ctk1b.py` | REV A+ | Melhorias de UI/UX na tela principal |
| `gui_ctk1c.py` | REV B | Multitela + aba de visualização de grafos |
| `gui_ctk1c2.py` | REV B | Spinner +/- para anos de histórico (limite 1–5), seletor de tema Light/Dark/System, menu suspenso de navegação |
| `gui_ctk1d.py` | REV C | Versão sem dependências de grafos (mais portátil) |
| `gui_ctk1d2.py` | REV H | Versão mais madura; inclui `GraphValidateLoader` (parser GEXF sem bibliotecas XML) e aba dedicada de grafos |

### Série PyQt6 (`gui_pyqt6_*.py`)

| Arquivo | Revisão | Destaques |
|---|---|---|
| `gui_pyqt6_1a.py` | REV A | Conversão completa do CustomTkinter para PyQt6 com melhorias de UI/UX |
| `gui_pyqt6_1b.py` | REV A+ | Ofuscação de tokens nos logs |
| `gui_pyqt6_1c.py` | REV D | Estabilização e ajustes de layout |
| `gui_pyqt6_1d.py` | REV E | QR Code carregado via buffer de bytes (sem arquivo temporário) |
| `gui_pyqt6_1d2.py` | REV E | Versão final com `GraphValidateLoader` e `GraphWidget` integrados |

> **Arquivo recomendado:** `gui_ctk1d2.py` (CTK) ou `gui_pyqt6_1d2.py` (PyQt6) — ambos são as revisões mais completas de cada série.

---

## Tecnologias

- **Python 3**
- **CustomTkinter** (série ctk) — tema moderno baseado em Tkinter
- **PyQt6** (série pyqt6) — framework Qt para Python
- Módulos internos: `orchestrator_hibrido_alpha0e`, `main_rebuild` (lapidador), `grafos_runner`

---

## Funcionalidades Principais

### Mineração
- Configuração de usuário-alvo, repositório e anos de histórico do GitHub
- Gerenciamento de múltiplos tokens de API (com máscara de segurança)
- Carga de tokens via QR Code ou arquivo JSON
- Início e parada graciosa da mineração em thread separada

### Pós-processamento
- Integração com o Lapidador (`main_rebuild.main`)
- Integração com o pipeline de grafos (`grafos_runner.run_graphs`)
- Checkbox para acionar o lapidador automaticamente ao fim da mineração

### Visualização de Grafos
- Leitura e validação de arquivos `.gexf` (sem dependência de bibliotecas XML externas)
- Listagem automática de arquivos `.gexf` no diretório da aplicação
- Exibição de estatísticas do grafo carregado (nós, arestas, atributos)

### Testes e Log
- Execução da suíte de testes unitários (`test_cli/run_all.py`) via subprocess
- Painel de log com streaming em tempo real (thread-safe via `queue.Queue` / `QThread`)
- Notificações na barra de status

---

## Como Executar

### Versão CustomTkinter
```bash
pip install customtkinter pillow pyzbar qrcode
python gui_ctk1d2.py
```

### Versão PyQt6
```bash
pip install PyQt6 pillow pyzbar qrcode
python gui_pyqt6_1d2.py
```

---

## Layout Geral (ambas as versões)

```
┌──────────────────────────────────────────────────────────────┐
│  Navbar / Abas: [Mineração] [Grafos] [Sobre]                 │
├───────────────────┬──────────────────────────────────────────┤
│ Target user       │                                          │
│ Target repo       │         Painel de Log                    │
│ Anos de histórico │    (streaming em tempo real)             │
│ Tokens (mascarados│                                          │
│ [▶ Iniciar]       │                                          │
│ [■ Parar]         │                                          │
│ [📊 Pós-processar]│                                          │
│ [🧪 Testes]       │                                          │
└───────────────────┴──────────────────────────────────────────┘
```

---

## Evolução das Revisões (Resumo)

```
REV A  →  Versão base funcional
REV B  →  Máscara de tokens + multitela
REV C  →  Portabilidade (sem grafos)
REV D  →  PyQt6 estabilizado
REV E  →  QR Code via buffer de bytes
REV H  →  Parser GEXF embutido + aba de grafos completa
```

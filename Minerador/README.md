# 🛠️ Mineradores — Visão Geral do Projeto

Este repositório reúne **três implementações independentes** de um Minerador de dados do GitHub, desenvolvidas por Daniel, Gabriel e Paulo como complemento às suas respectivas APIs de Grafos. Cada minerador coleta interações entre usuários de repositórios públicos e as transforma em dados estruturados para alimentar os grafos de rede.

---

## 📁 Estrutura

```
Minerador/
├── Daniel/
│   ├── main_miner.py
│   └── core/
│       ├── event_bus.py
│       └── miner_app.py
├── Gabriel/
│   ├── orchestrator_hibrido_alpha0e.py   # Produção (sem GUI)
│   └── orchestrator_hibrido_alpha0f.py   # Com GUI (CTk + PyQt6)
└── Paulo/
    ├── core/
    │   └── graph_registry.py
    ├── events/
    │   ├── event.py
    │   ├── event_bus.py
    │   └── event_type.py
    ├── graph/
    │   └── mining/
    │       ├── csv_loader.py
    │       └── interaction.py
    └── handler/
        └── mining_handler.py
```

Cada subpasta possui seu próprio `README.md` com detalhes de implementação.

---

## Conceito Comum

Todos os mineradores implementam a mesma ideia central: **coletar interações entre usuários em repositórios GitHub e convertê-las em arestas ponderadas de um grafo dirigido**. Os pesos refletem o tipo de interação, seguindo a tabela de referência do projeto:

| Tipo de Interação | Peso |
|---|---|
| Comentário em issue ou PR | 2 |
| Fechamento de issue por outro usuário | 3 |
| Review ou aprovação de PR | 4 |
| Merge de PR | 5 |

---

## Comparativo entre Implementações

| Aspecto | Daniel | Gabriel | Paulo |
|---|---|---|---|
| **Arquitetura** | Pub/Sub com EventBus Singleton | Orquestrador híbrido (async + threads) | Pub/Sub com EventBus tipado (Enum) |
| **Autenticação** | QR Code com múltiplos tokens | QR Code com múltiplos tokens | Não implementada (foco no pipeline pós-coleta) |
| **Paralelismo** | Pool de threads (1 thread/token) | `aiohttp` assíncrono + threads + modo sem token | Não aplicável (processa CSVs locais) |
| **Entrada de dados** | API REST do GitHub (JSON) | API REST do GitHub (JSON) | Arquivo CSV local |
| **Tipos de dado coletados** | Issues fechadas | Issues, PRs, comentários, reviews | Lê interações pré-formatadas de CSV |
| **Integração com Lapidador** | Gera arquivo compatível com Lapidador da API | Chama o Lapidador automaticamente ao fim da coleta | Integra diretamente com a API de Grafos via eventos |
| **Tipagem de eventos** | Strings livres (`"START_MINING"`) | — | Enum fortemente tipado (`EventType`) |
| **Dependências externas** | `qrcode`, `Pillow` | `aiohttp`, `requests`, `qrcode`, `Pillow`, `pyzbar` | Nenhuma (só biblioteca padrão) |
| **Interface gráfica** | Não | Opcional (versão `alpha0f`) | Não |

---

## Fluxo de Dados — Visão Integrada

```
                    ┌────────────────────────────────────┐
                    │         API do GitHub              │
                    │  (issues, PRs, comentários, reviews)│
                    └────────────┬───────────────────────┘
                                 │
              ┌──────────────────┼──────────────────┐
              │                  │                  │
        ┌─────▼──────┐   ┌───────▼──────┐   ┌──────▼───────┐
        │   Daniel   │   │    Gabriel   │   │    Paulo     │
        │ (threads)  │   │ (async+HTTP) │   │  (CSV local) │
        └─────┬──────┘   └───────┬──────┘   └──────┬───────┘
              │                  │                  │
              ▼                  ▼                  ▼
         JSON bruto          JSON bruto         CSV formatado
              │                  │                  │
              ▼                  ▼                  ▼
          Lapidador          Lapidador           MiningHandler
         (da API Daniel)    (da API Gabriel)    (Paulo interno)
              │                  │                  │
              └──────────────────┴──────────────────┘
                                 │
                                 ▼
                    Grafo Dirigido Ponderado
                    (exportável para Gephi GEXF)
```

---

## Pontos de Atenção para Integração

1. **Fonte de dados diferente**: Daniel e Gabriel coletam diretamente da API do GitHub; Paulo parte de um CSV pré-gerado — o CSV precisa ser produzido por um dos outros mineradores antes de ser consumido pelo Paulo.

2. **Formato de saída incompatível**: Daniel produz `{from, to, weight}`, Gabriel produz `{source, target, type}`, Paulo consome diretamente via eventos sem arquivo intermediário. Para um pipeline unificado, é necessário um conversor de formato.

3. **Autenticação**: Daniel e Gabriel exigem tokens do GitHub armazenados em QR Code; Paulo não precisa de autenticação (processa dados já coletados).

4. **Cobertura de tipos de interação**:
   - Daniel cobre apenas **fechamento de issues**
   - Gabriel cobre **comentários, fechamentos e reviews**
   - Paulo suporta todos os tipos via enum, mas depende do CSV de entrada para determinar quais estão presentes

5. **EventBus**: Daniel usa strings livres; Paulo usa enum tipado. Não são compatíveis entre si sem adaptação.

6. **Versões do Gabriel**: `alpha0f` requer `customtkinter` e `PyQt6` para a interface gráfica; `alpha0e` é a versão de produção sem dependências de UI.

---

## Requisitos por Implementação

| | Daniel | Gabriel | Paulo |
|---|---|---|---|
| Python | 3.10+ | 3.10+ | 3.10+ |
| `aiohttp` | ✗ | ✓ | ✗ |
| `requests` | ✗ | ✓ | ✗ |
| `qrcode` + `Pillow` | ✓ | ✓ | ✗ |
| `pyzbar` | ✗ | ✓ | ✗ |
| `customtkinter` / `PyQt6` | ✗ | Opcional (`alpha0f`) | ✗ |
| Token GitHub | ✓ | ✓ / ✗ (modo sem token) | ✗ |

---

## Próximos Passos Sugeridos

- Definir um formato de CSV ou JSON comum como interface entre os mineradores e a API de Grafos, eliminando as incompatibilidades atuais.
- Unificar o `EventBus` (preferencialmente usando o enum tipado do Paulo) para que os três módulos possam ser orquestrados em conjunto.
- Consolidar o pipeline completo: coleta (Daniel/Gabriel) → normalização (Lapidador) → CSV → carregamento (Paulo) → grafo → exportação GEXF.
- Considerar o modo sem token do Gabriel como fallback para ambientes sem acesso a tokens da API do GitHub.

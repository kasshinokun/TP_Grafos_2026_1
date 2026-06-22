# Changelog — rebuild_gama (Versão Final Consolidada)

## GUI de Testes Unitários (`gui/frames/testes_unitarios.py`)

Implementada a tela de Testes Unitários, antes um esqueleto vazio.
Roda a suíte real do projeto (`./tests`) de dentro da GUI, sem
reimplementar nenhuma lógica de teste.

Arquitetura em três camadas, separando descoberta/execução de
apresentação:

- **`gui/bridges/test_orchestrator.py`** (novo) — `TestOrchestrator`:
  descobre por introspecção (`inspect.getmembers` + `issubclass(...,
  unittest.TestCase)`) as classes de teste de cada módulo em
  `./tests`, organizadas por uma tabela estática de categorias
  (`CATEGORIES`) — algoritmos, API primitiva, estrutura/heurísticas,
  métricas, mineração, e API GraphQL (esta última baseada em pytest
  puro, tratada como categoria própria). Executa qualquer combinação
  (uma classe específica, ou "Todos da categoria") via
  `unittest.TextTestRunner`/`pytest.main` com saída capturada, e
  devolve um `RunReport` estruturado.
- **`gui/utils/test_formatting.py`** (novo) — funções puras de
  formatação de `RunReport`/`TestCaseResult` para texto (cabeçalho,
  lista de casos com ícones ✓/✗/‼/○, resumo agregado de múltiplas
  categorias). Não sabe nada sobre unittest/pytest.
- **`gui/frames/testes_unitarios.py`** — sidebar com dois comboboxes
  (Categoria → Execução, o segundo é repopulado dinamicamente pelo
  orchestrator conforme a categoria escolhida) e botões "Rodar
  testes", "Rodar todas as categorias" e "Limpar console"; área
  principal com pseudo-console (`CTkTextbox`) mostrando o relatório.

Tratamento de `tests/test_graphql_api.py` (usa `@pytest.fixture`,
incompatível com `unittest.TestLoader`): aparece como categoria
própria; se `pytest` não estiver instalado no ambiente, o relatório
mostra "indisponível" com instrução de instalação, em vez de quebrar a
descoberta das demais categorias ou travar a tela.

Bug encontrado e corrigido durante o desenvolvimento:
`unittest.TextTestRunner.run()` esvazia a `TestSuite` internamente
conforme cada teste executa (libera referências) — iterar a suíte
*depois* de rodá-la retorna só `None`. O orchestrator agora captura a
lista de testes (achatada, com `_iter_suite`) *antes* de chamar
`runner.run()`.

Validação: criados `tests/test_structure_extra.py` (sessão anterior,
23 testes) e `tests/test_orchestrator_bridge.py` (novo, 23 testes,
incluindo um módulo de teste sintético registrado em `sys.modules`
para validar os caminhos de falha/erro/skip sem precisar quebrar um
teste real do projeto). Suíte completa: **98/98 testes passando**.
Integração da GUI (sidebar, comboboxes, botões, console) validada de
ponta a ponta com mocks fiéis dos widgets `customtkinter`/`tkinter`,
já que este ambiente de build não possui Tk instalado.

## UX do canvas de visualização (`gui/graph_canvas.py`)

O modo "Gráfico" de `seek_n_path.py` (Busca & Caminhos) já desenhava o
grafo via `GraphCanvas`, com zoom por scroll do mouse, mas sem
scrollbars nem controles visuais de zoom — ao aplicar zoom, partes do
grafo saíam da área visível e ficavam inacessíveis. As outras duas
telas que reusam `GraphCanvas` (Visualização do Grafo e Métricas) já
tinham um slider de zoom na toolbar, mas também não tinham scrollbars.

Mudanças em `GraphCanvas` (afetam as 3 telas que o utilizam):

- **Novo `GraphCanvas.with_scrollbars(parent, ...)`**: classmethod que
  cria o canvas já encapsulado num frame com scrollbar horizontal e
  vertical (vinculadas a `xview`/`yview` nativos do Tk) e botões de
  zoom "+`/`−" flutuantes no canto inferior direito. Retorna
  `(container, canvas)` — `container` é o que se empacota no layout;
  `canvas` é a mesma instância de `GraphCanvas` de sempre, com toda a
  API anterior preservada (`load_adapter`, `set_node_colors`,
  `set_zoom_level`, `get_selected_node`, evento `<<NodeSelected>>`).
- **`scrollregion` dinâmico**: recalculado a cada `redraw()` conforme
  o bounding box do grafo já escalado pelo zoom, então as scrollbars
  só "aparecem com espaço para navegar" quando o conteúdo de fato
  excede a viewport.
- **Novos métodos públicos `zoom_in()` / `zoom_out()`**: aplicam um
  passo fixo de zoom (`zoom_step = 1.2`), usados pelos botões
  embutidos, mas chamáveis por qualquer controle externo.
- **Zoom mantém o centro da viewport**: ao aplicar zoom (slider,
  botões ou scroll do mouse), a posição de scroll é recalculada para
  manter o mesmo ponto do grafo centralizado, em vez de pular para o
  canto superior esquerdo.
- **Pan com o botão do meio do mouse** (`scan_mark`/`scan_dragto`
  nativos), sem interferir no arraste de nós (botão esquerdo).
- **Seleção/arraste de nó corrigidos para considerar o scroll**:
  passaram a usar `canvasx`/`canvasy` em vez de `event.x`/`event.y`
  diretos — sem isso, cliques ficariam desalinhados após rolar a tela.
- Corrigido bug de margem inconsistente entre o cálculo de zoom "fit"
  (`_center_layout`, usava margem de 100px) e a margem da scrollregion
  (`SCROLL_MARGIN = 60px`), que fazia o grafo "vazar" ligeiramente da
  viewport mesmo no zoom padrão de 100%.

Telas atualizadas para usar `GraphCanvas.with_scrollbars`:

- **`gui/frames/seek_n_path.py`**: ganhou também um slider de zoom na
  barra de controles (antes só existia o scroll do mouse, sem nenhum
  controle visual), seguindo o mesmo padrão das outras duas telas.
  Aparece apenas no modo "Gráfico".
- **`gui/screen_graph.py`** e **`gui/screen_metrics.py`**: apenas a
  criação do canvas foi alterada (de `GraphCanvas(...)` para
  `GraphCanvas.with_scrollbars(...)`); o restante de cada arquivo
  (`self.canvas`, slider já existente, callbacks) não precisou mudar.

Validação: como o ambiente de build não possui Tk/customtkinter
instalados, a renderização visual não pôde ser confirmada com
captura de tela real. A matemática de zoom/scroll/scrollregion foi
validada com um mock fiel da API do `tkinter.Canvas`
(`canvasx`/`canvasy`/`xview_moveto`/`scrollregion`), cobrindo: fit
inicial, zoom in/out repetido (incluindo saturação em
`min_zoom`/`max_zoom`), resize, pan, e seleção de nó com scroll
aplicado. A integração com `seek_n_path.py` e `screen_graph.py` foi
validada de ponta a ponta com mocks dos widgets `customtkinter`,
cobrindo carregamento de grafo real, alternância Console↔Gráfico,
zoom via botão/slider e sincronização entre eles. Recomenda-se um
teste visual manual no ambiente do usuário (com Tk real) para
confirmar o resultado renderizado antes de considerar finalizado.

## Bugs Corrigidos

### `grafo/utils/gexf_parser.py`
- **BUG CRÍTICO:** `for idx, node in nodes:` → corrigido para `for idx, node in enumerate(nodes):`
- Adicionado suporte a namespace gexf 1.2 e 1.3
- Adicionado parsing de peso das arestas (`weight`)
- Trata graciosamente arestas com IDs inválidos

### `grafo/graph/adjacency_matrix_graph.py`
- **OTIMIZAÇÃO:** `get_vertex_in_degree` era O(V) — adicionado `in_degree_count[]` para O(1) (igual à lista de adjacência)
- Adicionado método `is_connected()` via BFS fraca (faltava)
- Adicionado métodos `get_successors()` e `get_predecessors()` para duck-typing no Adapter
- `export_to_gephi()` com escape XML correto

### `gui/metrics_panel.py`
- Código estava incompleto (truncado pela QwenAI)
- Implementado completamente: `show_pagerank`, `show_betweenness`, `show_closeness`,
  `show_degree_centrality`, `show_structure_metrics`, `show_communities`,
  `show_bridging_ties`, `clear_all`, `show_loading`

### `tests/test_graph_api.py`
- `test_is_successor_predecessor` tinha lógica invertida para `is_predessor`
- Corrigido com semântica correta: `is_predessor(v, u)` verifica se u→v existe

### `tests/fixtures/__init__.py`
- Arquivo ausente — criado para tornar o diretório um pacote Python

### `grafo/__init__.py`
- Arquivo ausente — criado

## Outras Melhorias
- Adicionado arquivo `pytest.ini` para configuração de testes.
- Criados arquivos `__init__.py` ausentes para garantir que os diretórios sejam tratados como pacotes Python.

## Resultado dos Testes
- **43/43 testes passando** (0 falhas)
- Cobertura: API obrigatória + BFS/DFS/Dijkstra + 11 métricas de redes complexas

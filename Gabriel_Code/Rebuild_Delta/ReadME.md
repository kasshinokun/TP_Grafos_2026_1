# Rebuild Delta - Sistema de Análise e Visualização de Grafos
## 📋 Sobre o Projeto
O Rebuild Delta é uma aplicação acadêmica desenvolvida para a disciplina de Teoria dos Grafos (2026/1), 
focada na implementação, análise e visualização de estruturas de grafos. 
O sistema oferece uma suite completa de ferramentas para manipulação de grafos, cálculo de métricas de rede, 
detecção de comunidades e mineração de dados do GitHub através da API Rest e pré-implementação da GraphQL 
para definição de limites de requests por meio da análise retorno de status.
## 🎯 Objetivo
O principal objetivo do projeto é fornecer uma plataforma educacional e prática para:
- Implementação de estruturas de dados de grafos com múltiplas representações (lista de adjacência e matriz de adjacência)
- Cálculo de métricas de centralidade (Degree, Betweenness, Closeness, PageRank)
- Detecção de comunidades em redes complexas (Label Propagation, Modularidade, Bridging Ties)
- Análise estrutural de grafos (Densidade, Clustering, Assortatividade)
- Visualização interativa de grafos com layouts force-directed
- Mineração de dados do GitHub para construção de grafos reais de colaboração
- Execução de testes unitários integrados à interface gráfica
## 🏗️ Arquitetura
O projeto segue uma arquitetura modular em camadas com clara separação de responsabilidades:
```text
app_tp/
├── grafo/              # Núcleo do sistema - Estruturas de dados e algoritmos
│   ├── graph/          # Implementações de grafos (abstract, lista, matriz)
│   ├── networkx_pure/  # Algoritmos puros em Python (sem dependência do NetworkX)
│   └── utils/          # Utilitários (parser GEXF, etc.)
├── gui/                # Interface gráfica responsiva
│   ├── frames/         # Telas da aplicação
│   ├── graph_canvas.py # Canvas para visualização de grafos
│   └── workers.py      # Threads para tarefas em segundo plano
├── miner/              # Módulo de mineração de dados do GitHub
├── viz/                # Módulo de visualização (layouts force-directed)
├── tests/              # Suíte completa de testes unitários
├── csv/                # Arquivos de dados em formato CSV
└── gexf/               # Arquivos de grafos em formato GEXF
```
### Princípios Arquiteturais
- Separação de Concerns: Lógica de negócio isolada da interface gráfica
- API Abstrata: Interface comum para diferentes implementações de grafos
- Duck-Typing: Adapter pattern para interoperabilidade entre implementações
- Processamento Assíncrono: Workers threads para operações pesadas sem bloquear a UI
- Testabilidade: Suíte completa de testes integrada à GUI
### 🎨 Design Patterns
O projeto implementa diversos padrões de projeto:
- Adapter Pattern: Ponte entre diferentes implementações de grafos usando duck-typing
- Strategy Pattern: Diferentes algoritmos de mineração (Common, Hybrid)
- Factory Pattern: Criação de grafos a partir de diferentes fontes (CSV, GEXF)
- Observer Pattern: Notificações de progresso durante operações longas
- MVC-like: Separação entre Model (grafo), View (canvas) e Controller (frames)
- Bridge Pattern: Separação entre abstração (algoritmos) e implementação (estrutura de dados)
## 💻 Tecnologias Utilizadas
### Linguagem e Frameworks
- Python 3.x - Linguagem principal
- CustomTkinter - Interface gráfica moderna e responsiva
- Tkinter - Canvas para renderização de grafos
- [Pure NetworkX Fork](https://github.com/kasshinokun/TP_Grafos_2026_1/tree/main/Gabriel_Code/networkx_pure)(Funções da Networkx por implementação de Python Nativo)
  - Biblioteca de referência para comparação de algoritmos
## Bibliotecas Especializadas
- pytest - Framework de testes unitários
- unittest - Testes integrados à GUI
- xml.etree.ElementTree - Parser nativo para formato GEXF
- Rest API para coleta de dados do GitHub
- GraphQL - API para coleta de status do GitHub
- Formatos de Dados Suportados
- CSV - Formato tabular para interações
- GEXF - Graph Exchange XML Format (versões 1.2 e 1.3)
- JSON - Dados da API GraphQL/Rest do GitHub
## 📊 Funcionalidades Principais
1. Gestão de Grafos
- Importação de grafos a partir de arquivos CSV e GEXF
- Exportação para formato GEXF compatível com Gephi
- Gerenciamento de múltiplos grafos em runtime
2. Visualização Interativa
- Layout force-directed (Fruchterman-Reingold)
- Zoom com scroll do mouse e botões dedicados
- Pan com botão do meio do mouse
- Scrollbars horizontal e vertical
- Arraste de nós interativo
3. Métricas de Rede
- Centralidade: Degree, Betweenness, Closeness, PageRank
- Estruturais: Densidade, Clustering Coefficient, Assortatividade
- Comunidades: Label Propagation, Modularidade, Bridging Ties
4. Algoritmos de Busca e Caminhos
- Busca em largura (BFS) e profundidade (DFS)
- Caminhos mais curtos
- Fluxo máximo
- Teste de planaridade
- Coloração de grafos - em desenvolvimento
5. Mineração de Dados
- Coleta de dados de Status repositorio do GitHub via API GraphQL
- Coleta de dados de repositorio do GitHub via API Rest
- Rate limiting para respeitar limites da API
- Checkpointing para operações longas
- Suporte a QR codes para autenticação
6. Testes Unitários
- Interface gráfica para execução de testes
- Execução de suíte completa ou categorias específicas
- Relatórios formatados em console integrado
- Suporte a pytest e unittest
## 🚀 Como Executar
### Pré-requisitos
```bash
pip install -r requirements.txt
```
### Execução da Aplicação
```bash
cd app_tp

python app.py
```

### Execução dos Testes
```bash
cd app_tp

pytest tests/
```
## 📁 Estrutura de Arquivos
```text
Rebuild_Delta/
├── app_tp/                    # Aplicação principal
│   ├── app.py                 # Ponto de entrada da GUI
│   ├── filemanager.py         # Gerenciamento de arquivos
│   ├── grafo/                 # Módulo core de grafos
│   ├── gui/                   # Interface gráfica
│   ├── miner/                 # Minerador de dados
│   ├── viz/                   # Visualização
│   ├── tests/                 # Testes unitários
│   └── CHANGELOG.md           # Histórico de mudanças
├── apresentacao/              # Materiais de apresentação
│   ├── TP_Apresentacao_Streamlit.py
│   └── diagrama_classes_PureNetworkX.mermaid
└── Rebuild_Delta.zip          # Arquivo compactado do projeto
```
## 👥 Autores
- Gabriel da Silva Cassino
- Paulo Henrique Rodrigues Neves
- Daniel Lucas Soares Madureira
- Vinicius Cezar Pereira Menezes

## Apêndice
- [Apresentação em Streamlit](https://github.com/kasshinokun/TP_Grafos_2026_1/blob/main/Gabriel_Code/Rebuild_Delta/apresentacao/TP_Apresentacao_Streamlit.py)
- [Diagrama prévio de classes](https://github.com/kasshinokun/TP_Grafos_2026_1/blob/main/Gabriel_Code/Rebuild_Delta/apresentacao/diagrama_classes_PureNetworkX.mermaid)

## 📄 Licença
Este projeto está licenciado sob a GNU General Public License v3.0.
Veja o nosso arquivo [LICENSE.md](https://github.com/kasshinokun/TP_Grafos_2026_1/blob/main/LICENSE.md) para mais detalhes.

## 📝 Notas de Implementação
### Otimizações Realizadas
- Matriz de Adjacência: get_vertex_in_degree otimizado de O(V) para O(1) usando array de contagem
- Parser GEXF: Suporte a namespaces 1.2 e 1.3, parsing de pesos de arestas
- Canvas: Zoom mantém centro da viewport, pan não interfere no arraste de nós
### Melhorias de UX
- Scrollbars adicionadas ao canvas de visualização
- Controles visuais de zoom (botões e slider)
- Tratamento gracioso de erros (ex: pytest não instalado)
- Threads workers para operações pesadas

'Projeto desenvolvido como Trabalho Prático da disciplina de Teoria dos Grafos - 2026/1'

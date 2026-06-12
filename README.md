# Análise de Redes de Colaboração em Repositórios GitHub usando Teoria dos Grafos

## 📋 Descrição

Projeto desenvolvido para a disciplina de **Teoria de Grafos e Computabilidade** do curso de Engenharia de Software da Pontifícia Universidade Católica de Minas Gerais (PUC Minas).

Este trabalho consiste no desenvolvimento de uma ferramenta computacional que processa dados estruturados como grafos, aplicando conceitos da teoria dos grafos e boas práticas de engenharia de software para análise das interações entre colaboradores em repositórios GitHub.

## 👥 Equipe

- **Vinicius Cezar Pereira Menezes**
- **Paulo Henrique Rodrigues Neves**
- **Gabriel da Silva Cassino**
- **Daniel Lucas Soares Madureira**

## 👨‍ Orientação

**Prof. Leonardo Vilela Cardoso**

## 📅 Período

2026/1

## Sobre a graduação

- Disciplina: Teoria de Grafos e Computabilidade
- Curso: Engenharia de Computação
- Instituição: PUC Minas
- Ano: 2026

## 🎯 Objetivos

- Desenvolver uma API para manipulação de grafos (direcionados e ponderados)
- Extrair e analisar dados de interações em repositórios GitHub
- Aplicar algoritmos de grafos para análise de redes de colaboração
- Calcular métricas de centralidade, estrutura e coesão da rede
- Detectar comunidades de colaboradores

## 🏗️ Estrutura do Projeto

### Etapa 1 - Modelagem e Planejamento
- Escolha do repositório GitHub (>5000 estrelas)
- Extração de dados de interações:
  - Comentários em issues e pull requests
  - Fechamento de issues
  - Revisões, aprovações e merges de pull requests
- Modelagem do grafo com pesos diferenciados por tipo de interação

### Etapa 2 - Desenvolvimento da Ferramenta
Implementação da estrutura de grafos com:
- **Classe Abstrata**: `AbstractGraph`
- **Implementações**:
  - `AdjacencyMatrixGraph` (Matriz de Adjacência)
  - `AdjacencyListGraph` (Lista de Adjacência)

**API Obrigatória**:
- Operações básicas (add/remove edges, get vertex/edge count)
- Verificações (hasEdge, isSuccessor, isPredecessor)
- Relações entre arestas (isDivergent, isConvergent, isIncident)
- Graus de vértices (in-degree, out-degree)
- Pesos de vértices e arestas
- Propriedades do grafo (isConnected, isEmpty, isComplete)
- Exportação para GEPHI

### Etapa 3 - Análise Baseada em Dados
Cálculo de métricas:

**Métricas de Centralidade**:
- Degree Centrality
- Betweenness Centrality
- Closeness Centrality
- PageRank/Eigenvector Centrality

**Métricas de Estrutura e Coesão**:
- Densidade da rede
- Coeficiente de Agrupamento (Clustering Coefficient)
- Assortatividade

**Métricas de Comunidade**:
- Detecção de comunidades (Modularidade)
- Bridging ties

## 💻 Tecnologias

- **Linguagem**: [Java/Python] *(escolher uma)*
- **Controle de Versão**: Git/GitHub
- **Documentação**: LaTeX (template SBC)
- **Visualização**: GEPHI

## 📦 Instalação e Uso

### Pré-requisitos
- Java JDK 11+
- Python 3.8+
- Git
#### Linguagem escolhida
- Python 3.14+ 

### Clonando o Repositório
```bash
git clone https://github.com/kasshinokun/TP_Grafos_2026_1/.git
cd TP_Grafos_2026_1
```
### Compilação/Execução

[Inserção de instruções específicas conforme a linguagem escolhida]

### 🧪 Testes
O projeto inclui testes unitários para:
Validação da extração de dados do GitHub
Cobertura das funcionalidades da API de grafos
Verificação de casos de uso e plano de aceitação
### 📊 Resultados

[Seção para apresentar os resultados da análise do repositório escolhido]

### 📄 Documentação
Relatório Técnico: Disponível em LaTeX no diretório /docs
Apresentação: Slides e vídeo demonstrativo
### 🚀 Como Contribuir
Este é um trabalho acadêmico. Contribuições externas não serão aceitas.
### 📝 Licença
Projeto desenvolvido para fins acadêmicos. Ainda em análise.
### 🙏 Agradecimentos
- PUC Minas - Pontifícia Universidade Católica de Minas Gerais
- Prof. Leonardo Vilela Cardoso

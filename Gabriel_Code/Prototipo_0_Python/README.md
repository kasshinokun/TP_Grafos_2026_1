# GraphAnalyzer - Engenharia de Computação (EDA Architecture)

Este projeto implementa uma ferramenta de análise de grafos utilizando **PyQt6** e uma **Arquitetura Baseada em Eventos (EDA)**. Cada parte do sistema é uma micro-aplicação independente que se comunica via um barramento de eventos central, simulando requisições de API (GET/POST).

## Alunos do Grupo
- Gabriel da Silva Cassino


## Arquitetura
- **EventBus**: Mediador central que gerencia a comunicação assíncrona.
- **DataMicroApp**: Gerencia os dados dos alunos e simula o backend.
- **GraphMicroApp**: Implementa a lógica de grafos (Lista e Matriz de Adjacência).
- **UIMicroApp**: Interface gráfica que interage com o usuário.

## Como Executar
1. Certifique-se de ter o Python 3.11+ instalado.
2. Instale as dependências:
   ```bash
   pip install PyQt6
   ```
3. Execute a aplicação principal:
   ```bash
   python main.py
   ```

## Funcionalidades Implementadas
- Listagem de alunos via `GET /students`.
- Inicialização de grafos via `POST /create_graph`.
- Consulta de estatísticas via `GET /graph_stats`.
- Estruturas de dados de grafos conforme requisitos do PDF.

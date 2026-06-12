# Minerador GitHub Otimizado (Go)

Este minerador foi desenvolvido para coletar dados de interações de repositórios do GitHub com foco em performance e conformidade com os limites da API.

## Funcionalidades
- **GraphQL-First:** Utiliza a API GraphQL para coletar grandes volumes de dados (Issues, PRs, Comentários, Reviews) em poucas chamadas.
- **Multithreading:** Suporta processamento paralelo (1-4 threads) conforme solicitado.
- **Rotação de Tokens:** Gerencia um pool de até 24 tokens com rotação automática.
- **Gestão de Rate Limit:** Detecta erros 403/429 e coloca tokens em cooldown automaticamente seguindo os headers `X-RateLimit-Reset`.
- **Filtro Temporal:** Coleta dados dos últimos 3 anos por padrão.
- **Saída Estruturada:** Gera arquivos JSON individuais para cada tipo de interação necessária para a construção de grafos.

## Arquivos de Saída (Pasta `output/`)
- `issue_comments.json`
- `issue_closures.json`
- `pull_request_comments.json`
- `pull_request_reviews.json`
- `pull_request_approvals.json`
- `pull_request_merges.json`

## Como Usar
1. Configure o arquivo `tokens.json` com seus tokens e o repositório alvo.
2. Compile o projeto:
   ```bash
   go build -o miner ./cmd/miner/main_optimized.go
   ```
3. Execute o minerador:
   ```bash
   ./miner
   ```

## Requisitos do PDF Atendidos
- Coleta de comentários em issues e PRs.
- Coleta de eventos de fechamento de issues.
- Coleta de revisões, aprovações e merges de PRs.
- Pesos sugeridos podem ser aplicados no pós-processamento dos JSONs gerados.

# Documento de Design do Minerador GitHub

## 1. Introdução
Este documento detalha o design do minerador de dados do GitHub, que será desenvolvido em Python. O minerador terá como objetivo coletar informações específicas de um repositório-alvo, utilizando as APIs REST e/ou GraphQL do GitHub, respeitando os limites de taxa (rate limits) e implementando uma estratégia robusta de rotação de tokens para otimizar a coleta de dados.

## 2. Requisitos de Dados (Conforme PDF e Solicitação do Usuário)
O minerador deverá coletar os seguintes tipos de dados, salvando cada um em um arquivo JSON separado:

- Comentários em issues (`issue_comments.json`)
- Fechamento de issues (`issue_closures.json`)
- Comentários em pull requests (`pull_request_comments.json`)
- Revisões de pull requests (`pull_request_reviews.json`)
- Aprovações de pull requests (`pull_request_approvals.json`)
- Merges de pull requests (`pull_request_merges.json`)
- Aberturas de pull requests (`pull_request_openings.json`)

## 3. Configuração do Minerador
O minerador será configurado através de um arquivo `tokens.json` que conterá:

- `GITHUB_TOKENS`: Uma lista de 1 a 24 tokens de acesso pessoal do GitHub.
- `GITHUB_USER_TARGET`: O nome de usuário do proprietário do repositório-alvo (ex: "microsoft").
- `GITHUB_REPO_TARGET`: O nome do repositório-alvo (ex: "TypeScript").

## 4. Arquitetura do Minerador
O minerador será estruturado em módulos para garantir modularidade e facilitar a manutenção:

- **`main.py`**: Ponto de entrada principal, responsável por carregar configurações, inicializar threads e coordenar o processo de mineração.
- **`config_loader.py`**: Módulo para carregar e validar o arquivo `tokens.json`.
- **`github_api_client.py`**: Módulo que encapsula as chamadas às APIs REST e GraphQL do GitHub, incluindo lógica de retry, tratamento de rate limit e rotação de tokens.
- **`data_processor.py`**: Módulo para processar e formatar os dados coletados antes de salvá-los.
- **`data_saver.py`**: Módulo para salvar os dados em arquivos JSON, garantindo a estrutura correta.
- **`thread_manager.py`**: Módulo para gerenciar o pool de threads, distribuindo as tarefas de coleta entre elas.

## 5. Estratégia de Threads
O minerador suportará de 1 a 4 threads paralelas. A estratégia será a seguinte:

- Um pool de threads será criado, com o número de threads configurável (padrão 4, ou o número de tokens disponíveis, o que for menor, limitado a 4).
- Cada thread será responsável por coletar um tipo específico de dado ou um intervalo de tempo, dependendo da granularidade da coleta.
- A distribuição de tarefas entre as threads será gerenciada para evitar conflitos e otimizar o uso dos tokens.

## 6. Gerenciamento de Tokens e Rotação
Para lidar com os limites de taxa do GitHub e garantir a continuidade da mineração, será implementada uma estratégia de rotação e escalonamento de tokens:

- **Carregamento**: Todos os tokens da lista `GITHUB_TOKENS` serão carregados e mantidos em um pool.
- **Rotação**: Cada requisição à API será feita com um token do pool. Após cada requisição, o token será liberado para ser usado por outra thread ou em uma próxima requisição.
- **Escalonamento**: Se mais de 4 tokens forem fornecidos, o minerador fará uso de todos eles, escalonando o número de tokens disponíveis para as threads. A rotação garantirá que todos os tokens sejam utilizados de forma equitativa.
- **Tratamento de Erros (403/429)**: Se uma requisição retornar um erro 403 (Forbidden) ou 429 (Too Many Requests), ou indicar que o limite de taxa foi atingido (`x-ratelimit-remaining: 0`):
    - O token atual será marcado como "esgotado" ou "em cooldown".
    - O minerador tentará usar o próximo token disponível no pool.
    - O token esgotado entrará em um período de espera (`cooldown`) baseado no cabeçalho `x-ratelimit-reset` (para rate limit primário) ou `retry-after` (para rate limit secundário) [1] [2]. Se esses cabeçalhos não estiverem presentes, um tempo de espera padrão (ex: 60 segundos) será aplicado.
    - Após o período de cooldown, o token será reintegrado ao pool de tokens disponíveis.

## 7. Tratamento de Rate Limit e Cooldown
O GitHub possui limites de taxa primários e secundários para suas APIs REST e GraphQL [1] [2]. O minerador implementará as seguintes estratégias:

- **Monitoramento**: Os cabeçalhos de resposta `x-ratelimit-limit`, `x-ratelimit-remaining`, `x-ratelimit-used` e `x-ratelimit-reset` serão monitorados para cada requisição [1] [2].
- **Espera Automática**: Antes de fazer uma requisição, o minerador verificará o `x-ratelimit-remaining` do token atual. Se for baixo, ou se o `x-ratelimit-reset` indicar que o limite será redefinido em breve, o minerador aguardará até o tempo de reset.
- **Backoff Exponencial**: Em caso de erros de rate limit (403/429) ou outros erros de rede, será implementada uma estratégia de backoff exponencial com um número máximo de retries para evitar sobrecarregar o servidor e garantir a resiliência do minerador.
- **Limites Secundários**: Os limites secundários são mais difíceis de prever. O minerador será projetado para pausar as requisições e aguardar um período de tempo (com backoff exponencial) se encontrar erros relacionados a limites secundários [1] [2].

## 8. Coleta de Dados por Tipo

### 8.1. Comentários em Issues
- **API**: REST API (`GET /repos/{owner}/{repo}/issues/{issue_number}/comments`) [3]
- **Detalhes**: Iterar sobre todas as issues do repositório e, para cada issue, coletar seus comentários. A paginação será utilizada para coletar todos os comentários.

### 8.2. Fechamento de Issues
- **API**: GraphQL API (para buscar eventos de timeline de issues) ou REST API (para eventos de issues) [4]
- **Detalhes**: A GraphQL API pode ser mais eficiente para coletar eventos de timeline, filtrando por eventos de `ClosedEvent`. A REST API também oferece endpoints para eventos de issues (`GET /repos/{owner}/{repo}/issues/{issue_number}/events`).

### 8.3. Comentários em Pull Requests
- **API**: REST API (`GET /repos/{owner}/{repo}/pulls/{pull_number}/comments`) [5]
- **Detalhes**: Similar aos comentários de issues, iterar sobre todos os pull requests e coletar seus comentários.

### 8.4. Revisões de Pull Requests
- **API**: REST API (`GET /repos/{owner}/{repo}/pulls/{pull_number}/reviews`) [6]
- **Detalhes**: Coletar todas as revisões para cada pull request.

### 8.5. Aprovações de Pull Requests
- **API**: REST API (filtrando revisões com `state: APPROVED`) [6]
- **Detalhes**: Pode ser extraído a partir dos dados de revisões de pull requests, filtrando aquelas cujo estado é 'APPROVED'.

### 8.6. Merges de Pull Requests
- **API**: GraphQL API (para eventos de timeline de PRs) ou REST API (para eventos de PRs) [4]
- **Detalhes**: A GraphQL API pode ser usada para buscar eventos de timeline de pull requests, filtrando por eventos de `MergedEvent`. A REST API também oferece endpoints para eventos de pull requests.

### 8.7. Aberturas de Pull Requests
- **API**: GraphQL API (para buscar pull requests) ou REST API (`GET /repos/{owner}/{repo}/pulls`) [7]
- **Detalhes**: Coletar os pull requests e registrar seus dados de criação.

## 9. Janela Temporal
O minerador permitirá a configuração da janela temporal de coleta:

- **Início até agora**: Coletar todos os dados disponíveis desde o primeiro registro.
- **3-5 anos atrás até agora**: Coletar dados dentro de um período específico, que será configurável (ex: `since` parameter em algumas APIs ou filtragem pós-coleta).

## 10. Estrutura de Saída JSON
Cada tipo de dado coletado será salvo em um arquivo JSON separado, com uma estrutura de lista de objetos, onde cada objeto representa um item (comentário, revisão, etc.) e seus atributos relevantes.

## 11. Referências

[1] [Rate limits for the REST API - GitHub Docs](https://docs.github.com/en/rest/using-the-rest-api/rate-limits-for-the-rest-api)
[2] [Rate limits and query limits for the GraphQL API - GitHub Docs](https://docs.github.com/en/graphql/overview/resource-limitations)
[3] [REST API endpoints for issues - GitHub Docs](https://docs.github.com/en/rest/issues)
[4] [Events - GitHub Docs](https://docs.github.com/en/rest/issues/events)
[5] [REST API endpoints for pull request review comments - GitHub Docs](https://docs.github.com/rest/pulls/comments)
[6] [REST API endpoints for pull requests - GitHub Docs](https://docs.github.com/en/rest/pulls/reviews)
[7] [REST API endpoints for pull requests - GitHub Docs](https://docs.github.com/en/rest/pulls/pulls)

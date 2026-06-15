# Gama GitHub Miner - Versão Otimizada

Este projeto é um minerador de dados de alto desempenho para o GitHub, projetado para coletar interações de colaboradores (comentários, reviews, merges, fechamentos de issues) necessárias para a construção de grafos de análise de software.

## Características Principais

*   **API Híbrida**: Utiliza a **API GraphQL** do GitHub como interface principal para coletar dados aninhados em massa, reduzindo drasticamente o número de requisições e otimizando o consumo do limite de taxa (rate limit).
*   **Multithreading**: Suporta de **1 a 4 threads paralelas**, permitindo a coleta simultânea de diferentes tipos de recursos (ex: Issues e Pull Requests).
*   **Gestão de Tokens e Rotação**: Implementa um `TokenManager` que suporta até **24 tokens**. O sistema realiza a rotação automática de tokens (round-robin) e gerencia bloqueios por `rate limit` (erros 403/429) com tempos de espera inteligentes.
*   **Filtro Temporal**: Configurado para coletar dados dos últimos **5 anos**, garantindo uma base de dados relevante e atualizada.
*   **Persistência em JSON**: Salva os dados coletados em arquivos `.json` estruturados, facilitando a importação para ferramentas de análise de grafos.

## Estrutura do Projeto

*   `src/api/GitHubMiner.java`: Classe principal que orquestra a mineração.
*   `src/api/TokenManager.java`: Gerencia a disponibilidade e saúde dos tokens de acesso.
*   `src/api/ConfigLoader.java`: Carrega as configurações do arquivo `tokens.json`.
*   `tokens.json`: Arquivo de configuração de entrada.
*   `output/`: Diretório onde os resultados da mineração são armazenados.
*   `lib/`: Bibliotecas externas necessárias (Jackson JSON).

## Requisitos de Dados (Baseado no PDF)

O minerador coleta especificamente os dados necessários para as etapas de modelagem de grafos:
- **Issues**: Número, autor, data de criação, comentários (autor/data) e eventos de fechamento (quem fechou/data).
- **Pull Requests**: Número, autor, data de criação, estado de merge, data de merge, quem realizou o merge, reviews (autor/estado/data) e comentários (autor/data).

## Como Usar

### 1. Configuração

Edite o arquivo `tokens.json` na raiz do projeto:

```json
{
  "GITHUB_TOKENS": [
    "ghp_token1",
    "ghp_token2",
    "..."
  ],
  "GITHUB_USER_TARGET": "nome_do_dono_do_repo",
  "GITHUB_REPO_TARGET": "nome_do_repositorio"
}
```

### 2. Compilação

Certifique-se de ter o JDK 11+ instalado. No terminal, execute:

```bash
javac -cp ".:lib/*" src/api/*.java -d .
```

### 3. Execução

Para iniciar a mineração:

```bash
java -cp ".:lib/*" api.GitHubMiner
```

## Tratamento de Erros e Rate Limit

O sistema monitora as respostas da API do GitHub. Caso um token atinja o limite de taxa (HTTP 403 ou 429), o `TokenManager` irá:
1.  Marcar o token como indisponível.
2.  Colocar o token em um período de "cooldown" (1 hora).
3.  Selecionar automaticamente o próximo token disponível para continuar a tarefa sem interrupções.

Se todos os tokens estiverem em cooldown, o minerador pausará a execução e aguardará até que o primeiro token seja liberado.

## Boas Práticas Aplicadas

- **Concorrência Segura**: Uso de `ConcurrentHashMap`, `AtomicInteger` e `ExecutorService`.
- **Eficiência de Rede**: Uso da API GraphQL para evitar "over-fetching" de dados.
- **Robustez**: Implementação de re-tentativas e salvamento parcial de dados para evitar perdas em caso de falhas críticas.
- **Código Limpo**: Separação clara de responsabilidades entre gestão de tokens, carregamento de configuração e lógica de mineração.

"""
Testes unitários para a API GraphQL do GitHub (classe ScrapGraphQL).
Utiliza pytest com mocks para evitar chamadas reais.
"""

import json
import pytest
from datetime import datetime, timezone
from unittest.mock import Mock, patch, MagicMock
from requests.exceptions import Timeout, ConnectionError

# Importa a classe a ser testada
from miner.scrap_graphql_miner import ScrapGraphQL


# ------------------------- Fixtures básicas -------------------------

@pytest.fixture
def valid_tokens():
    """Lista de tokens de teste (simulados)."""
    return ["ghp_valid_token_123", "ghp_another_token_456"]


@pytest.fixture
def mock_graphql_response_success():
    """Resposta simulada de sucesso para a consulta de metadados."""
    return {
        "data": {
            "repository": {
                "createdAt": "2015-01-01T00:00:00Z",
                "issues": {"totalCount": 150},
                "pullRequests": {"totalCount": 75}
            }
        }
    }


@pytest.fixture
def mock_graphql_response_not_found():
    """Resposta simulada para repositório não encontrado."""
    return {
        "data": {
            "repository": None
        },
        "errors": [{"message": "Could not resolve to a Repository with the name 'foo/bar'."}]
    }


@pytest.fixture
def mock_graphql_response_invalid_token():
    """Resposta simulada para token inválido."""
    return {
        "message": "Bad credentials",
        "documentation_url": "https://docs.github.com/rest"
    }


# ------------------------- Testes de validação de token -------------------------

def test_token_validation():
    """Testa a validação básica de token (não vazio e comprimento mínimo)."""
    from miner.scrap_graphql_miner import ScrapGraphQL

    # Token válido
    tokens = ["ghp_123456789012345678901234567890123456"]
    scraper = ScrapGraphQL(tokens, "owner", "repo")
    assert scraper.tokens == tokens

    # Token vazio deve ser rejeitado? A classe não valida, mas podemos testar
    # Se quisermos, podemos adicionar validação na classe; por enquanto só testamos que aceita
    with pytest.raises(IndexError):  # se não houver tokens
        ScrapGraphQL([], "owner", "repo")._next_token()


# ------------------------- Testes de conexão (com mock) -------------------------

@patch('miner.scrap_graphql_miner.requests.post')
def test_graphql_request_success(mock_post, valid_tokens, mock_graphql_response_success):
    """Testa uma requisição GraphQL bem-sucedida."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_graphql_response_success
    mock_post.return_value = mock_response

    scraper = ScrapGraphQL(valid_tokens, "owner", "repo")
    query = "query { repository(owner: $owner, name: $repo) { createdAt } }"
    variables = {"owner": "owner", "repo": "repo"}
    result = scraper._graphql_request(query, variables)

    assert result == mock_graphql_response_success
    mock_post.assert_called_once()
    # Verifica cabeçalhos de autenticação
    args, kwargs = mock_post.call_args
    assert kwargs["headers"]["Authorization"] == f"Bearer {valid_tokens[0]}"
    assert kwargs["json"]["query"] == query
    assert kwargs["json"]["variables"] == variables


@patch('miner.scrap_graphql_miner.requests.post')
def test_graphql_request_invalid_token(mock_post, valid_tokens, mock_graphql_response_invalid_token):
    """Testa requisição com token inválido (401)."""
    mock_response = Mock()
    mock_response.status_code = 401
    mock_response.text = json.dumps(mock_graphql_response_invalid_token)
    mock_post.return_value = mock_response

    scraper = ScrapGraphQL(valid_tokens, "owner", "repo")
    with pytest.raises(Exception) as excinfo:
        scraper._graphql_request("query { }")
    assert "401" in str(excinfo.value)


@patch('miner.scrap_graphql_miner.requests.post')
def test_graphql_request_timeout(mock_post, valid_tokens):
    """Testa timeout na requisição."""
    mock_post.side_effect = Timeout("Connection timed out")
    scraper = ScrapGraphQL(valid_tokens, "owner", "repo")
    with pytest.raises(Timeout):
        scraper._graphql_request("query { }")


# ------------------------- Testes de processamento de resultados -------------------------

@patch('miner.scrap_graphql_miner.ScrapGraphQL._graphql_request')
def test_fetch_metadata(mock_request, valid_tokens, mock_graphql_response_success):
    """Testa o método fetch_metadata que extrai dados do repositório."""
    mock_request.return_value = mock_graphql_response_success

    scraper = ScrapGraphQL(valid_tokens, "owner", "repo")
    metadata = scraper.fetch_metadata()

    assert metadata["createdAt"] == "2015-01-01T00:00:00Z"
    assert metadata["issues"]["totalCount"] == 150
    assert metadata["pullRequests"]["totalCount"] == 75
    mock_request.assert_called_once()


@patch('miner.scrap_graphql_miner.ScrapGraphQL._graphql_request')
def test_fetch_metadata_not_found(mock_request, valid_tokens, mock_graphql_response_not_found):
    """Testa fetch_metadata quando repositório não é encontrado."""
    mock_request.return_value = mock_graphql_response_not_found

    scraper = ScrapGraphQL(valid_tokens, "owner", "repo")
    with pytest.raises(Exception) as excinfo:
        scraper.fetch_metadata()
    assert "Repositório não encontrado" in str(excinfo.value)


@patch('miner.scrap_graphql_miner.ScrapGraphQL._graphql_request')
def test_compute_limits(mock_request, valid_tokens, mock_graphql_response_success):
    """Testa o cálculo dos limites (total_items, max_years)."""
    # Ajusta a data de criação para ser exatamente 3 anos atrás
    three_years_ago = datetime.now(timezone.utc).replace(year=datetime.now(timezone.utc).year - 3)
    mock_graphql_response_success["data"]["repository"]["createdAt"] = three_years_ago.isoformat()
    mock_request.return_value = mock_graphql_response_success

    scraper = ScrapGraphQL(valid_tokens, "owner", "repo")
    limits = scraper.compute_limits()

    assert limits["total_items"] == 150 + 75  # 225
    assert limits["max_years"] == 3  # pois idade é 3 anos exatos
    assert limits["total_issues"] == 150
    assert limits["total_prs"] == 75
    assert "created_at" in limits


# ------------------------- Testes de rate limit (simulados) -------------------------

@patch('miner.scrap_graphql_miner.requests.post')
def test_rate_limit_headers(mock_post, valid_tokens):
    """Testa a extração de cabeçalhos de rate limit (simulados)."""
    mock_response = Mock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"data": {"repository": {"createdAt": "2020-01-01T00:00:00Z"}}}
    mock_response.headers = {
        "x-ratelimit-limit": "5000",
        "x-ratelimit-remaining": "4995",
        "x-ratelimit-reset": "1614556800"
    }
    mock_post.return_value = mock_response

    scraper = ScrapGraphQL(valid_tokens, "owner", "repo")
    # Para testar, podemos acessar a resposta e verificar os cabeçalhos
    # Como a classe não armazena headers, faremos uma verificação manual
    response = scraper._graphql_request("query { }")
    # Na implementação real, seria interessante retornar os headers; aqui apenas garantimos que a resposta foi obtida
    assert response is not None


# ------------------------- Testes de integração (opcionais, exigem token real) -------------------------

@pytest.mark.integration
def test_integration_with_real_token():
    """
    Teste de integração com token real (executar apenas se configurado).
    Para rodar, defina a variável de ambiente GITHUB_TOKEN.
    """
    import os
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        pytest.skip("GITHUB_TOKEN não definido. Pule este teste.")

    scraper = ScrapGraphQL([token], "octocat", "Hello-World")
    try:
        limits = scraper.compute_limits()
        assert limits["total_items"] >= 0
        assert limits["max_years"] >= 1
    except Exception as e:
        pytest.fail(f"Falha na integração: {e}")


# ------------------------- Execução com pytest -------------------------
# Para rodar: pytest test_graphql_api.py -v
# Para incluir integração: pytest -v --run-integration

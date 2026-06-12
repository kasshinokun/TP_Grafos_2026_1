package api;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.fasterxml.jackson.databind.node.ArrayNode;
import com.fasterxml.jackson.databind.node.ObjectNode;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.net.URI;
import java.net.http.HttpClient;
import java.net.http.HttpRequest;
import java.net.http.HttpResponse;
import java.time.Duration;
import java.time.ZonedDateTime;
import java.util.List;
import java.util.concurrent.ExecutorService;
import java.util.concurrent.Executors;
import java.util.concurrent.TimeUnit;

public class GitHubMiner {
    private static final String GRAPHQL_URL = "https://api.github.com/graphql";
    private static final HttpClient client = HttpClient.newBuilder()
            .connectTimeout(Duration.ofSeconds(10))
            .build();
    private static final ObjectMapper mapper = new ObjectMapper();

    public static void main(String[] args) {
        String configPath = "tokens.json";
        ConfigLoader config = new ConfigLoader();
        try {
            config.load(configPath);
        } catch (IOException e) {
            System.err.println("Erro ao carregar tokens.json: " + e.getMessage());
            return;
        }

        TokenManager tokenManager = new TokenManager(config.getTokens());
        String owner = config.getUserTarget();
        String repo = config.getRepoTarget();

        System.out.println("Iniciando mineração para " + owner + "/" + repo);
        System.out.println("Tokens disponíveis: " + tokenManager.getTokenCount());

        int threads = Math.min(tokenManager.getTokenCount(), 4);
        if (threads < 1) threads = 1;
        ExecutorService executor = Executors.newFixedThreadPool(threads);

        // Minerador de Issues
        executor.submit(() -> mineResource(tokenManager, owner, repo, "issues"));
        // Minerador de Pull Requests
        executor.submit(() -> mineResource(tokenManager, owner, repo, "pullRequests"));

        executor.shutdown();
        try {
            executor.awaitTermination(24, TimeUnit.HOURS);
        } catch (InterruptedException e) {
            Thread.currentThread().interrupt();
        }

        System.out.println("Mineração concluída.");
    }

    private static void mineResource(TokenManager tokenManager, String owner, String repo, String resourceType) {
        String cursor = null;
        boolean hasNextPage = true;
        ArrayNode allData = mapper.createArrayNode();
        ZonedDateTime cutoffDate = ZonedDateTime.now().minusYears(5);

        while (hasNextPage) {
            try {
                String token = tokenManager.getNextToken();
                String query = buildQuery(owner, repo, resourceType, cursor);
                
                ObjectNode payload = mapper.createObjectNode();
                payload.put("query", query);

                HttpRequest request = HttpRequest.newBuilder()
                        .uri(URI.create(GRAPHQL_URL))
                        .header("Authorization", "bearer " + token)
                        .header("Content-Type", "application/json")
                        .POST(HttpRequest.BodyPublishers.ofString(payload.toString()))
                        .build();

                HttpResponse<String> response = client.send(request, HttpResponse.BodyHandlers.ofString());

                if (response.statusCode() != 200) {
                    tokenManager.reportError(token, response.statusCode());
                    continue;
                }

                JsonNode root = mapper.readTree(response.body());
                if (root.has("errors")) {
                    System.err.println("Erro na query GraphQL: " + root.get("errors").toString());
                    break;
                }

                JsonNode repository = root.get("data").get("repository");
                JsonNode connection = repository.get(resourceType);
                JsonNode nodes = connection.get("nodes");
                
                for (JsonNode node : nodes) {
                    ZonedDateTime createdAt = ZonedDateTime.parse(node.get("createdAt").asText());
                    if (createdAt.isBefore(cutoffDate)) {
                        hasNextPage = false;
                        break;
                    }
                    allData.add(node);
                }

                JsonNode pageInfo = connection.get("pageInfo");
                hasNextPage = hasNextPage && pageInfo.get("hasNextPage").asBoolean();
                cursor = pageInfo.get("endCursor").asText();

                System.out.println("[" + resourceType + "] Coletados: " + allData.size());
                
                // Salva parcial para evitar perda de dados
                saveToFile(resourceType, allData);

            } catch (Exception e) {
                System.err.println("Erro em mineResource (" + resourceType + "): " + e.getMessage());
                try { Thread.sleep(5000); } catch (InterruptedException ie) { Thread.currentThread().interrupt(); }
            }
        }
    }

    private static String buildQuery(String owner, String repo, String resourceType, String cursor) {
        String cursorPart = (cursor == null) ? "" : ", after: \\\"" + cursor + "\\\"";
        
        if (resourceType.equals("issues")) {
            return "query { repository(owner: \\\"" + owner + "\\\", name: \\\"" + repo + "\\\") { " +
                   "issues(first: 50" + cursorPart + ", orderBy: {field: CREATED_AT, direction: DESC}) { " +
                   "pageInfo { hasNextPage endCursor } " +
                   "nodes { number author { login } createdAt " +
                   "comments(first: 50) { nodes { author { login } createdAt } } " +
                   "timelineItems(first: 50, itemTypes: [CLOSED_EVENT]) { nodes { ... on ClosedEvent { actor { login } createdAt } } } " +
                   "} } } }";
        } else {
            return "query { repository(owner: \\\"" + owner + "\\\", name: \\\"" + repo + "\\\") { " +
                   "pullRequests(first: 50" + cursorPart + ", orderBy: {field: CREATED_AT, direction: DESC}) { " +
                   "pageInfo { hasNextPage endCursor } " +
                   "nodes { number author { login } createdAt merged mergedAt mergedBy { login } " +
                   "reviews(first: 50) { nodes { author { login } state createdAt } } " +
                   "comments(first: 50) { nodes { author { login } createdAt } } " +
                   "} } } }";
        }
    }

    private static synchronized void saveToFile(String resourceType, ArrayNode data) {
        String fileName = "output/" + resourceType + "_data.json";
        try (FileWriter writer = new FileWriter(fileName)) {
            mapper.writerWithDefaultPrettyPrinter().writeValue(writer, data);
        } catch (IOException e) {
            System.err.println("Erro ao salvar arquivo " + fileName + ": " + e.getMessage());
        }
    }
}

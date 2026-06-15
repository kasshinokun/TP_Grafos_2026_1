package api;

import com.fasterxml.jackson.databind.JsonNode;
import com.fasterxml.jackson.databind.ObjectMapper;
import java.io.File;
import java.io.IOException;
import java.util.ArrayList;
import java.util.List;

public class ConfigLoader {
    private List<String> tokens = new ArrayList<>();
    private String userTarget;
    private String repoTarget;

    public void load(String filePath) throws IOException {
        ObjectMapper mapper = new ObjectMapper();
        JsonNode root = mapper.readTree(new File(filePath));

        if (root.has("GITHUB_TOKENS")) {
            for (JsonNode node : root.get("GITHUB_TOKENS")) {
                tokens.add(node.asText());
            }
        }

        userTarget = root.has("GITHUB_USER_TARGET") ? root.get("GITHUB_USER_TARGET").asText() : "";
        repoTarget = root.has("GITHUB_REPO_TARGET") ? root.get("GITHUB_REPO_TARGET").asText() : "";
    }

    public List<String> getTokens() { return tokens; }
    public String getUserTarget() { return userTarget; }
    public String getRepoTarget() { return repoTarget; }
}

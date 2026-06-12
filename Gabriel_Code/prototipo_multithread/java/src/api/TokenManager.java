package api;

import java.util.*;
import java.util.concurrent.*;
import java.util.concurrent.atomic.AtomicInteger;

public class TokenManager {
    private final List<String> tokens;
    private final Map<String, Long> cooldowns = new ConcurrentHashMap<>();
    private final AtomicInteger currentIndex = new AtomicInteger(0);
    private static final long SECONDARY_RATE_LIMIT_DELAY = 2000; // 2 segundos entre trocas para evitar detecção de abuso

    public TokenManager(List<String> tokens) {
        this.tokens = new ArrayList<>(tokens);
    }

    public synchronized String getNextToken() throws InterruptedException {
        int startIdx = currentIndex.get();
        int size = tokens.size();

        for (int i = 0; i < size; i++) {
            int idx = (startIdx + i) % size;
            String token = tokens.get(idx);
            Long cooldown = cooldowns.get(token);

            if (cooldown == null || System.currentTimeMillis() >= cooldown) {
                currentIndex.set((idx + 1) % size);
                return token;
            }
        }

        // Se todos estiverem em cooldown, espera pelo que vai liberar primeiro
        long minWait = Long.MAX_VALUE;
        for (Long cd : cooldowns.values()) {
            minWait = Math.min(minWait, cd - System.currentTimeMillis());
        }

        if (minWait > 0 && minWait != Long.MAX_VALUE) {
            System.out.println("[TokenManager] Todos os tokens em cooldown. Aguardando " + (minWait / 1000) + " segundos...");
            Thread.sleep(minWait + 1000);
            return getNextToken();
        }

        return tokens.get(0); // Fallback
    }

    public void reportError(String token, int statusCode) {
        if (statusCode == 403 || statusCode == 429) {
            long waitTime = 3600 * 1000; // 1 hora padrão para rate limit primário
            System.err.println("[TokenManager] Token bloqueado (Erro " + statusCode + "): " + maskToken(token));
            cooldowns.put(token, System.currentTimeMillis() + waitTime);
        }
    }

    private String maskToken(String token) {
        if (token == null || token.length() < 8) return "***";
        return token.substring(0, 4) + "..." + token.substring(token.length() - 4);
    }

    public int getTokenCount() {
        return tokens.size();
    }
}

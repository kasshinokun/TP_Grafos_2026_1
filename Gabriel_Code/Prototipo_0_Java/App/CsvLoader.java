package br.pucminas.grafo.mining;

import java.io.*;
import java.util.*;

/**
 * Carrega interações de um arquivo CSV.
 *
 * <h3>Formato esperado (com cabeçalho):</h3>
 * <pre>
 *   actor,target,type
 *   alice,bob,COMMENT_ON_ISSUE_OR_PR
 *   charlie,alice,PR_MERGE
 * </pre>
 *
 * O campo {@code type} deve corresponder a um valor do enum
 * {@link Interaction.InteractionType} (case-insensitive).
 *
 * <h3>Formato alternativo (sem coluna type):</h3>
 * <pre>
 *   actor,target
 * </pre>
 * Nesse caso, o tipo padrão {@code COMMENT_ON_ISSUE_OR_PR} é assumido.
 */
public class CsvLoader {

    /**
     * Lê o arquivo CSV e retorna a lista de interações.
     *
     * @param path caminho para o arquivo CSV
     * @return lista de interações carregadas
     * @throws IOException se o arquivo não puder ser lido
     */
    public static List<Interaction> load(String path) throws IOException {
        List<Interaction> list = new ArrayList<>();
        try (BufferedReader br = new BufferedReader(new FileReader(path))) {
            String header = br.readLine();
            if (header == null) return list;

            String[] cols = header.toLowerCase().split(",");
            int actorIdx  = indexOf(cols, "actor");
            int targetIdx = indexOf(cols, "target");
            int typeIdx   = indexOf(cols, "type");

            if (actorIdx < 0 || targetIdx < 0)
                throw new IllegalArgumentException(
                    "CSV deve ter colunas 'actor' e 'target'. Cabeçalho: " + header);

            String line;
            int lineNo = 1;
            while ((line = br.readLine()) != null) {
                lineNo++;
                line = line.trim();
                if (line.isEmpty() || line.startsWith("#")) continue;
                String[] parts = line.split(",", -1);
                if (parts.length <= Math.max(actorIdx, targetIdx)) {
                    System.err.println("[CSV] Linha " + lineNo + " ignorada (colunas insuficientes): " + line);
                    continue;
                }
                String actor  = parts[actorIdx].trim();
                String target = parts[targetIdx].trim();
                if (actor.isEmpty() || target.isEmpty() || actor.equals(target)) continue;

                Interaction.InteractionType type = Interaction.InteractionType.COMMENT_ON_ISSUE_OR_PR;
                if (typeIdx >= 0 && parts.length > typeIdx) {
                    String raw = parts[typeIdx].trim().toUpperCase();
                    try { type = Interaction.InteractionType.valueOf(raw); }
                    catch (IllegalArgumentException e) {
                        System.err.println("[CSV] Tipo desconhecido '" + raw + "' na linha " + lineNo + ". Usando padrão.");
                    }
                }
                list.add(new Interaction(actor, target, type));
            }
        }
        return list;
    }

    // ── Gerador de CSV de exemplo ──────────────────────────────────────────

    /**
     * Gera um CSV de exemplo com interações simuladas.
     * Útil para testar sem acesso à API do GitHub.
     */
    public static void generateSampleCsv(String path) throws IOException {
        String[] users = {"alice", "bob", "carol", "dave", "eve",
                          "frank", "grace", "hank", "iris", "jack"};
        Interaction.InteractionType[] types = Interaction.InteractionType.values();
        Random rnd = new Random(42);

        try (PrintWriter pw = new PrintWriter(new FileWriter(path))) {
            pw.println("actor,target,type");
            for (int i = 0; i < 120; i++) {
                String actor  = users[rnd.nextInt(users.length)];
                String target;
                do { target = users[rnd.nextInt(users.length)]; } while (target.equals(actor));
                Interaction.InteractionType t = types[rnd.nextInt(types.length)];
                pw.println(actor + "," + target + "," + t.name());
            }
        }
    }

    private static int indexOf(String[] arr, String key) {
        for (int i = 0; i < arr.length; i++)
            if (arr[i].trim().equals(key)) return i;
        return -1;
    }
}

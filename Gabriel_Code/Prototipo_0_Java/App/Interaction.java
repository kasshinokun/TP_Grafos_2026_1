package br.pucminas.grafo.mining;

/**
 * Representa uma interação bruta extraída de dados do GitHub.
 *
 * Campos:
 *  - actor  : usuário que realizou a ação
 *  - target : usuário alvo (autor do issue/PR, revisor, etc.)
 *  - type   : tipo da interação (ver {@link InteractionType})
 */
public class Interaction {

    public enum InteractionType {
        /** Comentário em issue ou pull request (peso 2) */
        COMMENT_ON_ISSUE_OR_PR(2),
        /** Fechamento de issue por outro usuário (peso 3) */
        ISSUE_CLOSED_BY_OTHER(3),
        /** Revisão/aprovação de pull request (peso 4) */
        PR_REVIEW_OR_APPROVAL(4),
        /** Merge de pull request (peso 5) */
        PR_MERGE(5);

        public final int weight;
        InteractionType(int w) { this.weight = w; }
    }

    public final String          actor;
    public final String          target;
    public final InteractionType type;

    public Interaction(String actor, String target, InteractionType type) {
        this.actor  = actor;
        this.target = target;
        this.type   = type;
    }

    @Override
    public String toString() {
        return actor + " --[" + type + "]--> " + target;
    }
}

package br.pucminas.grafo;

import br.pucminas.grafo.cli.CLI;
import br.pucminas.grafo.core.Application;

/**
 * Ponto de entrada da aplicação monolítica de análise de grafos.
 *
 * <p>
 * Instancia a {@link Application} (que monta toda a arquitetura EDA)
 * e entrega o controle ao {@link CLI}.
 * </p>
 */
public class Main {

    public static void main(String[] args) {
        Application app = new Application();
        CLI cli = new CLI(app);
        cli.run();
    }
}

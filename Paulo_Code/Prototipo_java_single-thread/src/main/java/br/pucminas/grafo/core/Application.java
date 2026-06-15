package br.pucminas.grafo.core;

import br.pucminas.grafo.events.EventBus;
import br.pucminas.grafo.graph.mining.MiningHandler;
import br.pucminas.grafo.handlers.*;

/**
 * Raiz de composição da aplicação.
 *
 * <p>
 * Instancia todos os componentes, registra os handlers no EventBus
 * e expõe o bus para uso externo (CLI, testes, etc.).
 * </p>
 */
public class Application {

    private final EventBus bus;
    private final GraphRegistry registry;

    // handlers (mantidos como campos para possível re-registro futuro)
    private final GraphHandler graphHandler;
    private final AlgorithmHandler algorithmHandler;
    private final MetricsHandler metricsHandler;
    private final MiningHandler miningHandler;

    public Application() {
        this.registry = new GraphRegistry();
        this.bus = new EventBus();

        this.graphHandler = new GraphHandler(registry);
        this.algorithmHandler = new AlgorithmHandler(registry);
        this.metricsHandler = new MetricsHandler(registry);
        this.miningHandler = new MiningHandler(registry);

        // Registra todos os handlers no bus
        graphHandler.registerAll(bus);
        algorithmHandler.registerAll(bus);
        metricsHandler.registerAll(bus);
        miningHandler.registerAll(bus);
    }

    public EventBus getBus() {
        return bus;
    }

    public GraphRegistry getRegistry() {
        return registry;
    }
}

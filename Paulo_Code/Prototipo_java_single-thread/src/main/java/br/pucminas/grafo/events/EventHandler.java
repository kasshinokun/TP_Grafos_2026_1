package br.pucminas.grafo.events;

/**
 * Contrato de todo handler registrado no EventBus.
 */
@FunctionalInterface
public interface EventHandler {
    void handle(Event event);
}

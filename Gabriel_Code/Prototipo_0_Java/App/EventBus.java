package br.pucminas.grafo.core;

import br.pucminas.grafo.events.Event;
import br.pucminas.grafo.events.EventHandler;
import br.pucminas.grafo.events.EventType;

import java.util.*;
import java.util.logging.Logger;

/**
 * Event Bus síncrono in-process.
 *
 * <p>Cada tipo de evento pode ter múltiplos handlers. A publicação é
 * síncrona (request–response): o chamador bloqueia até todos os
 * handlers concluírem e recebe o evento de volta com o resultado
 * preenchido — simulando uma chamada de API interna.</p>
 *
 * <pre>
 *   Event ev = bus.publish(new Event(EventType.GRAPH_ADD_EDGE)
 *                              .with("graphId", "g1")
 *                              .with("u", 0).with("v", 1));
 *   if (ev.isSuccess()) { ... }
 * </pre>
 */
public class EventBus {

    private static final Logger LOG = Logger.getLogger(EventBus.class.getName());

    /** Mapa de tipo → lista de handlers (ordem de registro preservada). */
    private final Map<EventType, List<EventHandler>> handlers = new EnumMap<>(EventType.class);

    // ── Registro ───────────────────────────────────────────────────────────

    public void subscribe(EventType type, EventHandler handler) {
        handlers.computeIfAbsent(type, k -> new ArrayList<>()).add(handler);
    }

    public void unsubscribe(EventType type, EventHandler handler) {
        List<EventHandler> list = handlers.get(type);
        if (list != null) list.remove(handler);
    }

    // ── Publicação ─────────────────────────────────────────────────────────

    /**
     * Publica um evento de forma síncrona.
     * Retorna o mesmo evento com resultado / erro preenchidos.
     */
    public Event publish(Event event) {
        List<EventHandler> list = handlers.getOrDefault(event.getType(), Collections.emptyList());
        if (list.isEmpty()) {
            LOG.warning("Nenhum handler registrado para: " + event.getType());
            event.setError("Nenhum handler para o evento: " + event.getType());
            return event;
        }
        for (EventHandler h : list) {
            try {
                h.handle(event);
                if (!event.isSuccess()) break; // interrompe cadeia em erro
            } catch (Exception ex) {
                event.setError(ex.getMessage());
                LOG.severe("Handler falhou para " + event.getType() + ": " + ex.getMessage());
                break;
            }
        }
        return event;
    }

    /** Atalho de fábrica para criar e publicar em uma linha. */
    public Event dispatch(EventType type) {
        return publish(new Event(type));
    }
}

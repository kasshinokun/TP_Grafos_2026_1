package br.pucminas.grafo.events;

import java.time.Instant;
import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/**
 * Envelope de evento que trafega pelo Event Bus.
 * Funciona como um "request/response" de API interna.
 */
public class Event {

    private final String id;
    private final EventType type;
    private final Map<String, Object> payload;
    private final Instant timestamp;

    // Campo de resposta preenchido pelo handler
    private Object result;
    private boolean success;
    private String errorMessage;

    public Event(EventType type) {
        this.id = UUID.randomUUID().toString();
        this.type = type;
        this.payload = new HashMap<>();
        this.timestamp = Instant.now();
        this.success = true;
    }

    // ── Builder fluente ────────────────────────────────────────────────────

    public Event with(String key, Object value) {
        payload.put(key, value);
        return this;
    }

    @SuppressWarnings("unchecked")
    public <T> T get(String key) {
        return (T) payload.get(key);
    }

    public Integer getInt(String key) {
        Object v = payload.get(key);
        if (v instanceof Integer i) return i;
        if (v instanceof String s)   return Integer.parseInt(s);
        return null;
    }

    public Double getDouble(String key) {
        Object v = payload.get(key);
        if (v instanceof Double d)  return d;
        if (v instanceof String s)  return Double.parseDouble(s);
        return null;
    }

    public String getString(String key) {
        Object v = payload.get(key);
        return v == null ? null : v.toString();
    }

    public Boolean getBoolean(String key) {
        Object v = payload.get(key);
        if (v instanceof Boolean b) return b;
        if (v instanceof String s)  return Boolean.parseBoolean(s);
        return null;
    }

    // ── Resposta ───────────────────────────────────────────────────────────

    public void setResult(Object result) {
        this.result = result;
    }

    public void setError(String message) {
        this.success = false;
        this.errorMessage = message;
    }

    @SuppressWarnings("unchecked")
    public <T> T getResult() {
        return (T) result;
    }

    // ── Getters ────────────────────────────────────────────────────────────

    public String getId()            { return id; }
    public EventType getType()       { return type; }
    public Instant getTimestamp()    { return timestamp; }
    public boolean isSuccess()       { return success; }
    public String getErrorMessage()  { return errorMessage; }
    public Map<String, Object> getPayload() { return payload; }

    @Override
    public String toString() {
        return "Event{id=" + id + ", type=" + type + ", success=" + success + "}";
    }
}

package auth

import (
	"sync"
	"time"
)

type TokenState struct {
	Token         string
	CooldownUntil time.Time
	Remaining     int
	ResetAt       time.Time
}

type Manager struct {
	mu     sync.Mutex
	tokens []*TokenState
	idx    int
}

func New(tokens []string) *Manager {
	m := &Manager{}
	for _, t := range tokens {
		m.tokens = append(m.tokens, &TokenState{
			Token:     t,
			Remaining: 5000, // Valor padrão inicial para REST
		})
	}
	return m
}

func (m *Manager) GetToken() *TokenState {
	m.mu.Lock()
	defer m.mu.Unlock()

	if len(m.tokens) == 0 {
		return nil
	}

	startIdx := m.idx
	for {
		t := m.tokens[m.idx%len(m.tokens)]
		m.idx++

		if time.Now().After(t.CooldownUntil) {
			return t
		}

		// Se voltamos ao início e todos estão em cooldown
		if m.idx%len(m.tokens) == startIdx%len(m.tokens) {
			// Encontrar o que volta mais cedo
			earliest := m.tokens[0]
			for _, token := range m.tokens {
				if token.CooldownUntil.Before(earliest.CooldownUntil) {
					earliest = token
				}
			}
			
			// Dormir até o earliest estar disponível se necessário, 
			// mas aqui apenas retornamos o melhor candidato ou esperamos externamente.
			// Para simplicidade do worker, retornamos o earliest e deixamos o client lidar.
			return earliest
		}
	}
}

func (m *Manager) ReportRateLimit(token string, resetAt time.Time) {
	m.mu.Lock()
	defer m.mu.Unlock()
	for _, t := range m.tokens {
		if t.Token == token {
			t.CooldownUntil = resetAt
			t.Remaining = 0
			break
		}
	}
}

func (m *Manager) ReportError(token string, duration time.Duration) {
	m.mu.Lock()
	defer m.mu.Unlock()
	for _, t := range m.tokens {
		if t.Token == token {
			t.CooldownUntil = time.Now().Add(duration)
			break
		}
	}
}

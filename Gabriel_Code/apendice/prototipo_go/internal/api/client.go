package api

import (
	"bytes"
	"encoding/json"
	"fmt"
	"io"
	"net/http"
	"strconv"
	"time"

	"github-miner/internal/auth"
)

type Client struct {
	tokenManager *auth.Manager
	httpClient   *http.Client
}

func NewClient(tm *auth.Manager) *Client {
	return &Client{
		tokenManager: tm,
		httpClient: &http.Client{
			Timeout: 30 * time.Second,
		},
	}
}

func (c *Client) DoRequest(method, url string, body []byte) ([]byte, http.Header, error) {
	var lastErr error
	for retries := 0; retries < 3; retries++ {
		ts := c.tokenManager.GetToken()
		if ts == nil {
			return nil, nil, fmt.Errorf("no tokens available")
		}

		// Esperar se o token ainda estiver em cooldown
		now := time.Now()
		if ts.CooldownUntil.After(now) {
			time.Sleep(time.Until(ts.CooldownUntil))
		}

		req, err := http.NewRequest(method, url, bytes.NewBuffer(body))
		if err != nil {
			return nil, nil, err
		}

		req.Header.Set("Authorization", "Bearer "+ts.Token)
		req.Header.Set("Accept", "application/vnd.github.v3+json")
		req.Header.Set("User-Agent", "GitHub-Miner-Go")

		resp, err := c.httpClient.Do(req)
		if err != nil {
			lastErr = err
			time.Sleep(time.Duration(retries+1) * time.Second)
			continue
		}
		defer resp.Body.Close()

		// Atualizar info de rate limit
		if remaining := resp.Header.Get("X-RateLimit-Remaining"); remaining != "" {
			rem, _ := strconv.Atoi(remaining)
			ts.Remaining = rem
		}
		if reset := resp.Header.Get("X-RateLimit-Reset"); reset != "" {
			res, _ := strconv.ParseInt(reset, 10, 64)
			ts.ResetAt = time.Unix(res, 0)
		}

		if resp.StatusCode == http.StatusForbidden || resp.StatusCode == http.StatusTooManyRequests {
			resetAt := ts.ResetAt
			if resetAt.IsZero() || resetAt.Before(time.Now()) {
				resetAt = time.Now().Add(1 * time.Minute)
			}
			c.tokenManager.ReportRateLimit(ts.Token, resetAt)
			continue
		}

		if resp.StatusCode >= 400 {
			lastErr = fmt.Errorf("status code %d: %s", resp.StatusCode, url)
			if resp.StatusCode == http.StatusUnauthorized {
				c.tokenManager.ReportError(ts.Token, 24*time.Hour) // Token inválido
			}
			continue
		}

		data, err := io.ReadAll(resp.Body)
		return data, resp.Header, err
	}
	return nil, nil, lastErr
}

func (c *Client) GraphQL(query string, variables map[string]interface{}) ([]byte, error) {
	payload := map[string]interface{}{
		"query":     query,
		"variables": variables,
	}
	body, _ := json.Marshal(payload)
	data, _, err := c.DoRequest("POST", "https://api.github.com/graphql", body)
	return data, err
}

func (c *Client) RestGet(url string) ([]byte, http.Header, error) {
	return c.DoRequest("GET", url, nil)
}

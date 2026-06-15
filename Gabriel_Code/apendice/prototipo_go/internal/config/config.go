package config

import (
	"encoding/json"
	"os"
)

type Config struct {
	GithubTokens     []string `json:"GITHUB_TOKENS"`
	GithubUserTarget string   `json:"GITHUB_USER_TARGET"`
	GithubRepoTarget string   `json:"GITHUB_REPO_TARGET"`
}

func Load(path string) (*Config, error) {
	b, err := os.ReadFile(path)
	if err != nil {
		return nil, err
	}
	var c Config
	err = json.Unmarshal(b, &c)
	if err != nil {
		return nil, err
	}
	return &c, nil
}

package main

import (
	"encoding/json"
	"fmt"
	"log"
	"os"
	"sync"
	"time"

	"github-miner/internal/api"
	"github-miner/internal/auth"
	"github-miner/internal/config"
	"github-miner/internal/export"
	"github-miner/internal/models"
)

const issuesQuery = `
query($owner: String!, $repo: String!, $cursor: String, $since: DateTime) {
  repository(owner: $owner, name: $repo) {
    issues(first: 100, after: $cursor, filterBy: {since: $since}, orderBy: {field: CREATED_AT, direction: DESC}) {
      pageInfo { hasNextPage, endCursor }
      nodes {
        number
        author { login }
        createdAt
        closedAt
        timelineItems(first: 50, itemTypes: [CLOSED_EVENT]) {
          nodes {
            ... on ClosedEvent {
              actor { login }
              createdAt
            }
          }
        }
        comments(first: 100) {
          nodes {
            author { login }
            body
            createdAt
          }
        }
      }
    }
  }
}`

const prsQuery = `
query($owner: String!, $repo: String!, $cursor: String) {
  repository(owner: $owner, name: $repo) {
    pullRequests(first: 50, after: $cursor, orderBy: {field: CREATED_AT, direction: DESC}) {
      pageInfo { hasNextPage, endCursor }
      nodes {
        number
        author { login }
        createdAt
        merged
        mergedAt
        mergedBy { login }
        reviews(first: 50) {
          nodes {
            author { login }
            state
            createdAt
          }
        }
        comments(first: 50) {
          nodes {
            author { login }
            body
            createdAt
          }
        }
      }
    }
  }
}`

func main() {
	cfg, err := config.Load("tokens.json")
	if err != nil {
		log.Fatalf("Erro ao carregar config: %v", err)
	}

	outputDir := "output"
	os.MkdirAll(outputDir, 0755)

	tm := auth.New(cfg.GithubTokens)
	client := api.NewClient(tm)
	writer := export.NewJSONWriter()
	defer writer.Close()

	since := time.Now().AddDate(-3, 0, 0)
	
	fmt.Printf("🚀 Iniciando Minerador Otimizado (GraphQL) para %s/%s\n", cfg.GithubUserTarget, cfg.GithubRepoTarget)
	fmt.Printf("🔑 Tokens: %d | 🧵 Threads: %d | 📅 Desde: %s\n", len(cfg.GithubTokens), 4, since.Format("2006-01-02"))

	var wg sync.WaitGroup
	wg.Add(2)

	// Mineração de Issues (GraphQL)
	go func() {
		defer wg.Done()
		mineIssuesGraphQL(client, writer, cfg.GithubUserTarget, cfg.GithubRepoTarget, since)
	}()

	// Mineração de PRs (GraphQL)
	go func() {
		defer wg.Done()
		minePRsGraphQL(client, writer, cfg.GithubUserTarget, cfg.GithubRepoTarget, since)
	}()

	wg.Wait()
	fmt.Println("\n✅ Mineração concluída com sucesso!")
}

func mineIssuesGraphQL(client *api.Client, writer *export.JSONWriter, owner, repo string, since time.Time) {
	var cursor *string
	for {
		variables := map[string]interface{}{
			"owner":  owner,
			"repo":   repo,
			"cursor": cursor,
			"since":  since.Format(time.RFC3339),
		}

		data, err := client.GraphQL(issuesQuery, variables)
		if err != nil {
			log.Printf("Erro GraphQL Issues: %v", err)
			break
		}

		var resp struct {
			Data struct {
				Repository struct {
					Issues struct {
						PageInfo struct {
							HasNextPage bool    `json:"hasNextPage"`
							EndCursor   string  `json:"endCursor"`
						} `json:"pageInfo"`
						Nodes []struct {
							Number    int       `json:"number"`
							Author    struct{ Login string `json:"login"` } `json:"author"`
							CreatedAt time.Time `json:"createdAt"`
							ClosedAt  time.Time `json:"closedAt"`
							TimelineItems struct {
								Nodes []struct {
									Actor struct{ Login string `json:"login"` } `json:"actor"`
									CreatedAt time.Time `json:"createdAt"`
								} `json:"nodes"`
							} `json:"timelineItems"`
							Comments struct {
								Nodes []struct {
									Author struct{ Login string `json:"login"` } `json:"author"`
									Body   string `json:"body"`
									CreatedAt time.Time `json:"createdAt"`
								} `json:"nodes"`
							} `json:"comments"`
						} `json:"nodes"`
					} `json:"issues"`
				} `json:"repository"`
			} `json:"data"`
		}

		if err := json.Unmarshal(data, &resp); err != nil {
			log.Printf("Erro parse GraphQL Issues: %v", err)
			break
		}

		issues := resp.Data.Repository.Issues
		for _, node := range issues.Nodes {
			if node.CreatedAt.Before(since) {
				return
			}

			// Salvar Comentários
			for _, c := range node.Comments.Nodes {
				writer.Write("output/issue_comments.json", models.IssueComment{
					IssueNumber: node.Number,
					Author:      c.Author.Login,
					Body:        c.Body,
					CreatedAt:   c.CreatedAt,
				})
			}

			// Salvar Closures
			for _, e := range node.TimelineItems.Nodes {
				writer.Write("output/issue_closures.json", models.IssueClosure{
					IssueNumber: node.Number,
					ClosedBy:    e.Actor.Login,
					OpenedBy:    node.Author.Login,
					ClosedAt:    e.CreatedAt,
				})
			}
		}

		if !issues.PageInfo.HasNextPage {
			break
		}
		cursor = &issues.PageInfo.EndCursor
		fmt.Printf("📦 Processadas %d issues... (Cursor: %s)\n", len(issues.Nodes), *cursor)
	}
}

func minePRsGraphQL(client *api.Client, writer *export.JSONWriter, owner, repo string, since time.Time) {
	var cursor *string
	for {
		variables := map[string]interface{}{
			"owner":  owner,
			"repo":   repo,
			"cursor": cursor,
		}

		data, err := client.GraphQL(prsQuery, variables)
		if err != nil {
			log.Printf("Erro GraphQL PRs: %v", err)
			break
		}

		var resp struct {
			Data struct {
				Repository struct {
					PullRequests struct {
						PageInfo struct {
							HasNextPage bool    `json:"hasNextPage"`
							EndCursor   string  `json:"endCursor"`
						} `json:"pageInfo"`
						Nodes []struct {
							Number    int       `json:"number"`
							Author    struct{ Login string `json:"login"` } `json:"author"`
							CreatedAt time.Time `json:"createdAt"`
							Merged    bool      `json:"merged"`
							MergedAt  time.Time `json:"mergedAt"`
							MergedBy  struct{ Login string `json:"login"` } `json:"mergedBy"`
							Reviews struct {
								Nodes []struct {
									Author struct{ Login string `json:"login"` } `json:"author"`
									State  string `json:"state"`
									CreatedAt time.Time `json:"createdAt"`
								} `json:"nodes"`
							} `json:"reviews"`
							Comments struct {
								Nodes []struct {
									Author struct{ Login string `json:"login"` } `json:"author"`
									Body   string `json:"body"`
									CreatedAt time.Time `json:"createdAt"`
								} `json:"nodes"`
							} `json:"comments"`
						} `json:"nodes"`
					} `json:"pullRequests"`
				} `json:"repository"`
			} `json:"data"`
		}

		if err := json.Unmarshal(data, &resp); err != nil {
			log.Printf("Erro parse GraphQL PRs: %v", err)
			break
		}

		prs := resp.Data.Repository.PullRequests
		for _, node := range prs.Nodes {
			if node.CreatedAt.Before(since) {
				return
			}

			// Salvar Comentários
			for _, c := range node.Comments.Nodes {
				writer.Write("output/pull_request_comments.json", models.PRComment{
					PRNumber:  node.Number,
					Author:    c.Author.Login,
					Body:      c.Body,
					CreatedAt: c.CreatedAt,
				})
			}

			// Salvar Reviews e Approvals
			for _, r := range node.Reviews.Nodes {
				writer.Write("output/pull_request_reviews.json", models.PRReview{
					PRNumber:  node.Number,
					Author:    r.Author.Login,
					State:     r.State,
					CreatedAt: r.CreatedAt,
				})
				if r.State == "APPROVED" {
					writer.Write("output/pull_request_approvals.json", models.PRApproval{
						PRNumber:   node.Number,
						Author:     r.Author.Login,
						ApprovedAt: r.CreatedAt,
					})
				}
			}

			// Salvar Merges
			if node.Merged {
				writer.Write("output/pull_request_merges.json", models.PRMerge{
					PRNumber: node.Number,
					MergedBy: node.MergedBy.Login,
					MergedAt: node.MergedAt,
				})
			}
		}

		if !prs.PageInfo.HasNextPage {
			break
		}
		cursor = &prs.PageInfo.EndCursor
		fmt.Printf("🚚 Processados %d PRs... (Cursor: %s)\n", len(prs.Nodes), *cursor)
	}
}

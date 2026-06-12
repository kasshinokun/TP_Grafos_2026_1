package main

import (
	"encoding/json"
	"fmt"
	"log"
	"os"
	"path/filepath"
	"sync"
	"time"

	"github-miner/internal/api"
	"github-miner/internal/auth"
	"github-miner/internal/config"
	"github-miner/internal/export"
	"github-miner/internal/models"
)

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

	// Filtro de tempo: 3 anos atrás
	since := time.Now().AddDate(-3, 0, 0)
	
	fmt.Printf("Iniciando mineração de %s/%s\n", cfg.GithubUserTarget, cfg.GithubRepoTarget)
	fmt.Printf("Tokens disponíveis: %d | Threads: %d\n", len(cfg.GithubTokens), 4)

	var wg sync.WaitGroup
	
	// Canal para processar Issues e PRs
	jobs := make(chan int, 100)

	// Iniciar Workers (1-4 conforme solicitado)
	numWorkers := 4
	if len(cfg.GithubTokens) < numWorkers {
		numWorkers = len(cfg.GithubTokens)
	}
	if numWorkers < 1 { numWorkers = 1 }

	for w := 1; w <= numWorkers; w++ {
		wg.Add(1)
		go worker(w, &wg, jobs, client, writer, cfg.GithubUserTarget, cfg.GithubRepoTarget)
	}

	// Coletar lista de Issues/PRs (simplificado via REST para este exemplo)
	// Em uma versão real, usaríamos GraphQL para listar todos rapidamente
	fmt.Println("Buscando lista de issues e PRs...")
	
	// Coleta de Issues
	page := 1
	for {
		url := fmt.Sprintf("https://api.github.com/repos/%s/%s/issues?state=all&since=%s&per_page=100&page=%d",
			cfg.GithubUserTarget, cfg.GithubRepoTarget, since.Format(time.RFC3339), page)
		
		data, header, err := client.RestGet(url)
		if err != nil {
			log.Printf("Erro ao buscar issues: %v", err)
			break
		}

		var issues []struct {
			Number int `json:"number"`
		}
		json.Unmarshal(data, &issues)

		if len(issues) == 0 {
			break
		}

		for _, issue := range issues {
			jobs <- issue.Number
		}

		// Checar link header para paginação
		if header.Get("Link") == "" || !contains(header.Get("Link"), `rel="next"`) {
			break
		}
		page++
	}

	close(jobs)
	wg.Wait()
	fmt.Println("Mineração concluída!")
}

func contains(s, substr string) bool {
	return filepath.Match("*"+substr+"*", s) == nil // Simplificação grosseira para exemplo
}

func worker(id int, wg *sync.WaitGroup, jobs <-chan int, client *api.Client, writer *export.JSONWriter, owner, repo string) {
	defer wg.Done()
	for number := range jobs {
		// 1. Coletar Comentários (Issue ou PR)
		mineComments(client, writer, owner, repo, number)
		
		// 2. Coletar Timeline/Events (para Closure)
		mineEvents(client, writer, owner, repo, number)

		// 3. Se for PR, coletar Reviews e Merges
		minePRDetails(client, writer, owner, repo, number)
	}
}

func mineComments(client *api.Client, writer *export.JSONWriter, owner, repo string, number int) {
	url := fmt.Sprintf("https://api.github.com/repos/%s/%s/issues/%d/comments", owner, repo, number)
	data, _, err := client.RestGet(url)
	if err != nil { return }

	var comments []models.IssueComment
	json.Unmarshal(data, &comments)
	for _, c := range comments {
		c.IssueNumber = number
		writer.Write("output/issue_comments.json", c)
	}
}

func mineEvents(client *api.Client, writer *export.JSONWriter, owner, repo string, number int) {
	url := fmt.Sprintf("https://api.github.com/repos/%s/%s/issues/%d/events", owner, repo, number)
	data, _, err := client.RestGet(url)
	if err != nil { return }

	var events []struct {
		Event     string `json:"event"`
		CreatedAt time.Time `json:"created_at"`
		Actor     struct { Login string `json:"login"` } `json:"actor"`
	}
	json.Unmarshal(data, &events)

	for _, e := range events {
		if e.Event == "closed" {
			writer.Write("output/issue_closures.json", models.IssueClosure{
				IssueNumber: number,
				ClosedBy:    e.Actor.Login,
				ClosedAt:    e.CreatedAt,
			})
		}
	}
}

func minePRDetails(client *api.Client, writer *export.JSONWriter, owner, repo string, number int) {
	// Tentar ver se é um PR
	url := fmt.Sprintf("https://api.github.com/repos/%s/%s/pulls/%d", owner, repo, number)
	data, _, err := client.RestGet(url)
	if err != nil { return }

	var pr struct {
		MergedAt time.Time `json:"merged_at"`
		MergedBy struct { Login string `json:"login"` } `json:"merged_by"`
	}
	if err := json.Unmarshal(data, &pr); err != nil || pr.MergedAt.IsZero() {
		return
	}

	// Salvar Merge
	writer.Write("output/pull_request_merges.json", models.PRMerge{
		PRNumber: number,
		MergedBy: pr.MergedBy.Login,
		MergedAt: pr.MergedAt,
	})

	// Coletar Reviews
	reviewUrl := fmt.Sprintf("https://api.github.com/repos/%s/%s/pulls/%d/reviews", owner, repo, number)
	rData, _, _ := client.RestGet(reviewUrl)
	var reviews []models.PRReview
	json.Unmarshal(rData, &reviews)
	for _, r := range reviews {
		r.PRNumber = number
		writer.Write("output/pull_request_reviews.json", r)
		if r.State == "APPROVED" {
			writer.Write("output/pull_request_approvals.json", models.PRApproval{
				PRNumber:   number,
				Author:     r.Author,
				ApprovedAt: r.CreatedAt,
			})
		}
	}
}

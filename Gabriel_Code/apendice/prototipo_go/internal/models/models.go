package models

import "time"

type UserInteraction struct {
	Repo        string    `json:"repo"`
	UserSource  string    `json:"user_source"`
	UserTarget  string    `json:"user_target"`
	Type        string    `json:"type"` // issue_comment, pr_comment, issue_closure, pr_review, pr_approval, pr_merge
	Weight      int       `json:"weight"`
	CreatedAt   time.Time `json:"created_at"`
	ReferenceID int       `json:"reference_id"` // Issue or PR number
}

// Estruturas específicas para exportação conforme solicitado
type IssueComment struct {
	IssueNumber int       `json:"issue_number"`
	Author      string    `json:"author"`
	Body        string    `json:"body"`
	CreatedAt   time.Time `json:"created_at"`
}

type IssueClosure struct {
	IssueNumber int       `json:"issue_number"`
	ClosedBy    string    `json:"closed_by"`
	OpenedBy    string    `json:"opened_by"`
	ClosedAt    time.Time `json:"closed_at"`
}

type PRComment struct {
	PRNumber  int       `json:"pr_number"`
	Author    string    `json:"author"`
	Body      string    `json:"body"`
	CreatedAt time.Time `json:"created_at"`
}

type PRReview struct {
	PRNumber  int       `json:"pr_number"`
	Author    string    `json:"author"`
	State     string    `json:"state"`
	CreatedAt time.Time `json:"created_at"`
}

type PRApproval struct {
	PRNumber   int       `json:"pr_number"`
	Author     string    `json:"author"`
	ApprovedAt time.Time `json:"approved_at"`
}

type PRMerge struct {
	PRNumber int       `json:"pr_number"`
	MergedBy string    `json:"merged_by"`
	MergedAt time.Time `json:"merged_at"`
}

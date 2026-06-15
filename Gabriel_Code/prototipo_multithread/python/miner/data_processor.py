import json

class DataProcessor:
    def __init__(self):
        pass

    def process_issue_comment(self, comment_data):
        # Extrai e formata dados relevantes de um comentário de issue
        return {
            "id": comment_data.get("id"),
            "node_id": comment_data.get("node_id"),
            "url": comment_data.get("url"),
            "html_url": comment_data.get("html_url"),
            "issue_url": comment_data.get("issue_url"),
            "user_login": comment_data.get("user", {}).get("login"),
            "created_at": comment_data.get("created_at"),
            "updated_at": comment_data.get("updated_at"),
            "body": comment_data.get("body"),
            "author_association": comment_data.get("author_association"),
        }

    def process_issue_closure(self, event_data):
        # Extrai e formata dados relevantes de um evento de fechamento de issue
        return {
            "id": event_data.get("id"),
            "node_id": event_data.get("node_id"),
            "url": event_data.get("url"),
            "actor_login": event_data.get("actor", {}).get("login"),
            "event": event_data.get("event"), # Should be 'closed'
            "commit_id": event_data.get("commit_id"),
            "commit_url": event_data.get("commit_url"),
            "created_at": event_data.get("created_at"),
            "issue_url": event_data.get("issue", {}).get("url"),
            "issue_number": event_data.get("issue", {}).get("number"),
        }

    def process_pull_request_comment(self, comment_data):
        # Extrai e formata dados relevantes de um comentário de pull request
        return {
            "id": comment_data.get("id"),
            "node_id": comment_data.get("node_id"),
            "url": comment_data.get("url"),
            "html_url": comment_data.get("html_url"),
            "pull_request_url": comment_data.get("pull_request_url"),
            "user_login": comment_data.get("user", {}).get("login"),
            "created_at": comment_data.get("created_at"),
            "updated_at": comment_data.get("updated_at"),
            "body": comment_data.get("body"),
            "author_association": comment_data.get("author_association"),
            "commit_id": comment_data.get("commit_id"),
            "original_commit_id": comment_data.get("original_commit_id"),
            "diff_hunk": comment_data.get("diff_hunk"),
            "path": comment_data.get("path"),
            "position": comment_data.get("position"),
            "original_position": comment_data.get("original_position"),
            "line": comment_data.get("line"),
            "original_line": comment_data.get("original_line"),
            "start_line": comment_data.get("start_line"),
            "original_start_line": comment_data.get("original_start_line"),
        }

    def process_pull_request_review(self, review_data):
        # Extrai e formata dados relevantes de uma revisão de pull request
        return {
            "id": review_data.get("id"),
            "node_id": review_data.get("node_id"),
            "user_login": review_data.get("user", {}).get("login"),
            "body": review_data.get("body"),
            "state": review_data.get("state"),
            "html_url": review_data.get("html_url"),
            "pull_request_url": review_data.get("pull_request_url"),
            "submitted_at": review_data.get("submitted_at"),
            "commit_id": review_data.get("commit_id"),
            "author_association": review_data.get("author_association"),
        }

    def process_pull_request_opening(self, pr_data):
        # Extrai e formata dados relevantes de uma abertura de pull request
        return {
            "id": pr_data.get("id"),
            "node_id": pr_data.get("node_id"),
            "url": pr_data.get("url"),
            "html_url": pr_data.get("html_url"),
            "issue_url": pr_data.get("issue_url"),
            "number": pr_data.get("number"),
            "state": pr_data.get("state"),
            "locked": pr_data.get("locked"),
            "title": pr_data.get("title"),
            "user_login": pr_data.get("user", {}).get("login"),
            "body": pr_data.get("body"),
            "created_at": pr_data.get("created_at"),
            "updated_at": pr_data.get("updated_at"),
            "closed_at": pr_data.get("closed_at"),
            "merged_at": pr_data.get("merged_at"),
            "merge_commit_sha": pr_data.get("merge_commit_sha"),
            "assignee_login": pr_data.get("assignee", {}).get("login"),
            "comments": pr_data.get("comments"),
            "review_comments": pr_data.get("review_comments"),
            "commits": pr_data.get("commits"),
            "additions": pr_data.get("additions"),
            "deletions": pr_data.get("deletions"),
            "changed_files": pr_data.get("changed_files"),
            "author_association": pr_data.get("author_association"),
        }

    def process_pull_request_merge(self, pr_data):
        # Extrai e formata dados relevantes de um merge de pull request
        # Assume que o PR já foi processado por process_pull_request_opening e tem o campo merged_at
        if pr_data.get("merged_at"):
            return {
                "id": pr_data.get("id"),
                "node_id": pr_data.get("node_id"),
                "number": pr_data.get("number"),
                "title": pr_data.get("title"),
                "user_login": pr_data.get("user", {}).get("login"),
                "merged_at": pr_data.get("merged_at"),
                "merge_commit_sha": pr_data.get("merge_commit_sha"),
                "merged_by_login": pr_data.get("merged_by", {}).get("login"),
            }
        return None

    def process_pull_request_approval(self, review_data):
        # Extrai e formata dados relevantes de uma aprovação de pull request
        # Assume que o review já foi processado por process_pull_request_review e tem o campo state
        if review_data.get("state") == "APPROVED":
            return {
                "id": review_data.get("id"),
                "node_id": review_data.get("node_id"),
                "user_login": review_data.get("user", {}).get("login"),
                "pull_request_url": review_data.get("pull_request_url"),
                "submitted_at": review_data.get("submitted_at"),
                "commit_id": review_data.get("commit_id"),
            }
        return None

# Exemplo de uso (para testes)
if __name__ == '__main__':
    processor = DataProcessor()

    # Exemplo de dados de comentário de issue
    sample_issue_comment = {
        "id": 123,
        "node_id": "IC_kwDOB_B2ys5_C-zC",
        "url": "https://api.github.com/repos/octocat/Spoon-Knife/issues/1/comments/123",
        "html_url": "https://github.com/octocat/Spoon-Knife/issues/1#issuecomment-123",
        "issue_url": "https://api.github.com/repos/octocat/Spoon-Knife/issues/1",
        "user": {"login": "octocat", "id": 1, "node_id": "MDQ6VXNlcjE=", "avatar_url": "...", "gravatar_id": "", "url": "https://api.github.com/users/octocat", "html_url": "https://github.com/octocat", "followers_url": "...", "following_url": "...", "gists_url": "...", "starred_url": "...", "subscriptions_url": "...", "organizations_url": "...", "repos_url": "...", "events_url": "...", "received_events_url": "...", "type": "User", "site_admin": False},
        "created_at": "2011-04-14T16:00:49Z",
        "updated_at": "2011-04-14T16:00:49Z",
        "author_association": "OWNER",
        "body": "Meow",
        "reactions": {"url": "https://api.github.com/repos/octocat/Spoon-Knife/issues/comments/123/reactions", "total_count": 0, "+1": 0, "-1": 0, "laugh": 0, "hooray": 0, "confused": 0, "heart": 0, "rocket": 0, "eyes": 0}
    }
    processed_comment = processor.process_issue_comment(sample_issue_comment)
    print("\nComentário de Issue Processado:", json.dumps(processed_comment, indent=2))

    # Exemplo de dados de evento de fechamento de issue
    sample_issue_closure_event = {
        "id": 12345,
        "node_id": "MDE2Oklzc3VlRXZlbnQxMjM0NQ==",
        "url": "https://api.github.com/repos/octocat/Spoon-Knife/issues/events/12345",
        "actor": {"login": "octocat", "id": 1, "node_id": "MDQ6VXNlcjE=", "avatar_url": "...", "gravatar_id": "", "url": "https://api.github.com/users/octocat", "html_url": "https://github.com/octocat", "followers_url": "...", "following_url": "...", "gists_url": "...", "starred_url": "...", "subscriptions_url": "...", "organizations_url": "...", "repos_url": "...", "events_url": "...", "received_events_url": "...", "type": "User", "site_admin": False},
        "event": "closed",
        "commit_id": "6dcb09b5b57875f334f61aebed695e2e4193db5e",
        "commit_url": "https://api.github.com/repos/octocat/Spoon-Knife/commits/6dcb09b5b57875f334f61aebed695e2e4193db5e",
        "created_at": "2011-04-14T16:00:49Z",
        "issue": {"url": "https://api.github.com/repos/octocat/Spoon-Knife/issues/1", "number": 1}
    }
    processed_closure = processor.process_issue_closure(sample_issue_closure_event)
    print("\nFechamento de Issue Processado:", json.dumps(processed_closure, indent=2))

    # Exemplo de dados de pull request (para abertura e merge)
    sample_pr_data = {
        "url": "https://api.github.com/repos/octocat/Spoon-Knife/pulls/1",
        "id": 1,
        "node_id": "MDExOlB1bGxSZXF1ZXN0MQ==",
        "html_url": "https://github.com/octocat/Spoon-Knife/pull/1",
        "issue_url": "https://api.github.com/repos/octocat/Spoon-Knife/issues/1",
        "number": 1,
        "state": "closed",
        "locked": False,
        "title": "Update the README with new information",
        "user": {"login": "octocat", "id": 1, "node_id": "MDQ6VXNlcjE=", "avatar_url": "...", "gravatar_id": "", "url": "https://api.github.com/users/octocat", "html_url": "https://github.com/octocat", "followers_url": "...", "following_url": "...", "gists_url": "...", "starred_url": "...", "subscriptions_url": "...", "organizations_url": "...", "repos_url": "...", "events_url": "...", "received_events_url": "...", "type": "User", "site_admin": False},
        "body": "This is a pretty simple change that we need to pull into master.",
        "created_at": "2011-01-26T19:01:12Z",
        "updated_at": "2011-01-26T19:01:12Z",
        "closed_at": "2011-01-26T19:01:12Z",
        "merged_at": "2011-01-26T19:01:12Z",
        "merge_commit_sha": "e5bd3914e2e596debea16f433f57875b5b90bcd6",
        "assignee": None,
        "comments": 0,
        "review_comments": 0,
        "commits": 1,
        "additions": 1,
        "deletions": 1,
        "changed_files": 1,
        "author_association": "OWNER",
        "merged_by": {"login": "octocat", "id": 1, "node_id": "MDQ6VXNlcjE=", "avatar_url": "...", "gravatar_id": "", "url": "https://api.github.com/users/octocat", "html_url": "https://github.com/octocat", "followers_url": "...", "following_url": "...", "gists_url": "...", "starred_url": "...", "subscriptions_url": "...", "organizations_url": "...", "repos_url": "...", "events_url": "...", "received_events_url": "...", "type": "User", "site_admin": False},
    }
    processed_pr_opening = processor.process_pull_request_opening(sample_pr_data)
    print("\nAbertura de PR Processada:", json.dumps(processed_pr_opening, indent=2))

    processed_pr_merge = processor.process_pull_request_merge(sample_pr_data)
    print("\nMerge de PR Processado:", json.dumps(processed_pr_merge, indent=2))

    # Exemplo de dados de revisão de pull request (para revisão e aprovação)
    sample_pr_review = {
        "id": 80,
        "node_id": "MDE3OlB1bGxSZXF1ZXN0UmV2aWV3ODA=",
        "user": {"login": "octocat", "id": 1, "node_id": "MDQ6VXNlcjE=", "avatar_url": "...", "gravatar_id": "", "url": "https://api.github.com/users/octocat", "html_url": "https://github.com/octocat", "followers_url": "...", "following_url": "...", "gists_url": "...", "starred_url": "...", "subscriptions_url": "...", "organizations_url": "...", "repos_url": "...", "events_url": "...", "received_events_url": "...", "type": "User", "site_admin": False},
        "body": "Looks good to me!",
        "state": "APPROVED",
        "html_url": "https://github.com/octocat/Spoon-Knife/pull/1#pullrequestreview-80",
        "pull_request_url": "https://api.github.com/repos/octocat/Spoon-Knife/pulls/1",
        "submitted_at": "2011-01-26T19:01:12Z",
        "commit_id": "6dcb09b5b57875f334f61aebed695e2e4193db5e",
        "author_association": "OWNER",
    }
    processed_pr_review = processor.process_pull_request_review(sample_pr_review)
    print("\nRevisão de PR Processada:", json.dumps(processed_pr_review, indent=2))

    processed_pr_approval = processor.process_pull_request_approval(sample_pr_review)
    print("\nAprovação de PR Processada:", json.dumps(processed_pr_approval, indent=2))

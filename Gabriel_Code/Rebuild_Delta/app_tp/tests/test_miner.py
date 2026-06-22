"""Testes unitários do minerador com mocking da API do GitHub."""
import unittest
from unittest.mock import Mock, patch, MagicMock
from miner.common_miner import CommonMiner
from miner.hybrid_miner import HybridMiner


class TestCommonMiner(unittest.TestCase):
    """Testes do minerador comum."""
    
    def setUp(self):
        self.tokens = ['fake_token_1', 'fake_token_2']
        self.miner = CommonMiner('microsoft', 'TypeScript', self.tokens)
    
    @patch('miner.common_miner.requests.Session.get')
    def test_fetch_issues_success(self, mock_get):
        """Testa busca bem-sucedida de issues."""
        # Mock response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                'number': 1,
                'user': {'login': 'user1'},
                'title': 'Bug report',
                'body': 'Found a bug'
            },
            {
                'number': 2,
                'user': {'login': 'user2'},
                'title': 'Feature request',
                'body': 'Please add feature'
            }
        ]
        mock_get.return_value = mock_response
        
        issues = self.miner._fetch_issues()
        
        self.assertEqual(len(issues), 2)
        self.assertEqual(self.miner.stats['issues_fetched'], 2)
    
    @patch('miner.common_miner.requests.Session.get')
    def test_fetch_pull_requests_success(self, mock_get):
        """Testa busca bem-sucedida de PRs."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                'number': 10,
                'user': {'login': 'dev1'},
                'title': 'Fix typo',
                'merged': False
            }
        ]
        mock_get.return_value = mock_response
        
        prs = self.miner._fetch_pull_requests()
        
        self.assertEqual(len(prs), 1)
        self.assertEqual(self.miner.stats['prs_fetched'], 1)
    
    @patch('miner.common_miner.requests.Session.get')
    def test_fetch_comments_success(self, mock_get):
        """Testa busca de comentários."""
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {
                'user': {'login': 'reviewer1'},
                'body': 'Looks good @user1'
            }
        ]
        mock_get.return_value = mock_response
        
        comments = self.miner._fetch_comments(1)
        
        self.assertEqual(len(comments), 1)
        self.assertEqual(self.miner.stats['comments_fetched'], 1)
    
    def test_extract_mentions(self):
        """Testa extração de menções @username."""
        text = "Thanks @user1 and @user2 for the help! cc @dev-team"
        mentions = self.miner._extract_mentions(text)
        
        self.assertIn('user1', mentions)
        self.assertIn('user2', mentions)
        self.assertEqual(len(mentions), 3)
    
    def test_build_graph_from_interactions(self):
        """Testa construção de grafo a partir de interações."""
        interactions = [
            {
                'type': 'comment',
                'author': 'user1',
                'mentions': ['user2', 'user3'],
                'assignees': []
            },
            {
                'type': 'review',
                'author': 'user2',
                'mentions': ['user1'],
                'assignees': []
            }
        ]
        
        graph = self.miner._build_graph_from_interactions(interactions)
        
        self.assertEqual(graph.get_vertex_count(), 3)
        self.assertGreater(graph.get_edge_count(), 0)
    
    def test_cancel_miner(self):
        """Testa cancelamento da mineração."""
        self.miner.is_cancelled = True
        
        graph = self.miner._build_empty_graph()
        
        self.assertEqual(graph.get_vertex_count(), 0)
    
    def test_get_stats(self):
        """Testa recuperação de estatísticas."""
        self.miner.stats['issues_fetched'] = 10
        self.miner.stats['prs_fetched'] = 5
        
        stats = self.miner.get_stats()
        
        self.assertEqual(stats['issues_fetched'], 10)
        self.assertEqual(stats['prs_fetched'], 5)


class TestHybridMiner(unittest.TestCase):
    """Testes do minerador híbrido."""
    
    def setUp(self):
        self.tokens = ['fake_token']
        self.miner = HybridMiner('microsoft', 'TypeScript', self.tokens)
    
    def test_weights_configuration(self):
        """Testa configuração de pesos."""
        self.assertEqual(self.miner.weights['comment'], 2)
        self.assertEqual(self.miner.weights['issue_commented'], 3)
        self.assertEqual(self.miner.weights['review'], 4)
        self.assertEqual(self.miner.weights['merge'], 5)
    
    def test_checkpoint_manager_initialization(self):
        """Testa inicialização do gerenciador de checkpoints."""
        self.assertIsNotNone(self.miner.checkpoint)
        self.assertEqual(self.miner.checkpoint.interval, 60)


if __name__ == '__main__':
    unittest.main()
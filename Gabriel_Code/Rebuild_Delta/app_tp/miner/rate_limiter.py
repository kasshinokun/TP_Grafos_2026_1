"""Rate limiter com token bucket para API do GitHub."""
import time
import threading
from typing import List


class GitHubRateLimiter:
    """Gerencia múltiplos tokens com rotação."""
    
    def __init__(self, tokens: List[str], requests_per_hour: int = 5000):
        self.tokens = tokens
        self.requests_per_hour = requests_per_hour
        self.current_token_idx = 0
        self.request_counts = {t: 0 for t in tokens}
        self.reset_times = {t: time.time() + 3600 for t in tokens}
        self.lock = threading.Lock()
    
    def get_token(self) -> str:
        """Retorna o token com mais quota disponível."""
        with self.lock:
            now = time.time()
            
            # Reseta contadores se passou 1 hora
            for token in self.tokens:
                if now >= self.reset_times[token]:
                    self.request_counts[token] = 0
                    self.reset_times[token] = now + 3600
            
            # Escolhe token com menor uso
            best_token = min(self.tokens, key=lambda t: self.request_counts[t])
            
            # Verifica se ainda tem quota
            if self.request_counts[best_token] >= self.requests_per_hour:
                # Todos os tokens estourados, espera
                min_reset = min(self.reset_times.values())
                wait_time = min_reset - now
                if wait_time > 0:
                    time.sleep(wait_time + 1)
                    return self.get_token()
            
            self.request_counts[best_token] += 1
            return best_token
    
    def get_remaining_quota(self) -> dict:
        """Retorna quota restante por token."""
        with self.lock:
            return {
                token: self.requests_per_hour - self.request_counts[token]
                for token in self.tokens
            }
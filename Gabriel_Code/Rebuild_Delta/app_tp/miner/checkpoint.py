"""Sistema de checkpoint para retomada de minerações longas."""
import pickle
import os
import time
from typing import Any, Optional
from datetime import datetime


class CheckpointManager:
    """Gerencia checkpoints periódicos do estado do grafo."""
    
    def __init__(self, checkpoint_dir: str = ".checkpoints", interval_seconds: int = 60):
        self.checkpoint_dir = checkpoint_dir
        self.interval = interval_seconds
        self.last_checkpoint_time = 0
        self.checkpoint_count = 0
        
        os.makedirs(checkpoint_dir, exist_ok=True)
    
    def should_checkpoint(self) -> bool:
        """Verifica se é hora de salvar checkpoint."""
        return (time.time() - self.last_checkpoint_time) >= self.interval
    
    def save(self, state: dict, repo_name: str) -> str:
        """Salva estado atual em arquivo."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{repo_name}_{timestamp}_cp{self.checkpoint_count}.pkl"
        filepath = os.path.join(self.checkpoint_dir, filename)
        
        with open(filepath, 'wb') as f:
            pickle.dump({
                'state': state,
                'timestamp': timestamp,
                'checkpoint_id': self.checkpoint_count
            }, f)
        
        self.last_checkpoint_time = time.time()
        self.checkpoint_count += 1
        
        # Mantém apenas os 3 últimos checkpoints
        self._cleanup_old_checkpoints(repo_name, keep=3)
        
        return filepath
    
    def load_latest(self, repo_name: str) -> Optional[dict]:
        """Carrega o checkpoint mais recente."""
        pattern = f"{repo_name}_*_cp*.pkl"
        files = [f for f in os.listdir(self.checkpoint_dir) if f.startswith(repo_name) and f.endswith('.pkl')]
        
        if not files:
            return None
        
        # Ordena por timestamp
        files.sort(reverse=True)
        filepath = os.path.join(self.checkpoint_dir, files[0])
        
        with open(filepath, 'rb') as f:
            data = pickle.load(f)
        
        return data['state']
    
    def _cleanup_old_checkpoints(self, repo_name: str, keep: int = 3):
        """Remove checkpoints antigos, mantendo os N mais recentes."""
        files = [f for f in os.listdir(self.checkpoint_dir) if f.startswith(repo_name)]
        files.sort(reverse=True)
        
        for old_file in files[keep:]:
            try:
                os.remove(os.path.join(self.checkpoint_dir, old_file))
            except OSError:
                pass
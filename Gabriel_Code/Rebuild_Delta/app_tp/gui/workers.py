"""Workers assíncronos para operações pesadas."""
import threading
import queue
from typing import Callable, Any

class GraphWorker(threading.Thread):
    """Executa algoritmos pesados em thread separada."""
    
    def __init__(self, task: Callable, on_complete: Callable, on_progress: Callable = None):
        super().__init__(daemon=True)
        self.task = task
        self.on_complete = on_complete
        self.on_progress = on_progress
        self.result = None
        self.error = None
        self._cancelled = False
    
    def run(self):
        try:
            self.result = self.task()
            if not self._cancelled:
                self.on_complete(self.result)
        except Exception as e:
            self.error = e
            if not self._cancelled:
                self.on_complete(None, error=e)
    
    def cancel(self):
        self._cancelled = True


class ProgressReporter:
    """Reporta progresso de volta à thread principal via queue."""
    
    def __init__(self, queue: queue.Queue):
        self.queue = queue
    
    def report(self, progress: float, message: str = ""):
        self.queue.put(('progress', progress, message))


class MinerWorker(GraphWorker):
    """Worker especializado para mineração com checkpoint."""
    
    def __init__(self, miner, on_complete, on_progress=None, checkpoint_interval=60):
        self.miner = miner
        self.checkpoint_interval = checkpoint_interval
        super().__init__(
            task=self._run_mining,
            on_complete=on_complete,
            on_progress=on_progress
        )
    
    def _run_mining(self):
        return self.miner.run_with_checkpoint(self.checkpoint_interval)
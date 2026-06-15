import threading
import queue
import time

class Worker(threading.Thread):
    def __init__(self, task_queue, results_queue, thread_id):
        super().__init__()
        self.task_queue = task_queue
        self.results_queue = results_queue
        self.thread_id = thread_id
        self.daemon = True # Permite que o programa principal saia mesmo que as threads estejam rodando

    def run(self):
        while True:
            try:
                task = self.task_queue.get(timeout=1) # Espera por tarefas por 1 segundo
                print(f"Thread {self.thread_id}: Executando tarefa {task.get("name", "")}")
                result = task["func"](*task["args"], **task["kwargs"])
                self.results_queue.put(result)
                self.task_queue.task_done()
            except queue.Empty:
                # Nenhuma tarefa na fila, a thread pode terminar se não houver mais tarefas
                break
            except Exception as e:
                print(f"Thread {self.thread_id}: Erro ao executar tarefa: {e}")
                self.task_queue.task_done()

class ThreadManager:
    def __init__(self, num_threads):
        self.num_threads = num_threads
        self.task_queue = queue.Queue()
        self.results_queue = queue.Queue()
        self.workers = []

    def add_task(self, func, *args, **kwargs):
        self.task_queue.put({"func": func, "args": args, "kwargs": kwargs, "name": func.__name__})

    def start_workers(self):
        for i in range(self.num_threads):
            worker = Worker(self.task_queue, self.results_queue, i + 1)
            self.workers.append(worker)
            worker.start()

    def wait_for_completion(self):
        self.task_queue.join() # Bloqueia até que todas as tarefas sejam processadas
        print("Todas as tarefas foram concluídas.")

    def get_results(self):
        results = []
        while not self.results_queue.empty():
            results.append(self.results_queue.get())
        return results

# Exemplo de uso (para testes)
if __name__ == '__main__':
    def sample_task(task_id, delay):
        print(f"Executando tarefa {task_id}...")
        time.sleep(delay)
        print(f"Tarefa {task_id} concluída.")
        return f"Resultado da tarefa {task_id}"

    manager = ThreadManager(num_threads=2)

    manager.add_task(sample_task, task_id=1, delay=2)
    manager.add_task(sample_task, task_id=2, delay=1)
    manager.add_task(sample_task, task_id=3, delay=3)

    manager.start_workers()
    manager.wait_for_completion()

    all_results = manager.get_results()
    print("Resultados finais:", all_results)

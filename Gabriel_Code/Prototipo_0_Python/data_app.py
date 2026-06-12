from core.base_app import MicroApp
from models.student_models import get_default_students

class DataMicroApp(MicroApp):
    def __init__(self):
        super().__init__("DataApp")
        self.students = get_default_students()

    def _handle_event(self, event_type: str, payload: dict):
        print(f"[{self.name}] Recebeu evento: {event_type}")
        if event_type == "API_GET_STUDENTS":
            print(f"[{self.name}] Processando GET /students")
            student_list = [{"name": s.name, "role": s.role} for s in self.students]
            self.bus.publish("RESPONSE_GET_STUDENTS", {"students": student_list})
        
        elif event_type == "API_POST_LOG_INTERACTION":
            print(f"[{self.name}] Processando POST /log_interaction: {payload}")
            # Simula salvar no banco de dados
            self.bus.publish("RESPONSE_POST_LOG_INTERACTION", {"status": "success"})

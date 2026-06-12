class Student:
    def __init__(self, name: str, role: str = "Developer"):
        self.name = name
        self.role = role

def get_default_students():
    names = [
        "José Cunha", "João Cruz", "Gabriel Silva", 
        "Kelly Silveira", "Yago Ferreira", "Misaki Tanaka"
    ]
    return [Student(name) for name in names]

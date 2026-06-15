import json
import os

class DataSaver:
    def __init__(self, output_dir="."): # Default to current directory
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)

    def save_to_json(self, data, filename):
        filepath = os.path.join(self.output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
        print(f"Dados salvos em {filepath}")

# Exemplo de uso (para testes)
if __name__ == '__main__':
    saver = DataSaver(output_dir="./output_test")
    sample_data = [
        {"id": 1, "content": "Primeiro comentário", "author": "user1"},
        {"id": 2, "content": "Segundo comentário", "author": "user2"}
    ]
    saver.save_to_json(sample_data, "sample_comments.json")

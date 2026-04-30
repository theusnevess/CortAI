import json
import os

path = r'C:\Users\Mathe\Documents\LUMA Cognitive Systems\CortAI\CortAI 1.0\OUT\full_creative_pipeline_execution.json'
out_dir = r'C:\Users\Mathe\Documents\LUMA Cognitive Systems\CortAI\CortAI 1.0\OUT\agents_outputs'
os.makedirs(out_dir, exist_ok=True)

try:
    with open(path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    for key, value in data.items():
        out_path = os.path.join(out_dir, f'{key}_output.json')
        with open(out_path, 'w', encoding='utf-8') as out_f:
            json.dump(value, out_f, indent=2, ensure_ascii=False)

    print(f"Sucesso! Os logs dos agentes foram divididos em {len(data)} arquivos individuais na pasta: {out_dir}")
except Exception as e:
    print(f"Erro: {e}")

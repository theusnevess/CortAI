import json
import os
import sys

# Garante que as rotas dos imports vão resolver para a pasta correta
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), 'backend')))

from app.creative.orchestrator.service import CreativeOrchestratorService
from app.creative.contracts.orchestrator_io import CreativeOrchestratorInput

def main():
    print("Iniciando Orchestrator Pipeline End-to-End...")
    orchestrator = CreativeOrchestratorService()

    input_payload = CreativeOrchestratorInput(
        account_id="demo_account_br",
        niche="science",
        topic="paradoxo de fermi",
        publish_slot="20260405T180000Z",
        force_refresh_trends=False
    )

    print(f"Executando pipeline para o tópico: {input_payload.topic} no nicho: {input_payload.niche}...")
    try:
        execution = orchestrator.execute(input_payload)

        output_file = os.path.join("OUT", "full_creative_pipeline_execution.json")
        os.makedirs("OUT", exist_ok=True)

        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(execution.to_dict(), f, indent=2, ensure_ascii=False)

        print(f"SUCESSO! O pipeline inteiro executou e o output final consolidado de todos os agentes foi salvo em: {output_file}")
    except Exception as e:
        print(f"ERRO DE EXECUÇÃO: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()

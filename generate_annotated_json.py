import json
import os

source_json = r'C:\Users\Mathe\Documents\LUMA Cognitive Systems\CortAI\CortAI 1.0\OUT\full_creative_pipeline_execution.json'
output_md = r'C:\Users\Mathe\Documents\LUMA Cognitive Systems\CortAI\CortAI 1.0\OUT\annotated_creative_pipeline.md'

agent_descriptions = {
    "account_health": "Guardião da Saúde da Conta (Restringe a conta em caso de baixa performance)",
    "trend_analysis": "Mapeia as Tendências atuais em alta (Hooks e visuais mais famosos)",
    "learning": "Deriva heurísticas com base nos resultados e aprendizados em vídeos anteriores",
    "novelty": "Mede e mitiga o Tédio Algorítmico, bloqueando formatos saturados",
    "strategy": "O Cérebro-Estrategista (Funde insights de Novelty, Trends e Learning e gera o plano macro)",
    "experiment": "Orquestrador de Testes A/B Dinâmicos",
    "creative_pack": "O Grande Contrato Consolidado (Contém o Script gerado, escolha de Voz e o Plano de Edição)",
    "asset_selection": "Diretor de Imagem do Pipeline Visual (Monta as flags ricas de cenários)",
    "pipeline_output": "Processo bruto de compilação da infraestrutura (Tempo em ms do Kokoro e ComfyUI)",
    "video_qc": "Sensor de Qualidade e Segurança (Decide pelo APPROVE/HOLD/REJECT do vídeo pronto)"
}

try:
    with open(source_json, 'r', encoding='utf-8') as f:
        data = json.load(f)

    with open(output_md, 'w', encoding='utf-8') as out_f:
        out_f.write("# Logs de Execução Completa do Pipeline CortAI\n\n")
        out_f.write("Abaixo estão as saídas registradas de cada um dos Agentes envolvidos no fluxo.\n\n")

        # Iterar sobre os agentes ordenando de forma lógica ou conforme ocorrem no JSON
        for key, value in data.items():
            agent_title = agent_descriptions.get(key, key.replace("_", " ").title())

            # Cabeçalho claro de Início do Agente
            out_f.write(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n")
            out_f.write(f"🟢🟢🟢 INÍCIO DA SAÍDA DO AGENTE: {key.upper()} 🟢🟢🟢\n")
            out_f.write(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n")
            out_f.write(f"## 🔍 {key.upper()}\n")
            out_f.write(f"> **Função/Descrição:** {agent_title}\n\n")

            out_f.write("```json\n")
            json.dump(value, out_f, indent=2, ensure_ascii=False)
            out_f.write("\n```\n\n")

            # Rodapé claro de Fim do Agente
            out_f.write(f"🔴🔴🔴 FIM DA SAÍDA DO AGENTE: {key.upper()} 🔴🔴🔴\n")
            out_f.write(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n\n\n\n")

    print(f"Sucesso! O arquivo anotado unificado foi gerado em: {output_md}")
except Exception as e:
    print(f"Erro: {e}")

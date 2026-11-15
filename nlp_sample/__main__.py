"""New review harness for original helper methods; no model or database calls."""
import argparse
import json
from pathlib import Path
from types import SimpleNamespace
from .analysis import AgentCore
from .workflow import ConversationSystem


class ModelTestDouble:
    """A fixed fixture response, not language understanding or a recorded model run."""

    def invoke(self, prompt):
        self.last_prompt = prompt
        return SimpleNamespace(content="Illustrative fixture response. NECESITO_MAS_INFO")


def main():
    parser = argparse.ArgumentParser(description="Inspect selected original NLP helper methods")
    parser.add_argument("question", nargs="?", default="top 5 productos en 2024")
    args = parser.parse_args()
    config = Path(__file__).resolve().parents[1] / "prompts/context.txt"
    fixture = ModelTestDouble()
    agent = AgentCore(str(config), fixture)
    conversation = ConversationSystem(agent, agent, agent)
    conversation.conversation_context.append({"role": "user", "content": args.question})
    context = conversation._construir_contexto_agent1()
    response = agent.invoke(context)
    print(json.dumps({
        "demonstration": "Original helpers with synthetic input and a fixed model test double",
        "model_calls": 0,
        "input": args.question,
        "computed_query_context": agent._analizar_contexto(args.question),
        "computed_grouping": agent._detectar_agrupacion(args.question),
        "context_includes_user_input": args.question in context,
        "fixture_response": response,
        "needs_input_for_fixture": conversation._agent_necesita_input(response),
    }, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()

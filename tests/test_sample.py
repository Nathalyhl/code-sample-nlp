"""New review tests around selected original code; no live model or database."""
import ast
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

from nlp_sample.analysis import AgentCore
from nlp_sample.workflow import ConversationSystem

ROOT = Path(__file__).resolve().parents[1]


class ModelFixture:
    """Explicit test double, not a semantic prediction."""

    def invoke(self, prompt):
        self.prompt = prompt
        return SimpleNamespace(content="Fixture response. NECESITO_MAS_INFO")


class OriginalSourceTests(unittest.TestCase):
    def setUp(self):
        self.fixture = ModelFixture()
        self.agent = AgentCore(str(ROOT / "prompts/context.txt"), self.fixture)
        self.system = ConversationSystem(self.agent, self.agent, self.agent)

    def test_selected_methods_match_published_provenance(self):
        manifest = json.loads((ROOT / "docs/SOURCE_MAP.json").read_text("utf8"))
        self.assertEqual(len(manifest["selection"]), 8)
        for entry in manifest["selection"]:
            with self.subTest(method=entry["method"]):
                source = (ROOT / entry["published_file"]).read_text("utf8")
                tree = ast.parse(source)
                cls = next(n for n in tree.body if isinstance(n, ast.ClassDef) and n.name == entry["class"])
                method = next(n for n in cls.body if isinstance(n, ast.FunctionDef) and n.name == entry["method"])
                digest = hashlib.sha256(ast.get_source_segment(source, method).encode("utf8")).hexdigest()
                self.assertEqual(digest, entry["published_method_sha256"])

    def test_prompt_uses_selected_original_config_fields(self):
        self.assertIn("Query refinement agent", self.agent.system_prompt)
        self.assertIn("NECESITO_MAS_INFO", self.agent.system_prompt)
        self.assertIn("PROCESANDO_CONSULTA", self.agent.system_prompt)

    def test_invocation_passes_context_to_fixture(self):
        response = self.agent.invoke("An illustrative user question")
        self.assertIn("An illustrative user question", self.fixture.prompt)
        self.assertEqual(response, "Fixture response. NECESITO_MAS_INFO")

    def test_original_ranking_and_grouping_behavior(self):
        context = self.agent._analizar_contexto("top 5 productos en 2024")
        self.assertTrue(context["es_ranking"])
        self.assertEqual(context["limit_valor"], 5)
        self.assertEqual(context["dimension_agrupacion"], "subpartida")
        self.assertEqual(self.agent._detectar_agrupacion("top 3 empresas"), "razon_social_exportador")

    def test_original_defaults_remain_visible(self):
        context = self.agent._analizar_contexto("ranking")
        self.assertEqual(context["limit_valor"], 10)
        self.assertEqual(context["dimension_agrupacion"], "subpartida")

    def test_average_and_department_intent(self):
        self.assertTrue(self.agent._analizar_contexto("promedio de exportaciones")["es_promedio"])
        self.assertEqual(self.agent._analizar_contexto("exportaciones por departamento")["dimension_agrupacion"], "region_de_origen")

    def test_context_accumulates_user_turns_and_truncates_assistant(self):
        self.system.conversation_context = [
            {"role": "user", "content": "Valle del Cauca"},
            {"role": "assistant", "content": "A" * 400},
            {"role": "user", "content": "2024"},
        ]
        context = self.system._construir_contexto_agent1()
        self.assertIn("Valle del Cauca", context)
        self.assertIn("2024", context)
        self.assertNotIn("A" * 301, context)
        self.assertIn("complete response omitted", context)

    def test_marker_and_question_mark_heuristics(self):
        self.assertTrue(self.system._agent_necesita_input("NECESITO_MAS_INFO"))
        self.assertFalse(self.system._agent_necesita_input("PROCESANDO_CONSULTA"))
        self.assertTrue(self.system._agent_necesita_input("Which period?"))
        self.assertFalse(self.system._agent_necesita_input("Unmarked response"))

    def test_all_three_selected_configs_have_provenance(self):
        manifest = json.loads((ROOT / "docs/SOURCE_MAP.json").read_text("utf8"))
        self.assertEqual(len(manifest["agent_configs"]), 3)
        for entry in manifest["agent_configs"]:
            config = json.loads((ROOT / entry["published_file"]).read_text("utf8"))
            self.assertEqual(len(config["instrucciones"]), len(entry["instruction_indices_zero_based"]))


if __name__ == "__main__":
    unittest.main()

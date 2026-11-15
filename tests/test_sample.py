"""New review tests around selected original code; no live model or database."""
import ast
import hashlib
import json
from pathlib import Path
from types import SimpleNamespace
import unittest

from nlp_sample.analysis import AgentCore
from nlp_sample.workflow import ConversationSystem
from nlp_sample.review import (
    FIRST_QUESTION, CONFIRMATION, READY_RESPONSE,
    build_review_system, language_limits, walkthrough,
)

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
        self.assertEqual(len(manifest["selection"]), 10)
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

    def test_context_prompt_retains_confirmation_condition(self):
        instructions = self.agent.config["instrucciones"]
        marker = instructions.index("Include at the end: 'PROCESANDO_CONSULTA'")
        self.assertIn("user CONFIRMS", instructions[marker - 1])

    def test_excluded_sql_boundary_is_explicit(self):
        sql = AgentCore(str(ROOT / "prompts/sql_agent.json"), self.fixture, tools=[object()])
        with self.assertRaisesRegex(NotImplementedError, "private SQL executor"):
            sql.invoke(READY_RESPONSE)


class OriginalOrchestrationTests(unittest.TestCase):
    def test_clarification_pauses_before_sql_and_analyst(self):
        system, refinement, sql, analyst, events = build_review_system()
        result = system.process(FIRST_QUESTION, verbose=False)
        self.assertTrue(result["necesita_input"])
        self.assertFalse(result["conversation_complete"])
        self.assertEqual(sql.inputs, [])
        self.assertEqual(analyst.prompts, [])
        self.assertEqual(events, ["refinement_model_fixture"])
        self.assertEqual(len(refinement.prompts), 1)

    def test_confirmed_turn_transfers_exact_agent_output(self):
        system, refinement, sql, analyst, events = build_review_system()
        system.process(FIRST_QUESTION, verbose=False)
        result = system.process(CONFIRMATION, verbose=False)
        self.assertTrue(result["success"])
        self.assertTrue(result["conversation_complete"])
        self.assertFalse(result["necesita_input"])
        self.assertEqual(sql.inputs, [READY_RESPONSE])
        self.assertIn(FIRST_QUESTION, refinement.prompts[1])
        self.assertIn(CONFIRMATION, refinement.prompts[1])
        self.assertIn("review_fixture", analyst.prompts[0])
        self.assertEqual(events, ["refinement_model_fixture", "refinement_model_fixture",
                                  "sql_boundary_fixture", "analyst_model_fixture"])

    def test_completion_clears_context_and_retains_trace(self):
        system, _, _, _, _ = build_review_system()
        system.process(FIRST_QUESTION, verbose=False)
        system.process(CONFIRMATION, verbose=False)
        self.assertEqual(system.conversation_context, [])
        self.assertEqual(len(system.history), 1)
        self.assertIn("agent3_analisis", system.history[0]["flujo_completo"])

    def test_sql_error_stops_before_analyst(self):
        system, _, sql, analyst, events = build_review_system(sql_error=True)
        system.process(FIRST_QUESTION, verbose=False)
        result = system.process(CONFIRMATION, verbose=False)
        self.assertFalse(result["success"])
        self.assertEqual(result["agent"], "Agent 2")
        self.assertEqual(len(sql.inputs), 1)
        self.assertEqual(analyst.prompts, [])
        self.assertNotIn("analyst_model_fixture", events)

    def test_model_exception_is_reported_by_original_error_path(self):
        from unittest.mock import patch
        system, refinement, _, _, _ = build_review_system()
        with patch.object(refinement, "invoke", side_effect=RuntimeError("Synthetic failure")):
            result = system.process(FIRST_QUESTION, verbose=False)
        self.assertFalse(result["success"])
        self.assertEqual(result["agent"], "System")
        self.assertEqual(result["metadata"]["error_type"], "RuntimeError")

    def test_walkthrough_reports_fixture_origins(self):
        report = walkthrough()
        self.assertEqual(report["live_model_calls"], 0)
        self.assertEqual(report["database_calls"], 0)
        self.assertTrue(report["second_turn"]["sql_received_exact_agent1_output"])
        self.assertTrue(report["second_turn"]["context_cleared_after_completion"])
        self.assertIn("not an observed model answer", report["second_turn"]["response_origin"])

    def test_known_language_limitations_are_characterized_not_hidden(self):
        report = language_limits()
        self.assertEqual(len(report["cases"]), 4)
        observed = [case["observed_original_behavior"] for case in report["cases"]]
        self.assertEqual(observed, ["subpartida", None, 10, True])
        self.assertTrue(all(not case["matches_intended_interpretation"] for case in report["cases"]))


if __name__ == "__main__":
    unittest.main()

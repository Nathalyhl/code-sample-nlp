"""Review scaffolding around original methods; all model/SQL replies are fixtures."""
from copy import deepcopy
import json
from pathlib import Path
from types import SimpleNamespace

from .analysis import AgentCore
from .workflow import ConversationSystem

ROOT = Path(__file__).resolve().parents[1]
FIRST_QUESTION = "Quiero el top 5 de productos por valor FOB."
CONFIRMATION = "2024. Sí, confirmo."
READY_CONTEXT = {
    "pregunta_reformulada": "Top 5 productos por valor FOB en 2024",
    "fecha_declaracion_exportacion": {"año": 2024},
    "mostrar_fob": True,
    "mostrar_neto": False,
    "tipo_consulta": "ranking",
    "limite": 5,
    "revalidado": True,
}
READY_RESPONSE = json.dumps(READY_CONTEXT, ensure_ascii=False) + "\nPROCESANDO_CONSULTA"
ANALYST_FIXTURE = (
    "This is a scripted review response. No database query was executed "
    "and no trade findings are claimed."
)


class ScriptedModel:
    """An explicitly scripted test double, not a recorded or live model."""

    def __init__(self, name, replies, events):
        self.name = name
        self.replies = iter(replies)
        self.events = events
        self.prompts = []

    def invoke(self, prompt):
        self.prompts.append(prompt)
        self.events.append(self.name)
        return SimpleNamespace(content=next(self.replies))


class SqlBoundaryFixture:
    """Routing fixture at the excluded SQL boundary; never connects to a database.

    The empty result list is a placeholder payload, not a query result or a
    reproduction of the private executor's empty-result handling.
    """

    nombre = "Explicit SQL boundary fixture"

    def __init__(self, events, error=False):
        self.events = events
        self.inputs = []
        self.error = error

    def invoke(self, context):
        self.inputs.append(context)
        self.events.append("sql_boundary_fixture")
        if self.error:
            return {"error": True, "mensaje": "Scripted SQL-boundary error; no query executed"}
        return {
            "success": True,
            "query_sql": "[private SQL execution excluded from this review]",
            "resultados": [],
            "metadata": {"numero_filas": 0, "tiempo_ejecucion_ms": 0.0},
            "review_fixture": "Contract placeholder, not observed database output",
        }


def build_review_system(sql_error=False):
    events = []
    refinement = ScriptedModel("refinement_model_fixture", [
        "Which year should I use?\nNECESITO_MAS_INFO", READY_RESPONSE,
    ], events)
    analyst = ScriptedModel("analyst_model_fixture", [ANALYST_FIXTURE], events)
    agent1 = AgentCore(str(ROOT / "prompts/context.txt"), refinement)
    agent2 = SqlBoundaryFixture(events, error=sql_error)
    agent3 = AgentCore(str(ROOT / "prompts/analyst_agent.json"), analyst)
    system = ConversationSystem(agent1, agent2, agent3)
    return system, refinement, agent2, analyst, events


def walkthrough():
    """Compute an execution trace from the actual original process method."""
    system, refinement, sql, analyst, events = build_review_system()
    first = system.process(FIRST_QUESTION, verbose=False)
    first_trace = {
        "input": FIRST_QUESTION,
        "needs_input": first["necesita_input"],
        "conversation_complete": first["conversation_complete"],
        "sql_fixture_calls": len(sql.inputs),
        "events": list(events),
    }
    second = system.process(CONFIRMATION, verbose=False)
    return {
        "evidence_type": "Original orchestration executed with scripted boundary fixtures",
        "live_model_calls": 0,
        "database_calls": 0,
        "first_turn": first_trace,
        "second_turn": {
            "input": CONFIRMATION,
            "needs_input": second["necesita_input"],
            "conversation_complete": second["conversation_complete"],
            "sql_received_exact_agent1_output": sql.inputs[0] == READY_RESPONSE,
            "analyst_received_sql_placeholder": "review_fixture" in analyst.prompts[0],
            "previous_question_preserved": FIRST_QUESTION in refinement.prompts[1],
            "context_cleared_after_completion": system.conversation_context == [],
            "response_origin": "scripted analyst fixture; not an observed model answer",
        },
        "events": list(events),
    }


def inspect_helpers(text):
    agent = AgentCore.__new__(AgentCore)
    return agent._analizar_contexto(text)


def language_limits():
    """Compare four actual legacy behaviors with explicitly authored expectations."""
    cases = [
        ("top 5 departamentos por valor FOB en 2024", "dimension_agrupacion", "region_de_origen"),
        ("promedio por país en 2024", "dimension_agrupacion", "pais_destino_final"),
        ("primeros 5 países destino en 2024", "limit_valor", 5),
        ("no quiero un ranking de productos", "es_ranking", False),
    ]
    records = []
    for question, field, intended in cases:
        observed = inspect_helpers(question)[field]
        records.append({"input": question, "field": field,
                        "intended_interpretation_for_review": intended,
                        "observed_original_behavior": deepcopy(observed),
                        "matches_intended_interpretation": observed == intended})
    return {"evidence_type": "Diagnostic examples, not an NLP benchmark",
            "expectation_origin": "Review-authored interpretations",
            "observed_origin": "Executed original helpers, unchanged",
            "cases": records}

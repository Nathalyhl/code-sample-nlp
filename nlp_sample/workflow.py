"Selected original thesis methods for code review. See docs/SOURCE_MAP.json.\nPrivate database execution and infrastructure are intentionally omitted."

import json
from datetime import datetime
from typing import Any, Dict
from .analysis import AgentCore
from .support import log_message, handle_error


class ConversationSystem:
    def __init__(self, agent1: AgentCore, agent2: AgentCore, agent3: AgentCore):
        """Initialize the three-agent conversation state."""
        self.agent1 = agent1
        self.agent2 = agent2
        self.agent3 = agent3
        self.history = []
        self.verbose = False
        self.conversation_context = []
        log_message("ConversationSystem initialized WITH MEMORY")
        log_message(f"   Agent 1: {agent1.nombre}")
        log_message(f"   Agent 2: {agent2.nombre}")
        log_message(f"   Agent 3: {agent3.nombre}")

    def _construir_contexto_agent1(self) -> str:
        """Build the context prompt from previous conversation turns."""
        if not self.conversation_context:
            return "No previous context. This is the first query."
        lineas = ["=" * 70, "COMPLETE CONVERSATION HISTORY:", "=" * 70, ""]
        for i, msg in enumerate(self.conversation_context, 1):
            role = "User" if msg["role"] == "user" else "Assistant"
            content = msg["content"]
            if msg["role"] == "assistant" and len(content) > 300:
                content = content[:300] + "... [complete response omitted]"
            lineas.append(f"[Turn {i}] {role}:")
            lineas.append(content)
            lineas.append("")
        lineas.extend(
            [
                "=" * 70,
                "CRITICAL PROCESSING INSTRUCTIONS:",
                "=" * 70,
                "1. ANALYZE the entire previous conversation history",
                "2. EXTRACT information already provided",
                "3. Do NOT ask again for information ALREADY in the history",
                "4. ACCUMULATE variables from ALL previous turns",
                "5. If the user repeats information, UPDATE/CONFIRM your record",
                "",
                "ILLUSTRATIVE CONTEXT ACCUMULATION:",
                "- Turn 1: User says 'Valle del Cauca' -> Store the department",
                "- Turn 2: User says '2024' -> Store the period AND KEEP the department",
                "- Turn 3: User says 'ambos' -> Store FOB+Weight AND KEEP the period and department",
                "",
                "=" * 70,
                "",
            ]
        )
        return "\n".join(lineas)

    def _agent_necesita_input(self, output: str) -> bool:
        """Detect whether the context agent requests more information."""
        output_upper = output.upper()
        if "NECESITO_MAS_INFO" in output_upper:
            if self.verbose:
                log_message("Detected NECESITO_MAS_INFO")
            return True
        if "PROCESANDO_CONSULTA" in output_upper:
            if self.verbose:
                log_message("Detected PROCESANDO_CONSULTA")
            return False
        if "?" in output:
            if self.verbose:
                log_message("Detected '?' - heuristic")
            return True
        if self.verbose:
            log_message("No markers - continue")
        return False

    def process(self, user_message: str, verbose: bool = True) -> Dict[str, Any]:
        """Process one turn through clarification, SQL-agent handoff and results interpretation."""
        self.verbose = verbose
        try:
            if verbose:
                log_message("\n" + "=" * 70)
                log_message("NEW USER MESSAGE")
                log_message("=" * 70)
                log_message(f"Input: {user_message}")
                log_message(
                    f"Accumulated context: {len(self.conversation_context)} messages"
                )
                log_message("=" * 70)
            self.conversation_context.append(
                {
                    "role": "user",
                    "content": user_message,
                    "timestamp": datetime.now().isoformat(),
                }
            )
            contexto_completo = self._construir_contexto_agent1()
            if verbose:
                log_message("\nCONTEXT SENT TO AGENT 1:")
                log_message("-" * 70)
                preview = contexto_completo[:800] + (
                    "..." if len(contexto_completo) > 800 else ""
                )
                log_message(preview)
                log_message("-" * 70)
            if verbose:
                log_message("\nAGENT 1: Processing with complete context...")
            agent1_output = self.agent1.invoke(contexto_completo)
            self.conversation_context.append(
                {
                    "role": "assistant",
                    "content": agent1_output,
                    "timestamp": datetime.now().isoformat(),
                }
            )
            if verbose:
                log_message("\nAGENT 1 OUTPUT:")
                log_message("-" * 70)
                log_message(agent1_output)
                log_message("-" * 70)
            necesita_input = self._agent_necesita_input(agent1_output)
            if verbose:
                log_message(f"\nNeeds more input? {necesita_input}")
            if necesita_input:
                if verbose:
                    log_message("WORKFLOW PAUSED - Waiting for more information")
                    log_message(
                        f"Total messages in context: {len(self.conversation_context)}"
                    )
                    log_message("=" * 70)
                return {
                    "success": True,
                    "necesita_input": True,
                    "respuesta": agent1_output,
                    "agent": "Agent 1",
                    "conversation_complete": False,
                    "metadata": {
                        "timestamp": datetime.now().isoformat(),
                        "mensaje_usuario": user_message,
                        "contexto_acumulado": len(self.conversation_context),
                        "turnos_conversacion": len(
                            [
                                m
                                for m in self.conversation_context
                                if m["role"] == "user"
                            ]
                        ),
                    },
                }
            if verbose:
                log_message("\nCONTINUING WORKFLOW - Agent 1 completed collection")
                log_message("AGENT 2: Executing SQL...")
            agent2_output = self.agent2.invoke(agent1_output)
            if verbose:
                log_message("\nAGENT 2 OUTPUT:")
                log_message("-" * 70)
                if isinstance(agent2_output, dict):
                    log_message(
                        f"   SQL: {agent2_output.get('query_sql', 'N/A')[:100]}..."
                    )
                    log_message(
                        f"   Rows: {agent2_output.get('metadata', {}).get('numero_filas', 0)}"
                    )
                log_message("-" * 70)
            if isinstance(agent2_output, dict) and agent2_output.get("error"):
                log_message("Error in Agent 2", level="ERROR")
                return {
                    "success": False,
                    "conversation_complete": True,
                    "agent": "Agent 2",
                    "error_message": agent2_output.get("mensaje", "SQL error"),
                    "respuesta": f"Error: {agent2_output.get('mensaje', 'SQL error')}",
                    "flujo_completo": {
                        "agent1_recopilacion": agent1_output,
                        "agent2_ejecucion": agent2_output,
                    },
                    "metadata": {
                        "timestamp": datetime.now().isoformat(),
                        "mensaje_usuario": user_message,
                    },
                }
            if verbose:
                log_message("\nAGENT 3: Analyzing results...")
            contexto = (
                agent1_output[:500] if len(agent1_output) > 500 else agent1_output
            )
            resultados = json.dumps(agent2_output, indent=2, ensure_ascii=False)
            agent3_input = f"Analyze the following SQL query results:\n\nCONTEXT:\n{contexto}\n\nRESULTS:\n{resultados}\n\nGenerate a concise, actionable executive analysis."
            agent3_output = self.agent3.invoke(agent3_input)
            if verbose:
                log_message("\nAGENT 3 OUTPUT:")
                log_message("-" * 70)
                preview = agent3_output[:500] + (
                    "..." if len(agent3_output) > 500 else ""
                )
                log_message(preview)
                log_message("-" * 70)
            resultado_final = {
                "success": True,
                "conversation_complete": True,
                "necesita_input": False,
                "flujo_completo": {
                    "agent1_recopilacion": agent1_output,
                    "agent2_ejecucion": agent2_output,
                    "agent3_analisis": agent3_output,
                },
                "respuesta_final": agent3_output,
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "mensaje_usuario": user_message,
                    "agentes_ejecutados": ["Agent 1", "Agent 2", "Agent 3"],
                    "tiempo_total_ms": self._calcular_tiempo_total(agent2_output),
                    "turnos_conversacion_total": len(
                        [m for m in self.conversation_context if m["role"] == "user"]
                    ),
                },
            }
            self.history.append(resultado_final)
            self.conversation_context = []
            if verbose:
                log_message("\nCONVERSATION COMPLETED")
                log_message("Conversation context cleared (complete workflow)")
                log_message("=" * 70)
            return resultado_final
        except Exception as e:
            handle_error("Conversation error", e)
            error_response = {
                "success": False,
                "conversation_complete": True,
                "necesita_input": False,
                "agent": "System",
                "error_message": str(e),
                "respuesta": f"Error: {str(e)}",
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "mensaje_usuario": user_message,
                    "error_type": type(e).__name__,
                },
            }
            self.history.append(error_response)
            return error_response

    def _calcular_tiempo_total(self, agent2_output: Dict[str, Any]) -> float:
        """Return the SQL duration supplied by Agent 2; this is not full workflow latency."""
        if isinstance(agent2_output, dict):
            return agent2_output.get("metadata", {}).get("tiempo_ejecucion_ms", 0.0)
        return 0.0

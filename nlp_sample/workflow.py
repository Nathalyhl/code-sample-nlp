'Selected original thesis methods for code review. See docs/SOURCE_MAP.json.\nThe remaining production methods and infrastructure are intentionally omitted.'
from .analysis import AgentCore
from .support import log_message


class ConversationSystem:
    def __init__(self, agent1: AgentCore, agent2: AgentCore, agent3: AgentCore):
        """Initialize the three-agent conversation state."""
        self.agent1 = agent1
        self.agent2 = agent2
        self.agent3 = agent3
        self.history = []
        self.verbose = False
        self.conversation_context = []
        log_message('ConversationSystem initialized WITH MEMORY')
        log_message(f'   Agent 1: {agent1.nombre}')
        log_message(f'   Agent 2: {agent2.nombre}')
        log_message(f'   Agent 3: {agent3.nombre}')

    def _construir_contexto_agent1(self) -> str:
        """Build the context prompt from previous conversation turns."""
        if not self.conversation_context:
            return 'No previous context. This is the first query.'
        lineas = ['=' * 70, 'COMPLETE CONVERSATION HISTORY:', '=' * 70, '']
        for i, msg in enumerate(self.conversation_context, 1):
            role = 'User' if msg['role'] == 'user' else 'Assistant'
            content = msg['content']
            if msg['role'] == 'assistant' and len(content) > 300:
                content = content[:300] + '... [complete response omitted]'
            lineas.append(f'[Turn {i}] {role}:')
            lineas.append(content)
            lineas.append('')
        lineas.extend(['=' * 70, 'CRITICAL PROCESSING INSTRUCTIONS:', '=' * 70, '1. ANALYZE the entire previous conversation history', '2. EXTRACT information already provided', '3. Do NOT ask again for information ALREADY in the history', '4. ACCUMULATE variables from ALL previous turns', '5. If the user repeats information, UPDATE/CONFIRM your record', '', 'ILLUSTRATIVE CONTEXT ACCUMULATION:', "- Turn 1: User says 'Valle del Cauca' -> Store the department", "- Turn 2: User says '2024' -> Store the period AND KEEP the department", "- Turn 3: User says 'ambos' -> Store FOB+Weight AND KEEP the period and department", '', '=' * 70, ''])
        return '\n'.join(lineas)

    def _agent_necesita_input(self, output: str) -> bool:
        """Detect whether the context agent requests more information."""
        output_upper = output.upper()
        if 'NECESITO_MAS_INFO' in output_upper:
            if self.verbose:
                log_message('Detected NECESITO_MAS_INFO')
            return True
        if 'PROCESANDO_CONSULTA' in output_upper:
            if self.verbose:
                log_message('Detected PROCESANDO_CONSULTA')
            return False
        if '?' in output:
            if self.verbose:
                log_message("Detected '?' - heuristic")
            return True
        if self.verbose:
            log_message('No markers - continue')
        return False

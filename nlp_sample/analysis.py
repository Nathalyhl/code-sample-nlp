'Selected original thesis methods for code review. See docs/SOURCE_MAP.json.\nThe remaining production methods and infrastructure are intentionally omitted.'
import json
import re
from typing import Any, Dict, Optional
from .support import log_message, handle_error


class AgentCore:
    def __init__(self, config_path: str, llm, tools: Optional[list]=None):
        """Load an agent from its JSON configuration."""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                if isinstance(config, list):
                    config = config[0]
            self.config = config
            self.llm = llm
            self.tools = tools or []
            self.nombre = config['nombre']
            self.tipo = config['tipo']
            self.system_prompt = self._build_prompt_from_json()
            log_message(f'Agent loaded: {self.nombre}')
            log_message(f'   Type: {self.tipo}')
            log_message(f'   Tools: {len(self.tools)}')
        except Exception as e:
            handle_error(f'Error initializing AgentCore from {config_path}', e)
            raise

    def _build_prompt_from_json(self) -> str:
        """Build the model prompt from configuration sections."""
        sections = []
        sections.append(f"# {self.config['nombre']}")
        sections.append(f"**Role:** {self.config['tipo']}")
        sections.append(f"**Objective:** {self.config['objetivo']}\n")
        if self.config.get('instrucciones'):
            sections.append('## DETAILED INSTRUCTIONS:')
            sections.extend(self.config['instrucciones'])
            sections.append('')
        if self.config.get('validaciones_previas'):
            sections.append('## REQUIRED VALIDATIONS:')
            for val in self.config['validaciones_previas']:
                sections.append(f'- {val}')
            sections.append('')
        if self.config.get('ejemplos'):
            sections.append('## REFERENCE EXAMPLES:')
            for i, ejemplo in enumerate(self.config['ejemplos'], 1):
                sections.append(f"\n### Example {i}: {ejemplo.get('nombre', 'Unnamed')}")
                sections.append('```json')
                sections.append(json.dumps(ejemplo, indent=2, ensure_ascii=False))
                sections.append('```')
            sections.append('')
        if self.config.get('formato_salida_agente3'):
            sections.append('## OUTPUT FORMAT:')
            sections.append('```json')
            sections.append(json.dumps(self.config['formato_salida_agente3'], indent=2, ensure_ascii=False))
            sections.append('```')
            sections.append('')
        if self.config.get('notas_adicionales'):
            sections.append('## IMPORTANT NOTES:')
            for nota in self.config['notas_adicionales']:
                sections.append(f'- {nota}')
        return '\n'.join(sections)

    def invoke(self, input_data: str) -> Any:
        """Invoke the configured language model or dispatch to the omitted SQL executor."""
        try:
            if self.tools and self.tipo == 'constructor_ejecutor_sql_redshift':
                return self._invoke_with_sql_execution(input_data)
            full_prompt = f"{self.system_prompt}\n\n{'=' * 70}\nUSER/PREVIOUS AGENT INPUT:\n{'=' * 70}\n\n{input_data}\n\n{'=' * 70}\nYOUR RESPONSE:\n{'=' * 70}\n"
            response = self.llm.invoke(full_prompt)
            return response.content.strip()
        except Exception as e:
            handle_error(f'Error invoking agent {self.nombre}', e)
            raise

    def _analizar_contexto(self, input_data: str) -> Dict[str, Any]:
        """Detect the query type from its textual context."""
        texto_lower = input_data.lower()
        contexto = {'tipo_consulta': 'totales_generales', 'necesita_groupby': False, 'dimension_agrupacion': None, 'necesita_orderby': False, 'necesita_limit': False, 'limit_valor': None, 'es_promedio': False, 'es_ranking': False}
        if any((palabra in texto_lower for palabra in ['top', 'principales', 'mayores', 'ranking', 'primeros'])):
            contexto['es_ranking'] = True
            contexto['tipo_consulta'] = 'top_n'
            contexto['necesita_groupby'] = True
            contexto['necesita_orderby'] = True
            dimension = self._detectar_agrupacion(input_data)
            if dimension:
                contexto['dimension_agrupacion'] = dimension
            else:
                contexto['dimension_agrupacion'] = 'pais_destino_final'
            limit_match = re.search('top\\s+(\\d+)', texto_lower)
            if limit_match:
                contexto['limit_valor'] = int(limit_match.group(1))
                contexto['necesita_limit'] = True
            else:
                contexto['limit_valor'] = 10
                contexto['necesita_limit'] = True
        elif any((palabra in texto_lower for palabra in ['promedio', 'media', 'average'])):
            contexto['es_promedio'] = True
            contexto['tipo_consulta'] = 'promedio'
        elif any((palabra in texto_lower for palabra in ['por departamento', 'por país', 'por empresa'])):
            contexto['necesita_groupby'] = True
            contexto['tipo_consulta'] = 'desglose_por_dimension'
            if 'por país' in texto_lower or 'por pais' in texto_lower:
                contexto['dimension_agrupacion'] = 'pais_destino_final'
            elif 'por departamento' in texto_lower:
                contexto['dimension_agrupacion'] = 'region_de_origen'
            elif 'por empresa' in texto_lower:
                contexto['dimension_agrupacion'] = 'razon_social_exportador'
        return contexto

    def _detectar_agrupacion(self, contexto: str) -> Optional[str]:
        """Detect the grouping dimension from textual context."""
        contexto_lower = contexto.lower()
        if any((palabra in contexto_lower for palabra in ['top', 'principales', 'mayores', 'ranking'])):
            log_message(f"DEBUG: Detecting ranking type in: '{contexto}'", level='DEBUG')
            if any((palabra in contexto_lower for palabra in ['productos', 'producto', 'subpartida'])):
                log_message('DEBUG: PRODUCT ranking', level='DEBUG')
                return 'subpartida'
            elif any((palabra in contexto_lower for palabra in ['empresas', 'empresa', 'exportadores', 'exportador', 'compañías'])):
                log_message('DEBUG: COMPANY ranking', level='DEBUG')
                return 'razon_social_exportador'
            elif any((palabra in contexto_lower for palabra in ['departamento', 'departamentos', 'regiones'])) and any((palabra in contexto_lower for palabra in ['exportan', 'exportaron', 'venden', 'vendieron'])):
                log_message('DEBUG: Exporting DEPARTMENT ranking', level='DEBUG')
                return 'region_de_origen'
            elif any((palabra in contexto_lower for palabra in ['países', 'paises', 'destino', 'destinos'])):
                log_message('DEBUG: DESTINATION COUNTRY ranking', level='DEBUG')
                return 'pais_destino_final'
            else:
                log_message('DEBUG: Ranking without a dimension - defaulting to PRODUCTS', level='DEBUG')
                return 'subpartida'
        if 'por país' in contexto_lower or 'países' in contexto_lower:
            return 'pais_destino_final'
        elif 'por departamento' in contexto_lower or 'departamentos' in contexto_lower:
            return 'region_de_origen'
        elif 'por empresa' in contexto_lower or 'empresas' in contexto_lower:
            return 'razon_social_exportador'
        elif 'por producto' in contexto_lower or 'productos' in contexto_lower:
            return 'subpartida'
        return None

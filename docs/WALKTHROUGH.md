# Reading a complete conversation path

This is a reading guide to the original `ConversationSystem.process` implementation. The example questions and boundary responses were scripted for review. They are not institutional conversations, recorded model outputs or database results.

## Files to keep open

- `nlp_sample/workflow.py`: the original controller, including `process`.
- `nlp_sample/analysis.py`: original prompt construction and model invocation.
- `prompts/context.txt`: selected refinement-agent instructions, including the confirmation condition.
- `nlp_sample/review.py`: separately identified test scaffolding that supplies boundary fixtures.

## Turn 1: an incomplete analytical question

Illustrative user input: **“Quiero el top 5 de productos por valor FOB.”**

The question expresses a product ranking and a monetary metric but supplies no period. In the full application, a pretrained model would interpret this input under the refinement-agent instructions. The offline review deliberately provides this scripted model reply:

```text
Which year should I use?
NECESITO_MAS_INFO
```

The original controller performs observable work around that response:

1. Append the user message to `conversation_context`.
2. Build a history prompt with `_construir_contexto_agent1`.
3. Call `agent1.invoke` and append its response.
4. Use `_agent_necesita_input` to detect `NECESITO_MAS_INFO`.
5. Return `necesita_input=True` and `conversation_complete=False`.

Agent 2 and Agent 3 are not called. The two messages remain available for the next turn. Those routing and state properties are checked by tests. The fixture itself does not demonstrate that an LLM can detect the missing year.

## Turn 2: supply the year and confirm

Illustrative input: **“2024. Sí, confirmo.”**

The controller rebuilds context with the earlier question and the current message. The scripted refinement response contains the following illustrative structured fields, followed by `PROCESANDO_CONSULTA`:

```json
{
  "pregunta_reformulada": "Top 5 productos por valor FOB en 2024",
  "fecha_declaracion_exportacion": {"año": 2024},
  "mostrar_fob": true,
  "mostrar_neto": false,
  "tipo_consulta": "ranking",
  "limite": 5,
  "revalidado": true
}
```

These field values are authored expectations for this example, not an observed extraction result from a model. Their Spanish identifiers match the original project interface.

The original controller detects that more input is not requested and passes **the exact first-agent output** to `agent2.invoke`. That handoff is directly tested; the review harness does not replace the controller with a new implementation.

## The SQL boundary

The complete database executor is intentionally private. Its integration point is represented by an explicit `SqlBoundaryFixture`. The fixture records the received context and returns a marked contract placeholder with no observed result rows and no executable SQL.

The placeholder exercises the controller's success route. It does not reproduce the private executor's behavior on a real empty query, verify a SQL translation, or establish database correctness. A separate test returns a scripted error and verifies that the original controller stops before calling the analyst.

The selected `AgentCore.invoke` method also retains its original SQL-dispatch branch. A newly identified exclusion guard now raises `NotImplementedError` at that boundary instead of leaving a reference to an absent method. This guard is review scaffolding, not historical thesis logic.

## Results interpretation and completion

The controller serializes the Agent 2 payload and combines it with context from Agent 1. It sends that input to Agent 3. The real model-dependent task would be to explain genuine query results; the offline reply instead says explicitly that it is scripted and makes no trade findings.

The original controller then places the outputs in `flujo_completo`, appends the final record to `history` and clears `conversation_context`. Tests check that earlier input reached the second refinement prompt, that the SQL placeholder reached the analyst, and that active context was cleared after completion.

## What the example establishes

| Evidence | Established here | Still requires separate evaluation |
| --- | --- | --- |
| Original controller executed | Clarification, handoff order and successful completion | Correct interpretation by a real model |
| Original prompt/invocation methods executed | Context and instructions reach the supplied model interface | Prompt effectiveness across diverse questions |
| SQL boundary fixture | Exact input transfer and controlled error routing | Real SQL generation, permissions and query results |
| Recorded state transitions | Context retention and success-path cleanup | Deployed session ownership and concurrent use |

The helper `_calcular_tiempo_total` returns the SQL duration supplied by Agent 2. Its name should not be interpreted as a measurement of the entire conversation's latency. Fixture timing values are placeholders, not performance results.

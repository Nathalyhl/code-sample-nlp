# Review notes and limitations

## What a reviewer can examine

The selected source supports a review of applied NLP in a larger data project: agent prompt construction, language-model invocation, lexical intent detection, grouping selection, conversational context and clarification handling.

In `AgentCore`, `_analizar_contexto` distinguishes totals, averages, rankings and dimension-based breakdowns. `_detectar_agrupacion` maps textual cues to fields such as product, exporter, origin department or destination. These are the original project's helpers, including their vocabulary and defaults.

In `ConversationSystem`, `_construir_contexto_agent1` renders prior turns and instructions for the refinement agent. `_agent_necesita_input` checks the original protocol markers, then uses a question-mark heuristic. The sample retains those behaviors rather than silently redesigning them.

## Provenance and editorial changes

`SOURCE_MAP.json` records original relative file names, source hashes, method ranges and selected JSON instruction indices. The original files were read without modification. The ten published methods were compared with the originals at syntax-tree level after reversing the explicitly mapped English text translations and removing docstrings.

The editorial changes are normalized formatting, omitted source comments, English docstrings and translations of diagnostic/prompt presentation text. Function names, compatibility keys, Spanish lexical patterns and protocol markers are retained. The selected agent JSON files contain translated excerpts of original instructions; omitted instructions are not implicitly claimed to be present.

The original `process` method and its timing helper now complete the selected conversation path. The original code and collaborative research predate this portfolio packaging. The local entry point, logging adapter, tests, source manifest and English review documentation are later scaffolding and editorial work. They should not be described as unchanged historical thesis artifacts.

## Synthetic examples

The question file contains illustrative inputs authored for review. It does not contain model-generated answers or real institutional queries. The console demonstration computes outputs from the selected original helpers. A model test double has a fixed, clearly labeled response solely to exercise the invocation boundary.

No AWS identity, database, real model or export dataset is used. No export totals, precision/recall, semantic accuracy percentage or generalization score is reported. A successful fixture test establishes only the behavior exercised by that fixture.

## Limitations visible in the original source

- Matching uses lowercase text and a finite vocabulary, mainly Spanish; it does not provide broad multilingual coverage or robust morphological analysis.
- A ranking without an explicit number defaults to 10, and a ranking without a recognized dimension can default to products. These are implementation choices, not proof that the user's intended meaning was recovered.
- Context assembly truncates assistant messages longer than 300 characters. Previous user messages and assistant messages can influence later interpretation.
- Marker detection uses substring matching. Without a marker, a question mark can trigger clarification; otherwise it permits progression. This can misclassify model responses.
- The selected `invoke` method retains its original SQL-dispatch branch. An explicitly labeled review-only guard raises `NotImplementedError` at that excluded boundary. The harness injects a separate contract fixture into the original controller.
- Original agent instructions express desired behavior; they do not guarantee that a language model avoids factual errors or follows every constraint.

These limits are retained and documented so that the sample is a faithful representation of the selected work.

## Further evaluation

A research evaluation could independently label natural-language questions, compare interpretations against reference fields, assess clarification quality and test SQL execution equivalence. It should record the actual model/version, inference settings, prompts, repeated-run variation and relevant error categories. Those experiments are proposed next steps, not completed results in this repository.


## Executed language diagnostics

`python -m nlp_sample --limits` computes the following outputs from the unchanged original helpers. Intended interpretations are newly authored review expectations, not independent reference annotations.

| Input | Intended interpretation for review | Observed original behavior |
| --- | --- | --- |
| “top 5 departamentos por valor FOB en 2024” | Group by `region_de_origen` | Groups by `subpartida` |
| “promedio por país en 2024” | Average grouped by `pais_destino_final` | Sets average intent but omits grouping |
| “primeros 5 países destino en 2024” | Limit of 5 | Uses the default limit of 10 |
| “no quiero un ranking de productos” | Do not treat as an affirmative ranking | Marks ranking intent |

These cases expose defaults, limited numeric-expression recognition, mutually exclusive intent branches and absent negation handling. Characterization tests retain the observed behavior so that packaging changes cannot silently claim to have repaired the original algorithms. A separate, explicitly labeled revision would be needed to change that behavior.

## Evidence from the complete control-flow example

The [walkthrough](WALKTHROUGH.md) executes the original `process` method with scripted model and SQL boundaries. Tests verify a clarification turn, a confirmed handoff, payload transfer to the analyst, success-path context cleanup, a SQL-boundary error and a model exception. This is implementation evidence, not a measure of text-understanding accuracy.

The original exception path returns exception text, and some error routes retain active context. The timing helper reports Agent 2's supplied SQL duration rather than the full pipeline latency. Those historical behaviors remain visible; production hardening and performance evaluation are outside this selection.

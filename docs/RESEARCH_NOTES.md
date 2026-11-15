# Review notes and limitations

## What a reviewer can examine

The selected source supports a review of applied NLP in a larger data project: agent prompt construction, language-model invocation, lexical intent detection, grouping selection, conversational context and clarification handling.

In `AgentCore`, `_analizar_contexto` distinguishes totals, averages, rankings and dimension-based breakdowns. `_detectar_agrupacion` maps textual cues to fields such as product, exporter, origin department or destination. These are the original project's helpers, including their vocabulary and defaults.

In `ConversationSystem`, `_construir_contexto_agent1` renders prior turns and instructions for the refinement agent. `_agent_necesita_input` checks the original protocol markers, then uses a question-mark heuristic. The sample retains those behaviors rather than silently redesigning them.

## Provenance and editorial changes

`SOURCE_MAP.json` records original relative file names, source hashes, method ranges and selected JSON instruction indices. The original files were read without modification. The eight published methods were compared with the originals at syntax-tree level after reversing the explicitly mapped English text translations and removing docstrings.

The editorial changes are normalized formatting, omitted source comments, English docstrings and translations of diagnostic/prompt presentation text. Function names, compatibility keys, Spanish lexical patterns and protocol markers are retained. The selected agent JSON files contain translated excerpts of original instructions; omitted instructions are not implicitly claimed to be present.

The original code and collaborative research predate this portfolio packaging. The local entry point, logging adapter, tests, source manifest and English review documentation are later scaffolding and editorial work. They should not be described as unchanged historical thesis artifacts.

## Synthetic examples

The question file contains illustrative inputs authored for review. It does not contain model-generated answers or real institutional queries. The console demonstration computes outputs from the selected original helpers. A model test double has a fixed, clearly labeled response solely to exercise the invocation boundary.

No AWS identity, database, real model or export dataset is used. No export totals, precision/recall, semantic accuracy percentage or generalization score is reported. A successful fixture test establishes only the behavior exercised by that fixture.

## Limitations visible in the original source

- Matching uses lowercase text and a finite vocabulary, mainly Spanish; it does not provide broad multilingual coverage or robust morphological analysis.
- A ranking without an explicit number defaults to 10, and a ranking without a recognized dimension can default to products. These are implementation choices, not proof that the user's intended meaning was recovered.
- Context assembly truncates assistant messages longer than 300 characters. Previous user messages and assistant messages can influence later interpretation.
- Marker detection uses substring matching. Without a marker, a question mark can trigger clarification; otherwise it permits progression. This can misclassify model responses.
- The selected `invoke` method retains a branch to the full SQL executor, which is outside this excerpt. That branch is not used by the review harness.
- Original agent instructions express desired behavior; they do not guarantee that a language model avoids factual errors or follows every constraint.

These limits are retained and documented so that the sample is a faithful representation of the selected work.

## Further evaluation

A research evaluation could independently label natural-language questions, compare interpretations against reference fields, assess clarification quality and test SQL execution equivalence. It should record the actual model/version, inference settings, prompts, repeated-run variation and relevant error categories. Those experiments are proposed next steps, not completed results in this repository.

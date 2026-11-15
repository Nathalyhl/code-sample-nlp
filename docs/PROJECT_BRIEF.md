# Project brief

## Research context

The master's project concerned the optimization of Colombian export microdata through an automated data system and an LLM-based multi-agent query chatbot. Its institutional setting was economic analysis at the Cámara de Comercio de Cali, where historical files needed to be prepared and consulted efficiently.

Nathaly Henao Lugo participated across the data-engineering and chatbot phases. The original research was authored jointly with Alejandro Perez Lugo and Mauricio Guzmán Arango. This portfolio presents selected evidence from that work, while keeping its complete source and institutional materials separate.

## Data engineering phase

The broader project combined Python data preparation, Apache Airflow task orchestration and AWS storage/query services. Its architecture followed monthly export files through transformation and storage toward an analytical warehouse, using S3, Parquet, Glue and Redshift.

The work involved understanding historical variables, arranging a coherent analytical schema, managing processing dates and coordinating dependent tasks. This data infrastructure supplied the setting in which the conversational interface could answer meaningful questions.

Only the architecture is described here. The full ingestion pipeline, warehouse configuration, Glue implementation, institutional rows and deployment settings are outside this sample. This repository does not claim to have independently verified every cloud component described in the thesis.

## Conversational NLP phase

The chatbot assigned complementary responsibilities to three agents:

1. **Query refinement:** identify the user's period and requested metric, collect optional filters and ask for confirmation before progressing.
2. **SQL work:** combine structured parameters with the interpreted natural-language request to prepare and execute an analytical query.
3. **Results interpretation:** explain the returned data for a nontechnical reader.

The selected original Python methods show how agent configuration becomes a prompt, how a model is invoked, how rankings and grouping dimensions are detected, and how previous conversation turns are supplied to the first agent, and how the original controller pauses, transfers outputs and completes the chain. Selected instructions from all three original configuration files explain the intended division of work.

## What was selected

The ten methods are selected from two original source files, not taken from a newly invented language analyzer. Their names and control flow remain intact. English presentation edits are recorded in the source map. The original method driving the three-agent chain is included. Complete database execution remains outside the sample and is represented by an explicit review-only boundary.

This boundary allows a reviewer to inspect representative implementation decisions without receiving the complete platform. The reviewer can see both the wider architecture and concrete code for language-related operations.

## Engineering decisions and tradeoffs

| Decision in the original code | Purpose | Limit to discuss |
| --- | --- | --- |
| Agent instructions in JSON | Separate role instructions from invocation code | Prompt quality still needs empirical evaluation |
| A shared prompt-construction method | Keep configuration sections organized | Selected configurations omit parts of the full setup |
| Explicit conversational history | Let the model reuse information from earlier turns | Long assistant messages are truncated; history is not unbounded model memory |
| Response markers | Distinguish clarification from progression | A question-mark fallback and substring matching are heuristic |
| Context and grouping helpers | Supply query-shaping cues for rankings and averages | Vocabulary and defaults can misinterpret ambiguous requests |
| Separate agent roles | Organize refinement, SQL work and explanation | Responsibility separation alone cannot ensure correct answers |

## Scope of the evidence

The original project applied pretrained LLMs; it did not involve training a new foundation model. This sample demonstrates source design and selected helper behavior. It does not assert a new NLP benchmark, deployment performance or independently confirmed thesis timing measurements.

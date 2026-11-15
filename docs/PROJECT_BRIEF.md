# Project brief

## Problem and contribution

The master's project, **Optimization of export microdata with an automated system and an LLM-based multi-agent query chatbot**, connected a data pipeline with a natural-language interface. Its institutional context was the analysis of Colombian exports at the Cámara de Comercio de Cali. The source records contain structured trade attributes such as dates, destinations, product classifications, values and weights.

The project treated reliable data preparation and reliable question interpretation as connected problems. A correct natural-language interpretation is useful only if its fields map to a coherent schema; a well-maintained warehouse becomes more accessible when analysts can ask questions conversationally.

Nathaly Henao Lugo contributed across data engineering, orchestration and the chatbot workflow. The research was a joint project with Alejandro Perez Lugo and Mauricio Guzmán Arango. This portfolio preserves that distinction between individual participation and joint authorship.

## Complete system architecture

### Data preparation and orchestration

The data workflow acquires monthly DIAN files, checks their structure, converts them into a consistent analytical representation and coordinates storage and loading. Python supplies the transformation logic, Airflow coordinates tasks, and the AWS architecture uses S3, Glue and Redshift.

Important engineering concerns include logical processing dates, schema consistency, null values, duplicate handling, reproducible transformations, task failures and repeated loads. These concerns establish the context for the NLP component without requiring the reviewer to receive the complete pipeline implementation.

### Conversational understanding

The first agent interprets the user's request and gathers the information required for analysis. Period and metric are essential. Optional information may include destination, origin, product or exporter, depending on the complete system's schema. Missing information triggers a clarification turn.

The key intermediate artifact is a structured representation of meaning. Separating that representation from SQL makes it possible to inspect what the system understood before it accesses data.

### Query generation and execution

The second agent maps the structured request to a SQL query. The maintained application validates the query independently at the database boundary and uses a read-only transaction. This distinction matters: syntactically valid model output can still express the wrong question, so meaning and executable behavior need separate checks.

The local sample uses a restricted SQL compiler with bound values and an in-memory, query-only SQLite database. This enables a reviewer to trace question interpretation into actual executed results without an AWS account. It demonstrates the boundary design rather than reproducing the complete Redshift deployment.

### Results interpretation

The third agent in the wider project converts query results into a comprehensible response. Its evidence is the validated question and returned rows. Explanations should preserve units, distinguish totals from rankings and avoid unsupported market narratives.

The sample uses deterministic answer formatting to make this last stage reproducible. It demonstrates evidence flow; it does not measure an LLM's ability to generate accurate prose.

## Selected implementation decisions

| Decision | Purpose | Tradeoff |
| --- | --- | --- |
| Explicit semantic object | Inspect and evaluate interpretation before SQL | Only supported meanings can be represented |
| Separate analyzer and workflow | Compare language backends without replacing execution | Backend correctness still requires empirical evaluation |
| Clarification and rejection outcomes | Make uncertainty observable | Conservative rules reduce coverage |
| Per-conversation state | Resolve follow-ups without sharing another user's context | A deployed service must enforce session ownership |
| Parameterized query construction | Keep values separate from SQL structure | This sample supports a limited query vocabulary |
| Synthetic data and a local backend | Let reviewers reproduce the workflow safely | Institutional data quality and cloud behavior are not exercised |

## Relationship between the thesis and this sample

The thesis documents the full system and its development. The maintained private project contains a later English revision and engineering checks. This repository is a new, deliberately selected adaptation for code review.

The semantic extraction, conversation flow and separation of agents reflect the broader project. The offline rules, small SQLite dataset and diagnostic evaluation were prepared specifically for this sample. Their measured results belong to this sample alone.

The thesis discusses additional components such as vector memory and authentication. Those features are not demonstrated here, and the sample does not claim to verify every component described in the thesis. Historical timing claims are also excluded from this repository's evaluation.

## What a reviewer can assess

A reviewer can inspect how the code normalizes text, represents intent, handles missing information, preserves explicit conversational context, validates model output, constructs a bounded database operation and traces the final answer to returned rows. The evaluation retains unsuccessful paraphrases, allowing discussion of the difference between implementation reliability and linguistic generalization.

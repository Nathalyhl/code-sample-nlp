"""Analyze user text into a validated semantic representation.

The offline rules are a transparent reference baseline created for this sample.
The thesis system delegated language understanding to pretrained LLM agents.
"""
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
import unicodedata
from typing import Callable


@dataclass(frozen=True)
class Query:
    start_year: int
    end_year: int
    metric: str
    operation: str = "total"
    destination: str | None = None
    top_k: int = 5

    def __post_init__(self):
        if any(type(y) is not int or not 1900 <= y <= 2099 for y in (self.start_year, self.end_year)):
            raise ValueError("Years must be integers from 1900 through 2099")
        if self.start_year > self.end_year:
            raise ValueError("The start year must not exceed the end year")
        if self.metric not in {"fob_usd", "net_weight_kg", "operations"}:
            raise ValueError("Unsupported metric")
        if self.operation not in {"total", "ranking"}:
            raise ValueError("Unsupported operation")
        if self.destination not in {None, "Chile", "Peru", "Mexico", "United States", "China", "Ecuador"}:
            raise ValueError("Unsupported destination")
        if type(self.top_k) is not int or not 1 <= self.top_k <= 50:
            raise ValueError("The ranking size must be from 1 through 50")
        if self.operation == "ranking" and self.destination:
            raise ValueError("A destination ranking cannot also filter one destination")


@dataclass(frozen=True)
class Analysis:
    decision: str
    reason: str
    query: Query | None = None

    def to_dict(self):
        return asdict(self)


def normalize(text: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", text.casefold())
                   if not unicodedata.combining(c))


class RuleAnalyzer:
    """Conservative English/Spanish patterns with explicit abstention."""

    def analyze(self, text: str, previous: Query | None = None) -> Analysis:
        if not isinstance(text, str) or not text.strip() or len(text) > 2000:
            return Analysis("clarify", "invalid_input")
        value = normalize(text)
        if re.search(r"\b(ignore|instructions|drop|delete|password|secret|ignora|borra)\b", value):
            return Analysis("reject", "unsafe_request")
        if re.search(r"\b(compare|except|excluding|without|not|monthly|month|profit|price|gdp|comparar|excepto|mensual|mes|ganancia)\b", value):
            return Analysis("clarify", "unsupported_request")
        followup = bool(re.match(r"\s*(now|and|ahora|y)\b", value)) and previous is not None
        years = [int(y) for y in re.findall(r"\b(?:19|20)\d{2}\b", value)]
        if len(years) > 2 or (len(years) == 2 and not re.search(r"\b(between|from|through|entre|desde)\b", value)):
            return Analysis("clarify", "ambiguous_period")
        start = years[0] if years else previous.start_year if followup else None
        end = years[-1] if years else previous.end_year if followup else None
        metrics = [name for name, pattern in {
            "fob_usd": r"\b(fob|export value|valor exportado)\b",
            "net_weight_kg": r"\b(net weight|kilograms|kg|peso neto)\b",
            "operations": r"\b(number of operations|operation count|count|numero de operaciones)\b",
        }.items() if re.search(pattern, value)]
        if len(metrics) > 1:
            return Analysis("clarify", "ambiguous_metric")
        metric = metrics[0] if metrics else previous.metric if followup else None
        rank = re.search(r"\b(top|ranking)\s*(\d+)?", value)
        operation = "ranking" if rank else previous.operation if followup else "total"
        top_k = int(rank.group(2) or 5) if rank else previous.top_k if followup else 5
        aliases = {"chile": "Chile", "peru": "Peru", "mexico": "Mexico",
                   "united states": "United States", "estados unidos": "United States",
                   "china": "China", "ecuador": "Ecuador"}
        destinations = {name for alias, name in aliases.items()
                        if re.search(r"\b" + re.escape(alias) + r"\b", value)}
        if len(destinations) > 1:
            return Analysis("clarify", "ambiguous_destination")
        destination = next(iter(destinations), previous.destination if followup else None)
        explicit = re.search(r"\b(?:to|towards|hacia|a)\s+([a-z ]+?)(?=\s+(?:in|for|during|en)\b|[?.!,]|$)", value)
        if explicit and explicit.group(1).strip().removeprefix("the ") not in aliases:
            return Analysis("clarify", "unsupported_destination")
        if start is None:
            return Analysis("clarify", "missing_period")
        if metric is None:
            return Analysis("clarify", "missing_metric")
        if not followup and not re.search(r"\b(export\w*|fob|net weight|peso neto|operation\w*|operacion\w*)\b", value):
            return Analysis("clarify", "unsupported_request")
        try:
            query = Query(start, end, metric, operation, destination, top_k)
        except ValueError:
            return Analysis("clarify", "invalid_combination")
        return Analysis("ready", "complete", query)


class ModelAnalyzer:
    """Provider-independent boundary for a caller-supplied language model.

    No model is configured or invoked by the default demo or evaluation.
    The caller owns authentication, model selection, costs and data policy.
    """

    def __init__(self, generate: Callable[[str], str]):
        self.generate = generate
        self.instructions = (Path(__file__).resolve().parents[1] / "prompts/context.txt").read_text("utf8")

    def analyze(self, text: str, previous: Query | None = None) -> Analysis:
        if not isinstance(text, str) or not text.strip() or len(text) > 2000:
            return Analysis("clarify", "invalid_input")
        payload = json.dumps({"user_text": text, "previous_query": asdict(previous) if previous else None})
        try:
            result = self.generate(self.instructions + "\nINPUT DATA:\n" + payload)
            if not isinstance(result, str) or len(result) > 10000:
                raise ValueError("Invalid model response size")
            data = json.loads(result)
            decision, reason = data["decision"], data["reason"]
            if decision not in {"ready", "clarify", "reject"} or not isinstance(reason, str) or len(reason) > 100:
                raise ValueError("Invalid model response contract")
            query = Query(**data["query"]) if decision == "ready" else None
            return Analysis(decision, reason, query)
        except (ValueError, TypeError, KeyError):
            return Analysis("clarify", "invalid_model_response")


def analyze_text(text: str) -> dict:
    """Small public entry point for reviewers exploring their own questions."""
    return RuleAnalyzer().analyze(text).to_dict()

"""Connect semantic text analysis to parameterized SQL and grounded answers."""
import csv
from pathlib import Path
import sqlite3

from .analysis import Query, RuleAnalyzer

ROOT = Path(__file__).resolve().parents[1]


def build_query(query: Query) -> tuple[str, tuple]:
    # Only validated enum values select SQL structure; user text is never SQL.
    aggregates = {"fob_usd": "SUM(fob_usd)", "net_weight_kg": "SUM(net_weight_kg)", "operations": "COUNT(*)"}
    aggregate = aggregates[query.metric]
    projection = f"destination, {aggregate} AS value" if query.operation == "ranking" else f"{aggregate} AS value"
    sql = f"SELECT {projection} FROM exports WHERE year BETWEEN ? AND ?"
    params = [query.start_year, query.end_year]
    if query.destination:
        sql += " AND destination = ?"
        params.append(query.destination)
    if query.operation == "ranking":
        sql += " GROUP BY destination ORDER BY value DESC, destination ASC LIMIT ?"
        params.append(query.top_k)
    return sql, tuple(params)


def database() -> sqlite3.Connection:
    connection = sqlite3.connect(":memory:")
    connection.row_factory = sqlite3.Row
    connection.execute("CREATE TABLE exports (year INTEGER, destination TEXT, fob_usd REAL, net_weight_kg REAL)")
    with (ROOT / "data/synthetic_exports.csv").open(encoding="utf8", newline="") as source:
        rows = [(int(r["year"]), r["destination"], float(r["fob_usd"]), float(r["net_weight_kg"])) for r in csv.DictReader(source)]
    connection.executemany("INSERT INTO exports VALUES (?, ?, ?, ?)", rows)
    connection.commit()
    connection.execute("PRAGMA query_only = ON")
    return connection


class Conversation:
    """One instance per user conversation; only explicit follow-ups inherit context."""

    def __init__(self, analyzer=None):
        self.analyzer = analyzer or RuleAnalyzer()
        self.previous = None

    def process(self, text: str) -> dict:
        analysis = self.analyzer.analyze(text, self.previous)
        result = analysis.to_dict()
        if analysis.query is None:
            return result
        sql, params = build_query(analysis.query)
        connection = database()
        try:
            rows = [dict(row) for row in connection.execute(sql, params)]
        finally:
            connection.close()
        self.previous = analysis.query
        units = {"fob_usd": "USD", "net_weight_kg": "kg", "operations": "operations"}
        unit = units[analysis.query.metric]
        if not rows or rows[0]["value"] is None:
            answer = "No matching synthetic records were found."
        elif analysis.query.operation == "ranking":
            answer = "; ".join(f"{row['destination']}: {row['value']:,.2f} {unit}" for row in rows)
        else:
            answer = f"The total is {rows[0]['value']:,.2f} {unit}."
        result.update(sql=sql, parameters=params, rows=rows, answer=answer,
                      data_source="Synthetic demonstration records; not official trade statistics")
        return result

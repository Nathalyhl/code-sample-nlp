"""Run a complete offline example or analyze a question from the command line."""
import argparse
import json
from .workflow import Conversation

parser = argparse.ArgumentParser(description="Applied NLP and text-to-query code sample")
parser.add_argument("question", nargs="?")
args = parser.parse_args()
conversation = Conversation()
questions = [args.question] if args.question else [
    "What was the FOB value of exports to Chile in 2023?",
    "Now for 2024?",
    "Top 3 export destinations by net weight in 2024",
    "What was the FOB value of exports?",
]
for question in questions:
    print(json.dumps({"input": question, "result": conversation.process(question)}, indent=2, ensure_ascii=True))

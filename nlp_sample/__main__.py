"""Review entry point: original orchestration and clearly separated fixtures."""
import argparse
import json
from .review import inspect_helpers, language_limits, walkthrough


def main():
    parser = argparse.ArgumentParser(description="Review original conversational NLP code")
    parser.add_argument("question", nargs="?", help="Inspect the original intent helper for one question")
    parser.add_argument("--limits", action="store_true", help="Inspect documented original language limitations")
    args = parser.parse_args()
    if args.limits:
        result = language_limits()
    elif args.question:
        result = {"input": args.question, "computed_original_helper_output": inspect_helpers(args.question)}
    else:
        result = walkthrough()
    print(json.dumps(result, indent=2, ensure_ascii=True))


if __name__ == "__main__":
    main()

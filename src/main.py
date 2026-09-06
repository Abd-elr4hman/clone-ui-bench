import os
import argparse
import asyncio

from src.benchmark import run_benchmark


def main():
    parser = argparse.ArgumentParser(description="Run UI cloning benchmark")
    parser.add_argument(
        "--parallel",
        "-p",
        type=int,
        default=3,
        help="Number of parallel requests (default: 3)",
    )
    parser.add_argument(
        "--config", "-c", type=str, help="Path to JSON config file with models and URLs"
    )
    parser.add_argument(
        "--judge",
        "-j",
        type=str,
        help=(
            "Comma-separated judge model ids, e.g. 'google/gemini-3.8-flash,"
            "x-ai/grok-4.6'. Overrides the config file's `judges` key."
        ),
    )

    args = parser.parse_args()

    # Validate parallel requests
    if args.parallel < 1:
        print("Error: Number of parallel requests must be at least 1")
        return

    # Validate config file if provided
    if args.config and not os.path.exists(args.config):
        print(f"Error: Config file '{args.config}' does not exist")
        return

    judges = [j.strip() for j in args.judge.split(",") if j.strip()] if args.judge else None

    asyncio.run(run_benchmark(args.parallel, args.config, judges))


if __name__ == "__main__":
    main()

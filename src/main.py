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

    args = parser.parse_args()

    # Validate parallel requests
    if args.parallel < 1:
        print("Error: Number of parallel requests must be at least 1")
        return

    # Validate config file if provided
    if args.config and not os.path.exists(args.config):
        print(f"Error: Config file '{args.config}' does not exist")
        return

    asyncio.run(run_benchmark(args.parallel, args.config))


if __name__ == "__main__":
    main()

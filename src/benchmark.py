import os
from dotenv import load_dotenv

import asyncio
import pandas as pd

from src.browser.browser import browser_singleton
from src.browser.screenshot_page import screenshot_page_async
from src.utils.parse_responses import extract_clone, extract_score
from src.utils.render_html import render
from src.utils.clean_url import clean_url
from src.utils.clean_path_for_saveing import clean_path_for_saving

from src.task import clone_ui
from src.judge import DEFAULT_JUDGES, run_judges
from src.rate_limiter.rate_limiter import rate_limit
from src.utils.load_config import load_config

load_dotenv()


CURRENT_PATH = os.getcwd()


DEFAULT_MODELS = [
    "openai/gpt-6-astra-pro",
    "anthropic/claude-opus-5",
    "google/gemini-3.8-flash",
    "x-ai/grok-4.6",
    "qwen/qwen3.8-max-0902",
    "moonshotai/kimi-k3",
    "z-ai/glm-5v-turbo",
]

DEFAULT_URLS = [
    "https://stripe.com",
    "https://airbnb.com",
    "https://github.com",
    "https://dribbble.com",
    "https://medium.com",
    "https://spotify.com",
    "https://netflix.com",
    "https://apple.com",
    "https://google.com",
    "https://twitter.com",
    "https://linkedin.com",
    "https://instagram.com",
    "https://youtube.com",
    "https://amazon.com",
    "https://slack.com",
    "https://discord.com",
    "https://figma.com",
    "https://notion.so",
    "https://vercel.com",
    "https://tailwindcss.com",
]


def safe_extract_score(response_message):
    """Parse a judge score, or None if the judge broke format."""
    if response_message is None:
        return None
    try:
        return extract_score(response_message)
    except Exception as e:
        print(f"could not parse judge score ({type(e).__name__}: {e})")
        return None


async def run_scenario(model_name: str, url: str, judge_models: list[str]):
    # visit website and screen it
    og_file_name = clean_url(url)
    og_file_path = os.path.join(
        CURRENT_PATH, "data", "og", model_name, og_file_name + ".png"
    )

    try:
        directory = os.path.dirname(og_file_path)
        if not os.path.exists(directory):
            os.makedirs(directory)
    except Exception as e:
        raise OSError(f"Error creating directory or file: {e}")

    base64_og = await screenshot_page_async(url, og_file_path)

    #
    response_message = await clone_ui(base64_og, model_name)

    # extract and render clone
    page = extract_clone(response_message)

    # The task prompt makes the <HTML>/<CSS> blocks mandatory, so a response
    # without them is a failed task, not a broken run. Score it 0 and move on.
    if page["body"] is None or page["css"] is None:
        return {
            "url": url,
            "model_name": model_name,
            "base64_og": clean_path_for_saving(og_file_path),
            "base64_clone": None,
            "judge_score": 0,
            "judge_models": ",".join(judge_models),
            "response_message": response_message,
            "error": "response missing <HTML>/<CSS> blocks",
            **{f"judge_score::{m}": None for m in judge_models},
            **{f"judge_response::{m}": None for m in judge_models},
        }

    rendered = render(page["body"], page["css"])

    # save rendered clone
    clone_file_name = clean_url(url)
    clone_file_path = os.path.join(
        CURRENT_PATH, "data", "clone", model_name, clone_file_name + ".png"
    )

    try:
        directory = os.path.dirname(clone_file_path)
        if not os.path.exists(directory):
            os.makedirs(directory)
    except Exception as e:
        raise OSError(f"Error creating directory or file: {e}")

    base64_clone = await screenshot_page_async(rendered, clone_file_path)

    # judge panel
    judge_responses = await run_judges(base64_og, base64_clone, judge_models)
    judge_scores = {m: safe_extract_score(r) for m, r in judge_responses.items()}

    scored = [s for s in judge_scores.values() if s is not None]
    mean_score = sum(scored) / len(scored) if scored else None

    return {
        "url": url,
        "model_name": model_name,
        "base64_og": clean_path_for_saving(og_file_path),
        "base64_clone": clean_path_for_saving(clone_file_path),
        "judge_score": mean_score,
        "judge_models": ",".join(judge_models),
        "response_message": response_message,
        "error": None if scored else "every judge failed",
        **{f"judge_score::{m}": s for m, s in judge_scores.items()},
        **{f"judge_response::{m}": r for m, r in judge_responses.items()},
    }


async def run_benchmark(
    parallel: int = 3, config_file: str = None, judge_models: list[str] = None
):
    # Load configuration
    if config_file:
        models, urls, config_judges = load_config(config_file)
    else:
        models, urls, config_judges = DEFAULT_MODELS, DEFAULT_URLS, DEFAULT_JUDGES

    # An explicit --judge beats the config file, which beats the default.
    judge_models = judge_models or config_judges

    print(f"{len(models)} models x {len(urls)} urls = {len(models) * len(urls)} tasks")
    print(f"judges: {', '.join(judge_models)}")

    all_results = []

    semaphore = asyncio.Semaphore(parallel)
    limited_run_scenario = rate_limit(semaphore)(run_scenario)

    try:
        tasks = [
            limited_run_scenario(model_name, url, judge_models)
            for url in urls
            for model_name in models
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Error in result {i}: {result}")
                continue
            if isinstance(result, dict):
                all_results.append(result)

    finally:
        # Clean up singleton
        await browser_singleton.close()

    df = pd.DataFrame(all_results)

    # save df
    df_path = os.path.join(CURRENT_PATH, "data", "results.csv")

    try:
        directory = os.path.dirname(df_path)
        if not os.path.exists(directory):
            os.makedirs(directory)
    except Exception as e:
        raise OSError(f"Error creating directory or file: {e}")

    # With additional options
    df.to_csv(df_path, index=False, encoding="utf-8", sep=",")

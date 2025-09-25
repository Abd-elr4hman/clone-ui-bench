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
from src.judge import run_judge
from src.rate_limiter.rate_limiter import rate_limit
from src.utils.load_config import load_config

load_dotenv()


API_SEMAPHORE = asyncio.Semaphore(3)
CURRENT_PATH = os.getcwd()
RESULT_PATH = os.path.join(CURRENT_PATH, "data")


DEFAULT_MODELS = [
    "anthropic/claude-sonnet-4",
    "anthropic/claude-opus-4.1",
    "google/gemini-2.5-flash-image-preview",
    "google/gemini-2.5-pro",
    "z-ai/glm-4.5v",
    "openai/gpt-5",
    "openai/gpt-5-mini",
    "openai/o3-pro",
    "bytedance/ui-tars-1.5-7b",
    "x-ai/grok-4",
    "baidu/ernie-4.5-vl-424b-a47b",
    "qwen/qwen3-vl-235b-a22b-instruct",
    "qwen/qwen3-vl-235b-a22b-thinking",
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


@rate_limit(API_SEMAPHORE)
async def run_scenario(model_name: str, url: str):
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

    # judge model
    judge_response_message = await run_judge(base64_og, base64_clone)
    judge_score = extract_score(judge_response_message)

    return {
        "url": url,
        "model_name": model_name,
        "base64_og": clean_path_for_saving(og_file_path),
        "base64_clone": clean_path_for_saving(clone_file_path),
        "judge_score": judge_score,
        "judge_response": judge_response_message,
        "response_message": response_message,
    }


async def run_benchmark(config_file: str = None):
    # Load configuration
    if config_file:
        models, urls = load_config(config_file)
    else:
        models, urls = DEFAULT_MODELS, DEFAULT_URLS

    all_results = []
    try:
        tasks = [run_scenario(model_name, url) for url in urls for model_name in models]

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

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

load_dotenv()

MODELS = [
    "anthropic/claude-sonnet-4",
    "anthropic/claude-opus-4.1",
    "google/gemini-2.5-flash-image-preview",
    "google/gemini-2.5-proz-ai/glm-4.5v",
    "openai/gpt-5",
    "openai/gpt-5-mini",
    "openai/o3-pro",
    "bytedance/ui-tars-1.5-7b",
    "x-ai/grok-4",
    "baidu/ernie-4.5-vl-424b-a47b",
]

URLS = [
    "https://www.facebook.com/",
    "https://www.instagram.com/accounts/login/",
    "https://medium.com/",
    "https://www.zoom.us/signin#/login",
    "https://www.netflix.com/eg-en/login",
    "https://accounts.spotify.com/en/login",
    "https://www.twitch.tv/login",
    "https://signin.ebay.com/signin/",
    "https://en.khanacademy.org/login",
    "https://www.sandbox.paypal.com/eg/signin",
]

CURRENT_PATH = os.getcwd()


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


async def run_benchmark():
    all_results = []
    try:
        tasks = [run_scenario(model_name, url) for url in URLS for model_name in MODELS]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"Error in result {i}: {result}")
                continue

        all_results += results

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
    except OSError as e:
        raise f"Error creating directory or file: {e}"

    # With additional options
    df.to_csv(df_path, index=False, encoding="utf-8", sep=",")


asyncio.run(run_benchmark())

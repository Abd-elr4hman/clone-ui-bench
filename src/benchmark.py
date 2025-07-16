import os
from dotenv import load_dotenv

import asyncio
import pandas as pd

from utils.browser import browser_singleton
from utils.screenshot_page import screenshot_page_async
from utils.parse_responses import extract_clone, extract_score
from utils.render_html import render
from utils.clean_url import clean_url
from utils.clean_path_for_saveing import clean_path_for_saving

from providers import ProviderFactory
from judge import run_judge

load_dotenv()

MODELS = [
    "claude-sonnet-4-20250514"
]

URLS= [
    "https://www.facebook.com/",
    "https://www.instagram.com/accounts/login/",
    "https://medium.com/",
    "https://www.zoom.us/signin#/login",
    "https://www.netflix.com/eg-en/login",
    "https://accounts.spotify.com/en/login",
    "https://www.twitch.tv/login",
    "https://signin.ebay.com/signin/",
    "https://en.khanacademy.org/login",
    "https://www.sandbox.paypal.com/eg/signin"
]

CURRENT_PATH = os.getcwd()

async def run_scenario(model_name:str, url:str):
    # visit website and screen it 
    og_file_name = clean_url(url)
    og_file_path = os.path.join(CURRENT_PATH, 'data', 'og', og_file_name+".png")

    try:
        directory = os.path.dirname(og_file_path)
        if not os.path.exists(directory):
            os.makedirs(directory)
    except Exception as e:
        raise OSError(f"Error creating directory or file: {e}")
    
    base64_og = await screenshot_page_async(url, og_file_path)
    
    # get provider and run task
    provider = ProviderFactory.get_provider(model_name)
    response_message = await provider.run_task(base64_image=base64_og)
    
    # extract and render clone
    page = extract_clone(response_message)
    rendered = render(page["body"], page["css"])

    # save rendered clone
    clone_file_name = clean_url(url)
    clone_file_path = os.path.join(CURRENT_PATH, 'data', 'clone', clone_file_name+".png")

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
                'url': url, 
                'model_name': model_name, 
                'base64_og': clean_path_for_saving(og_file_path),
                'base64_clone': clean_path_for_saving(clone_file_path),
                'judge_score': judge_score,
                "judge_response": judge_response_message
            }


async def run_benchmark():
    all_results = []
    try:
        for model_name in MODELS:
            tasks = [run_scenario(model_name, url) for url in URLS]
            
            results = await asyncio.gather(*tasks, return_exceptions=True)

            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    print(f"Error in result {i}: {result}")
                    continue

            all_results.append(results)
    finally:
        # Clean up singleton
        await browser_singleton.close()

    df = pd.DataFrame(all_results)

    # save df
    df_path = os.path.join(CURRENT_PATH, 'data',"results.csv")

    try:
        directory = os.path.dirname(df_path)
        if not os.path.exists(directory):
            os.makedirs(directory)
    except OSError as e:
        raise f"Error creating directory or file: {e}"
    
    # With additional options
    df.to_csv(df_path, 
            index=False,
            encoding='utf-8',
            sep=',')
    

asyncio.run(run_benchmark())
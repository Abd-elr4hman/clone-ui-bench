from providers import ProviderFactory
from utils import screenshot_page, render, extract_content, extract_score
from judge import run_judge

from dotenv import load_dotenv
load_dotenv()

MODELS = [
    "claude-sonnet-4-20250514"
]

URLS= [
    "https://www.facebook.com/"
]

def run_scenario(model_name:str, url:str):
    # visit website and screen it 
    base64_og = screenshot_page(url, "og_screenshot.png")

    # 
    provider = ProviderFactory.get_provider(model_name)
    response_message = provider.run_task(base64_image=base64_og)
    page = extract_content(response_message)
    rendered = render(page["body"], page["css"])
    base64_clone = screenshot_page(rendered, "clone_screenshot.png")

    # judge model
    judge_response_message = run_judge(base64_og, base64_clone)
    judge_score = extract_score(judge_response_message)
    print(judge_response_message)
    print("/n")
    print(judge_score)
    
    return base64_og, base64_clone, judge_score


if __name__ == "__main__":
    # run task on all models
    # should be asyncio.gather(run_benchmark)
    for model_name in MODELS:
        for url in URLS:
            _,_, judge_score = run_scenario(model_name, url)
            

    

    
    
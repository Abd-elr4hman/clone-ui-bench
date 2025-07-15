import base64
from time import sleep
from bs4 import BeautifulSoup

from selenium.webdriver.chrome.options import Options
from selenium import webdriver

def screenshot_page(url: str, output_path):
    """Use this to screenshot a webpage"""
    try: 
        # initiate the webdriver
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # Run in headless mode (optional)
        chrome_options.add_argument('--disable-gpu')
        chrome_options.add_argument('--window-size=1920,1080')
        driver = webdriver.Chrome(options=chrome_options)

        # get the url 
        driver.get(url)
        sleep(1) 
        base64_image = driver.get_screenshot_as_base64()
        driver.save_screenshot(output_path)
        print(f"Screenshot Saved to{output_path}")
        
        # close
        driver.close()
        return base64_image
    
    except Exception as e:
        raise ValueError(e)

    finally:
        driver.quit()
    

def extract_content(response_message: str):
    """Extract HTML and CSS from text"""
    soup = BeautifulSoup(response_message, 'html.parser')
    body_tag = str(soup.find('body'))
    css_tag = str(soup.find('css'))  # Looks for <css> tags
    return {
        'body': body_tag,
        'css': css_tag
    }


def render(html_body:str, css:str):
    """Render HTML/CSS."""

    # check html and css are not empty
    if len(html_body) == 0 | len(css) ==0 :
        raise ValueError("Invalid html or css. Must be a non empty string.")

    
    # Combine HTML and CSS
    full_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>{css}</style>
        </head>
        <body>
            {html_body}
        </body>
        </html>
        """

    # Encode the HTML as base64 and create a data URL
    html_encoded = base64.b64encode(full_html.encode('utf-8')).decode('utf-8')
    data_url = f"data:text/html;base64,{html_encoded}"
    return data_url
    

def extract_score(response_message: str):
    """Extract score from text"""
    soup = BeautifulSoup(response_message, 'html.parser')
    score= str(soup.find('score'))
    return score

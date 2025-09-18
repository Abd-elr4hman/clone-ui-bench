import base64
from .browser import browser_singleton


async def screenshot_page_async(url: str, output_path: str):
    """Screenshot function using singleton browser"""
    browser = await browser_singleton.get_browser()
    context = await browser.new_context(locale="en-US")  # Custom context
    page = await context.new_page()
    await page.set_viewport_size({"width": 1920, "height": 1080})

    try:
        await page.goto(url)
        await page.wait_for_timeout(1000)

        screenshot_bytes = await page.screenshot(path=output_path)
        base64_image = base64.b64encode(screenshot_bytes).decode()

        print(f"Screenshot saved to {output_path}")
        return base64_image
    except Exception as e:
        raise ValueError(f"Error screenshotting {url}: {e}")
    finally:
        await page.close()

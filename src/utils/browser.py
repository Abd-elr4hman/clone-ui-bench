import asyncio
from playwright.async_api import async_playwright

class BrowserSingleton:
    _instance = None
    _browser = None
    _playwright = None
    _lock = asyncio.Lock()
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    async def get_browser(self):
        if self._browser is None:
            async with self._lock:
                if self._browser is None:  # Double-check locking
                    self._playwright = await async_playwright().start()
                    self._browser = await self._playwright.chromium.launch(headless=True)
        return self._browser
    
    async def close(self):
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright:
            await self._playwright.stop()
            self._playwright = None


# get browser
browser_singleton = BrowserSingleton()
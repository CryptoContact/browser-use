import asyncio
import gc
import logging
from dataclasses import dataclass, field
from DrissionPage import Drission

logger = logging.getLogger(__name__)

@dataclass
class BrowserConfig:
    """Configuration for the Browser."""
    headless: bool = False
    disable_security: bool = True
    extra_chromium_args: list[str] = field(default_factory=list)
    chrome_instance_path: str | None = None
    proxy: dict | None = field(default=None)

class Browser:
    """Browser using DrissionPage wrapped for asynchronous use."""

    def __init__(self, config: BrowserConfig = BrowserConfig()):
        logger.debug('Initializing new browser')
        self.config = config
        self.driver = None

    async def new_context(self):
        """Create a new browser context by initializing DrissionPage."""
        return await asyncio.to_thread(self._create_driver)

    def _create_driver(self):
        options = {
            'headless': self.config.headless,
            'disable_security': self.config.disable_security,
            'extra_chromium_args': self.config.extra_chromium_args,
            'chrome_instance_path': self.config.chrome_instance_path,
            'proxy': self.config.proxy
        }
        self.driver = Drission(options=options)
        logger.debug("Driver created with options: %s", options)
        return self.driver

    async def get_driver(self):
        """Get the current browser driver; create one if it doesn't exist."""
        if self.driver is None:
            return await self.new_context()
        return self.driver

    async def close(self):
        """Close the browser instance and clean up resources."""
        try:
            if self.driver is not None:
                await asyncio.to_thread(self.driver.quit)
                self.driver = None
                logger.debug("Browser closed successfully.")
        except Exception as e:
            logger.debug(f'Failed to close browser properly: {e}')
        finally:
            gc.collect()

    def __del__(self):
        """Cleanup when the object is destroyed."""
        try:
            if self.driver:
                # Use the running event loop if available; otherwise run the close() coroutine.
                loop = asyncio.get_running_loop()
                if loop.is_running():
                    loop.create_task(self.close())
                else:
                    asyncio.run(self.close())
        except Exception as e:
            logger.debug(f'Failed to cleanup browser in destructor: {e}')

# --- Example usage when running this module directly ---
if __name__ == "__main__":
    async def main():
        logging.basicConfig(level=logging.DEBUG)
        config = BrowserConfig(headless=True)
        browser = Browser(config)
        driver = await browser.get_driver()
        # Run blocking driver.get() in a thread
        await asyncio.to_thread(driver.get, 'https://www.google.com')
        # Since DrissionPage is synchronous, accessing title is blocking
        title = await asyncio.to_thread(lambda: driver.title)
        print("Page title:", title)
        await browser.close()

    asyncio.run(main())
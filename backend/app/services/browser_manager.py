import os
import uuid
import datetime
from typing import Optional, List, Dict, Any, Tuple
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from backend.app.core.config import settings

class BrowserSession:
    def __init__(self, run_id: str):
        self.run_id = run_id
        self.playwright = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.console_logs: List[str] = []
        self.page_errors: List[str] = []

    async def initialize(self, headless: bool = True):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(
            headless=headless,
            args=["--no-sandbox", "--disable-dev-shm-usage"]
        )
        await self.create_clean_context()

    async def create_clean_context(self) -> Page:
        if self.context:
            await self.context.close()
            
        self.context = await self.browser.new_context(
            viewport={"width": 1280, "height": 800},
            ignore_https_errors=True
        )
        self.page = await self.context.new_page()
        self.console_logs = []
        self.page_errors = []

        # Wire up diagnostic logging
        self.page.on("console", lambda msg: self.console_logs.append(f"[{msg.type}] {msg.text}"))
        self.page.on("pageerror", lambda err: self.page_errors.append(str(err)))
        return self.page

    async def capture_screenshot(self, prefix: str = "step") -> Tuple[str, str, str]:
        """
        Captures a screenshot, stores in artifacts dir, and returns (artifact_id, file_path, file_name).
        """
        if not self.page:
            return "", "", ""
        
        artifact_id = f"art-{uuid.uuid4().hex[:8]}"
        timestamp = datetime.datetime.now(datetime.timezone.utc).strftime("%Y%m%d_%H%M%S")
        file_name = f"{self.run_id}_{prefix}_{timestamp}_{artifact_id}.png"
        file_path = os.path.join(settings.ARTIFACTS_DIR, file_name)

        await self.page.screenshot(path=file_path, full_page=False)
        return artifact_id, file_path, file_name

    async def close(self):
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception:
            pass

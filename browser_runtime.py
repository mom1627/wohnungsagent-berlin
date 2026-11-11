"""Launch Playwright's bundled Chromium, or an explicitly configured local binary."""
import os


async def launch_chromium(playwright):
    binary = os.getenv("HOUSING_CHROMIUM_EXECUTABLE")
    options = {"executable_path": binary} if binary else {}
    return await playwright.chromium.launch(headless=True, **options)

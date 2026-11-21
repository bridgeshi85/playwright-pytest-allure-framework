"""Page Object for the HAR record and replay demonstration."""

from playwright.sync_api import Locator, Page


class HarDemoPage:
    """Encapsulates semantic locators for the /har-demo page."""

    URL_PATH = "/har-demo"

    def __init__(self, page: Page) -> None:
        self.page = page

    @property
    def success_panel(self) -> Locator:
        """Return the panel displayed after all API responses load."""
        return self.page.get_by_test_id("har-demo-success")

    @property
    def profile_value(self) -> Locator:
        """Return the rendered profile display name."""
        return self.page.get_by_test_id("har-demo-profile")

    @property
    def permission_value(self) -> Locator:
        """Return the rendered primary permission."""
        return self.page.get_by_test_id("har-demo-permission")

    @property
    def metrics_value(self) -> Locator:
        """Return the rendered active-project count."""
        return self.page.get_by_test_id("har-demo-metrics")

    def goto(self, base_url: str) -> None:
        """Navigate to the HAR demo page."""
        self.page.goto(f"{base_url.rstrip('/')}{self.URL_PATH}")

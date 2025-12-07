import logging

logger = logging.getLogger(__name__)


class HomePage:
    def __init__(self, page):
        self.page = page

    def should_show_welcome_text(self):
        logger.info("Checking welcome text")
        return self.page.get_by_test_id("welcome-text").is_visible()

import logging
logger = logging.getLogger(__name__)


class LoginPage:
    def __init__(self, page):
        self.page = page

    def goto(self, base_url):
        logger.info(f"Navigating to login page: {base_url}")
        self.page.goto(base_url)

    def login(self, username: str, password: str):
        logger.info("Performing login action")
        self.page.get_by_test_id("input-username").fill(username)
        logger.info(f"username entered: {username}")
        self.page.get_by_test_id("input-password").fill(password)
        logger.info("password entered")
        self.page.get_by_test_id("btn-login").click()
        logger.info("login button clicked")
        self.page.wait_for_load_state("networkidle")


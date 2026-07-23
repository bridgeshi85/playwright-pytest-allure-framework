import logging

logger = logging.getLogger(__name__)


class TaskPage:
    """Page object for the Task management page.

    HTML structure:
        <main>
          <div>
            <input type="text" placeholder="Task title">
            <input type="text" placeholder="Description">
            <button>Add Task</button>
          </div>
          <ul>
            <li>
              <h3>Task title</h3>
              <p>Task description</p>
            </li>
          </ul>
        </main>
    """

    def __init__(self, page):
        self.page = page
        self.title_input = page.get_by_placeholder("Task title")
        self.description_input = page.get_by_placeholder("Description")
        self.add_task_button = page.get_by_role("button", name="Add Task")
        self.task_list = page.locator("ul")

    def goto(self, base_url: str):
        logger.info(f"Navigating to task page: {base_url}")
        self.page.goto(base_url)

    def add_task(self, title: str, description: str):
        """Fill in the task form and submit it."""
        logger.info(f"Adding task: title='{title}', description='{description}'")
        self.title_input.fill(title)
        self.description_input.fill(description)
        self.add_task_button.click()
        logger.info("Clicked 'Add Task' button")
        # 🌟 等待输入框的值被前端逻辑清空
        self.title_input.wait_for(state="visible")  # 确保元素还在

        # 利用 playwright 的 expect 断言库自带的自动等待重试机制
        from playwright.sync_api import expect
        expect(self.title_input).to_be_empty(timeout=5000)

        logger.info("Form cleared after submission")

    def get_task_items(self):
        """Return all <li> locators inside the task list."""
        return self.task_list.locator("li")

    def task_is_exist(self, title: str) -> bool:
        """Return True if an <h3> with the given title is existed in the task list."""
        # Match the <li> that contains an <h3> with exactly the given title text
        item = self.task_list.locator("li").filter(has=self.page.locator("h3", has_text=title))
        exists = item.count() > 0
        logger.info(f"Task '{title}' exists: {exists}")
        return exists

    def get_task_description(self, title: str) -> str:
        """Return the description text of the task with the given title."""
        item = self.task_list.locator("li").filter(has=self.page.locator("h3", has_text=title))
        description = item.locator("p").inner_text()
        logger.info(f"Task '{title}' description: '{description}'")
        return description

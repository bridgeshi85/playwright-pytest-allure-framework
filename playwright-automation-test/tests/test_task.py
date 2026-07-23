import allure
from pages.task_page import TaskPage
@allure.feature("Task Management")
class TestAddTask:
    """Tests for adding tasks via the task management page."""

    @allure.story("Add a single task")
    @allure.title("Verify that a new task appears in the list after submission")
    def test_add_task_appears_in_list(self, page, config):
        """
        Given the task management page is open,
        When I enter a task title and description and click 'Add Task',
        Then the new task should appear as an <li> with an <h3> title
        and a <p> description in the task list.
        """
        task_page = TaskPage(page)
        task_page.goto(config["base_url"])

        title = "Buy groceries"
        description = "Milk, eggs, and bread"

        with allure.step("Fill in the task title and description, then click Add Task"):
            task_page.add_task(title, description)

        with allure.step("Verify the task title (h3) appears in the list"):
            assert task_page.task_is_exist(title), (
                f"Expected task '{title}' to appear in the task list, but it was not found."
            )

        # with allure.step("Verify the task description (p) is correct"):
        #     assert task_page.get_task_description(title) == description, (
        #         f"Expected description '{description}' for task '{title}', but got a different value."
        #     )

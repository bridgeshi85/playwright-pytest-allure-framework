import pytest


# 1. 不同作用域的fixture
@pytest.fixture(scope="session")
def session_fixture():
    print("\nSession fixture setup")
    yield "session_data"
    print("Session fixture teardown")


@pytest.fixture(scope="module")
def module_fixture():
    print("Module fixture setup")
    yield "module_data"
    print("Module fixture teardown")


@pytest.fixture(scope="function")
def function_fixture():
    print("Function fixture setup")
    yield "function_data"
    print("Function fixture teardown")


# 测试函数
def test_execution_order(
        session_fixture,  # 作用域最大，最先执行
        module_fixture,  # 作用域次之
        function_fixture,  # 作用域最小
):
    print("\nTest execution")
    assert True

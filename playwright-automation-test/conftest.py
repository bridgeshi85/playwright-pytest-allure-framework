import pytest


@pytest.fixture(scope="class")
def resource_class():
    print("\n[setup] class fixture")
    yield "fixture返回的内容"
    print("[teardown] class fixture")
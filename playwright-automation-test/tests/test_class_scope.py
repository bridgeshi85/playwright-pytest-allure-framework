import pytest


@pytest.fixture
def db():
    print("[setup] db")
    yield
    print("[teardown] db")


@pytest.fixture
def login():
    print("[setup] login")
    yield
    print("[teardown] login")


@pytest.fixture
def prepare_data():
    print("[setup] prepare_data")
    yield
    print("[teardown] prepare_data")


def test_api(prepare_data, login, db):
    print("执行 test_api")
    
    
from demo_greeting import greet


def test_greet_with_name() -> None:
    assert greet("Alice") == "Hello, Alice!"


def test_greet_with_empty_string() -> None:
    assert greet("") == "Hello, !"

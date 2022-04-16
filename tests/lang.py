from utils import message_utils

def test_hello_world():
    assert message_utils.build('hello_world') == 'Hello world'

def test_formatting():
    assert message_utils.build('hello_user', user="pat") == 'Hello pat'

def test_failure():
    assert message_utils.build('hello') == 'hello'

def test() -> bool:
    try:
        message_utils.load()
        test_hello_world()
        test_formatting()
    except AssertionError as e:
        print(e.with_traceback(None))
        return False
    return True
    
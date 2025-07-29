import pytest
from src.task import clone_ui
from openai.types.chat.chat_completion import ChatCompletion

def read_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except FileNotFoundError:
        raise FileNotFoundError(f"File '{file_path}' not found")
    except IOError as e:
        raise IOError(f"Error reading file '{file_path}': {e}")

@pytest.mark.asyncio
async def test_clone_ui():
    model = 'openai/gpt-4.1'
    file_path = "src/tests/base64_image_string.txt"
    
    base64_image= read_file(file_path)
    
    message = await clone_ui(base64_image, model)
    assert isinstance(message, ChatCompletion)
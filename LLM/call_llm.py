import requests
import re


def call_llm(model, messages, convid=None):
    """
    Calls the specified LLM model using Ollama.

    Args:
        model (str): Model name like 'ollama/qwen:4b'
        messages (list): List of message dicts with 'role' and 'content'
        convid (str): Unused in Ollama, but kept for compatibility

    Returns:
        tuple: (response text, None) - None for convid
    """
    if "ollama/" in model:
        model = re.sub(r"^ollama/", "", model)
        return get_ollama_ans(model, messages)
    else:
        print("Only Ollama models are supported now.")
        return None, None


def get_ollama_ans(model, messages):
    """
    Sends a chat request to Ollama's local API.

    Args:
        model (str): The model name, e.g. 'qwen:4b'
        messages (list): Chat history as list of dicts

    Returns:
        tuple: (generated response, None)
    """
    url = "http://localhost:11434/api/chat"

    payload = {
        "model": model,
        "messages": messages,
        "stream": False
    }

    try:
        response = requests.post(url, json=payload, timeout=120)
        if response.status_code == 200:
            content = response.json()['message']['content']
            return content.strip(), None  # Ollama does not support conversation IDs
        else:
            print(f"Ollama request failed with status code {response.status_code}")
            print(response.text)
            return "Error", None
    except requests.exceptions.RequestException as e:
        print(f"An error occurred: {e}")
        return "Error", None
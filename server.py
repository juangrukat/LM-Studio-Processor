import requests

def query_llm(server_url: str, prompt: str, timeout: int = 60) -> dict:
    """
    Sends a prompt to the LLM server and returns the response.
    
    Args:
        server_url (str): The URL of the LLM server
        prompt (str): The prompt to send to the LLM
        timeout (int): Timeout in seconds for the request
        
    Returns:
        dict: The response from the LLM server
        
    Raises:
        Exception: If there's an error communicating with the server
    """
    try:
        # Split timeout between connection and read
        response = requests.post(
            f"{server_url}/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": prompt}]
            },
            timeout=(10, timeout)  # (connection timeout, read timeout)
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.ReadTimeout:
        error_msg = f"Server is taking too long to respond (timeout after {timeout}s). Try with a shorter prompt or increase timeout."
        print(f"ERROR: {error_msg}")
        raise Exception(error_msg)
    except requests.exceptions.ConnectTimeout:
        error_msg = "Could not connect to server (connection timeout). Is LM Studio running?"
        print(f"ERROR: {error_msg}")
        raise Exception(error_msg)
    except requests.exceptions.RequestException as e:
        error_msg = f"Server error: {str(e)}"
        print(f"ERROR: {error_msg}")
        raise Exception(error_msg) 
import requests

def query_llm(server_url: str, prompt: str) -> dict:
    """
    Sends a prompt to the LLM server and returns the response.
    
    Args:
        server_url (str): The URL of the LLM server
        prompt (str): The prompt to send to the LLM
        
    Returns:
        dict: The response from the LLM server
        
    Raises:
        Exception: If there's an error communicating with the server
    """
    try:
        response = requests.post(
            f"{server_url}/v1/chat/completions",
            json={
                "messages": [{"role": "user", "content": prompt}]
            }
        )
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        error_msg = f"Server error: {str(e)}"
        print(f"ERROR: {error_msg}")
        raise Exception(error_msg) 
from promptflow.core import tool
import requests
import json
import os

# --- CONFIGURATION ---
# Get Secrets from Environment Variables (set by Azure or locally)
API_KEY = os.environ.get("AZURE_OPENAI_API_KEY")
API_BASE = os.environ.get("AZURE_OPENAI_ENDPOINT")

# 2. Hardcoded Settings (Safe to keep here)
DEPLOYMENT_NAME = "gpt-5-mini"
API_VERSION = "2025-04-01-preview"

@tool
def chat_with_gpt5(system_prompt: str, user_input: str):
    """
    Manually calls the new GPT-5 'Responses' API using Environment Variables.
    Requires AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT to be set.
    """
    
    # Validation: Check if keys are missing
    if not API_KEY or not API_BASE:
        return "Error: Missing Environment Variables. Please set AZURE_OPENAI_API_KEY and AZURE_OPENAI_ENDPOINT in your .env file or environment."

    # Clean up the URL (Remove trailing slash if present)
    base_url = API_BASE.rstrip("/")
    
    # Construct the specific URL
    url = f"{base_url}/openai/responses?api-version={API_VERSION}"
    
    headers = {
        "Content-Type": "application/json",
        "api-key": API_KEY
    }
    
    # Build Payload (Using 'input' parameter)
    payload = {
        "model": DEPLOYMENT_NAME,
        "input": [ 
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
    }
    
    # Send Request
    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status() 
        
        # Parse Answer
        data = response.json()
        
        # Format 1: Content List (Preview)
        if 'content' in data and isinstance(data['content'], list):
            for item in data['content']:
                if 'text' in item:
                    return str(item['text']).strip()
        
        # Format 2: Standard Chat
        if 'choices' in data and len(data['choices']) > 0:
            choice = data['choices'][0]
            if 'message' in choice and 'content' in choice['message']:
                return str(choice['message']['content']).strip()
            elif 'text' in choice:
                return str(choice['text']).strip()
            
        # Format 3: Output String
        if 'output' in data:
            return str(data['output']).strip()
            
        # Format 4: Direct result
        if 'result' in data:
            return str(data['result']).strip()
        
        # Last resort
        return str(data).strip()
        
    except Exception as e:
        error_msg = f"Error calling GPT-5: {e}"
        if 'response' in locals():
            error_msg += f"\nResponse: {response.text}"
        return error_msg
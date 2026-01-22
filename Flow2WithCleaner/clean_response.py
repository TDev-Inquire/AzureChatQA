from promptflow.core import tool
import json
import ast

@tool
def clean_json_response(raw_response: str) -> str:
    """
    Cleans up raw JSON responses to extract just the text content.
    Handles various GPT-5 response formats.
    """
    
    # If it's already clean text (no JSON structure), return as-is
    if not raw_response.strip().startswith('{') and not raw_response.strip().startswith('['):
        return raw_response.strip()
    
    data = None
    
    # Try multiple parsing methods
    # Method 1: Parse as JSON
    try:
        data = json.loads(raw_response)
    except json.JSONDecodeError:
        pass
    
    # Method 2: Parse as Python literal (handles single quotes)
    if data is None:
        try:
            data = ast.literal_eval(raw_response)
        except:
            pass
    
    # If we successfully parsed the data
    if data is not None:
        # Helper function to extract text from nested structures
        def extract_text_content(obj):
            """Recursively extract text content from response object."""
            if isinstance(obj, str):
                return obj.strip()
            
            if isinstance(obj, list):
                # Check if this is a list of output items
                for item in obj:
                    if isinstance(item, dict):
                        # Look for message type items
                        if item.get('type') == 'message':
                            if 'content' in item and isinstance(item['content'], list):
                                text_parts = []
                                for content_item in item['content']:
                                    if isinstance(content_item, dict) and content_item.get('type') == 'output_text':
                                        if 'text' in content_item:
                                            text_parts.append(content_item['text'])
                                if text_parts:
                                    return '\n'.join(text_parts).strip()
                # Try first item if no message found
                if len(obj) > 0:
                    return extract_text_content(obj[0])
            
            if isinstance(obj, dict):
                # GPT-5 specific: Check for output array with content
                if 'output' in obj and isinstance(obj['output'], list):
                    for output_item in obj['output']:
                        if isinstance(output_item, dict) and output_item.get('type') == 'message':
                            # Found message type, extract from content
                            if 'content' in output_item and isinstance(output_item['content'], list):
                                text_parts = []
                                for content_item in output_item['content']:
                                    if isinstance(content_item, dict) and content_item.get('type') == 'output_text':
                                        if 'text' in content_item:
                                            text_parts.append(content_item['text'])
                                if text_parts:
                                    return '\n'.join(text_parts).strip()
                
                # Check for direct text/content fields
                if 'text' in obj and isinstance(obj['text'], str):
                    return obj['text'].strip()
                
                # Handle content arrays (standard format)
                if 'content' in obj:
                    if isinstance(obj['content'], list):
                        text_parts = []
                        for item in obj['content']:
                            if isinstance(item, dict):
                                # Look for output_text type
                                if item.get('type') == 'output_text' and 'text' in item:
                                    text_parts.append(item['text'])
                                elif 'text' in item:
                                    text_parts.append(item['text'])
                            elif isinstance(item, str):
                                text_parts.append(item)
                        if text_parts:
                            return '\n'.join(text_parts).strip()
                    elif isinstance(obj['content'], str):
                        return obj['content'].strip()
                
                # Handle message format
                if 'message' in obj and isinstance(obj['message'], dict):
                    return extract_text_content(obj['message'])
                
                # Handle choices format (standard OpenAI)
                if 'choices' in obj and isinstance(obj['choices'], list) and len(obj['choices']) > 0:
                    return extract_text_content(obj['choices'][0])
            
            return None
        
        # Try to extract text
        text = extract_text_content(data)
        if text:
            return text
        
        # If no text found, return formatted JSON (better than raw)
        return json.dumps(data, indent=2)
    
    # Return original if we can't parse it
    return raw_response.strip()

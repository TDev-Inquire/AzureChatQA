from promptflow.core import tool

@tool
def generate_prompt_context(search_result: object) -> str:
    """
    Simple pass-through. 
    If the search result is already text (from local lookup), return it.
    """
    
    # Case 1: Input is already a clean string (Our Local Tool)
    if isinstance(search_result, str):
        return search_result

    # Case 2: Input is a list (Legacy/Azure Search) - simple join
    if isinstance(search_result, list):
        # Join items with newlines, converting dicts to strings if needed
        return "\n\n".join([str(item) for item in search_result])

    # Fallback
    return str(search_result)
from promptflow.core import tool
from azure.search.documents import SearchClient
from azure.core.credentials import AzureKeyCredential
import os
import json

# --- CONFIGURATION ---
# Get configuration from environment variables
SEARCH_ENDPOINT = os.environ.get("AZURE_SEARCH_ENDPOINT")
SEARCH_KEY = os.environ.get("AZURE_SEARCH_KEY")
INDEX_NAME = os.environ.get("AZURE_SEARCH_INDEX_NAME")


def format_store_for_llm(store_data):
    """Format store data as readable text for LLM consumption"""
    lines = [
        f"Store: {store_data.get('name', 'Unknown')} (ID: {store_data.get('storeId', 'N/A')})",
        f"Location: {store_data['location'].get('address', 'N/A')}, {store_data['location'].get('city', 'N/A')}, {store_data['location'].get('state', 'N/A')}",
        f"Store Leader: {store_data['leadership'].get('storeLeader', 'N/A')} ({store_data['leadership'].get('storeLeaderEmail', 'N/A')})",
        f"District: {store_data['leadership'].get('districtName', 'N/A')} - {store_data['leadership'].get('districtLeader', 'N/A')}",
        f"Region: {store_data['leadership'].get('regionName', 'N/A')} - {store_data['leadership'].get('regionLeader', 'N/A')}",
        f"Area: {store_data['leadership'].get('areaName', 'N/A')} - {store_data['leadership'].get('areaLeader', 'N/A')}",
        f"Hours: Mon {store_data['operatingHours'].get('monday', 'Closed')} | Tue {store_data['operatingHours'].get('tuesday', 'Closed')} | Wed {store_data['operatingHours'].get('wednesday', 'Closed')} | Thu {store_data['operatingHours'].get('thursday', 'Closed')} | Fri {store_data['operatingHours'].get('friday', 'Closed')} | Sat {store_data['operatingHours'].get('saturday', 'Closed')} | Sun {store_data['operatingHours'].get('sunday', 'Closed')}"
    ]
    if store_data.get('additionalInfo'):
        lines.append(f"Info: {store_data['additionalInfo']}")
    return "\n".join(lines)


def format_document_for_llm(doc_data):
    """Format document data as readable text for LLM consumption"""
    return f"""
DOCUMENT INFORMATION
====================
Title: {doc_data.get('title', 'Unknown')}

CONTENT
-------
{doc_data.get('content', '[No content available]')}
"""


@tool
def lookup_indexed_knowledge(query: str):
    """
    Search Azure Index. 
    Returns formatted, readable content for store metadata and documents.
    Requires AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_KEY, and AZURE_SEARCH_INDEX_NAME env variables.
    """
    # Validate environment variables
    if not SEARCH_ENDPOINT or not SEARCH_KEY or not INDEX_NAME:
        return "Error: Missing Azure Search environment variables. Please set AZURE_SEARCH_ENDPOINT, AZURE_SEARCH_KEY, and AZURE_SEARCH_INDEX_NAME in your .env file or environment."
    
    try:
        # 1. Connect
        credential = AzureKeyCredential(SEARCH_KEY)
        client = SearchClient(endpoint=SEARCH_ENDPOINT,
                              index_name=INDEX_NAME,
                              credential=credential)

        # 2. Define Fields to Retrieve
        target_fields = [

        ]

        # 3. Run Search with expanded query for state abbreviations
        # Expand common abbreviations to improve search results
        expanded_query = query
        state_mapping = {
        }

        for abbrev, full_name in state_mapping.items():
            if abbrev in query:
                expanded_query = query.replace(abbrev, f"{abbrev} {full_name}")
                break
        
        results = client.search(
            search_text=expanded_query, 
            select=target_fields, 
            top=10,  # Increased from 5 to get more results
            search_mode="any"  # Match any term instead of all terms
        )

        formatted_results = []
        for doc in results:
            
            # --- SCENARIO A: STORE RECORD (Has City/Address) ---
            if doc.get("City") and doc.get("Address"):
                
                store_data = {

                }
                
                # Add any additional content/notes if present
                if doc.get('content'):
                    store_data['additionalInfo'] = doc.get('content')
                
                formatted_results.append(format_store_for_llm(store_data))

            # --- SCENARIO B: DOCUMENT/PDF CONTENT ---
            # Check for actual content - documents should have chunk or content fields with real data
            elif doc.get("chunk") or doc.get("content"):
                content_text = (doc.get("chunk") or doc.get("content") or "").strip()
                if content_text and content_text != "[No content available]":
                    doc_data = {
                        "type": "DOCUMENT",
                        "title": doc.get("Title") or "Document",
                        "content": content_text
                    }
                    formatted_results.append(format_document_for_llm(doc_data))

        # Handle no results case
        if not formatted_results:
            return "No relevant information found in the knowledge base for this query."

        return "\n\n".join(formatted_results)

    except Exception as e:
        return f"Error querying Azure Search: {str(e)}"
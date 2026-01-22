# 🤖 Bring Your Own Data RAG Chatbot

## 📖 Overview
The **Bring Your Own Data RAG Chatbot** is a powerful **enterprise RAG (Retrieval-Augmented Generation)** solution that lets you chat with your own indexed data using cutting-edge AI models.

This intelligent assistant combines **Azure AI Search** for lightning-fast document retrieval with **Azure OpenAI's GPT-5** models to provide accurate, context-aware answers based exclusively on your organizational knowledge base.

Perfect for internal documentation, knowledge bases, store information, policy documents, and any searchable content you want to make conversational! 🚀

---

## 📑 Table of Contents
- [Architecture](#️-architecture)
- [Prerequisites](#-prerequisites)
- [Required Azure Resources](#-required-azure-resources)
- [Configuration](#️-configuration--environment-variables)
- [Deployment Guide](#-deployment-guide)
- [Prompt Flow Components](#-prompt-flow-components)
- [Security Best Practices](#-security-best-practices)
- [Requirements](#-requirements)
- [Troubleshooting](#-troubleshooting)
- [License](#-license)

---

## 🏗️ Architecture

**Flow Engine**  
- Azure AI Prompt Flow (Python-based)
- Modular tool architecture with jinja2 templates
- Multi-round conversation support with history

**Knowledge Base**  
- Azure AI Search (semantic search)
- Vector & hybrid search capabilities
- Custom index with your business data

**Intelligence Engine**  
- Azure OpenAI Service
- GPT-5 or GPT-5-Mini models
- Context-aware response generation

**Web Interface (Optional)**  
- Python Web App (Flask/Streamlit)
- Hosted on Azure App Service (Linux)
- Real-time chat interface

**Conversation Management**  
- Stateful conversation history
- Query modification with context
- Response cleaning and formatting

---

## ⚡ Prerequisites

- **Azure Subscription** with appropriate permissions
- **Python 3.10+** installed locally
- **Azure CLI** (for deployment)
- Basic understanding of Prompt Flow concepts

---

## 🗂️ Required Azure Resources

### 1. **Azure OpenAI Service** 💡
   - **SKU**: Standard
   - **Models Required**: 
     - `gpt-5-mini` or `gpt-4` deployment
   - **Purpose**: Generate intelligent responses

### 2. **Azure AI Search** 🔍
   - **SKU**: Basic or Standard (S1 recommended)
   - **Features Needed**:
     - Semantic search (optional but recommended)
     - Custom index with your data
   - **Purpose**: Fast document retrieval

### 3. **Azure AI Foundry Hub & Project** 🏭
   - **Purpose**: Host and deploy Prompt Flow
   - **Deployment**: Real-time endpoint

### 4. **Azure App Service** (Optional - for Web UI) 🌐
   - **SKU**: B1 or higher (Linux)
   - **Runtime**: Python 3.10
   - **Purpose**: Host web interface

### 5. **Storage Account** (Optional) 📦
   - **SKU**: Standard GPv2
   - **Purpose**: Store conversation logs, cache

---

## ⚙️ Configuration & Environment Variables

Create a `.env` file in your project root (never commit this!):

```bash
# Azure OpenAI Configuration
AZURE_OPENAI_API_KEY=your_openai_api_key_here
AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com

# Azure Search Configuration
AZURE_SEARCH_ENDPOINT=https://your-search-service.search.windows.net
AZURE_SEARCH_KEY=your_search_api_key_here
AZURE_SEARCH_INDEX_NAME=your_index_name

# Bot Configuration (for WebApp integration)
MicrosoftAppId=your_app_id
MicrosoftAppPassword=your_app_password
MicrosoftAppType=MultiTenant
MicrosoftAppTenantId=your_tenant_id

# Prompt Flow Configuration
PROMPT_FLOW_ENDPOINT=your_promptflow_endpoint
PROMPT_FLOW_API_KEY=your_promptflow_api_key

# Timeouts and Retries
AI_TIMEOUT_SECONDS=30
MAX_RETRIES=2
```

> 🔒 **Security Note**: Use the provided `.env.example` as a template. Never commit `.env` files to version control!

---

## 🚀 Deployment Guide

### Step 1: Prepare Your Data Index 📚

1. **Upload your data** to Azure AI Search:
   ```bash
   # Use Azure Portal's Import Data wizard, or
   # Use Azure Search SDK to index documents programmatically
   ```

2. **Configure your index** with appropriate fields:
   - Text content fields
   - Metadata (titles, categories, etc.)
   - Vector embeddings (optional, for semantic search)

### Step 2: Set Up Prompt Flow 🔧

1. **Create a new Prompt Flow** in Azure AI Foundry:
   ```bash
   # Navigate to your AI Foundry project
   # Create → Prompt Flow → Standard Flow
   ```

2. **Import flow definition**:
   - Use the provided `flow.dag.yaml`
   - Upload all `.py` and `.jinja2` files

3. **Configure connections**:
   - Azure OpenAI connection
   - Azure AI Search connection

4. **Test the flow** locally:
   ```bash
   pip install promptflow promptflow-tools
   pf flow test --flow ./Flow2WithCleaner
   ```

### Step 3: Deploy Prompt Flow Endpoint 🚢

```bash
# Deploy to Azure AI Foundry
pf flow build --source ./Flow2WithCleaner --output ./build
az ml online-endpoint create --name rag-chatbot-endpoint
az ml online-deployment create --name blue --endpoint rag-chatbot-endpoint
```

### Step 4: Deploy Web App (Optional) 🌐

```bash
# Create App Service
az webapp create \
  --resource-group <your-rg> \
  --plan <your-plan> \
  --name <your-app-name> \
  --runtime "PYTHON:3.10"

# Configure environment variables
az webapp config appsettings set \
  --name <your-app-name> \
  --resource-group <your-rg> \
  --settings @env.json

# Deploy code
cd WebApp
az webapp up --name <your-app-name>
```

Startup Command:
```bash
pip install -r requirements.txt && python app.py
```

### Step 5: Enable Authentication 🔐

1. Navigate to **App Service → Authentication**
2. Add Identity Provider → **Microsoft**
3. Configure:
   - **Tenant Type**: Single Tenant (recommended)
   - **Require Authentication**: Yes
   - **Unauthenticated requests**: Return 401

---

## 🧩 Prompt Flow Components

### Tools Overview

| Tool | Purpose | Input | Output |
|------|---------|-------|--------|
| **modify_query_with_history** | Rewrites user question with conversation context | query + history | standalone_question |
| **tool_lookup** | Searches Azure AI Search index | query | search_results |
| **generate_prompt_context** | Formats search results for LLM | search_results | formatted_context |
| **chat_with_gpt5** | Generates AI response | system_prompt + user_input | ai_response |
| **clean_response** | Cleans/formats final output | raw_response | clean_text |

### Flow Architecture

```
User Input → Query Modification → Search Index → Format Context → GPT-5 → Clean Response → Output
              ↑                                                        ↓
              └─────────────── Conversation History ──────────────────┘
```

### Prompt Templates 📝

**System Prompt** (`Prompt_variants.jinja2`):
- Instructs the AI to use only provided context
- Enforces citation requirements
- Prevents hallucination

**Query Rewriting** (`modify_query_with_history.jinja2`):
- Makes follow-up questions standalone
- Preserves conversation context
- Improves search relevance

---

## 🔒 Security Best Practices

✅ **DO**:
- Use Azure Key Vault for secrets
- Enable App Service Authentication
- Rotate API keys regularly
- Use managed identities where possible
- Monitor API usage and costs
- Set up alerts for unusual activity

❌ **DON'T**:
- Commit `.env` files to version control
- Hardcode credentials in source code
- Share API keys in chat/email
- Use production keys in development
- Expose endpoints without authentication

---

## 📦 Requirements

### Flow2WithCleaner (Prompt Flow)
```txt
promptflow
promptflow-tools
azure-search-documents
azure-identity
requests
python-dotenv
```

### WebApp (Optional Web Interface)
```txt
streamlit  # or flask
requests
python-dotenv
```

Install dependencies:
```bash
pip install -r requirements.txt
```

---

## 🐛 Troubleshooting

### Issue: "Missing Environment Variables"
**Solution**: Ensure all required env vars are set in `.env` or App Service Configuration.

### Issue: "Search returns no results"
**Solution**: 
- Verify index name is correct
- Check if data is properly indexed
- Test search query in Azure Portal

### Issue: "OpenAI API errors"
**Solution**:
- Verify API key and endpoint
- Check model deployment name
- Ensure sufficient quota

### Issue: "Slow response times"
**Solution**:
- Optimize search query
- Reduce context size
- Use GPT-5-Mini for faster responses
- Increase timeout values

### Issue: "Invalid JSON response from GPT"
**Solution**:
- Review system prompt clarity
- Check response cleaning logic
- Add retry logic for malformed responses

---

## 🎨 Customization

### Modify Search Behavior
Edit `tool_lookup.py`:
- Adjust `top` parameter for more/fewer results
- Change `search_mode` (any vs. all)
- Add custom filters

### Customize AI Personality
Edit `Prompt_variants.jinja2`:
- Change system instructions
- Adjust tone and style
- Modify citation format

### Add New Tools
Create new `.py` files with `@tool` decorator:
```python
from promptflow.core import tool

@tool
def my_custom_tool(input: str) -> str:
    # Your logic here
    return output
```

---

## 🚦 Monitoring & Observability

**Recommended Metrics**:
- Response latency
- Search query performance
- Token usage (cost tracking)
- Error rates
- User satisfaction (thumbs up/down)

**Logging**:
- Enable Application Insights
- Log conversation turns
- Track search relevance

---

## 🤝 Contributing

This is a starter template! Feel free to:
- Add new data sources
- Implement caching layers
- Build advanced UIs
- Add multi-language support
- Integrate with Teams/Slack

---

## 📄 License

MIT License - Feel free to use, modify, and distribute!

---

## 🎉 Get Started Now!

1. Clone this repository
2. Copy `.env.example` to `.env` and fill in your credentials
3. Install dependencies: `pip install -r requirements.txt`
4. Test locally: `pf flow test --flow ./Flow2WithCleaner`
5. Deploy and chat! 🚀

**Happy chatting with your data!** 💬✨

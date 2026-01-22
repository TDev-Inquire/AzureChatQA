# Security Guidelines

## Environment Variables

This project requires sensitive credentials to connect to Azure services. **Never commit credentials to version control.**

### Setup Instructions

1. Copy `.env.example` to `.env`:
   ```bash
   cp .env.example .env
   ```

2. Fill in your actual credentials in `.env`:
   - `AZURE_OPENAI_API_KEY` - Your Azure OpenAI API key
   - `AZURE_OPENAI_ENDPOINT` - Your Azure OpenAI resource endpoint
   - `AZURE_SEARCH_ENDPOINT` - Your Azure Search service endpoint
   - `AZURE_SEARCH_KEY` - Your Azure Search API key
   - `AZURE_SEARCH_INDEX_NAME` - Your search index name
   - `MicrosoftAppId` / `MicrosoftAppPassword` - Bot credentials (if using WebApp)
   - `PROMPT_FLOW_ENDPOINT` / `PROMPT_FLOW_API_KEY` - Prompt Flow credentials

3. The `.env` file is in `.gitignore` and will not be committed to version control.

### Local Development

For local development, create a `.env` file with your credentials. This file should never be committed.

### Production Deployment

For production deployments:
- Use Azure Key Vault or your cloud provider's secrets manager
- Pass credentials as environment variables during deployment
- Never hardcode credentials in configuration files

### Credentials in Code

All hardcoded credentials have been removed from this repository. If you find any:
1. **Immediately invalidate those credentials** in your Azure account
2. Report it as a security issue
3. Rotate new credentials

## Validation

The application validates that required environment variables are set at runtime and will provide helpful error messages if they're missing.

## Sensitive Data

The `.gitignore` file ensures:
- `.env` files are not committed
- `__pycache__` directories are excluded
- Python compiled files are excluded
- IDE configuration files are excluded
- Log files are excluded

## Best Practices

- ✅ Use environment variables for all credentials
- ✅ Keep `.env` file local only (in `.gitignore`)
- ✅ Rotate credentials periodically
- ✅ Use least-privilege access tokens
- ✅ Monitor API usage and costs
- ❌ Never commit `.env` files
- ❌ Never hardcode secrets in code
- ❌ Never share credentials in logs or messages
- ❌ Never push credentials to version control

## Emergency Procedures

If credentials are exposed:

1. **Immediately revoke the exposed credentials** in Azure Portal
2. **Generate new credentials**
3. **Update `.env` file** with new credentials
4. **Check git history** to see if credentials were ever committed:
   ```bash
   git log --all -S "your_exposed_key" -p
   ```
5. **Rewrite history if necessary** using `git filter-branch` (use with caution)
6. **Force push to remove exposure** (coordinate with team)
7. **Monitor the old credentials** for any suspicious activity

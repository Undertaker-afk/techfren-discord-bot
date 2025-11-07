# GitHub and MCP Integration

## Overview

This bot now supports automatic analysis and summarization of GitHub repositories, DeepWiki MCP projects, and Grep.app MCP projects when their links are shared in Discord channels.

## Features

### GitHub Repository Analysis

When a GitHub repository link is shared (e.g., `https://github.com/owner/repo`), the bot automatically:

1. **Scrapes repository metadata** from the GitHub API:
   - Repository description and topics
   - Star count, fork count, watchers
   - License information
   - Primary programming language and language breakdown
   - Creation and last update dates
   - Homepage URL (if available)

2. **Fetches the README** content (truncated to 5000 characters by default)

3. **Creates an AI-powered summary** using the Perplexity API to analyze:
   - Tech stack and main technologies used
   - Project purpose and key features
   - Main use cases and highlights

4. **Posts the summary in a thread** attached to the original message containing the link

### MCP DeepWiki Integration

When a DeepWiki MCP project link is shared (e.g., `https://mcp.deepwiki.com/...`), the bot:

1. Scrapes the project profile page using Firecrawl
2. Extracts key information about the MCP project
3. Generates an AI-powered summary with relevant context
4. Posts the summary in a thread

### MCP Grep.app Integration

When a Grep.app MCP project link is shared (e.g., `https://mcp.grep.app/...`), the bot:

1. Scrapes the project page using Firecrawl
2. Extracts project details and features
3. Generates an AI-powered summary
4. Posts the summary in a thread

## Configuration

### GitHub API Token (Optional but Recommended)

To avoid GitHub API rate limits, configure a personal access token:

1. **Generate a token**:
   - Go to [GitHub Settings > Tokens](https://github.com/settings/tokens)
   - Click "Generate new token (classic)"
   - Select scopes: `public_repo` (read access to public repositories)
   - Generate and copy the token

2. **Add to .env file**:
   ```bash
   GITHUB_API_TOKEN=ghp_your_token_here
   ```

3. **Rate limits**:
   - Without token: 60 requests/hour
   - With token: 5,000 requests/hour

### README Truncation Limit

Control how much of the README is processed:

```bash
# In .env file
REPO_README_MAX_LENGTH=5000  # Default: 5000 characters
```

## How It Works

### Automatic Detection

The bot monitors all messages in configured channels for URLs matching:

- **GitHub**: `https://github.com/{owner}/{repo}`
- **DeepWiki**: `https://mcp.deepwiki.com/...`
- **Grep.app**: `https://mcp.grep.app/...`

### Processing Flow

1. **URL Detection**: Bot identifies supported URLs in messages
2. **Scraping**: 
   - GitHub: Uses GitHub REST API for metadata and README
   - MCP sites: Uses Firecrawl for web scraping
3. **Summarization**: Perplexity API analyzes the content
4. **Thread Creation**: Summary posted in a thread attached to the original message
5. **Database Storage**: Summary stored for future reference

### Thread Naming

Threads are automatically named based on the link type:

- GitHub: `GitHub Repo: github.com/owner/repo`
- DeepWiki: `DeepWiki MCP: mcp.deepwiki.com/...`
- Grep.app: `Grep.app MCP: mcp.grep.app/...`

## Example Usage

### In the links-dump Channel

1. **User posts**: `Check out this cool repo: https://github.com/microsoft/vscode`

2. **Bot responds** by:
   - Creating a thread on the message
   - Posting a formatted summary like:

   ```
   🔧 GitHub Repository Summary:

   **Tech Stack**: TypeScript, JavaScript, CSS
   **Main Purpose**: Visual Studio Code is a lightweight but powerful source code editor
   **Key Features**:
   - Extensible plugin architecture
   - Built-in Git integration
   - IntelliSense code completion
   - Debugging support
   [... more details ...]
   ```

3. **Database**: Summary is stored and associated with the message

### Multiple Links

If a message contains multiple supported links, each link gets its own thread with a summary.

## Fallback Behavior

- **GitHub scraping fails**: Falls back to Firecrawl for basic web scraping
- **API rate limit**: Returns error message in thread
- **Private repositories**: Returns "Repository not found" error
- **Invalid URLs**: Skipped silently

## Integration with Existing Features

- **Works alongside X/Twitter summarization**: Both features operate independently
- **Links-dump channel enforcement**: Link requirement still applies
- **Database storage**: Uses existing `scraped_url` and `scraped_content_summary` fields
- **Same LLM backend**: Uses Perplexity API like other summarization features

## Technical Details

### New Files

- `github_handler.py`: GitHub API integration and scraping
- `mcp_handler.py`: DeepWiki and Grep.app scraping via Firecrawl
- `GITHUB_MCP_INTEGRATION.md`: This documentation

### Modified Files

- `bot.py`: Added URL detection and handler invocation in `on_message` event
- `requirements.txt`: Added `aiohttp` dependency for async HTTP requests
- `config.py`: Added GitHub token configuration
- `.env.sample`: Added GitHub token and README truncation settings

### Dependencies

- **aiohttp**: Async HTTP client for GitHub API calls
- **Firecrawl**: Web scraping for MCP sites (already configured)
- **Perplexity API**: AI-powered summarization (already configured)

## Troubleshooting

### GitHub API Rate Limit

**Symptom**: "API rate limit exceeded" errors

**Solution**:
1. Add `GITHUB_API_TOKEN` to `.env`
2. Verify token has proper scopes
3. Check rate limit status: `curl -H "Authorization: token YOUR_TOKEN" https://api.github.com/rate_limit`

### README Too Long

**Symptom**: Summaries are incomplete or timeout

**Solution**:
1. Reduce `REPO_README_MAX_LENGTH` in `.env`
2. Recommended range: 3000-7000 characters

### Threads Not Creating

**Symptom**: Summaries not appearing in threads

**Solution**:
1. Verify bot has `Create Public Threads` permission
2. Check bot logs for error messages
3. Ensure channel supports threads (text channels only)

### MCP Sites Not Scraping

**Symptom**: DeepWiki/Grep.app links not being processed

**Solution**:
1. Verify `FIRECRAWL_API_KEY` is configured
2. Check Firecrawl API quotas and limits
3. Test URL manually with Firecrawl

## Future Enhancements

Potential improvements for future versions:

- Support for GitLab, Bitbucket, and other code hosting platforms
- Repository dependency analysis
- Code quality metrics extraction
- Star history tracking over time
- Comparison between multiple repositories
- Support for specific file/directory links
- Integration with additional MCP registries

## Resources

- [GitHub REST API Documentation](https://docs.github.com/en/rest)
- [DeepWiki MCP](https://mcp.deepwiki.com)
- [Grep.app MCP](https://mcp.grep.app)
- [Firecrawl API](https://docs.firecrawl.dev)

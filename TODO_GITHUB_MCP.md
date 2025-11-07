# TODO: GitHub & MCP Integration Enhancements

This TODO document tracks future improvements related to the automated GitHub repository analysis and MCP (DeepWiki & Grep.app) integration.

## Documentation & Reference

- [GITHUB_MCP_INTEGRATION.md](./GITHUB_MCP_INTEGRATION.md) — Overview of the implemented integration
- [DeepWiki MCP Spec](https://mcp.deepwiki.com) — Source profiles for MCP projects
- [Grep.app MCP Directory](https://mcp.grep.app) — Additional MCP projects supported by the bot

## Task List

### 1. GitHub Repository Insights
- [ ] Add dependency file parsing (e.g., package.json, requirements.txt) for key dependencies
- [ ] Include contributor statistics (top 5 contributors, recent activity)
- [ ] Cache repository analyses to avoid repeated API calls within a configurable TTL
- [ ] Provide diff-aware summaries when a repo link is reposted after updates

### 2. DeepWiki MCP Enhancements
- [ ] Introduce structured parsing of profile sections (description, features, setup)
- [ ] Highlight MCP capabilities and target audience in summaries
- [ ] Add detection of related MCP projects for cross-references

### 3. Grep.app MCP Enhancements
- [ ] Normalize project metadata scraped from Grep.app (name, description, language)
- [ ] Add syntax-highlighted code snippet summaries when relevant
- [ ] Support query parameter parsing to refine summarization prompts

### 4. Summarization & Thread Experience
- [ ] Customize prompt templates per link type (GitHub vs DeepWiki vs Grep.app)
- [ ] Append quick links to documentation or demos in thread replies
- [ ] Add reaction-based feedback to let users rate summary usefulness

### 5. Operational Improvements
- [ ] Monitor GitHub API rate limits and post warnings when thresholds are approaching
- [ ] Log and surface Firecrawl errors with actionable retry suggestions
- [ ] Expand automated tests covering GitHub/MCP handlers and thread creation logic

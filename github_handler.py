"""
GitHub handler module for the Discord bot.
Handles scraping GitHub repository metadata using the GitHub REST API.
"""

import asyncio
import logging
import re
import base64
import os
from typing import Optional, Dict, Any
import json
import aiohttp

logger = logging.getLogger('discord_bot.github_handler')

GITHUB_API_BASE_URL = "https://api.github.com"
REPO_README_MAX_LENGTH = 5000

def _get_github_token() -> Optional[str]:
    """
    Retrieve a GitHub API token from the environment or a local config module.
    
    Checks the `GITHUB_API_TOKEN` environment variable first; if not present, attempts to import a local `config` module and return its `github_api_token` attribute. Returns `None` if no token is found or if the config access fails.
    
    Returns:
        Optional[str]: The GitHub API token, or `None` if unavailable.
    """
    token = os.getenv('GITHUB_API_TOKEN')
    if token:
        return token
    try:
        import config  # type: ignore
        return getattr(config, 'github_api_token', None)
    except Exception:
        return None

def _get_readme_limit(default: int = REPO_README_MAX_LENGTH) -> int:
    """
    Determine the maximum README length to use when fetching and truncating README content.
    
    Checks the REPO_README_MAX_LENGTH environment variable and returns its integer value if valid; if the environment variable is present but not an integer, logs a warning and falls back. If the environment variable is not set, attempts to read `repo_readme_max_length` from a local `config` module. On any error or missing configuration, returns the provided `default`.
    
    Parameters:
        default (int): Fallback limit to use when no valid environment or config value is available.
    
    Returns:
        int: The determined README length limit.
    """
    env_value = os.getenv('REPO_README_MAX_LENGTH')
    if env_value:
        try:
            return int(env_value)
        except ValueError:
            logger.warning(f"Invalid REPO_README_MAX_LENGTH value '{env_value}', defaulting to {default}")
    try:
        import config  # type: ignore
        return int(getattr(config, 'repo_readme_max_length', default))
    except Exception:
        return default

async def is_github_url(url: str) -> bool:
    """
    Determine whether a URL points to a GitHub repository (contains an owner/repository path).
    
    Returns:
        True if the URL contains a GitHub owner/repo path, False otherwise.
    """
    pattern = r'(?:^https?://(?:www\.)?github\.com)/([^/]+)/([^/\s?#]+)'
    return bool(re.search(pattern, url))

def extract_repo_info(url: str) -> Optional[Dict[str, str]]:
    """
    Extract the owner and repository name from a GitHub URL.
    
    Supports URLs with optional scheme (http/https), optional "www.", and an optional trailing ".git" on the repository name.
    
    Returns:
        dict: A mapping with keys 'owner' and 'repo' when extraction succeeds, `None` otherwise.
    """
    try:
        pattern = r'(?:https?://)?(?:www\.)?github\.com/([^/]+)/([^/\s?#]+)'
        match = re.search(pattern, url)
        
        if match:
            owner = match.group(1)
            repo = match.group(2)
            
            repo = repo.rstrip('.git')
            
            return {
                'owner': owner,
                'repo': repo
            }
        
        logger.debug(f"No repo info found in URL: {url}")
        return None
    except Exception as e:
        logger.error(f"Error extracting repo info from URL {url}: {str(e)}", exc_info=True)
        return None

async def fetch_repo_metadata(owner: str, repo: str) -> Optional[Dict[str, Any]]:
    """
    Fetch repository metadata for a GitHub repository.
    
    Parameters:
        owner (str): Repository owner name.
        repo (str): Repository name.
    
    Returns:
        Repository metadata as a dictionary if successful, `None` if the repository was not found, access is forbidden, or an error occurred while fetching.
    """
    try:
        logger.info(f"Fetching metadata for GitHub repo: {owner}/{repo}")
        
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "TechFren-Discord-Bot"
        }
        
        token = _get_github_token()
        if token:
            headers["Authorization"] = f"token {token}"
            logger.debug("Using authenticated GitHub API request")
        
        url = f"{GITHUB_API_BASE_URL}/repos/{owner}/{repo}"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 404:
                    logger.warning(f"Repository not found: {owner}/{repo}")
                    return None
                elif response.status == 403:
                    logger.warning(f"Access forbidden to repository: {owner}/{repo}")
                    return None
                elif response.status != 200:
                    logger.error(f"GitHub API returned status {response.status} for {owner}/{repo}")
                    return None
                
                data = await response.json()
                logger.info(f"Successfully fetched metadata for {owner}/{repo}")
                return data
                
    except Exception as e:
        logger.error(f"Error fetching repo metadata for {owner}/{repo}: {str(e)}", exc_info=True)
        return None

async def fetch_repo_readme(owner: str, repo: str) -> Optional[str]:
    """
    Retrieve and decode a repository's README from the GitHub API.
    
    Fetches the README file for the given repository, decodes its base64 content to UTF-8, and enforces a configurable maximum length (truncating and appending "\n\n... (README truncated for brevity)" if exceeded). Returns `None` when no README is found, the content is empty, or an error occurs during fetching or decoding.
    
    Parameters:
        owner (str): Repository owner name.
        repo (str): Repository name.
    
    Returns:
        Optional[str]: Decoded README text (possibly truncated), or `None` if unavailable or on error.
    """
    try:
        logger.info(f"Fetching README for GitHub repo: {owner}/{repo}")
        
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "TechFren-Discord-Bot"
        }
        
        token = _get_github_token()
        if token:
            headers["Authorization"] = f"token {token}"
        
        url = f"{GITHUB_API_BASE_URL}/repos/{owner}/{repo}/readme"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status == 404:
                    logger.info(f"No README found for repository: {owner}/{repo}")
                    return None
                elif response.status != 200:
                    logger.warning(f"GitHub API returned status {response.status} for README of {owner}/{repo}")
                    return None
                
                data = await response.json()
                
                content = data.get('content', '')
                if not content:
                    logger.warning(f"Empty README content for {owner}/{repo}")
                    return None
                
                try:
                    decoded_content = base64.b64decode(content).decode('utf-8')
                    
                    max_length = _get_readme_limit(REPO_README_MAX_LENGTH)
                    
                    if len(decoded_content) > max_length:
                        logger.info(f"Truncating README from {len(decoded_content)} to {max_length} characters")
                        decoded_content = decoded_content[:max_length] + "\n\n... (README truncated for brevity)"
                    
                    logger.info(f"Successfully fetched README for {owner}/{repo} ({len(decoded_content)} chars)")
                    return decoded_content
                except Exception as e:
                    logger.error(f"Error decoding README content: {str(e)}", exc_info=True)
                    return None
                
    except Exception as e:
        logger.error(f"Error fetching README for {owner}/{repo}: {str(e)}", exc_info=True)
        return None

async def fetch_repo_languages(owner: str, repo: str) -> Optional[Dict[str, int]]:
    """
    Fetch the byte-count breakdown of languages used in a GitHub repository.
    
    Parameters:
        owner (str): GitHub repository owner (username or organization).
        repo (str): Repository name.
    
    Returns:
        Optional[Dict[str, int]]: Mapping of language names to byte counts, or `None` if the request failed or an error occurred.
    """
    try:
        logger.info(f"Fetching languages for GitHub repo: {owner}/{repo}")
        
        headers = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "TechFren-Discord-Bot"
        }
        
        token = _get_github_token()
        if token:
            headers["Authorization"] = f"token {token}"
        
        url = f"{GITHUB_API_BASE_URL}/repos/{owner}/{repo}/languages"
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url, headers=headers) as response:
                if response.status != 200:
                    logger.warning(f"GitHub API returned status {response.status} for languages of {owner}/{repo}")
                    return None
                
                data = await response.json()
                logger.info(f"Successfully fetched languages for {owner}/{repo}")
                return data
                
    except Exception as e:
        logger.error(f"Error fetching languages for {owner}/{repo}: {str(e)}", exc_info=True)
        return None

def format_language_breakdown(languages: Dict[str, int]) -> str:
    """
    Create a human-readable top-5 language breakdown showing each language's percentage of the repository.
    
    Parameters:
        languages (Dict[str, int]): Mapping of language names to byte counts.
    
    Returns:
        str: "No language data available" if there are no languages or total bytes is zero; otherwise a newline-separated list of up to five lines formatted as "  - {language}: {percentage:.1f}%".
    """
    if not languages:
        return "No language data available"
    
    total_bytes = sum(languages.values())
    if total_bytes == 0:
        return "No language data available"
    
    sorted_languages = sorted(languages.items(), key=lambda x: x[1], reverse=True)
    
    language_lines = []
    for lang, bytes_count in sorted_languages[:5]:
        percentage = (bytes_count / total_bytes) * 100
        language_lines.append(f"  - {lang}: {percentage:.1f}%")
    
    return "\n".join(language_lines)

def format_as_markdown(repo_data: Dict[str, Any], readme_content: Optional[str], languages: Optional[Dict[str, int]]) -> str:
    """
    Compose a Markdown document representing GitHub repository information.
    
    Parameters:
        repo_data (Dict[str, Any]): Repository metadata as returned by the GitHub API (e.g., full_name, description, html_url, stargazers_count, forks_count, watchers_count, open_issues_count, topics, license, homepage, created_at, updated_at).
        readme_content (Optional[str]): Decoded README content to include, or None to omit.
        languages (Optional[Dict[str, int]]): Mapping of language names to byte counts used to produce a language breakdown, or None to omit.
    
    Returns:
        str: A Markdown-formatted string containing repository header, description, URL, statistics, optional language breakdown, topics, license, homepage, timestamps, and README section (if provided).
    """
    try:
        markdown = f"# GitHub Repository: {repo_data.get('full_name', 'Unknown')}\n\n"
        
        if repo_data.get('description'):
            markdown += f"**Description:** {repo_data['description']}\n\n"
        
        markdown += f"**Repository URL:** {repo_data.get('html_url', 'N/A')}\n\n"
        
        markdown += "## Repository Statistics\n\n"
        markdown += f"- **Stars:** {repo_data.get('stargazers_count', 0):,}\n"
        markdown += f"- **Forks:** {repo_data.get('forks_count', 0):,}\n"
        markdown += f"- **Watchers:** {repo_data.get('watchers_count', 0):,}\n"
        markdown += f"- **Open Issues:** {repo_data.get('open_issues_count', 0):,}\n\n"
        
        if languages:
            markdown += "## Language Breakdown\n\n"
            markdown += format_language_breakdown(languages) + "\n\n"
        
        if repo_data.get('topics'):
            markdown += "## Topics\n\n"
            topics_str = ", ".join(repo_data['topics'])
            markdown += f"{topics_str}\n\n"
        
        if repo_data.get('license'):
            license_name = repo_data['license'].get('name', 'Unknown')
            markdown += f"**License:** {license_name}\n\n"
        
        if repo_data.get('homepage'):
            markdown += f"**Homepage:** {repo_data['homepage']}\n\n"
        
        created_at = repo_data.get('created_at', 'Unknown')
        updated_at = repo_data.get('updated_at', 'Unknown')
        markdown += f"**Created:** {created_at}\n"
        markdown += f"**Last Updated:** {updated_at}\n\n"
        
        if readme_content:
            markdown += "## README\n\n"
            markdown += readme_content + "\n\n"
        
        return markdown
    except Exception as e:
        logger.error(f"Error formatting GitHub data as markdown: {str(e)}", exc_info=True)
        return "Error formatting GitHub repository information."

async def scrape_github_repo(url: str) -> Optional[Dict[str, Any]]:
    """
    Scrapes a GitHub repository URL and returns formatted markdown plus the raw fetched data.
    
    Returns:
        Optional[Dict[str, Any]]: A dictionary with:
            - 'markdown': a formatted markdown string representing the repository,
            - 'raw_data': a dict with:
                - 'metadata': repository metadata dict,
                - 'readme': README content string or None,
                - 'languages': mapping of language names to byte counts or None.
        Returns `None` if scraping fails.
    """
    try:
        logger.info(f"Scraping GitHub repository: {url}")
        
        repo_info = extract_repo_info(url)
        if not repo_info:
            logger.warning(f"Failed to extract repo info from URL: {url}")
            return None
        
        owner = repo_info['owner']
        repo = repo_info['repo']
        
        repo_data = await fetch_repo_metadata(owner, repo)
        if not repo_data:
            logger.warning(f"Failed to fetch repo metadata for {owner}/{repo}")
            return None
        
        readme_task = fetch_repo_readme(owner, repo)
        languages_task = fetch_repo_languages(owner, repo)
        
        readme_content, languages = await asyncio.gather(readme_task, languages_task)
        
        markdown_content = format_as_markdown(repo_data, readme_content, languages)
        
        return {
            'markdown': markdown_content,
            'raw_data': {
                'metadata': repo_data,
                'readme': readme_content,
                'languages': languages
            }
        }
        
    except Exception as e:
        logger.error(f"Error scraping GitHub repository {url}: {str(e)}", exc_info=True)
        return None
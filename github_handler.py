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
    token = os.getenv('GITHUB_API_TOKEN')
    if token:
        return token
    try:
        import config  # type: ignore
        return getattr(config, 'github_api_token', None)
    except Exception:
        return None

def _get_readme_limit(default: int = REPO_README_MAX_LENGTH) -> int:
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
    Check if a URL is from GitHub.
    
    Args:
        url (str): The URL to check
        
    Returns:
        bool: True if the URL is from GitHub, False otherwise
    """
    pattern = r'(?:^https?://(?:www\.)?github\.com)/([^/]+)/([^/\s?#]+)'
    return bool(re.search(pattern, url))

def extract_repo_info(url: str) -> Optional[Dict[str, str]]:
    """
    Extract repository owner and name from a GitHub URL.
    
    Args:
        url (str): The GitHub URL
        
    Returns:
        Optional[Dict[str, str]]: Dictionary with 'owner' and 'repo' keys, or None if extraction failed
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
    Fetch repository metadata from GitHub API.
    
    Args:
        owner (str): Repository owner
        repo (str): Repository name
        
    Returns:
        Optional[Dict[str, Any]]: Repository metadata or None if fetch failed
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
    Fetch repository README content from GitHub API.
    
    Args:
        owner (str): Repository owner
        repo (str): Repository name
        
    Returns:
        Optional[str]: README content (decoded) or None if fetch failed
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
    Fetch repository language breakdown from GitHub API.
    
    Args:
        owner (str): Repository owner
        repo (str): Repository name
        
    Returns:
        Optional[Dict[str, int]]: Language breakdown (language: bytes) or None if fetch failed
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
    Format language breakdown as a readable string with percentages.
    
    Args:
        languages (Dict[str, int]): Language breakdown (language: bytes)
        
    Returns:
        str: Formatted language breakdown
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
    Format GitHub repository data as markdown.
    
    Args:
        repo_data (Dict[str, Any]): Repository metadata from GitHub API
        readme_content (Optional[str]): README content
        languages (Optional[Dict[str, int]]): Language breakdown
        
    Returns:
        str: Formatted markdown content
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
    Scrape a GitHub repository by fetching metadata, README, and language breakdown.
    
    Args:
        url (str): The GitHub repository URL
        
    Returns:
        Optional[Dict[str, Any]]: Dictionary with 'markdown' and 'raw_data' keys, or None if scraping failed
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

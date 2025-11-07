"""
MCP (Model Context Protocol) handler module for the Discord bot.
Handles scraping MCP-related URLs like mcp.deepwiki.com and mcp.grep.app
using the Firecrawl API.
"""

import logging
import re
from typing import Optional, Dict, Any

from firecrawl_handler import scrape_url_content

logger = logging.getLogger('discord_bot.mcp_handler')

async def is_deepwiki_url(url: str) -> bool:
    """
    Determine whether the given URL belongs to mcp.deepwiki.com.
    
    Returns:
        `true` if the URL is from mcp.deepwiki.com, `false` otherwise.
    """
    pattern = r'(?:^https?://)?(?:www\.)?mcp\.deepwiki\.com'
    return bool(re.search(pattern, url))

async def is_grep_app_url(url: str) -> bool:
    """
    Check if a URL is from mcp.grep.app.
    
    Args:
        url (str): The URL to check
        
    Returns:
        bool: True if the URL is from mcp.grep.app, False otherwise
    """
    pattern = r'(?:^https?://)?(?:www\.)?mcp\.grep\.app'
    return bool(re.search(pattern, url))

async def scrape_deepwiki_content(url: str) -> Optional[Dict[str, Any]]:
    """
    Fetch enhanced markdown scraped from a DeepWiki MCP URL.
    
    Parameters:
        url (str): The DeepWiki MCP URL to scrape.
    
    Returns:
        Optional[Dict[str, Any]]: A dict with a single key `'markdown'` containing the scraped content prefixed with a header and the source URL, or `None` if scraping failed.
    """
    try:
        logger.info(f"Scraping DeepWiki MCP URL: {url}")
        
        markdown_content = await scrape_url_content(url)
        
        if not markdown_content:
            logger.warning(f"Failed to scrape DeepWiki content from URL: {url}")
            return None
        
        enhanced_markdown = f"# DeepWiki MCP Project\n\n"
        enhanced_markdown += f"**Source URL:** {url}\n\n"
        enhanced_markdown += markdown_content
        
        return {
            'markdown': enhanced_markdown
        }
        
    except Exception as e:
        logger.error(f"Error scraping DeepWiki URL {url}: {str(e)}", exc_info=True)
        return None

async def scrape_grep_app_content(url: str) -> Optional[Dict[str, Any]]:
    """
    Fetch and return enhanced markdown scraped from a Grep.app MCP URL.
    
    Prefixes the retrieved markdown with a standard header and the source URL before returning it.
    
    Parameters:
        url (str): Grep.app MCP page URL to scrape.
    
    Returns:
        Optional[Dict[str, Any]]: A dictionary with a single key `'markdown'` containing the enhanced markdown, or `None` if scraping failed.
    """
    try:
        logger.info(f"Scraping Grep.app MCP URL: {url}")
        
        markdown_content = await scrape_url_content(url)
        
        if not markdown_content:
            logger.warning(f"Failed to scrape Grep.app content from URL: {url}")
            return None
        
        enhanced_markdown = f"# Grep.app MCP Project\n\n"
        enhanced_markdown += f"**Source URL:** {url}\n\n"
        enhanced_markdown += markdown_content
        
        return {
            'markdown': enhanced_markdown
        }
        
    except Exception as e:
        logger.error(f"Error scraping Grep.app URL {url}: {str(e)}", exc_info=True)
        return None
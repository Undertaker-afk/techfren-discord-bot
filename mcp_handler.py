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
    Check if a URL is from mcp.deepwiki.com.
    
    Args:
        url (str): The URL to check
        
    Returns:
        bool: True if the URL is from mcp.deepwiki.com, False otherwise
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
    Scrape content from a DeepWiki MCP URL using Firecrawl.
    
    Args:
        url (str): The DeepWiki URL to scrape
        
    Returns:
        Optional[Dict[str, Any]]: Dictionary with 'markdown' key containing scraped content, or None if scraping failed
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
    Scrape content from a Grep.app MCP URL using Firecrawl.
    
    Args:
        url (str): The Grep.app URL to scrape
        
    Returns:
        Optional[Dict[str, Any]]: Dictionary with 'markdown' key containing scraped content, or None if scraping failed
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

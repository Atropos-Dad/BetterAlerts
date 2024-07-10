import logging; logger = logging.getLogger(__name__)

import feedparser
from urllib.parse import urlparse,parse_qs
from urllib.parse import urlparse
from datetime import date
from dateutil.parser import parse as parse_date
import requests

from article_parser import assess_article

def get_urls_from_rss_feed(rss_url):
    '''
    Returns a list of URLs from the given RSS feed URL.'''
    try:
        feed = feedparser.parse(rss_url)
        # Check for errors
        if feed.bozo:
            raise ValueError(f"Error parsing RSS feed: {feed.bozo_exception}")
        
        # Extract URLs from the feed
        urls = [entry.link for entry in feed.entries if 'link' in entry]

        return urls
    
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return []

def resolve_url(url):
    '''Resolves the final URL after following all redirects.'''
    try:
        response = requests.head(url, allow_redirects=True, timeout=5)
        return response.url
    
    except requests.RequestException as e:
        logger.error(f"Error resolving URL: {e}")
        logger.error(f"URL: {url}")
        return None

def extract_formated_url(redirected_url):
    # removes the tracking url from the actual url
    parsed_url = urlparse(redirected_url)
    query_params = parse_qs(parsed_url.query)
    actual_url = query_params.get('url', [None])[0]

    # incase the final url is a redirect, will resolve to final! 
    resolved_url = resolve_url(actual_url)

    return resolved_url

def fetch_rss_feed_from_url(rss_url):
    '''
    Fetches the RSS feed from the given URL and returns the feed object.
    '''
    if rss_url.startswith('http://') or rss_url.startswith('https://'):
        feed = feedparser.parse(rss_url)
    else:
        with open(rss_url, 'rb') as file:
            feed = feedparser.parse(file)
    
    if feed.bozo:
        raise ValueError(f"Error parsing RSS feed: {feed.bozo_exception}")
    
    return feed

def get_urls_and_assess(company, rss_url, startup_blurb, clean_up_url=True):
    valid_urls = []
    today = date.today()

    try:
        feed = fetch_rss_feed_from_url(rss_url)

        
        logger.info(f"Fetching RSS feed from: {rss_url} - Feed title: {feed.feed.title} - Number of entries: {len(feed.entries)}")

        for entry in feed.entries:
            if 'link' in entry:
                url = entry.link
                
                clean_url = extract_formated_url(url) if clean_up_url else url
                
                date_published_str = entry.get('published')

                if date_published_str != None:
                    date_published = parse_date(date_published_str).date()
                    
                    logger.debug(f"URL: {clean_url}, Published Date: {date_published}, Today's Date: {today}")
                    
                    if date_published == today:
                        try:
                            result = assess_article(company, clean_url, startup_blurb)

                            if result is not None and result["is_referenced"]:
                                valid_urls.append(result)
                                logger.debug(result)

                        except Exception as e:
                            logger.error(f"Error assessing article: {e}")
                            
                    else:
                        # break completly from this loop! The rest of the articles are not from today
                        logger.debug(f"Breaking loop - article is not from today")
                        break
                else:
                    logger.warning(f"No date found for URL: {clean_url}")
            else:
                logger.warning("No link found in entry")

        return valid_urls
    
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return []

def get_urls(rss_url, clean_up_url=True):
    urls = []
    try:
        if rss_url.startswith('http://') or rss_url.startswith('https://'):
            feed = feedparser.parse(rss_url)
        else:
            with open(rss_url, 'rb') as file:
                feed = feedparser.parse(file)
                
        # Check for errors
        if feed.bozo:
            logger.error(f"Error parsing RSS feed: {feed.bozo_exception}")
            raise ValueError(f"Error parsing RSS feed: {feed.bozo_exception}")
        
        logger.info(f"Fetching RSS feed from: {rss_url} - Feed title: {feed.feed.title} - Number of entries: {len(feed.entries)}")

        for entry in feed.entries:
            if 'link' in entry:
                url = entry.link
                
                if clean_up_url:
                    clean_url = extract_formated_url(url)
                else:
                    clean_url = url
                
                urls.append(clean_url)
            else:
                logger.warning("No link found in entry")

        return urls
    except Exception as e:
        logger.error(f"An error occurred: {e}")
        return []
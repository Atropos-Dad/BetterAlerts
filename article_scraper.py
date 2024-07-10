import requests
from bs4 import BeautifulSoup
import random
import logging; logger = logging.getLogger(__name__)
import asyncio
from playwright.async_api import async_playwright

version = random.randint(100, 199)
user_agent = f'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/{version}.0.0.0 Safari/537.36'

headers = {
    'User-Agent': user_agent
}

async def get_article_html_playwright(url):
    '''
    Fetches the html content of the article using playwright
    Args: 
        url: The url of the article
    Returns:
        str: The html content of the article
    '''
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        await page.goto(url)
        html = await page.content()
        await browser.close()
        return html

is_text_shorter_than = lambda text, length: len(text) < length

def validate_article_parse(article):
    """
    Checks if the article is valid based on certain conditions.

    Args:
        article (str): The article content.

    Returns:
        bool: True if the article is valid, False otherwise.
    """
    # Empty! 
    if article is None:
        logger.warning("No article found - refer back to soup.find bug")
        return False
    
    # Empty string?
    elif article.get_text().strip() == "":
        logger.warning("Article is empty")
        return False
    
    # too little text
    elif is_text_shorter_than(article.get_text(), 50):
        logger.warning("Article is less than 50 characters")
        return False
    
    # we're all good :)
    return True

def check_for_protection(text, threshold=3):
    """
    Checks if the given text contains any protection-related keywords. Stuff like "cloudflare, ddos, challenge, captcha, etc"
    Simple and dumb and good
    """
    key_words = ["cloudflare", "ddos", "challenge", "captcha"]

    text = text.lower()
    
    count = sum(text.count(word) for word in key_words)
    
    return count > threshold

encode_replace_decode = lambda text: text.encode('utf-8', errors='replace').decode()

#beautifulsoup, just take the text
def get_article_text_no_html(html):
    soup = BeautifulSoup(html, 'html.parser')
    return soup.get_text()

def get_article_text(url):

    """
    Fetches the text content of an article from the provided URL.

    Returns:
        str: The text content of the article or an error message if the article is not found.
    """

    ## first get html
    try:
        # URL getter
        response = requests.get(url, timeout=5, headers=headers)  

    except Exception as e:
        logger.error(f"Error fetching article: {e}")
        raise ValueError(f"Error fetching article: {e}")
    
    ## check for 403 forbidden
    if response.status_code == 403:

        # if we are blocked, send it off to playwright
        response = asyncio.run(get_article_html_playwright(url))

        if check_for_protection(response):
            # if the playwright response contains protection-related keywords, we are blocked properly, womp womp
            logger.debug(f"Article content {response}")
            raise ValueError(f"Article {url} is protected. Unable to scrape.")
            
    else:
        response = response.text # otherwise we got the all clear
    
    ## parse the html, try find the article via article tag
    soup = BeautifulSoup(response, 'html.parser')
    soup.encode("utf-8")

    article = soup.find('article')


    logger.info(f"Scraped article {url} successfully.")

    if validate_article_parse(article): # if the article parse is valid
        return get_article_text_no_html(encode_replace_decode(article.get_text()))
    
    # else return the original response of the whole page
    return get_article_text_no_html(encode_replace_decode(response))

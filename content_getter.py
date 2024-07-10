from os import environ
import google.generativeai as genai
import markdownify as md
import json
from article_scraper import get_article_text


safe = [
        
        {
            "category": "HARM_CATEGORY_HARASSMENT",
            "threshold": "BLOCK_NONE",
        },
        {
            "category": "HARM_CATEGORY_HATE_SPEECH",
            "threshold": "BLOCK_NONE",
        },
        {
            "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
            "threshold": "BLOCK_NONE",
        },
        {
            "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
            "threshold": "BLOCK_NONE",
        },
    ]

model_config = {
    "temperature": 1
}
model = genai.GenerativeModel('gemini-1.5-pro', safety_settings=safe, generation_config=model_config)



import logging
logger = logging.getLogger(__name__)

def remove_newlines(string):
    return string.replace("\n", "").replace("\\\n", "")

remove_blank_lines = lambda text: '\n'.join(line for line in text.splitlines() if line.strip())

def clean_up_html(text):
    # remove new lines
    # remove blank lines
    # remove extra spaces
    # keep just latin text 
    # remove all other characters
    cleaned_text = ' '.join(text.split())
    cleaned_text = ''.join(c for c in cleaned_text if c.isalnum() or c.isspace())
    cleaned_text = cleaned_text.encode('ascii', 'ignore').decode('ascii')
    return cleaned_text

def make_json_safe(text):
  """
  Escapes characters in a string to make it safe for JSON.

  Args:
      text: The text string to convert.

  Returns:
      A JSON-safe string representation of the text.
  """
  # Escape control characters and quotes
  json_escaped = text.replace("\\", "\\\\")\
                     .replace('"', '\\"')\
                     .replace("\b", "\\b")\
                     .replace("\f", "\\f")\
                     .replace("\n", "\\n")\
                     .replace("\r", "\\r")\
                     .replace("\t", "\\t")

  # Escape non-ASCII characters
  non_ascii_escaped = []
  for char in json_escaped:
    if ord(char) >= 127:
      # Convert to hex string with leading zeros
      escaped_char = "\\u{:04x}".format(ord(char))
    else:
      escaped_char = char
    non_ascii_escaped.append(escaped_char)

  return ''.join(non_ascii_escaped)

def get_article_text_ai(url):

    """
    Fetches and processes the content of an article from a given URL using an AI model.

    Returns:
        dict: A JSON response with features "is_article", "is_accessible", and "content".
              Returns None if the article is not accessible or not an article.
    """ 

    try:
        text = get_article_text(url)
        logger.debug(f"Processed Article input to AI: {text}")
    except Exception as e:
        logger.error(f"Error getting article text: {e}")
        return None
    
    html = make_json_safe(remove_newlines(md.markdownify((text))))
    logger.debug(f"AI processed Article (json cleaning): {text}")


    if logger.isEnabledFor(logging.DEBUG):
        logger.debug(f"prompting AI with html: {remove_newlines(html)}")
    else:
        logger.info(f"Submitting {url} html content for content analysis.")

    
    
    response = model.generate_content(f"""
    Your response will be in exact and valid JSON. The json should have three features, "is_article", "is_accessible" and "content". 
    You will be shown the markdown version of a webpage containing an article. 
    Some of the elements of the page are not required and should not be included. 
    These elements include but are not limited to: other article titles, links to other pages, the title of the publisher, advertisements, phrases such as "Share" and tags should be removed along with any other non-article content.
    Remove all of this content. The content field should ONLY be content that is part of the article (i.e. elements a human would be most interested in reading).
    The title should be preceded by a "title:" tag.
    If the content you are given is incomplete to the point of being illegible, or is behind paywall, respond with "is_accessible" being 'false' in lower-caps.
    If the webpage is not an article, response with "is_article" being 'false'. 
    If the webpage is an article, the content feature of your response should be an EXACT copy of the markdown version of the text of the article with no additional syntax.
    In the event that the article is not accessible, or is not an article, the content feature should still contain as much markdown as possible.
    The article content should include the date (if in article) structured as date: dd/mm/year, if no date is present state there is no date.
            
    Please ensure your response contains no formatting, and is simply the pure json response (i.e no new lines, no spaces, no tabs, no use of ```json formatting, etc.)
    If there are any elements of the content which would break the json formatting, you have permission to alter the content to ensure the json is valid.


    Example webpage markdown: 
    Exmaple reply with JUST article markdown:
           
    Webpage markdown: {html}
    Reply with article markdown:""")
    
    response = remove_newlines(response.text)

    logger.debug(f"AI article output (content cleaning): {text}")

    # Serialize the response text to escape special characters
    # serialized_response = json.dumps(response)

    # Log the serialized (and thus safely escaped) response
    # logger.debug(f"AI response (conversion from html to md with serialize): {serialized_response}")
    
    try:
        # Deserialize the serialized text back to a Python object
        response_json = json.loads(response) # christ
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON: {e.msg} at position {e.pos}")

    
    
    
    if response_json['is_article'] in ["True", "true", True] and response_json['is_accessible'] in ["True", "true", True]:
        return response_json
    else:
        logger.warning(f"AI response (conversion from html to md) indicates that the article at {url} is not accessible or not an article.")
        logger.debug(f"AI response: {response_json}")
        return None
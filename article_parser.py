from content_getter import get_article_text_ai
import google.generativeai as genai
from datetime import datetime
import json
from os import environ

# Set up logging configuration
import logging; logger = logging.getLogger(__name__)

# load dotenv
from dotenv import load_dotenv
load_dotenv()


genai.configure(api_key=environ['GOOGLE_API_KEY'])


def prompt_ai_with_article(company, url, startup_blurb):
    """
    This function prompts the AI with an article and returns the AI's response.
    """

     # Get the article text from the URL
    content = get_article_text_ai(url)

    if content == None:
        logger.warning(f"The article's content was not able to be analyzed. Was the page accessible? What was the safety rating? {url}")
        return None

    logger.info(f"Prompting parsing AI with article for {company} with url {url}")
    
    model_config = {
        "temperature": 1
    }

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

    # Define the prompt and the model
    model = genai.GenerativeModel('gemini-1.5-pro', generation_config=model_config, safety_settings=safe)
    
    # load a prompt from a file
    with open("prompt", "r", encoding='utf-8') as f:
        prompt = f.read()

    # Replace the variables in the prompt
    prompt = prompt.format(company=company, url=url, startup_blurb=startup_blurb, content=content["content"])

    # Generate the content!!
    response = model.generate_content(prompt)
    
    logger.debug(f"Raw Response from AI: {response}")

    if response.text == None:
        logger.warning(f"Empty response! {response.candidates[0].safety_ratings}" )

    return response.text


def assess_article(company, url, startup_blurb):
    logger.debug(f"Assessing article for {company} with link {url}")
    response = prompt_ai_with_article(company, url, startup_blurb)
    if response == None:
        return None

    current_date = datetime.now().strftime("%d-%m-%Y")

    # turn json result into reader friendly format
    json_read = json.loads(response)

    # for each element in json_read, check if any are null and replace with current date
    for key in json_read:
        if json_read[key] == None or json_read[key] == "null":
            logger.warning(f"Null value found in response for {company} - {url} - {key}")

    
    json_read["date"] = current_date

    # for title we need to encode it to utf-8
    try:
        json_read["title"] = json_read["title"].encode("utf-8").decode("utf-8")
    except ValueError:
        logging.error(f"Error encoding title to utf-8: {response}")
        pass
    except:
        logging.error(f"Error processing response: {response} - URL: {url} - Company: {company}")
        pass
    
    json_read["url"] = url

    # common category changes to correct for 
    if json_read["category"] == "Investment":
        json_read["category"] = "Investments"
    if json_read["category"] == "Startup update":
        json_read["category"] = "Startup updates"

    if json_read["is_referenced"] == False:
        logger.info(f"The article for {company} with link {url} is not about the company. Reason: {json_read['reason']}")
    else:
        logger.info(f"The article for {company} with link {url} is about the company. Reason: {json_read['reason']}")

    return json_read


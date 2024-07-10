from datetime import datetime
from os import environ
from venv import logger
from pyairtable import Api # capital A???? wtf?
from tqdm import tqdm
from rss_parsing import get_urls_and_assess
from pickle_function_cache import cache_responses

api = Api(api_key=environ['AIRTABLE_API_KEY']) 

airtable_base_id = environ['AIRTABLE_BASE']
comapny_table_id = environ['COMPANY_TABLE']
alert_table_id = environ['ALERTS_TABLE']
article_table_id = environ['ARTICLE_TABLE']

# there is a linked record field in another table to start up name
# we have to add records to that other table, which link back to the start up name

def populate():
    # Get the alert table
    alert_table = api.table(airtable_base_id, alert_table_id)
    company_table = api.table(airtable_base_id, comapny_table_id)


    # Iterate over the records in the main table
    for record in tqdm(company_table.all()):
        startup_name = record["fields"]["Startup Name"]
        record_id = record["id"]
        logger.info(f"Processing {startup_name}, ID: {record_id}...")


        # Create a new record with the linked ID in a list
        alert = alert_table.create({
            "Startup Name": [record_id],  # Wrap ID in a list for linking
            "Status": "Not Active"
        })

        logger.info(f"Created alert for {startup_name}")

def populate_with_keywords():
    # Get the alert table
    alert_table = api.table(airtable_base_id, alert_table_id)
    company_table = api.table(airtable_base_id,comapny_table_id)


    # Iterate over the records in the main table
    for record in tqdm(company_table.all()):
        startup_name = record["fields"]["Startup Name"]
        record_id = record["id"]
        logger.info(f"Processing {startup_name}, ID: {record_id}...")


        # Create a new record with the linked ID in a list
        alert = alert_table.create({
            "Startup Name": [record_id],  # Wrap ID in a list for linking
            "Status": "Not Active",
            "Keyword": "startup"
        })

        logger.info(f"Created alert for {startup_name}")

def get_alert_table():
    alert_table = api.table(airtable_base_id, alert_table_id)
    return alert_table

def get_company_table():
    company_table = api.table(airtable_base_id,comapny_table_id)
    return company_table

def get_new_table_approved():
    new_table = api.table(airtable_base_id,article_table_id)
    return new_table

def get_all_rss_feeds():
    '''
    Returns a list of all active RSS feeds from the airtable.
    '''
    alert_table = get_alert_table()
    all_alert_rows = alert_table.all()
    rss_feeds = []
    for alert_row_record in tqdm(all_alert_rows):
        alert_row = alert_row_record["fields"]
        if alert_row["Status"] == "Active":
            rss_feeds.append(alert_row["RSS url"])
    return rss_feeds

#@cache_responses("rss_feeds.dat")
def get_all_rss_feeds_and_startup_name():
    '''
    Returns a list of tuples, each containing the RSS feed URL and the startup name associated with the feed.
    Doesn't return feeds that are not active and will return the startup name as a string.
    This is slow because of how we use airtable API atm. Could be faster.
    '''
    company_table = get_company_table()
    alert_table = get_alert_table()
    all_alert_rows = alert_table.all()
    
    rss_feeds = []
    logger.info("Collecting all RSS feeds and startup names from airtable")
    for alert_row_record in all_alert_rows:
        alert_row = alert_row_record["fields"]
        startup_record = company_table.get(alert_row["Startup Name"][0])["fields"]
        startup_name = startup_record["Startup Name"]
        startup_blurb = startup_record.get("Startup Blurb", "No blurb available")
        rss_feeds.append((alert_row["RSS url"], startup_name, startup_blurb))
    
    return rss_feeds

def MOCK_update_airtable_with_new_entries(create_in_airtable = True, feed_tuple=("mockrss-ansi.rss", "Zerve", "The core component in Enterprise AI platforms is the development of Machine Learning & Deep Learning Models. Zerve facilitates this from end to end, not only including data integration to model management, but also DevOps and full orchestration of the models in Production.")):
    '''
    This function is for testing purposes only. It will only process one local RSS feed and add it to the airtable.
    '''

    new_table = get_new_table_approved()
    rss_feeds = [feed_tuple] 

    for rss_tuple in rss_feeds: 
        logger.info(f"Processing {rss_tuple}")
        startup_name, rss_url, startup_blurb = rss_tuple[1], rss_tuple[0], rss_tuple[2]

        urls = get_urls_and_assess(startup_name, rss_url, startup_blurb, False) # will return only valid articles

        if not urls:
            logger.warning(f"No valid articles to add for {startup_name} - or failed for other reaons")
            continue
        
        logger.info(f"Adding {len(urls)} articles for {startup_name} to airtable")

        for result in tqdm(urls):
            if create_in_airtable:
                create_new_entry(new_table, startup_name, result)

def update_airtable_with_new_entries():
    new_table = get_new_table_approved()
    rss_feeds = get_all_rss_feeds_and_startup_name()

    for rss_tuple in rss_feeds: 
        logger.info(f"Processing {rss_tuple}")
        startup_name, rss_url, startup_blurb = rss_tuple[1], rss_tuple[0], rss_tuple[2]

        urls = get_urls_and_assess(startup_name, rss_url, startup_blurb) # will return only valid articles

        if not urls:
            logger.warning(f"No valid articles to add for {startup_name} - or failed for other reaons")
            continue
        
        logger.info(f"Adding {len(urls)} articles for {startup_name} to airtable")
        for result in tqdm(urls):
            create_new_entry(new_table, startup_name, result)
            
def create_new_entry(new_table, startup_name, result):
    try:
        response = new_table.create({
            "Startup name": startup_name,
            "Title": result.get("title", ""),
            "Link": result.get("url", ""),
            "Category": result.get("category", ""),
            "Date": result.get("date", datetime.now().strftime("%d-%m-%Y")),
            "Context": result.get("context", ""),
            "Raised": result.get("investment", ""),
        })
        logger.debug(f"Added to airtable : {response}")
    except Exception as e:
        logger.error(f"Error creating entry for {startup_name}: {e}")
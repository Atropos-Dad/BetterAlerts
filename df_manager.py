import pandas as pd
import feedparser
from pyairtable import Api
from os import environ
from tqdm import tqdm
from datetime import datetime
from airtable_interface import get_all_rss_feeds_and_startup_name

# Initialize Airtable API
api = Api(api_key=environ['AIRTABLE_API_KEY'])

# Fetch RSS feeds, startup names, and blurbs
feeds = get_all_rss_feeds_and_startup_name()
print(feeds)
data = []

# Define today's date
today = datetime.today().date()

# Parse each RSS feed and count the entries from today
for rss_url, startup_name, startup_blurb in feeds:
    feed = feedparser.parse(rss_url)
    num_entries_today = sum(
        1 for entry in feed.entries if 'published' in entry and datetime.strptime(entry.published, '%Y-%m-%dT%H:%M:%SZ').date() == today
    )
    data.append((startup_name, num_entries_today, startup_blurb))
    print(f"Startup: {startup_name}, Number of entries from today: {num_entries_today}")

# Create a DataFrame from the data
df = pd.DataFrame(data, columns=['Startup Name', 'Number of Entries Today', 'Startup Blurb'])

# Print the DataFrame
print(df)

# Pickle the DataFrame
pickle_file_path = 'startup_rss_feed_entries_today.pkl'
df.to_pickle(pickle_file_path)

# Confirm that the DataFrame has been pickled
print(f"DataFrame has been pickled to {pickle_file_path}")

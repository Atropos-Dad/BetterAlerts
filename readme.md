# Better Alerts!
## Description
Better Alerts is a LLM enabled web scraping tool designed to extract data from publications with a paticular focus on assessing RSS feeds (from google alerts). The current prompt used to extract data is specific to Irish tech start-ups and with some small modifications could be expanded to other contexts too!

At the moment, 'google_alert_creator.py' will only function when the google_alerts.whl is installed. If you have an airtable of RSS feeds already aggregated or you plan to get it from a different source, you should be able to bypass this step (do remember to take the .whl out of requirements.txt!). If you *DO* want to automatically create google alerts, you can install the .whl in this repo. Or if you'd rather build it yourself, this .whl is an almost identical clone of https://github.com/9b/google-alerts with some minor changes for conveniance. You can build/install google-alerts yourself too, the only essential change is updating beautifulsoup4 in the requirements.txt so that it's a newer version! 


## Installation
Normal `pip -r requirements.txt` install (unless rebuilding the .whl)! then run main.py. 

The current airtable_interface.py assumes this schema:

- A company table with the fields startup name (pk) and start up blurb
- A google alerts table with a 'linked field' to startup name in the company table, and an RSS url and status field (Active, Not Active)
- An 'events' alert table with a Startup Name, Title, Link, Category, Date, Context, Raised

We also have a field, 'Approved', in the 'events' table, and an automation to copy it over to another table upon human verification.

Applying Better Alerts to another context would probably require a rewrite of this component!


## Contributing
Contributions are of course welcome! There are for sure some places in which additional work is needed for this tool to be leveraged by a general audience!

- [ ] Article source expansion
- [ ] Proper logging 
- [ ] Unit tests! 
- [ ] More generic outputs
- [ ] generating output as processing occurs
- [ ] Generic 'plug 'n play' llm interface


## Authors
https://github.com/De3pBlu3
https://github.com/MiaBorkoo
https://github.com/dylan-teehan-skc

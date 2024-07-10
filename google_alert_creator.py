from dotenv import load_dotenv
from os import environ
from google_alerts import GoogleAlerts
from airtable_interface import get_alert_table, get_company_table
from tqdm import tqdm


load_dotenv()

username = environ['GOOGLE_EMAIL']
password = environ['GOOGLE_PASS']

# Create an instance
ga = GoogleAlerts(username, password) # this is going to save your username/password to a file on your computer! Use a throwaway account! 

# Authenticate your user
ga.authenticate() 


def delete_all_alerts():
    for alert in ga.list():
        print(f"Deleting {alert}")
        ga.delete(alert['monitor_id'])


def create_alerts():
    
    # Retrieve the Airtable tables for alerts and companies
    alert_table = get_alert_table()
    all_alert_rows = alert_table.all()
    company_table = get_company_table()

    # Iterate over all alert records in Airtable
    for alert_row_record in tqdm(all_alert_rows):
        # time.sleep(2)
        alert_row = alert_row_record["fields"]

        if alert_row["Status"] == "Not Active":

            # cross reference to the company table to get the company name for the alert as opposed to the ID
            company_record = company_table.get(alert_row["Startup Name"][0])
            company = company_record["fields"]
            alert_row["Startup Name"] = company["Startup Name"]
        
            
            #startup name and keyword should both be wrapped in quotes unless they are blank
            google_alert_str = f"\"{alert_row['Startup Name']}\" {alert_row.get('Keyword', '')}".strip()      
            
            try:
                created_alert = ga.create(google_alert_str, {'delivery': 'RSS'})
            except:
                print(f"Failed to create alert for {alert_row['Startup Name']}")
                print(f"Google Alert String: {google_alert_str}")
                print(created_alert)
                continue

            # Update the status in Airtable
            try:
                alert_table.update(alert_row_record["id"], {"Status": "Active", "RSS url": created_alert[0]['rss_link']})
            except:
                print(f"Failed to update status for {alert_row['Startup Name']}")
                print(f"Google Alert String: {google_alert_str}")
                print(created_alert)
                continue
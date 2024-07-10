from os import environ
from dotenv import load_dotenv
from airtable_interface import update_airtable_with_new_entries, MOCK_update_airtable_with_new_entries
import logging
from halo import Halo

fh = logging.FileHandler("debug.log", encoding="utf-8")
sh = logging.StreamHandler()
fh.setLevel(logging.DEBUG)
sh.setLevel(logging.INFO)

logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.DEBUG,
    # format="%(asctime)s [%(levelname)s] %(message)s",
    # format with filename and line number
    format="%(asctime)s [%(levelname)s] %(filename)s:%(lineno)d %(message)s",
    handlers=[
        fh,
        sh
    ]
)

load_dotenv()

def main():
    spinner = Halo(text='Checking feeds', spinner='dots')
    spinner.start()
    update_airtable_with_new_entries()
    spinner.stop()


if __name__ == "__main__":
    main()

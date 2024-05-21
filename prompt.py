import datetime
import external

from enum import Enum, auto


def prompt_wizard(main_dir):
    class State(Enum):
        START = auto(),
        SELECTED_DATA_DIR = auto(),
        CAPEX_JSON_SCRAPED = auto(),

    state = State.START

    today = datetime.date.today()

    while(True):
        match state:
            case State.START:
                (dir,reports_date) = find_latest_data_dir(main_dir)
                if(reports_date == today):
                    state = State.SELECTED_DATA_DIR
                    data_dir = dir
                else:
                    data_dir = create_new_data_dir(main_dir,today)
            case State.SELECTED_DATA_DIR:
                if(data_dir_contains_capex_json(data_dir)):
                    state = State.CAPEX_JSON_SCRAPED
                else:
                    prompt(f"""The capex portfolio data needs to be downloaded from capexinsider.com. Please 
login to capexinsider.com. When finished, enter the name of your browser ({",".join(ftypes.BROWSER_TYPES)}):""",
                           choices=ftypes.BROWSER_TYPES)
                    msg("Retrieving capex portfolio data...")
                    scrape_capex(data_dir)
                    state = State.CAPEX_JSON_SCRAPED
            case State.CAPEX_JSON_SCRAPED:
                external.open_dir(data_dir)
                prompt(f"""Please login to your brokerage and download the appropriate holdings reports, placing them in the just opened
directory window ({data_dir}), afterwards, hit enter:""")
                prompt()


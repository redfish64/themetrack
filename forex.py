import argparse
import re
from currency_converter import CurrencyConverter
from datetime import date

from util import error

#TODO 2.1 warn when the date is not available, so user can download new currency tables
converter = CurrencyConverter(fallback_on_missing_rate=True,fallback_on_wrong_date=True)

def convert(curr_from,curr_to,amt,conv_date=None):
    """converts one currency to another on the given date

    Args:
        date (_type_): date to convert the currency, defaults to today
        curr_from (_type_): _description_
        curr_to (_type_): _description_
        amt (_type_): _description_

    Returns:
        _type_: _description_
    """
    if(conv_date is None):
        conv_date = date.today()
    #TODO 2 we aren't using date for now
    return converter.convert(amt,curr_from,curr_to, conv_date)

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        usage="%(prog)s [--date yyyy/mm/dd] <sym1> <sym2> <amt>...",
        description="parses and prints out stuff",
        exit_on_error=True,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--date", default=None, help="date to convert")
    parser.add_argument("curr_from", help="currency to convert from")
    parser.add_argument("curr_to", help="currency to convert to")
    parser.add_argument("amt", type=float, help="amt to convert")

    conf = parser.parse_args()

    if(conf.date is not None):
        m = re.match(r'(\d\d\d\d)/(\d\d\)/(\d\d)')
        if(not m):
            error(f"Can't parse date, {conf.date}")
        yyyy,mm,dd = m.groups()

        conv_date = date(int(yyyy),int(mm),int(dd))
    else:
        conv_date = None

    print(f"{conf.amt} {conf.curr_from} is {convert(conf.curr_from,conf.curr_to,conf.amt,conv_date)} {conf.curr_to}")
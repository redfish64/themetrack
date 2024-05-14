import argparse
import re
from forex_python.converter import CurrencyRates
import diskcache as dc
from datetime import date

from util import error

cache = dc.Cache('finane_cache')

converter = CurrencyRates()

@cache.memoize()
def get_rate(curr_from,curr_to,conv_date):
    return converter.get_rate(curr_from,curr_to,conv_date)

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
    return get_rate(curr_from,curr_to,conv_date) * amt

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
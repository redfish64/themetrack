import util
import capex_scraper
import ib_parser
import pandas as pd
import re


def match_holding_to_pick(h,p):
    brokerage = get_brokerage(h)
    pick_type = get_pick_type(p)

    match brokerage:
        case Brokerage.InteractiveBrokers:
            hticker = h['Symbol']
            hmarket = get_ib_market(h['Listing Exch'])

            match pick_type:
                case PickType.CapexBig5:
                    pmarket,pticker = read_big5_ticker(p['Ticker'])
                case _:
                    pticker = p['Ticker']

            return hticker == pticker and hmarket == pmarket


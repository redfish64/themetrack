import util
import capex_scraper
import ib_parser
import pandas as pd
from ftypes import Brokerage, PickType, BROKERAGE_COLUMN, Market
import re

#associates markets in the capex big5 list with markets it might represent
BIG5_MARKET_MATCHING = {
    "HK": ["HKE"],
    "HKEX": ["HKE"],
    "HKG": ["HKE"],
    "NYSEAMERICAN": ["NYSE"],
    "OTCMKTS": ["OTC"],
    "US": ['NYSE','AMEX','NASDAQ']
    }

#associates markets in the interactive broker spreadsheets with markets it might represent
IB_MARKET_MATCHING = {
    #none so far
}

def get_brokerage(holdings_row : pd.Series):
    """Matches a row to a Brokerage enum
    Returns:
        Pick | None 
    """
    return Brokerage.get(holdings_row[BROKERAGE_COLUMN],None)
    
def get_pick_type(pick_row : pd.Series):
    """Matches a row to a Pick enum
    Returns:
        Pick | None 
    """
    CAPEX_MATCH = {
        "Total Portfolio" : PickType.CapexTotalPortfolio,
        "Skeleton Portfolio" : PickType.CapexSkeletonPortfolio,
        "Divi Portfolio" : PickType.CapexDiviPortfolio,
        "BIG 5 MEMBERS AREA" : PickType.CapexBig5
    }

    if(capex_scraper.CAPEX_NAME_COL in pick_row):
        return CAPEX_MATCH.get(pick_row[capex_scraper.CAPEX_NAME_COL],None)
    
    util.error(f"Can't determine type of pick for row {pick_row}")



def get_ib_market(s):
    return Market[s]

def find_matching_values(matching_table,market):
    markets = BIG5_MARKET_MATCHING.get(market,[])
    markets = markets + [market]


def read_big5_ticker(s):
    """reads a BIG5 ticket, which sometimes has the market in front, like ASX:FOO
    """
    m = re.match(r"^([A-Z0-9]+):([A-Z0-9]+)$",s)
    if m is not None: #if <market>:<ticker>
        market = m.group(1)
        ticker = m.group(2)

        markets = find_matching_markets(BIG5_MARKET_MATCHING,market)

        return markets,ticker

    if re.match(r"^[A-Z0-9]+$",s):
        return None,s        


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


import util
import capex_scraper
import ib_parser
import pandas as pd
from ftypes import Brokerage, PickType, BROKERAGE_COLUMN, Market
import re

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

BIG5_MARKET_MATCHING = {
    "AMEX" : Market.AMEX, #
    "AMS" : Market.AMS, 
    "ASX" : Market.ASX, #
    "BCBA" : None,
    "BIT" : None,
    "CPH" : xMarket.CPH,
    "CVE" : xMarket.CVE,
    "DE" : xMarket.DE,
    "EBR" : xMarket.EBR,
    "EC" : xMarket.EC,
    "ELI" : xMarket.ELI,
    "EPA" : xMarket.EPA,
    "EURONEXT" : xMarket.EURONEXT,
    "FRA" : Market.FRA,
    "GPW" : xMarket.GPW,
    "HK" : Market.HKG,
    "HKEX" : Market.HKG,
    "HKG" : Market.HKG,
    "JSE" : Market.JSE,
    "KLSE" : Market.KLSE,
    "LON" : Market.LSE, #
    "LSE" : Market.LSE, #
    "LSIN" : Market.LSIN,
    "MCX" : Market.MCX,
    "MIL" : Market.MIL,
    "MYX" : Market.MYX,
    "NAG" : Market.NAG,
    "NASDAQ" : Market.NASDAQ, #
    "NSE" : Market.NSE,
    "NYSE" : Market.NYSE, #
    "NYSEAMERICAN" : Market.NYSE, #
    "OL" : Market.OL,
    "OSE" : Market.OSE,
    "OSL" : Market.OSL,
    "OTC" : Market.OTC, #
    "OTCMKTS" : Market.OTC,
    "PA" : Market.PA,
    "SGX" : Market.SGX, #
    "SI" : Market.SI,
    "STO" : Market.STO,
    "TASE" : Market.TASE,
    "TLV" : Market.TLV,
    "TSE" : Market.TSE, #
    "TYO" : Market.TYO,
    "US" : Market.US,
    "WSE" : Market.WSE
}

def read_big5_ticker(s):
    """reads a BIG5 ticket, which sometimes has the market in front, like ASX:FOO
    """
    m = re.match(r"^([A-Z0-9]+):([A-Z0-9]+)$",s)
    if m is not None: #if <market>:<ticker>
        smarket = m.group(1)
        ticker = m.group(2)

        if hasattr(Market,smarket):
            return Market[smarket],ticker
        
        #sometimes big5 has some weird ma
        return None,ticker
        


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


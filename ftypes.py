from dataclasses import dataclass
from enum import Enum,auto
from re import L

from enum import Enum, auto
import re

import util

FINANCE_DATA_DIR = "data"
FINANCE_REPORTS_DIR = "reports"

THEME_TRACK_CONFIG_FILE = 'theme_track_config.xlsx'

YAHOO_FINANCE_CACHE_FILE = 'yahoo_finance_cache.json'

FOREX_URL = 'https://www.ecb.europa.eu/stats/eurofxref/eurofxref.zip'
FOREX_FILENAME = 'forex.zip'

WELCOME_BAT_FILE = r'dos_scripts\welcome.bat'
WELCOME_BAT_ENV = 'IN_WELCOME_BAT'

ADJ_CLOSE_START_PRICE_PREFIX = 'R:AdjCloseStartPrice'
ADJ_CLOSE_END_PRICE_PREFIX = 'R:AdjCloseEndPrice'

PRICE_START_DATE_PREFIX = 'R:PriceStartDate'
PRICE_END_DATE_PREFIX = 'R:PriceEndDate'

GAIN_LOSS_PREFIX = 'R:GainLoss'

GAIN_LOSS_NOT_ALL_DATA_PRESENT_PREFIX = 'R:GainLossNotAllPresent'


class PickType(Enum):
    CapexTotalPortfolio = auto(),
    CapexSkeletonPortfolio = auto(),
    CapexDiviPortfolio = auto(),
    CapexBig5 = auto(),
    CapexClosed = auto(),

PICK_TYPE_TO_BIT_FLAG = {
    PickType.CapexTotalPortfolio : 1,
    PickType.CapexSkeletonPortfolio : 2,
    PickType.CapexDiviPortfolio : 4,
    PickType.CapexBig5 : 8,
    PickType.CapexClosed : 16,
}

PICK_TYPE_TO_CAPGAINS_PRIORITY = { 
    PickType.CapexTotalPortfolio : 1,
    PickType.CapexSkeletonPortfolio : 2,
    PickType.CapexBig5 : 3,
    PickType.CapexDiviPortfolio : 4,
    PickType.CapexClosed : 5,
}

PICK_TYPE_TO_DIVI_PRIORITY = { 
    PickType.CapexDiviPortfolio : 1,
    PickType.CapexTotalPortfolio : 2,
    PickType.CapexSkeletonPortfolio : 3,
    PickType.CapexBig5 : 4,
    PickType.CapexClosed : 5,
}


def bit_mask_has_pick_type(bm : int, pt : PickType):
     return (bm & PICK_TYPE_TO_BIT_FLAG[pt]) != 0

def pick_types_to_bitmask(pt_list : list[PickType]):
     return sum([PICK_TYPE_TO_BIT_FLAG[pt] for pt in pt_list])
          


CAPEX_FILENAME_TO_PICK_TYPE= {
    "Closed Positions" : PickType.CapexClosed,
    "BIG 5 MEMBERS AREA" : PickType.CapexBig5,
    "Total Portfolio" : PickType.CapexTotalPortfolio,
    "Skeleton Portfolio" : PickType.CapexSkeletonPortfolio,
    "Divi Portfolio" : PickType.CapexDiviPortfolio,
}

class BrokerageTypes(Enum):
    InteractiveBrokers = auto(),
    Schwab = auto(),

class DataTypes(Enum):
    Pick = auto(),
    Holding = auto(),
    Event = auto(),

class SCType(Enum):
    Data = auto(),
    Report = auto(),

class SpecialColumns(Enum):
    DBrokerage = auto(),
    DMultHoldings = auto(),
    DJoinResult = auto(),
    DCapexGainsPickTypeOrder = auto(),
    DDiviPickTypeOrder = auto(),
    DCapexGainsPickTypeShortDesc = auto(),
    DDiviPickTypeShortDesc = auto(),
    DJoinAllBitMask = auto(),
    DRefreshedDate = auto(),
    DAcctName = auto(),
    DDataType = auto(),
    RPickType = auto(),
    RPickPriority = auto(),
    RCurrValueCurrency = auto(),
    RCurrValueForeign = auto(),
    RCurrValue = auto(),
    RExchange = auto(),
    RTicker = auto(),
    RTheme = auto(),
    RSector = auto(),
    RCatPerc = auto(),
    RTotalPerc = auto(),
    RCatTotalPerc = auto(),
    RQuantity = auto(),
    CMatchColumns = auto(),
    CYahooTicker = auto(),

    def get_col_name(self):
        
        return f"{self.name[0]}:{self.name[1:]}"
            
    def get_col_desc(self):
            #columns that are either read from or populated by the finance app
            DESCRIPTION = {
                SpecialColumns.DBrokerage: f"brokerage security is held at, populated by finance app, one of {','.join(BrokerageTypes._member_names_)}",
                SpecialColumns.RPickType: f"type of pick, capex big5, capex total portfolio, etc., one of "
                            f"{','.join([x.name for x in CAPEX_FILENAME_TO_PICK_TYPE.values()])}, populated by finance app",
                SpecialColumns.RPickPriority: """
ThemePriority is used when there are multiple matches 
for a held security. The one with the lower ThemePriority 
value (closer to 1) will be chosen as the theme. So if a 
security is in both CapexSkeletonPortfolio with ThemePriority 2, 
and CapexDiviPortfolio with ThemePriority 3, then CapexSkeletonPortfolio 
will be chosen""",
                SpecialColumns.DJoinResult: """
SpecialColumns.The result of matching holdings to picks:
    SpecialColumns.1:1  - holding exactly matches a single pick
    Many - holding matches more than one pick
    None - holding matches no picks
""",
                SpecialColumns.DJoinAll: "If the JoinResult is many, a comma separated list of picks that were matched",
                SpecialColumns.CMatchColumns: """
This field determines how the holdings and picks are joined. It is a comma separated list of holdings to a 
comma separated list of picks, ex. "Region,Ticker=Region,Ticker"
""",
                SpecialColumns.DCapexName: 'fileName from capex json',
                SpecialColumns.DRefreshedDate: 'refreshed field from capex json',
                SpecialColumns.DAcctName: 'name of account security is related to',
                SpecialColumns.RCurrValueCurrency: f'currency of {SpecialColumns.RCurrValueForeign.get_col_name()}',
                SpecialColumns.RCurrValueForeign: 'current value in foreign currency',
                SpecialColumns.RCurrValue: 'current value in USD', #TODO 2.5 allow other currencies
                SpecialColumns.RExchange: 'Stock Exchange', #TODO 2.5 allow other currencies
            }

            return DESCRIPTION[self]

PICK_TYPE_TO_SHORT_NAME = { 
    PickType.CapexBig5 : "Big5",
    PickType.CapexClosed : "Closed",
    PickType.CapexDiviPortfolio : "Income",
    PickType.CapexTotalPortfolio : "CapGains",
    PickType.CapexSkeletonPortfolio : "Skeleton",
}

SHORT_NAME_TO_PICK_TYPE = {v: k for k,v in PICK_TYPE_TO_SHORT_NAME.items()}

# order for categories in divi report
# these will be added together if a stock falls in multiple categories, to give a total score, lower value is first
PICK_TYPE_TO_ORDER_DIVI = {
    PickType.CapexDiviPortfolio : -16,
    PickType.CapexTotalPortfolio : -8,
    PickType.CapexSkeletonPortfolio : -4,
    PickType.CapexBig5 : -2,
    PickType.CapexClosed : -1,
}

# order for categories in cap gains report, otherwise same as PICK_TYPE_TO_SCORE_DIVI
PICK_TYPE_TO_ORDER_CAP_GAINS = {
    PickType.CapexTotalPortfolio : -16,
    PickType.CapexSkeletonPortfolio : -8,
    PickType.CapexDiviPortfolio : -4,
    PickType.CapexBig5 : -2,
    PickType.CapexClosed : -1,
}

@dataclass
class ReportConfig:
    name : str
    always_show_pick_bitmask : int # bitmask of pick types to always show rows for, even if zero funds are invested 
    columns : list [(str,str,str)] #column name, display_as, excel_format
    column_order : list [str] #columns to order the rows by
    sum_columns : list [str] #list of column names to sort by
    cat_column : str #category column used to combine rows
    is_cat_type : bool



@dataclass
class Config:
    version : str
    currency : str
    reports : list[ReportConfig]
    currency_formats : dict[str,str] # currency to excel format
    hist_perf_periods : list[str]
    hist_perf_slip_days : int

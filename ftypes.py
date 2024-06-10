from dataclasses import dataclass
from enum import Enum,auto
from re import L

from enum import Enum, auto
import re

import util

FINANCE_DATA_DIR = "data"
FINANCE_REPORTS_DIR = "reports"

THEME_TRACK_CONFIG_FILE = 'theme_track_config.xlsx'

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

SYSTEM_RULES_FILENAME="system_rules.xlsx"

class BrokerageTypes(Enum):
    InteractiveBrokers = auto(),
    Schwab = auto(),

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
    DCapexName = auto(),
    DAcctName = auto(),
    RPickType = auto(),
    RPickDesc = auto(),
    RPickPriority = auto(),
    RMatchColumns = auto(),
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
                SpecialColumns.RPickDesc: "The way to describe additional picks for a one to many scenario",
                SpecialColumns.DJoinResult: """
SpecialColumns.The result of matching holdings to picks:
    SpecialColumns.1:1  - holding exactly matches a single pick
    Many - holding matches more than one pick
    None - holding matches no picks
""",
                SpecialColumns.DJoinAll: "If the JoinResult is many, a comma separated list of picks that were matched",
                SpecialColumns.RMatchColumns: """
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
    columns : dict [str,(str,str)] #column name to display_as and excel_format

@dataclass
class Config:
    currency : str
    capex_stocks_report : ReportConfig
    capex_theme_report : ReportConfig
    divi_stocks_report : ReportConfig
    divi_theme_report : ReportConfig
    currency_formats : dict[str,str] # currency to excel format
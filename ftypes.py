from dataclasses import dataclass
from enum import Enum,auto
from re import L

from enum import Enum, auto
import re

import util

FINANCE_DATA_DIR = "data"
FINANCE_REPORTS_DIR = "reports"

THEME_TRACK_CONFIG_FILE = 'theme_track_config.xlsx'

CAPEX_FILENAME_TO_PICK_TYPE= {
    "Closed Positions" : "CapexClosed",
    "BIG 5 MEMBERS AREA" : "CapexBig5",
    "Total Portfolio" : "CapexTotalPortfolio",
    "Skeleton Portfolio" : "CapexSkeletonPortfolio",
    "Divi Portfolio" : "CapexDiviPortfolio",
}

class BrokerageTypes(Enum):
    InteractiveBrokers = auto(),
    Schwab = auto(),

class SCType(Enum):
    Data = auto(),
    Report = auto(),

class SpecialColumns(Enum):
    DBrokerage = auto(),
    DJoinResult = auto(),
    DJoinAll = auto(),
    DCapexName = auto(),
    DRefreshedDate = auto(),
    DAcctName = auto(),
    RPickType = auto(),
    RPickPriority = auto(),
    RPickDesc = auto(),
    RMatchColumns = auto(),
    RCurrValueCurrency = auto(),
    RCurrValueForeign = auto(),
    RCurrValue = auto(),
    RExchange = auto(),
    RTicker = auto(),
    RTheme = auto(),
    RThemePerc = auto(),
    RTotalPerc = auto(),
    RThemeTotalPerc = auto(),

    def get_col_name(self):
        
        return f"{self.name[0]}:{self.name[1:]}"
            
    def get_col_desc(self):
            #columns that are either read from or populated by the finance app
            DESCRIPTION = {
                SpecialColumns.DBrokerage: f"brokerage security is held at, populated by finance app, one of {",".join(BrokerageTypes._member_names_)}",
                SpecialColumns.RPickType: f"type of pick, capex big5, capex total portfolio, etc., one of "
                            f"{",".join(CAPEX_FILENAME_TO_PICK_TYPE.values())}, populated by finance app",
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

    




# class Region(Enum):
#     USA = auto()
#     Europe = auto()
#     Asia = auto()

# class PickType(Enum):
#     CapexTotalPortfolio = auto()
#     CapexSkeletonPortfolio = auto()
#     CapexDiviPortfolio = auto()
#     CapexBig5 = auto()
#     CapexClosed = auto()

# class Brokerage(Enum):
#     InteractiveBrokers = auto()

# class AssetCategory(Enum):
#     Stock = auto()
#     Warrant = auto()

# @dataclass
# class Asset:
#     symbol : str
#     name : str
#     market : Market
#     region : Region
#     currency : str
#     asset_category : AssetCategory


# class Holding():
#     def __init__(self,asset,other_fields : dict) -> None:
#         self.asset = asset
#         self.other_fields = other_fields


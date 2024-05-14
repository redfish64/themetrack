from dataclasses import dataclass
from enum import Enum,auto
from re import L

from enum import Enum, auto
import re

import util

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
    Magic = auto(),
    Report = auto(),

class SpecialColumns(Enum):
    Brokerage = auto(),
    PickType = auto(),
    PickPriority = auto(),
    PickDesc = auto(),
    JoinResult = auto(),
    JoinAll = auto(),
    MatchColumns = auto(),
    CapexName = auto(),
    RefreshedDate = auto(),
    AcctName = auto()


    def get_col_name(self):
        COL_TYPE = {
            SpecialColumns.Brokerage: SCType.Data,
            SpecialColumns.PickType: SCType.Report,
            SpecialColumns.PickPriority: SCType.Magic,
            SpecialColumns.PickDesc: SCType.Magic,
            SpecialColumns.JoinResult: SCType.Data,
            SpecialColumns.JoinAll: SCType.Data,
            SpecialColumns.MatchColumns: SCType.Magic,
            SpecialColumns.CapexName: SCType.Data,
            SpecialColumns.RefreshedDate: SCType.Data,
            SpecialColumns.AcctName: SCType.Data
        }   

        match COL_TYPE[self]:
            case SCType.Data:
                pre = "D"
            case SCType.Magic:
                pre = "M"
            case SCType.Report:
                pre = "R"
        
        return f"{pre}:{self.name}"
            
    def get_col_desc(self):
            #columns that are either read from or populated by the finance app
            DESCRIPTION = {
                SpecialColumns.Brokerage: f"brokerage security is held at, populated by finance app, one of {",".join(BrokerageTypes._member_names_)}",
                SpecialColumns.PickType: f"type of pick, capex big5, capex total portfolio, etc., one of "
                            f"{",".join(CAPEX_FILENAME_TO_PICK_TYPE.values())}, populated by finance app",
                SpecialColumns.PickPriority: """
ThemePriority is used when there are multiple matches 
for a held security. The one with the lower ThemePriority 
value (closer to 1) will be chosen as the theme. So if a 
security is in both CapexSkeletonPortfolio with ThemePriority 2, 
and CapexDiviPortfolio with ThemePriority 3, then CapexSkeletonPortfolio 
will be chosen""",
                SpecialColumns.PickDesc: "The way to describe additional picks for a one to many scenario",
                SpecialColumns.JoinResult: """
SpecialColumns.The result of matching holdings to picks:
    SpecialColumns.1:1  - holding exactly matches a single pick
    Many - holding matches more than one pick
    None - holding matches no picks
""",
                SpecialColumns.JoinAll: "If the JoinResult is many, a comma separated list of picks that were matched",
                SpecialColumns.MatchColumns: """
This field determines how the holdings and picks are joined. It is a comma separated list of holdings to a 
comma separated list of picks, ex. "Region,Ticker=Region,Ticker"
""",
                SpecialColumns.CapexName: 'fileName from capex json',
                SpecialColumns.RefreshedDate: 'refreshed field from capex json',
                SpecialColumns.AcctName: 'name of account security is related to',
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


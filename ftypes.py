from dataclasses import dataclass
from enum import Enum,auto
from re import L

from enum import Enum, auto
import re
import util

CAPEX_FILENAME_TO_CAPEX_NAME= {
    "Closed Positions" : "CapexClosed",
    "BIG 5 MEMBERS AREA" : "CapexBig5",
    "Total Portfolio" : "CapexTotalPortfolio",
    "Skeleton Portfolio" : "CapexSkeletonPortfolio",
    "Divi Portfolio" : "CapexDiviPortfolio",
}

class Brokerage(Enum):
    InteractiveBrokers = auto()

#columns that are either read from or populated by the finance app
SPECIAL_COLUMNS_TO_DESCRIPTION = {
    "Brokerage": f"brokerage security is held at, populated by finance app, one of {",".join(Brokerage._member_names_)}",
    "PickType": "type of pick, capex big5, capex total portfolio, etc., populated by finance app",
    "PickPriority": """
ThemePriority is used when there are multiple matches 
for a held security. The one with the lower ThemePriority 
value (closer to 1) will be chosen as the theme. So if a 
security is in both CapexSkeletonPortfolio with ThemePriority 2, 
and CapexDiviPortfolio with ThemePriority 3, then CapexSkeletonPortfolio 
will be chosen""",
    "PickDesc": "The way to describe additional picks for a one to many scenario",
    "JoinRes": """
The result of matching holdings to picks:
    1:1  - holding exactly matches a single pick
    Many - holding matches more than one pick
    None - holding matches no picks
""",
    "JoinManyDesc": "If a 'many' join, the contents of PickDesc for each of the join besides the first",
    "MatchColumns": """
This field determines how the holdings and picks are joined. It is a comma separated list of holdings to a 
comma separated list of picks, ex. "Region,Ticker=Region,Ticker"
""",
    "CapexName" : f'Name of capex portfolio, one of {",".join(CAPEX_FILENAME_TO_CAPEX_NAME.values())}',
    "CapexName" : 'fileName from capex json',
    "RefreshedDate" : 'refreshed field from capex json',
}

def assert_column_name(col_name):
    if(col_name not in SPECIAL_COLUMNS_TO_DESCRIPTION):
        util.error(f"Internal error, looking for {col_name} in SPECIAL_COLUMNS_TO_DESCRIPTION")

    return col_name



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


from dataclasses import dataclass
from enum import Enum,auto
from re import L

from enum import Enum, auto
import re

#artificial column in holdings indicating the Brokerage
BROKERAGE_COLUMN = "Brokerage"

class RecordType(Enum):
    InteractiveBrokers = auto()
    CapexTotalPortfolio = auto()
    CapexSkeletonPortfolio = auto()
    CapexDiviPortfolio = auto()
    CapexBig5 = auto()
    CapexClosed = auto()


class Region(Enum):
    USA = auto()
    Europe = auto()
    Asia = auto()

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


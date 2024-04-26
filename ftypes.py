from dataclasses import dataclass
from enum import Enum,auto
from re import L

from enum import Enum, auto
import re

#artificial column in holdings indicating the Brokerage
BROKERAGE_COLUMN = "Brokerage"

class Brokerage(Enum):
    InteractiveBrokers = auto()

class PickType(Enum):
    CapexTotalPortfolio = auto()
    CapexSkeletonPortfolio = auto()
    CapexDiviPortfolio = auto()
    CapexBig5 = auto()

class Market(Enum):
    AMEX = auto() # American Stock Exchange
    AMS = auto() # Euronext Amsterdam
    ASX = auto() 
    BAN = auto() # Stock Exchange of Thailand
    BLN = auto() # Borse Berlin
    BOM = auto() # Bombay Stock Exchange
    BRU = auto() # Euronext Brussels
    DUS = auto() # Boerse Dusseldorf
    EDA = auto() # Xetra Stock Exchange
    EDP = auto() # Eurex Exchange
    EUF = auto() # Euronext Paris
    FCS = auto() # Shenzhen Stock Exchange
    FCZ = auto() # Shanghai Stock Exchange
    FRA = auto() # Frankfurt Stock Exchange
    HAM = auto() # Hamburg Stock Exchange
    HAN = auto() # Hannover Stock Exchange
    HKG = auto() # Hong Kong Stock Exchange
    IBIS = auto() 
    JAK = auto() # Indonesia Stock Exchange
    JASDAQ = auto() # JASDAQ Securities Exchange
    JNET = auto() # Osaka Securities Exchange
    KAR = auto() # Karachi Stock Exchange
    KUL = auto() # Kuala Lumpur Stock Exchange
    LSE = auto() 
    MTF = auto() # MTS France SAS
    MUN = auto() # Borse Muenchen
    NAG = auto() # Nagoya Stock Exchange
    NASDAQ = auto() # NASDAQ
    NSM = auto() # NASDAQ Global Select Market
    NSX = auto() # Australian Stock Exchange
    NYSE = auto() # New York Stock Exchange
    NYSEARC = auto() # New York Stock Exchange Archipelago
    OSL = auto() # Oslo Stock Exchange
    OTC = auto() #Over the counter
    SBF = auto() 
    SEHK = auto() 
    SEO = auto() # Korea Stock Exchange
    SGX = auto() 
    SIN = auto() # Singapore Stock Exchange
    SSO = auto() # Stockholm Stock Exchange
    STU = auto() # Boerse Stuttgart
    TAI = auto() # Taiwan Stock Exchange
    TOK = auto() # Tokyo Stock Exchange
    TSE = auto() 
    VENTURE = auto() 
    VIE = auto() # Vienna Stock Exchange
    WEL = auto() # New Zealand Stock Exchange
    XETRA = auto() # Deutsche Boerse AG
    XLON = auto() # London Stock Exchange
    XSTC = auto() # Hochiminh Stock Exchange
    XSWX = auto() # Six Swiss Exchange
    XVTX = auto() # Six Swiss Exchange


class Region(Enum):
    USA = auto()
    Europe = auto()
    Asia = auto()

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


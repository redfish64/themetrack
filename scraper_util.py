import requests
from bs4 import BeautifulSoup
import re
import json
import urllib.request as ur 
import browser_cookie3
from fake_useragent import UserAgent
import argparse
from enum import Enum,auto


class Browser(Enum):
    Chrome = auto()
    Chromium = auto()
    Brave = auto()
    Firefox = auto()
    Safari = auto()
    Edge = auto()

_cookie_getter = { Browser.Chrome : browser_cookie3.chrome, 
                   Browser.Chromium : browser_cookie3.chromium, 
                   Browser.Brave : browser_cookie3.brave,
                   Browser.Firefox : browser_cookie3.firefox, 
                   Browser.Safari : browser_cookie3.safari, 
                   Browser.Edge : browser_cookie3.edge
                   }

name_to_browser  = { "chrome" : Browser.Chrome, "chromium" : Browser.Chromium, "brave" : Browser.Brave, "firefox" : Browser.Firefox, 
                    "safari" : Browser.Safari, "edge" : Browser.Edge}

def create_url_opener(browser=Browser.Chrome):
    ua = UserAgent()

    _user_agent = [ua.chrome,ua.chrome,ua.chrome,ua.firefox,ua.safari,ua.edge]
    user_agent = _user_agent[browser.value -1]
    cj = _cookie_getter[browser]()
    
    opener = ur.build_opener(ur.HTTPCookieProcessor(cj))
    opener.addheaders = [('User-Agent', user_agent)]

    return opener

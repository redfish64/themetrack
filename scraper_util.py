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

_cookie_getter = [ browser_cookie3.chrome,browser_cookie3.chromium,browser_cookie3.brave,browser_cookie3.firefox,browser_cookie3.safari,browser_cookie3.edge]

def create_url_opener(browser=Browser.Chrome):
    ua = UserAgent()

    #kind of hacky but works
    _user_agent = [ua.chrome,ua.chrome,ua.chrome,ua.firefox,ua.safari,ua.edge]
    user_agent = _user_agent[browser.value]
    cj = _cookie_getter[browser.value]()
    
    opener = ur.build_opener(ur.HTTPCookieProcessor(cj))
    opener.addheaders = [('User-Agent', user_agent)]

    return opener

import urllib.request as ur 
import browser_cookie3
from fake_useragent import UserAgent
import argparse

#it has some special header, called session id, that's not being put in here. ib keeps logging me out
#i'd be careful before continuing this.

parser = argparse.ArgumentParser(
    usage="%(prog)s",
    description="gets the activity report from interactive brokers, be sure to be logged in",
    exit_on_error=True,
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)

config = parser.parse_args()

print("Getting IB activity report")
ua = UserAgent()
user_agent = ua.chrome
cj = browser_cookie3.brave()
opener = ur.build_opener(ur.HTTPCookieProcessor(cj))
opener.addheaders = [('User-Agent', user_agent)]

# url = ("https://www.interactivebrokers.com.au/AccountManagement/Statements/Run?format=13&"
#     "fromDate=20240517&language=en&period=DAILY&reportDate=20240517&statementCategory="
#     "DEFAULT_STATEMENT&statementType=DEFAULT_ACTIVITY&toDate=20240517")

data = opener.open(url).read()

print(data)

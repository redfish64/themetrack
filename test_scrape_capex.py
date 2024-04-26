import requests
from bs4 import BeautifulSoup
import re
import json
import urllib.request as ur 
import browser_cookie3
from fake_useragent import UserAgent
import argparse

parser = argparse.ArgumentParser(
    usage="%(prog)s [capex file]",
    description="either loads capex file directly or its passed in with a filename. outputs infogram I guess",
    exit_on_error=True,
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
parser.add_argument("file", nargs='?', help="capex_html_file")

config = parser.parse_args()

if(config.file is not None):
    capex_file = open(config.file).read()
else:
    print("Getting capex online")
    raise Exception("not doing this right now")
    ua = UserAgent()
    user_agent = ua.chrome
    cj = browser_cookie3.brave()
    opener = ur.build_opener(ur.HTTPCookieProcessor(cj))
    opener.addheaders = [('User-Agent', user_agent)]
    url = "https://capexinsider.com/login/portfolio/"

    capex_file = opener.open(url).read()


soup = BeautifulSoup(capex_file, "html.parser")

infogram_url = f'https://e.infogram.com/{soup.find("div",{"class":"infogram-embed"})["data-id"]}'

r = requests.get(infogram_url)
soup = BeautifulSoup(r.text, "html.parser")

script = [
    t 
    for t in soup.findAll("script") 
    if "window.infographicData" in t.text
][0].text

extract = re.search(r".*window\.infographicData=(.*?);$", script)

data = json.loads(extract.group(1))

entities = data["elements"]["content"]["content"]["entities"]

tables = [
    (entities[key]["props"]["chartData"]["sheetnames"], entities[key]["props"]["chartData"]["data"])
    for key in entities.keys()
    if ("props" in entities[key]) and ("chartData" in entities[key]["props"])
]

data = []
for t in tables:
    for i, sheet in enumerate(t[0]):
        data.append({
            "sheetName": sheet,
            "table": dict([(t[1][i][0][j],t[1][i][1][j])  for j in range(len(t[1][i][0])) ])
        })
print(data)

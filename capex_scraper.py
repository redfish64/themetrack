from math import inf
import os
from weakref import ref
import requests
from bs4 import BeautifulSoup
import re
import json
import urllib.request as ur 
import browser_cookie3
from fake_useragent import UserAgent
import argparse
import util
import pandas as pd
import datetime
import scraper_util
from ftypes import PickType
import ftypes


#index of key to type of data. This is a list because this is also the order we get 
#the data in (ie. 'Total Portfolio' comes first, etc.)
CAPEX_ID_TO_TYPE = [('6ce881df-bfd9-4b15-b6d5-e2f2419729c6', PickType.CapexTotalPortfolio),
                    ('100a4630-266d-4b57-ad2d-df5df49666f1', PickType.CapexDiviPortfolio),
                    ('ea14de63-4993-4c24-925e-c5d06e31604d', PickType.CapexBig5),
                    ('722013a3-0f6c-4663-a296-88e3dc3c28c4', PickType.CapexSkeletonPortfolio),
                    ('ed3f781c-f68a-4e54-9b9c-e59c3289766a', PickType.CapexClosed),
]

def get_dict_tree_value_by_path(tree, path):
    current = tree
    for key in path:
        # Try to get the value for the key, if key is not found, return None
        if key in current:
            current = current[key]
        else:
            return None
    return current

def read_capex_portfolio_html(opener):
        url = "https://capexinsider.com/login/portfolio/"

        capex_html = opener.open(url).read()
        capex_soup = BeautifulSoup(capex_html, "html.parser")

        infogram_urls = [f'https://e.infogram.com/{ie["data-id"]}' for ie in capex_soup.find_all("div",{"class":"infogram-embed"})]

        print(f"Found {len(infogram_urls)} html urls")

        infogram_html_list = []
        for i,url in enumerate(infogram_urls):
            print(f"Reading html data {i}")
            infogram_html_list.append(opener.open(url).read())

        data_urls = []

        for ih in infogram_html_list:
            soup = BeautifulSoup(ih, "html.parser")
        
            #grabs the first script with window.infographicData
            script = [
                t 
                for t in soup.findAll("script") 
                if "window.infographicData" in t.text
                ][0].text
            
            #grab the window.infographicData which should json
            extract = re.search(r".*window\.infographicData=(.*);$", script)

            data = json.loads(extract.group(1))

            entities = data["elements"]["content"]["content"]["entities"]

            for key in entities.keys():
                #co: the url seems to be wrong nowadays
                #url = get_dict_tree_value_by_path(entities[key],["props","chartData","custom","live","url"])

                live_key = get_dict_tree_value_by_path(entities[key],["props","chartData","custom","live","key"])
                live_provider = get_dict_tree_value_by_path(entities[key],["props","chartData","custom","live","provider"])
                #if(live_provider == "atlas_google_drive"):
                if(live_key is not None):
                    url = f"https://live-data.jifo.co/{live_key}"
                else:
                    print(f"No live key for live provider {live_provider}, url {url}")

                if(url is not None):
                    data_urls.append((live_key,url))

        table_data = []

        print(f"Found {len(data_urls)} table urls")

        for i,(key,data_url) in enumerate(data_urls):
            print(f"Reading table url {i}, {data_url}")

            try:
                table_data.append((key,opener.open(data_url).read()))
            except Exception as e:
                print(f"Read failed, {e}")
        
        return(capex_html,infogram_html_list,table_data)


def extract_index_and_id_from_filepath(filename):
    pattern = r'.*/capex_data_(\d+)_([0-9a-f-]+)\.json'
    match = re.match(pattern, filename)
    if match:
        return int(match.group(1)), match.group(2)
    raise ValueError("Invalid filename format")


def convert_capex_portfolio_data_to_pandas(fp,td_json):
    subdir_datestr = util.extract_subdir_date_from_filepath(fp)

    version = 0 if subdir_datestr < "2025-05-01" else 1 

    if(version > 0):
        (index,id) = extract_index_and_id_from_filepath(fp)
    

    td = json.loads(td_json.decode())
    #convert data to pandas
    table = td['data'][0]
    headers = table[0]

    out_table = {}

    def add_cell(ri,c,ch):
        """adds a new cell. creates row if necessary

        Args:
            ri : row index
            c : cell value
            ch : column header
        """

        #get or create the column
        column = out_table.get(ch,[])

        #if the column isn't up to the current row index, we add blank values for 
        #the previous rows so we are lined up to the current row properly
        column += [None] * (ri-(len(column)))
        
        #add the value
        column.append(c)

        #replace it back
        out_table[ch] = column

    for ri,r in enumerate(table[1:]):
        for c,ch in zip(r,headers):
            if(isinstance(c,dict)):
                if(c['type'] != 'link'):
                    util.error(f"Can't understand cell of row in table, got {c} in row {r}")

                add_cell(ri,c['value'],ch)
                if('href' in c):
                    add_cell(ri,c['href'],ch+"_href")
            else:
                add_cell(ri,c,ch)

    #make sure all the columns are of equal length (if some rows don't have hrefs for some cells, they may not be the same length)
    for col in out_table.values():
        col += [None] * (len(table)-1-(len(col)))

    res =  pd.DataFrame(out_table)

    if(version == 0):
        fn = td['fileName']
        pick_type = ftypes.CAPEX_FILENAME_TO_PICK_TYPE[fn].name
        refreshed_date = datetime.datetime.fromtimestamp(int(td['refreshed'])/1000)
    else:
        for capex_id, pt in CAPEX_ID_TO_TYPE:
            if capex_id == id:
                pick_type = pt.name
        if(not pick_type):
            raise ValueError(f"No PickType found for ID: {id}")

        refreshed_date = datetime.datetime.strptime(td['refreshed'], '%Y-%m-%dT%H:%M:%S.%fZ')

    res[ftypes.SpecialColumns.DRefreshedDate.get_col_name()]= refreshed_date
    res[ftypes.SpecialColumns.RPickType.get_col_name()]= pick_type

    return res

def read_capex_to_dir(browser : scraper_util.Browser, dir):
    opener = scraper_util.create_url_opener(browser=browser)

    (capex_html,infogram_htmls,table_data_json) = read_capex_portfolio_html(opener)

    if(len(table_data_json) == 0):
        util.error("Could not read capex data. Make sure you selected the right browser and have logged into capexinsider.com")

    #TODO 2 check that necessary tables are all there. Also check on load from cache

    for index,(key,td) in enumerate(table_data_json):
        open(os.path.join(dir,f"capex_data_{index}_{key}.json"),"wb").write(td)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        usage="%(prog)s [-w] [table data files...]",
        description="loads and parses capex and infogram files. If filenames are present on commandline, then won't load them from internuts. Stores outputs to files",
        exit_on_error=True,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--no-write", default=False, action='store_true', help="doesn't write loaded files")
    parser.add_argument("table_data_files", nargs='*',help="capex json files from the cloud")

    config = parser.parse_args()

    opener = scraper_util.create_url_opener(browser=scraper_util.Browser.Brave)

    if(config.table_data_files == []):
        (capex_html,infogram_htmls,table_data_json) = read_capex_portfolio_html(opener)

        if(not config.no_write):
            open("out_capex.html","wb").write(capex_html)

            for index,ih in enumerate(infogram_htmls):
                open(f"out_ih_{index}.html","wb").write(ih)

            for index,(key,td) in enumerate(table_data_json):
                open(f"out_table_data_{key}.json","wb").write(td)
    else:
        table_data_json = [open(ih,"rb").read() for ih in config.table_data_files]
      
    pandas = [convert_capex_portfolio_data_to_pandas(td_json) for td_json in table_data_json]

    for p in pandas:
        print("------------------------------")
        print(p.to_csv())

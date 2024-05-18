from math import inf
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
import ftypes


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

        infogram_html_list = [ opener.open(url).read() for url in infogram_urls]

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
                url = get_dict_tree_value_by_path(entities[key],["props","chartData","custom","live","url"])
                if(url is None):
                    live_key = get_dict_tree_value_by_path(entities[key],["props","chartData","custom","live","key"])
                    live_provider = get_dict_tree_value_by_path(entities[key],["props","chartData","custom","live","provider"])
                    if(live_provider == "atlas_google_drive"):
                        url = f"https://atlas.jifo.co/api/connectors/{live_key}"
                if(url is not None):
                    data_urls.append(url)

        table_data = [opener.open(data_url).read() for data_url in data_urls]

        return(capex_html,infogram_html_list,table_data)


def convert_capex_portfolio_data_to_pandas(td_json):
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

    fn = td['fileName']
    pick_type = ftypes.CAPEX_FILENAME_TO_PICK_TYPE[fn]
    refreshed_date = datetime.datetime.fromtimestamp(int(td['refreshed'])/1000)

    res[ftypes.SpecialColumns.DCapexName.get_col_name()] = fn
    res[ftypes.SpecialColumns.DRefreshedDate.get_col_name()]= refreshed_date
    res[ftypes.SpecialColumns.RPickType.get_col_name()]= pick_type

    return res

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

            for index,td in enumerate(table_data_json):
                open(f"out_table_data_{index}.json","wb").write(td)
    else:
        table_data_json = [open(ih,"rb").read() for ih in config.table_data_files]
      
    pandas = [convert_capex_portfolio_data_to_pandas(td_json) for td_json in table_data_json]

    for p in pandas:
        print("------------------------------")
        print(p.to_csv())

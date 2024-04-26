import os
from enum import Enum, auto
import argparse
import re
import sys
import util
import capex_scraper
import ib_parser
import pandas as pd
from ftypes import Brokerage, PickType
import matcher


def get_files_with_ext(directory, ext):
    """Returns all files ending in given extension"""
    files = []
    
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        if os.path.isfile(item_path) and item_path.lower().endswith(ext):
            files.append(item_path)

    return files

def get_template_path(template_name):
    util.get_code_file_path(template_name)

def is_capex_json(filename : str):
    return re.match(r"^capex.*\.json$",filename.lower()) is not None

def is_ib_holding_activity_csv(filename : str):
    return re.match(r"^holdings_ib_activity.*\.csv$",filename.lower()) is not None

def join_holdings_and_picks(holdings : pd.DataFrame, picks : pd.DataFrame):
    """Does a join in order to try and match picks to holdings, 
       returning a new dataframe containing indexes of each join. Multiple or zero matches are possible."""
    joins = []

    # we do a line by line cartesian product O(m*n) join here because there just aren't a lot of rows and its more
    # flexible than trying to create columns and matching normally 
    for hi,h in holdings:
        for pi,p in picks:
            if(matcher.match_holding_to_pick(h,p)):
                joins.append(hi,pi)

parser = argparse.ArgumentParser(
    usage="%(prog)s [options] [directory of financial files]...",
    description="joins holdings files with recommendation files for analysis in a spreadsheet",
    exit_on_error=True,
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
parser.add_argument("finance_dir", help="directory containing financial files")

config = parser.parse_args()

picks_df = pd.DataFrame()
holdings_df = pd.DataFrame()

for item in os.listdir(config.finance_dir):
    item_path = os.path.join(config.finance_dir, item)
    if os.path.isfile(item_path):
        if is_capex_json(item):
            table_json_data = open(item_path,"rb").read()
            df = capex_scraper.convert_capex_portfolio_data_to_pandas(table_json_data)
            picks_df = pd.concat([picks_df,df],ignore_index=True)
        elif is_ib_holding_activity_csv(item):
            ib_df = ib_parser.parse_holding_activity(item_path)
            ib_df[Brokerage.InteractiveBrokers.name] = Brokerage.InteractiveBrokers

            holdings_df = pd.concat([holdings_df,ib_df],ignore_index=True)
        else:
            util.warn(f"skipping file {item_path}, don't know how to handle")
    else:
        util.warn(f"skipping dir {item_path}")

res = join_holdings_and_picks(holdings_df,picks_df)

# def print_csv_array(l):
#     for i in l:
#         print(i.to_csv())
#         print("---------------------------")

# print_csv_array(picks_df_list)
# print_csv_array(holdings_df_list)


# def verify_fields(fields, *expected_fields):
#     if fields == expected_fields:
#         return
#     pdb.set_trace()
    
#     # Find missing or unexpected fields
#     missing_fields = set(expected_fields) - set(fields)
#     unexpected_fields = set(fields) - set(expected_fields)

#     errs = []
#     if missing_fields:
#         errs.append(f"Missing fields:{missing_fields}")
#     if unexpected_fields:
#         errs.append(f"Unexpected fields:{unexpected_fields}")

#     error("Fields don't match expected: "+(",".join(errs)))
    
# def read_big5(fn):
#     with open(fn, newline='') as csvfile:
#         r = csv.DictReader(csvfile)
#         h = r.next()

#         verify_fields(h,"Issue","Date","Theme","Name","Ticker")

#         return list(r)
    

# def get_data_maps(d):
#     capex_rows = []
#     holdings = []

#     for fn in os.listdir(d):
#         file_path = os.path.join(d, fn)
#         if not os.path.isfile(file_path):
#             continue
#         ft = get_filetype(fn)
#         if ft is None:
#             warning(f"Cannot determine type of file for {file_path}, ignoring"
#                     "...")
#             continue

#         if ft == FileCategory.Capex_Big5:
#             capex_rows = capex_rows + read_big5(file_path)
#         elif ft == FileCategory.Capex_ClosedPos:
#             capex_rows = capex_rows + read_closed_pos(file_path)
#         elif ft == FileCategory.Capex_CapGains:
#             capex_rows = capex_rows + read_cap_gains(file_path)
#         elif ft == FileCategory.Capex_IncPort:
#             capex_rows = capex_rows + read_inc_port(file_path)
#         elif ft == FileCategory.Capex_SkelPort:
#             capex_rows = capex_rows + read_skel_port(file_path)
#         elif ft == FileCategory.TDAmer:
#             holdings = holdings + read_tdamer(file_path)
#         elif ft == FileCategory.Canaccord:
#             holdings = holdings + read_canaccord(file_path)
#         elif ft == FileCategory.Schwab:
#             holdings = holdings + read_schwab(file_path)
#         elif ft == FileCategory.IB:
#             holdings = holdings + read_ib(file_path)
#         else:
#             error(f"Internal error, don't know about filetype {ft.name}")


# holdings,capex = get_data_maps(config.finance_dir)

# for h in holdings:
#     capex_rows = find_matching_capex(h,capex)
#     l = len(capex_rows)
#     if l > 1:
#         warning(f"Found multiple capex entries for {desc_holding(h)}: {','.join(map(desc_capex,capex_rows))}. Will divide allocation evenly between them.")

#         cl = len(capex_rows)
#         for c in capex_rows:
#             add_allocation(h,c,1./cl)

#         continue

#     if l == 0:
#         warning(f"No matching capex entry for {desc_holding(h)}, using theme {DEFAULT_THEME}")
#         add_allocation(h,default_c,1.)
#         continue

#     add_allocation(h,c,1.)

# for h in holdings:
#     print_holding(h)

    

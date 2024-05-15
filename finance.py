import os
from enum import Enum, auto
import argparse
import re
import sys
import util
import capex_scraper
import ib_parser
import override_parser
import schwab_parser
import pandas as pd
from functools import cmp_to_key
import ftypes
import forex


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
    return re.match(r"^holdings_ib_activity.*\.(?:csv|xlsx)$",filename.lower()) is not None

def is_schwab_csv(filename : str):
    return re.match(r"^holdings_schwab.*\.(?:csv|xlsx)$",filename.lower()) is not None

def is_system_overrides_file(filename : str):
    return re.match(r"^system_overrides.*\.(?:csv|xlsx)$",filename.lower()) is not None

def is_overrides_file(filename : str):
    return re.match(r"^overrides.*\.(?:csv|xlsx)$",filename.lower()) is not None

def join_holdings_and_picks(holdings_df : pd.DataFrame, picks_df : pd.DataFrame):

    # Set indices to preserve original row numbers
    holdings_df['holdings_index'] = holdings_df.index
    picks_df['picks_index'] = picks_df.index

    res_df_list = []

    all_match_columns = {}

    #PERF this is very slow, but we can speed it up later, by matching multiple holdings at a time 
    # that have the same MatchColumns value
    for hi,h in holdings_df.iterrows():
        #this should never be None because it was checked when the file was parsed
        h_mc,p_mc = override_parser.parse_match_columns(h[ftypes.SpecialColumns.MatchColumns.get_col_name()])

        for mc in h_mc + p_mc:
            all_match_columns[mc] = True   

        #match against the picks
                
        # Construct the boolean mask dynamically
        mask = pd.Series(True, index=picks_df.index)  # Start with all True
        for column in h_mc:
            value = util.get_df_row_val(h,column) 
            mask &= (picks_df[column] == value)  # Update mask to narrow down the rows

        filtered_picks_df = picks_df[mask]

        joined_df = filtered_picks_df.assign(**h)

        res_df_list.append(joined_df)

    res = pd.concat(res_df_list, ignore_index=True)
    return res,all_match_columns.keys()

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

system_overrides = []
user_overrides = []

data_dir_files = os.listdir(config.finance_dir)
data_dir_files.sort()

for item in data_dir_files:
    item_path = os.path.join(config.finance_dir, item)
    if os.path.isfile(item_path):
        if is_capex_json(item):
            table_json_data = open(item_path,"rb").read()
            df = capex_scraper.convert_capex_portfolio_data_to_pandas(table_json_data)
            picks_df = pd.concat([picks_df,df],ignore_index=True)
        elif is_ib_holding_activity_csv(item):
            ib_df = ib_parser.parse_holding_activity(item_path)

            holdings_df = pd.concat([holdings_df,ib_df],ignore_index=True)
        elif is_schwab_csv(item):
            schwab_df = schwab_parser.parse_file(item_path)

            holdings_df = pd.concat([holdings_df,schwab_df],ignore_index=True)
        elif is_system_overrides_file(item):
            ov = override_parser.parse_override_file(item_path)
            system_overrides += ov
        elif is_overrides_file(item):
            ov = override_parser.parse_override_file(item_path)
            user_overrides += ov
        else:
            util.warn(f"skipping file {item_path}, don't know how to handle")
    else:
        util.warn(f"skipping dir {item_path}")

override_parser.run_overrides(system_overrides,user_overrides,holdings_df)
override_parser.run_overrides(system_overrides,user_overrides,picks_df)


join_res,match_columns = join_holdings_and_picks(holdings_df,picks_df)

#PERF: this code is probably inefficient, not a pandas expert
res = []

for hi in holdings_df.index:
    joined_rows = join_res[join_res['holdings_index'] == hi]
    num_joined_rows = len(joined_rows)
    if(num_joined_rows == 0):
        res.append(holdings_df.loc[hi].to_dict())
        res[-1][ftypes.SpecialColumns.JoinResult.get_col_name()] = 'None'
    elif(num_joined_rows == 1):
        res.append(joined_rows.iloc[0].to_dict())
        res[-1][ftypes.SpecialColumns.JoinResult.get_col_name()] = '1:1'
    elif(num_joined_rows > 1):
        sorted_join_rows = joined_rows.sort_values(by=[ftypes.SpecialColumns.PickPriority.get_col_name()])

        res.append(sorted_join_rows.iloc[0].to_dict())
        desc = ",".join([r[ftypes.SpecialColumns.PickDesc.get_col_name()] for _,r in sorted_join_rows.iterrows()])

        res[-1][ftypes.SpecialColumns.JoinResult.get_col_name()] = 'Many'
        res[-1][ftypes.SpecialColumns.JoinAll.get_col_name()] = desc


res_pd = pd.DataFrame(res)

def move_columns_to_front(df, columns_to_front):
    """
    Reorder DataFrame columns by moving specified columns to the front.
    """
    #remove any columns that aren't in the dataframe (for example, if there are no many joins, then they're won't be a JoinMany)
    columns_to_front = [col for col in columns_to_front if col in df.columns]

    # Create a new column order
    new_order = columns_to_front + [col for col in df.columns if col not in columns_to_front]
    
    # Return the reordered DataFrame
    return df[new_order]

match_columns = list(match_columns)
match_columns.sort()


def fill_in_forex(df):

    def update_native_currency(row):
        curr_from = row[ftypes.SpecialColumns.CurrValueCurrency.get_col_name()]
        amt_from = row[ftypes.SpecialColumns.CurrValueForeign.get_col_name()]
        amt_to = forex.convert(curr_from,"USD",amt_from) #TODO 2 figure out dates here

        return amt_to

    df[ftypes.SpecialColumns.CurrValue.get_col_name()] = df.apply(update_native_currency,axis=1)

fill_in_forex(res_pd)

#res_pd = move_columns_to_front(res_pd,match_columns+[ftypes.SpecialColumns.JoinResult.get_col_name(),ftypes.SpecialColumns.JoinAll.get_col_name()])
front_columns = [c for c in res_pd.columns if re.match(r'^[A-Z]:',c)]
front_columns.sort()

res_pd = move_columns_to_front(res_pd,front_columns)

print(res_pd.to_csv())
print("-"*40)
# print(holdings_df.to_csv())
# print("-"*40)
print(picks_df.to_csv())

print("TODO 2: For each pick, if there are multiple matching holdings, complain somehow possibly")

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

    

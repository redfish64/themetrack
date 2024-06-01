import datetime
import os
import argparse
import pathlib
import re
import shutil
import sys
import util
import capex_scraper
import ib_parser
import rules_parser
import schwab_parser
import pandas as pd
import ftypes
import forex
import reports
import external
import scraper_util
import config_parser
import array_log as al

CREATE_SNAPSHOT_COMMAND = 'create-snapshot'
CREATE_REPORTS_COMMAND = 'create-reports'
DOWNLOAD_CAPEX_COMMAND = 'download-capex'

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

#TODO 2.5 for the following, don't use the name to match, but look at the file contents.
#Otherwise the user has to rename which may be confusing to them.

def is_capex_json(filename : str):
    return re.match(r"^capex.*\.json$",filename.lower()) is not None

def is_ib_holding_activity_csv(filename : str):
    return re.match(r"^holdings_ib.*\.(?:csv|xlsx)$",filename.lower()) is not None

def is_schwab_csv(filename : str):
    return re.match(r"^holdings_schwab.*\.(?:csv|xlsx)$",filename.lower()) is not None

def is_system_overrides_file(filename : str):
    return re.match(r"^system_overrides.*\.(?:csv|xlsx)$",filename.lower()) is not None

def is_config_file(filename : str):
    return filename == ftypes.THEME_TRACK_CONFIG_FILE

def join_holdings_and_picks(holdings_df : pd.DataFrame, picks_df : pd.DataFrame):
    """Returns the cartesian product of holdings and picks using "RMatchColumns" in each
    holding row to join them.

    Returns:
        pd.DataFrame: cartesian product
    """

    # Set indices to preserve original row numbers
    holdings_df['holdings_index'] = holdings_df.index
    picks_df['picks_index'] = picks_df.index

    res_df_list = []

    all_match_columns = {}

    #PERF this is very slow, but we can speed it up later, by matching multiple holdings at a time 
    # that have the same MatchColumns value
    for hi,h in holdings_df.iterrows():
        #this should never be None because it was checked when the file was parsed
        h_mc,p_mc = rules_parser.parse_match_columns(h[ftypes.SpecialColumns.RMatchColumns.get_col_name()])

        for mc in h_mc + p_mc:
            all_match_columns[mc] = True   

        #match against the picks
                
        # Construct the boolean mask dynamically
        mask = pd.Series(True, index=picks_df.index)  # Start with all True
        for h_column,p_column in zip(h_mc,p_mc):
            value = util.get_df_row_val(h,h_column) 
            mask &= (picks_df[p_column] == value)  # Update mask to narrow down the rows

        filtered_picks_df = picks_df[mask]

        joined_df = filtered_picks_df.assign(**h)

        res_df_list.append(joined_df)

    res = pd.concat(res_df_list, ignore_index=True)
    return res,all_match_columns.keys()


def get_main_dir():
    if os.name == 'nt':  # Windows
        base_dir = "C:\\"
        config_dir = os.path.join(base_dir, 'Theme Track')
    else:  # Linux
        base_dir = os.path.expanduser('~')
        config_dir = os.path.join(base_dir, 'theme_track')

    return config_dir


def get_datafile(file : str) -> str:
    """Regardless if using pyinstaller or not, will return the pathname of a the given file.
    If not using pyinstaller, assumes file is in the same directory as the program.
    """
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, file)

    script_dir = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(script_dir, file)

def get_dirs_latest_first(dirname):
    # Get the directory path
    dir_path = pathlib.Path(dirname)

    # List all immediate subdirectories
    subdirs = [f for f in dir_path.iterdir() if f.is_dir()]

    # Sort the subdirectories by modification time, descending
    sorted_subdirs = sorted(subdirs, reverse=True)

    return sorted_subdirs

def get_latest_valid_snapshot_dir(main_dir):
    valid_dir = None

    #search latest previous snapshots first
    if(os.path.exists(main_dir)):
        for d in get_dirs_latest_first(main_dir):
            d2 = os.path.join(d,ftypes.THEME_TRACK_CONFIG_FILE)
            if(os.path.exists(d2)):
                valid_dir = d
                break

    return valid_dir        
    
def get_sub_dir_from_config(args):
    if(args.sub_dir is None):
        full_path_sub_dir = get_latest_valid_snapshot_dir(args.main_dir)
    else: #they chose one
        full_path_sub_dir = os.path.join(args.main_dir,args.sub_dir)

    if(full_path_sub_dir is None):
        util.error("Cannot find any snapshot directory. Please run (cmd) {CREATE_SNAPSHOT_COMMAND} first")

    if(not os.path.exists(full_path_sub_dir)):
        util.error(f"Cannot find snapshot directory {full_path_sub_dir}")

    return full_path_sub_dir

def create_snapshot(args):
    print("create snapshot!")
    dir = os.path.join(args.main_dir,args.sub_dir)
    theme_track_config_dest = os.path.join(dir,ftypes.THEME_TRACK_CONFIG_FILE)
    if(os.path.exists(theme_track_config_dest)):
        print(f"{theme_track_config_dest} already exists.")
        if(not args.no_open_window):
            print("Opening a gui window to output directory")
            external.open_dir(dir)
    else:
        print(f"Creating snapshot at {dir}")

        #find the best theme_track_config file to use
        theme_track_config_src = None

        get_latest_valid_snapshot_dir(args.main_dir)

        #if not present use default one hardcoded into program
        if(theme_track_config_src is None):
            theme_track_config_src = get_datafile(ftypes.THEME_TRACK_CONFIG_FILE)

        os.makedirs(dir, exist_ok=True)
        shutil.copyfile(theme_track_config_src,theme_track_config_dest)

        print(f"Copied {ftypes.THEME_TRACK_CONFIG_FILE} from {theme_track_config_src} to {dir}")

        if(not args.no_open_window):
            print("Opening a gui window to output directory")
            external.open_dir(dir)

        print("Done!")

    print(f"""Now, please do the following:
1. Copy brokerage reports to {dir}
2. Login in capexinsider.com
3. Run "(cmd) {DOWNLOAD_CAPEX_COMMAND} (browser)" to download capex files into the directory. Browser is the browser you logged in with and is
   one of: {", ".join([x.name for x in scraper_util.Browser])}
4. Edit {theme_track_config_dest} as necessary.
5. Run "(cmd) {CREATE_REPORTS_COMMAND}" to create the final report. If you need to make changes, re-edit {ftypes.THEME_TRACK_CONFIG_FILE} and re-run this step
""")

def download_capex(args):
    sub_dir = get_sub_dir_from_config(args)
    capex_scraper.read_capex_to_dir(scraper_util.name_to_browser[args.browser], sub_dir)

    print(f"""Done!
If your brokerage files are already in {sub_dir}, run "(cmd) {CREATE_REPORTS_COMMAND}", otherwise download them,
place them into the directory, and run "(cmd) {CREATE_REPORTS_COMMAND}" afterwards
""")

def today_as_yyyy_mm_dd():
    today = datetime.date.today()
    return today.strftime('%Y-%m-%d')

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

def fill_in_forex(df):

    def update_native_currency(row):
        curr_from = row[ftypes.SpecialColumns.RCurrValueCurrency.get_col_name()]
        amt_from = row[ftypes.SpecialColumns.RCurrValueForeign.get_col_name()]

        if(pd.isna(curr_from) or pd.isna(amt_from)):
            return None
        
        amt_to = forex.convert(curr_from,"USD",amt_from) #TODO 2 figure out dates here

        return amt_to

    df[ftypes.SpecialColumns.RCurrValue.get_col_name()] = df.apply(update_native_currency,axis=1)


def create_reports(args):
    sub_dir = get_sub_dir_from_config(args)

    picks_df = pd.DataFrame()
    holdings_df = pd.DataFrame()

    fi = util.read_standardized_csv(os.path.join(util.get_installation_directory(),ftypes.SYSTEM_RULES_FILENAME))
    system_overrides = rules_parser.parse_override_file(fi)

    user_overrides = []
    config_file = None

    data_dir_files = os.listdir(sub_dir)
    data_dir_files.sort()

    for item in data_dir_files:
        item_path = os.path.join(sub_dir, item)
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
            elif is_config_file(item):
                if(config_file is not None):
                    util.error(f"There can only be one config file, got {item_path} and {config_file}")
                config,user_overrides = config_parser.parse_config_file(item_path)
                config_file = item_path
            else:
                util.warn(f"skipping file {item_path}, don't know how to handle")
        else:
            util.warn(f"skipping dir {item_path}")

    if(args.rules_log is not None):
        holdings_id = int(args.rules_log)

        rules_log = al.Log({"df": "holdings", "df_index" : holdings_id -1})
    else:
        rules_log = al.Log(None,turn_off=True)

    with al.add_log_context(rules_log,{"df": "holdings"}):
        rules_parser.run_rules(system_overrides,user_overrides,holdings_df,rules_log)
    with al.add_log_context(rules_log,{"df": "picks"}):
        rules_parser.run_rules(system_overrides,user_overrides,picks_df,rules_log)

    if(picks_df.empty):
        util.error(f"Capex files have not been downloaded, please run (cmd) {DOWNLOAD_CAPEX_COMMAND}")
    if(holdings_df.empty):
        util.error("There are no brokerage reports that could be processed. Please download them and put them in {sub_dir}")

    if(config_file is None):
        util.error(f'There is no {ftypes.THEME_TRACK_CONFIG_FILE} in {sub_dir}. Please run (cmd) {CREATE_SNAPSHOT_COMMAND}')

    join_res,match_columns = join_holdings_and_picks(holdings_df,picks_df)

    #PERF: this code is probably inefficient, not a pandas expert
    res = []

    for hi in holdings_df.index:
        joined_rows = join_res[join_res['holdings_index'] == hi]
        num_joined_rows = len(joined_rows)
        if(num_joined_rows == 0):
            res.append(holdings_df.loc[hi].to_dict())
            res[-1][ftypes.SpecialColumns.DJoinResult.get_col_name()] = 'None'
        elif(num_joined_rows == 1):
            res.append(joined_rows.iloc[0].to_dict())
            res[-1][ftypes.SpecialColumns.DJoinResult.get_col_name()] = '1:1'
            res[-1][ftypes.SpecialColumns.DJoinAll.get_col_name()] = res[-1][ftypes.SpecialColumns.RPickDesc.get_col_name()]
            res[-1][ftypes.SpecialColumns.DJoinAllBitMask.get_col_name()] = (
                ftypes.pick_types_to_bitmask([ftypes.PickType[res[-1][ftypes.SpecialColumns.RPickType.get_col_name()]]])
            )

        elif(num_joined_rows > 1):
            sorted_join_rows = joined_rows.sort_values(by=[ftypes.SpecialColumns.RPickPriority.get_col_name()])

            res.append(sorted_join_rows.iloc[0].to_dict())
            desc = ",".join([r[ftypes.SpecialColumns.RPickDesc.get_col_name()] for _,r in sorted_join_rows.iterrows()])

            res[-1][ftypes.SpecialColumns.DJoinResult.get_col_name()] = 'Many'
            res[-1][ftypes.SpecialColumns.DJoinAll.get_col_name()] = desc
            res[-1][ftypes.SpecialColumns.DJoinAllBitMask.get_col_name()] = (
                ftypes.pick_types_to_bitmask([ftypes.PickType[r[ftypes.SpecialColumns.RPickType.get_col_name()]] 
                                              for _,r in sorted_join_rows.iterrows()])
            )

    #add any empty picks with no investments
    for pi in picks_df.index:
        joined_rows = join_res[join_res['picks_index'] == pi]
        num_joined_rows = len(joined_rows)
        if(num_joined_rows == 0):
            res.append(picks_df.loc[pi].to_dict())
            res[-1][ftypes.SpecialColumns.DJoinResult.get_col_name()] = 'None'

    res_pd = pd.DataFrame(res)

    #now update holdings rows to show which picks have multiple holdings for them.
    #Ususally this shouldn't occur I would imagine, unless the user somehow owns the same security in multiple ways
    #ADR's/non-ADR's, multiple brokerages, etc.
    for pi in picks_df.index:
        joined_rows = join_res[join_res['picks_index'] == pi]
        
        if(num_joined_rows > 1):
            res.append(sorted_join_rows.iloc[0].to_dict())
            desc_list = sorted([r[ftypes.SpecialColumns.RPickDesc.get_col_name()] for _,r in join_res.iterrows()])
            desc = ",".join(desc_list)

            res[res['picks_index'] == pi,ftypes.SpecialColumns.DMultHoldings.get_col_name()] = desc



    match_columns = list(match_columns)
    match_columns.sort()

    fill_in_forex(res_pd)

    #res_pd = move_columns_to_front(res_pd,match_columns+[ftypes.SpecialColumns.JoinResult.get_col_name(),ftypes.SpecialColumns.JoinAll.get_col_name()])
    front_columns = [c for c in res_pd.columns if re.match(r'^[A-Z]:',c)]
    front_columns.sort()

    res_pd = move_columns_to_front(res_pd,front_columns)

    # print(res_pd.to_csv())
    # print("-"*40)
    # # print(holdings_df.to_csv())
    # # print("-"*40)
    # print(picks_df.to_csv())

    REPORT_OUT_FILE = "report_out.xlsx"

    report_out_path = os.path.join(sub_dir,REPORT_OUT_FILE)

    #TODO, add rules to report:    al.create_df(rules_log)
    reports.make_report_workbook(res_pd,holdings_df,picks_df,config.currency,rules_log,report_out_path)

    print(f"Report finished! The report is located here {report_out_path}")

    print("TODO 2: For each pick, if there are multiple matching holdings, complain somehow possibly")  

    if(args.rules_log is not None):
        for msg,context in rules_log.get_logs():
            print(f"{context}: {msg}")

    
def setup_argparse():
    parser = argparse.ArgumentParser(
        description="joins holdings files with pick files for analysis in a spreadsheet",
        exit_on_error=True,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("--main-dir", default=default_main_dir, help="main directory of theme track. All reports, config and data files will go here")

    subparsers = parser.add_subparsers(title="commands", description="Available commands", help="Use `command -h` for more details", dest="command")

    # Subparser for the 'scrape' command
    parser_snapshot = subparsers.add_parser(CREATE_SNAPSHOT_COMMAND, help="Creates a new directory to produce reports")
    parser_snapshot.add_argument('--sub-dir', type=str, default=today_as_yyyy_mm_dd(), 
                                 help="The name of the sub-dir to create.")
    parser_snapshot.add_argument('--use-default', default=False,action='store_true', 
                                 help=f'Normally, {ftypes.THEME_TRACK_CONFIG_FILE} from the previous snapshot is copied into the new one. If set '
                                 'the default will always be used.')
    parser_snapshot.add_argument('--no-open-window', default=False,action='store_true', 
                                 help='Normally, a gui window will open up of the snapshot dir created. Using this option prevents this.')
    parser_snapshot.set_defaults(func=create_snapshot)

    # Subparser for the 'scrape' command
    parser_scrape = subparsers.add_parser(DOWNLOAD_CAPEX_COMMAND, help="Downloads capex portfolio. Make sure to log in prior to calling this")
    parser_scrape.add_argument('--sub-dir', type=str, 
                               help="The name of the sub-dir to download the capex files into. Defaults to the latest directory.")
    parser_scrape.add_argument('browser', type=str, choices=["chrome","firefox","brave"], help="The browser used to login to website")
    parser_scrape.set_defaults(func=download_capex)

    # Subparser for the 'create-reports' command
    parser_create_reports = subparsers.add_parser(CREATE_REPORTS_COMMAND, help="Create reports from the provided data")
    parser_create_reports.add_argument('--sub-dir', type=str, 
                                       help="The name of the sub-dir to download the capex files into. Defaults to the latest directory.")
    parser_create_reports.add_argument('--rules-log', type=str, 
                                       help=f"Turns on rule logs and specifies the row in the {reports.HOLDINGS_WS_TITLE} to print logs for")
    parser_create_reports.set_defaults(func=create_reports)

    return parser

default_main_dir = get_main_dir()

parser = setup_argparse()

args = parser.parse_args()

# Call the appropriate function based on the command
if args.command:
    args.func(args)
else:
    parser.print_help()


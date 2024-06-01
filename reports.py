from dataclasses import dataclass
from enum import Enum, auto
from functools import partial
import re
from typing import Any, Callable
import pandas as pd
import ftypes
from openpyxl.styles import Font
import array_log as al
import util

STOCKS_WS_TITLE = 'Securities Report'
THEMES_WS_TITLE = 'Themes Report'
HOLDINGS_WS_TITLE = 'Holdings Input Data'
PICK_WS_TITLE = 'Pick Input Data'
JOINED_DATA_WS_TITLE = 'Joined Data'
NA_STR_NAME = '(none)'

#TODO 4 maybe one day parse the excel format, ex. '"$"#,##0.00', directly
def calc_num_len(fixed : int,num_decimals : int ,val : float):
    """Calculates the number of characters taken up by the end result in the spreadsheet for a float.

    Args:
        fixed (int): number of additional characters to add to the total. For ex. for '"$"#,##0.00' there is 1 for the dollar sign
        num_decimals (int): number of decimal places after the ., ex. for 1234.567, 2 would be 1234.58
        val (float): value to calculate length for

    Returns:
        int: number of characters
    """

    #we get the val_str for the number without any decimals to calculate its length correctly and simply
    #PERF could be faster
    if(isinstance(val,str)):
        val_str = val
    else:
        val_str = f"{round(val):,}"
    return fixed + len(val_str) + (0 if num_decimals == 0 else num_decimals + 1) # +1 for the '.'

def generic_len(val):
    return len(str(val))

def get_currency_format(currency_symbol):
    currency_formats = {
        'USD': ('"$"#,##0.00',partial(calc_num_len,1,2)),  # US Dollar
        'EUR': ('"€"#,##0.00',partial(calc_num_len,1,2)),  # Euro
        'GBP': ('"£"#,##0.00',partial(calc_num_len,1,2)),  # British Pound
        'JPY': ('"¥"#,##0',partial(calc_num_len,1,2)),     # Japanese Yen (no decimal places)
        'CNY': ('"¥"#,##0.00',partial(calc_num_len,1,2)),  # Chinese Yuan
        'INR': ('"₹"#,##0.00',partial(calc_num_len,1,2)),  # Indian Rupee
        'AUD': ('"$"#,##0.00',partial(calc_num_len,1,2)),  # Australian Dollar
        'CAD': ('"$"#,##0.00',partial(calc_num_len,1,2)),  # Canadian Dollar
        'CHF': ('"CHF"#,##0.00',partial(calc_num_len,3,2)),# Swiss Franc
        'HKD': ('"$"#,##0.00',partial(calc_num_len,1,2)),  # Hong Kong Dollar
        'NZD': ('"$"#,##0.00',partial(calc_num_len,1,2)),  # New Zealand Dollar
        'KRW': ('"₩"#,##0',partial(calc_num_len,1,2)),     # South Korean Won (no decimal places)
        'SGD': ('"$"#,##0.00',partial(calc_num_len,1,2)),  # Singapore Dollar
        'BRL': ('"R$"#,##0.00',partial(calc_num_len,2,2)), # Brazilian Real
        'ZAR': ('"R"#,##0.00',partial(calc_num_len,1,2)),  # South African Rand
    }

    return currency_formats.get(currency_symbol, ('"$"#,##0.00',partial(calc_num_len,1,2)))  # Default format if not found

class PortfolioReportType(Enum):
     CapGains = auto(),
     Divi = auto(),

# order for categories in divi report
# these will be added together if a stock falls in multiple categories, to give a total score, lower value is first
PICK_TYPE_TO_SCORE_DIVI = {
    ftypes.PickType.CapexDiviPortfolio : -16,
    ftypes.PickType.CapexTotalPortfolio : -8,
    ftypes.PickType.CapexSkeletonPortfolio : -4,
    ftypes.PickType.CapexBig5 : -2,
    ftypes.PickType.CapexClosed : -1,
}

# order for categories in cap gains report, otherwise same as PICK_TYPE_TO_SCORE_DIVI
PICK_TYPE_TO_SCORE_CAP_GAINS = {
    ftypes.PickType.CapexTotalPortfolio : -16,
    ftypes.PickType.CapexSkeletonPortfolio : -8,
    ftypes.PickType.CapexDiviPortfolio : -4,
    ftypes.PickType.CapexBig5 : -2,
    ftypes.PickType.CapexClosed : -1,
}
@dataclass
class PortfolioReportInfo:
    """Information used by reports for each type of report
    """
    category_column : ftypes.SpecialColumns
    pick_type_to_order_score : dict[ftypes.PickType : int]
    stocks_row_filter : Callable[[Any],bool]
    category_name : str #name of category in reports
    stocks_ws_title : str #title of stocks report worksheet
    cat_ws_title : str #title of category report worksheet


#TODO 2.5 remove pick priority stuff, since pick priority now depends on the report 

def cap_gains_row_filter(row):
    """Shows all capgain and skeleton rows and any other row with a value attached
    """
    val = row[ftypes.SpecialColumns.RCurrValue.get_col_name()]
    if val != 0.0 and not pd.isna(val):
        return True

    bm = util.default_df_val(row[ftypes.SpecialColumns.DJoinAllBitMask.get_col_name()],0)
    return (
        ftypes.bit_mask_has_pick_type(bm,ftypes.PickType.CapexTotalPortfolio)
        or ftypes.bit_mask_has_pick_type(bm,ftypes.PickType.CapexSkeletonPortfolio)
    )
#TODO 2 ????????????????theme needs pickpriority because otherwise were getting the theme from big5 which may not have it.
#also, we may consider doing the whole join twice, once for each report category? But probably not.
def divi_row_filter(row):
    """Shows all divi rows and any other row with a value attached
    """
    val = row[ftypes.SpecialColumns.RCurrValue.get_col_name()]
    if val != 0.0 and not pd.isna(val):
        return True
    bm = util.default_df_val(row[ftypes.SpecialColumns.DJoinAllBitMask.get_col_name()],0)
    return (
        ftypes.bit_mask_has_pick_type(bm,ftypes.PickType.CapexDiviPortfolio)
    )

REPORT_TYPE_TO_REPORT_INFO = { 
                                PortfolioReportType.CapGains : PortfolioReportInfo(
                                    category_column=ftypes.SpecialColumns.RTheme,
                                    pick_type_to_order_score=PICK_TYPE_TO_SCORE_CAP_GAINS,
                                    stocks_row_filter=cap_gains_row_filter,
                                    category_name="Theme",
                                    stocks_ws_title="CapGains Stocks",
                                    cat_ws_title="CapGains Themes",
                                ),
                                PortfolioReportType.Divi : PortfolioReportInfo(
                                    category_column=ftypes.SpecialColumns.RSector,
                                    pick_type_to_order_score=PICK_TYPE_TO_SCORE_DIVI,
                                    stocks_row_filter=divi_row_filter,
                                    category_name="Sector",
                                    stocks_ws_title="Divi Stocks",
                                    cat_ws_title="Divi Themes",
                                ),
                                }

#this is a column we add only for reporting. It cannot be accessed during data generation, so we don't create a 
#ftypes.SpecialColumns entry for it
REPORT_PORTFOLIO_COLUMN = "ReportCat"

#how to sort the report categories
REPORT_PORTFOLIO_SORT_ORDER_COLUMN = "ReportCatSort"


header_font = Font(bold=True, italic=True)

def style_report_ws(ws):
    #Make header stylish
    for cell in ws[1]:
        cell.font = header_font

GENERIC_EXCEL_TYPE = ("@",generic_len)

def col_to_excel_type(col_name : str, native_currency_code : str):
    return ({
        REPORT_PORTFOLIO_COLUMN : ("@",len),
        ftypes.SpecialColumns.RCurrValue.get_col_name() : get_currency_format(native_currency_code),
        ftypes.SpecialColumns.RExchange.get_col_name() : ("@",len),
        ftypes.SpecialColumns.RTicker.get_col_name() : ("@",len),
        ftypes.SpecialColumns.RTheme.get_col_name() : ("@",len),
        ftypes.SpecialColumns.RSector.get_col_name() : ("@",len),
        ftypes.SpecialColumns.RCatPerc.get_col_name() : ("0.00%",partial(calc_num_len,1,2)),
        ftypes.SpecialColumns.RTotalPerc.get_col_name() : ("0.00%",partial(calc_num_len,1,2)),
        ftypes.SpecialColumns.RCatTotalPerc.get_col_name() : ("0.00%",partial(calc_num_len,1,2)),
        ftypes.SpecialColumns.DRefreshedDate.get_col_name() : ("YYYY-MM-DD",lambda val: 4+3+3)
    }).get(col_name,GENERIC_EXCEL_TYPE)




def update_number_formats(orig_cols,ws,num_rows,native_currency_code,always_use_generic=False):
    """Updates the style of the cell according to the column type, so percentages look like %0.01,
        money looks like $1,000,000,000.00 etc.

        Also does a somewhat sloppy job of calcuating column width. Can't really do better without
        actually talking to excel

    Args:
        orig_cols (_type_): Original names of columns from ftypes.SpecialColumns
        ws (_type_): worksheet to modify
        num_rows (_type_): number of rows to modify (after the header)
    """
    for (oc,col) in zip(list(orig_cols),ws.iter_cols()):
        excel_type,max_len_fn = GENERIC_EXCEL_TYPE if always_use_generic else col_to_excel_type(oc, native_currency_code)
        max_len = len(col[0].value)
        for cell in col[1:num_rows+1]:
            cell.number_format = excel_type
            max_len = max(max_len_fn(cell.value),max_len)

        adjusted_width = (max_len + 2) * 1.2
        ws.column_dimensions[col[0].column_letter].width = adjusted_width      


def add_df(df,title,writer,native_currency_code,orig_cols=None,always_use_generic_number_format=False):
    if(orig_cols is None):
        orig_cols = list(df.columns)
    df.to_excel(writer, index=False, sheet_name=title)
    ws = writer.sheets[title]
    style_report_ws(ws)
    update_number_formats(orig_cols,ws,df.shape[0],native_currency_code,always_use_generic=always_use_generic_number_format)


def make_portfolio_reports(report_type : PortfolioReportType, joined_df : pd.DataFrame, holdings_df : pd.DataFrame, 
                           picks_df : pd.DataFrame, native_currency_code : str,
                          ):

    report_info = REPORT_TYPE_TO_REPORT_INFO[report_type]

    COL_TO_REPORT_NAME = {
        REPORT_PORTFOLIO_COLUMN : "Portfolio(s)",
        ftypes.SpecialColumns.RCurrValue.get_col_name() : f"Value {native_currency_code}",
        ftypes.SpecialColumns.RExchange.get_col_name() : "Exchange",
        ftypes.SpecialColumns.RTicker.get_col_name() : "Ticker",
        ftypes.SpecialColumns.RSector.get_col_name() : "Sector",
        ftypes.SpecialColumns.RTheme.get_col_name() : "Theme",
        ftypes.SpecialColumns.RCatPerc.get_col_name() : f"% of {report_info.category_name}",
        ftypes.SpecialColumns.RTotalPerc.get_col_name() : "% of Total",
    }

    def pick_types_to_sort_order_key(pt_list):
        score = 0

        for pt in pt_list:
            score += report_info.pick_type_to_order_score[pt]

        return score
    
    #create report_category_column and report category sort order column (for sorting)
    def set_report_cat_and_sort_order(row):
        val = row[ftypes.SpecialColumns.DJoinAll.get_col_name()]
        if(pd.isna(val)):
            val = ''
        pick_types_str = re.findall(r',?(.*?):[^,]*',val)

        desc = row[ftypes.SpecialColumns.RPickDesc.get_col_name()]
        if(pd.isna(desc)):
            desc = ''
        desc_match = re.fullmatch(r'(.*?):.*',desc)
        if(desc_match is not None):
            pick_types_str.append(desc_match.group(1))

        pick_types = sorted(list(set([ftypes.PickType[pt] for pt in pick_types_str])),key=lambda pt: pt.name)

        short_names = [PICK_TYPE_TO_REPORT_CAT_SHORT_NAME[p] for p in pick_types]

        row[REPORT_PORTFOLIO_COLUMN] = "/".join(short_names)
        row[REPORT_PORTFOLIO_SORT_ORDER_COLUMN] = pick_types_to_sort_order_key(pick_types)

        return row

    joined_df = joined_df.apply(set_report_cat_and_sort_order,axis=1)

    total_sum = joined_df[ftypes.SpecialColumns.RCurrValue.get_col_name()].sum()

    def get_total_perc(row):
        val = row[ftypes.SpecialColumns.RCurrValue.get_col_name()]

        return val/total_sum
    
    category_df = pd.pivot_table(joined_df, values=ftypes.SpecialColumns.RCurrValue.get_col_name(), 
                                    index=[report_info.category_column.get_col_name()],
                                    aggfunc="sum", fill_value=0).copy()
    category_df[ftypes.SpecialColumns.RCatTotalPerc.get_col_name()] = category_df.apply(get_total_perc,axis=1)
    
    STOCKS_DF_SORT = [
        report_info.category_column.get_col_name(),
        REPORT_PORTFOLIO_SORT_ORDER_COLUMN,
        ftypes.SpecialColumns.RTicker.get_col_name(),
        ftypes.SpecialColumns.RExchange.get_col_name(),
    ]
    
    CATEGORY_DF_SORT = [
        report_info.category_column.get_col_name(),
    ]
    
    stocks_df = joined_df[[
        report_info.category_column.get_col_name(),
        REPORT_PORTFOLIO_COLUMN,
        REPORT_PORTFOLIO_SORT_ORDER_COLUMN,
        ftypes.SpecialColumns.DJoinAllBitMask.get_col_name(),
        ftypes.SpecialColumns.RExchange.get_col_name(),
        ftypes.SpecialColumns.RTicker.get_col_name(),
        ftypes.SpecialColumns.RCurrValue.get_col_name()]].copy()
    
    def get_cat_perc(row):
        cat = row[report_info.category_column.get_col_name()]
        val = row[ftypes.SpecialColumns.RCurrValue.get_col_name()]
        cat_val = category_df.loc[cat,ftypes.SpecialColumns.RCurrValue.get_col_name()]

        return val/cat_val


    stocks_df[ftypes.SpecialColumns.RCatPerc.get_col_name()] = stocks_df.apply(get_cat_perc,axis=1)
    stocks_df[ftypes.SpecialColumns.RTotalPerc.get_col_name()] = stocks_df.apply(get_total_perc,axis=1)

    #we need to filter out empty rows that don't correspond to our report type. For capgains, we don't want empty divi
    #portfolio rows, since there are so many and its distracting. For divi, vic versa.
    stocks_df = stocks_df[stocks_df.apply(report_info.stocks_row_filter,axis=1)]

    def get_cat_total_perc_for_df(row):
        cat = row[report_info.category_column.get_col_name()]
        cat_val = category_df.loc[cat][ftypes.SpecialColumns.RCurrValue.get_col_name()]

        return cat_val/total_sum

    # we feed the data back into the main df, as well, so that the data page has all the data
    joined_df[ftypes.SpecialColumns.RCatPerc.get_col_name()] = stocks_df[ftypes.SpecialColumns.RCatPerc.get_col_name()]
    joined_df[ftypes.SpecialColumns.RTotalPerc.get_col_name()] = stocks_df[ftypes.SpecialColumns.RTotalPerc.get_col_name()]
    joined_df[ftypes.SpecialColumns.RCatTotalPerc.get_col_name()] = joined_df.apply(get_cat_total_perc_for_df,axis=1)

    #this will convert the index containing the category to a regular column. We
    #do this so we can treat category_df just like stocks_df. Otherwise we 
    #have to do a lot of special things due to it having a custom index.
    category_df.reset_index(inplace=True) 

    stocks_df.sort_values(by=STOCKS_DF_SORT,inplace=True)

    stocks_df.drop(columns=[REPORT_PORTFOLIO_SORT_ORDER_COLUMN])

    category_df.sort_values(by=CATEGORY_DF_SORT,inplace=True)

    orig_stock_df_cols = list(stocks_df.columns)
    stocks_df.rename(columns=COL_TO_REPORT_NAME, inplace=True)
    orig_theme_df_cols = list(category_df.columns)
    category_df.rename(columns=COL_TO_REPORT_NAME, inplace=True)

    def add_reports(writer):
        add_df(stocks_df, report_info.stocks_ws_title, writer, native_currency_code, orig_cols=orig_stock_df_cols)
        add_df(category_df, report_info.cat_ws_title, writer, native_currency_code, orig_cols=orig_theme_df_cols)

    return add_reports


#TODO 2.5 get rid of pick priority. We will have different priorities based on whether a divi or cap gains report

PICK_TYPE_TO_REPORT_CAT_SHORT_NAME = { 
    ftypes.PickType.CapexBig5 : "Big5",
    ftypes.PickType.CapexClosed : "Closed",
    ftypes.PickType.CapexDiviPortfolio : "Income",
    ftypes.PickType.CapexTotalPortfolio : "CapGains",
    ftypes.PickType.CapexSkeletonPortfolio : "Skeleton",
}


def make_report_workbook(orig_joined_df : pd.DataFrame, holdings_df : pd.DataFrame, picks_df : pd.DataFrame, native_currency_code : str, 
                         rules_log : al.Log, output_file : str) -> pd.DataFrame:
    
    #PERF, this table is pretty large, but we don't want to go mucking with it here and then use it for something else later
    joined_df = orig_joined_df.copy()

    joined_df[ftypes.SpecialColumns.RTheme.get_col_name()] = joined_df[ftypes.SpecialColumns.RTheme.get_col_name()].fillna(NA_STR_NAME)
    joined_df[ftypes.SpecialColumns.RSector.get_col_name()] = joined_df[ftypes.SpecialColumns.RSector.get_col_name()].fillna(NA_STR_NAME)

    #make_portfolio_reports returns a function here because debugging while within a "with pd.ExcelWriter..." is a pain,
    #so we minimize the amount of code inside it
    add_capgains_reports_fn = make_portfolio_reports(PortfolioReportType.CapGains,joined_df,holdings_df,picks_df,native_currency_code)
    add_divi_reports_fn = make_portfolio_reports(PortfolioReportType.Divi,joined_df,holdings_df,picks_df,native_currency_code)
    
    # Export to Excel
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        add_capgains_reports_fn(writer)
        add_divi_reports_fn(writer)

        add_df(picks_df, PICK_WS_TITLE, writer, native_currency_code, always_use_generic_number_format=True)
        add_df(orig_joined_df, JOINED_DATA_WS_TITLE, writer, native_currency_code)
        






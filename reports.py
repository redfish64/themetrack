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

@dataclass
class PortfolioReportInfo:
    """Information used by reports for each type of report
    """
    category_column : ftypes.SpecialColumns
    pick_type_order_col : ftypes.SpecialColumns
    stocks_row_filter : Callable[[Any],bool]
    category_name : str #name of category in reports
    stocks_ws_title : str #title of stocks report worksheet
    cat_ws_title : str #title of category report worksheet
    pick_type_short_name_col : ftypes.SpecialColumns


#TODO 2.5 remove pick priority stuff, since pick priority now depends on the report 

def cap_gains_row_filter(row):
    """Shows all capgain and skeleton rows and any other row with a value attached. The idea here is that
    we want to show investments in non capex stocks, but we don't want to show rows for all the
    non-capex stock picks.
    """
    val = row[ftypes.SpecialColumns.RCurrValue.get_col_name()]
    if val != 0.0 and not pd.isna(val):
        return True

    bm = util.default_df_val(row[ftypes.SpecialColumns.DJoinAllBitMask.get_col_name()],0)
    return (
        ftypes.bit_mask_has_pick_type(bm,ftypes.PickType.CapexTotalPortfolio)
        or ftypes.bit_mask_has_pick_type(bm,ftypes.PickType.CapexSkeletonPortfolio)
    )

def divi_row_filter(row):
    """Shows all divi rows and any other row with a value attached. The idea here is that
    we want to show investments in non divi stocks, but we don't want to show rows for all the
    non-divi stock picks.
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
                                    stocks_row_filter=cap_gains_row_filter,
                                    pick_type_order_col=ftypes.SpecialColumns.DCapexGainsPickTypeOrder,
                                    category_name="Theme",
                                    stocks_ws_title="CapGains Stocks",
                                    cat_ws_title="CapGains Themes",
                                    pick_type_short_name_col=ftypes.SpecialColumns.DCapexGainsPickTypeShortDesc,
                                ),
                                PortfolioReportType.Divi : PortfolioReportInfo(
                                    category_column=ftypes.SpecialColumns.RSector,
                                    stocks_row_filter=divi_row_filter,
                                    pick_type_order_col=ftypes.SpecialColumns.DDiviPickTypeOrder,
                                    category_name="Sector",
                                    stocks_ws_title="Divi Stocks",
                                    cat_ws_title="Divi Themes",
                                    pick_type_short_name_col=ftypes.SpecialColumns.DDiviPickTypeShortDesc,
                                ),
                                }


header_font = Font(bold=True, italic=True)

def style_report_ws(ws):
    #Make header stylish
    for cell in ws[1]:
        cell.font = header_font

GENERIC_EXCEL_TYPE = ("@",generic_len)

def col_to_excel_type(col_name : str, native_currency_code : str):
    return ({
        ftypes.SpecialColumns.DCapexGainsPickTypeShortDesc : ("@",len),
        ftypes.SpecialColumns.DDiviPickTypeShortDesc : ("@",len),
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


def calc_max_len(format_code, value):
    # Extract prefix from the format code
    prefix_match = re.match(r'\"([^\"]+)\"', format_code)
    prefix = prefix_match.group(1) if prefix_match else ''

    # Check if the format is for percentage
    if re.match(r'0\.0+%', format_code):
        # Percentage format
        decimal_places = format_code.count('0') - 2
        formatted_value = f"{value * 100:.{decimal_places}f}%"
    elif re.match(r'\"\D*\"#,##0\.00', format_code):
        # Currency format with any prefix
        formatted_value = f"{prefix}{value:,.2f}"
    elif format_code == '@':
        # General text format
        formatted_value = str(value)
    else:
        # General numeric format
        decimal_places = format_code.count('0')
        formatted_value = f"{value:,.{decimal_places}f}"

        #TODO 3 this function isn't perfect, but it handles common formats. Otherwise it falls back to this generic clause where we add 2 for some slop
        return len(formatted_value) + 2 
    return len(formatted_value)

def update_number_formats(excel_formats,ws,num_rows,native_currency_code):
    """Updates the style of the cell according to the column type, so percentages look like %0.01,
        money looks like $1,000,000,000.00 etc.

        Also does a somewhat sloppy job of calcuating column width. Can't really do better without
        actually talking to excel

    Args:
        excel_formats (_type_): excel format for each row
        ws (_type_): worksheet to modify
        num_rows (_type_): number of rows to modify (after the header)
    """
    for (excel_format,col) in zip(excel_formats,ws.iter_cols()):
        max_len = len(col[0].value)
        for cell in col[1:num_rows+1]:
            cell.number_format = excel_format
            max_len = max(calc_max_len(excel_format, cell.value),max_len)

        adjusted_width = (max_len + 2) * 1.2
        ws.column_dimensions[col[0].column_letter].width = adjusted_width      



def make_portfolio_reports(config : ftypes.Config, report_config : ftypes.ReportConfig, joined_df : pd.DataFrame, holdings_df : pd.DataFrame, 
                           picks_df : pd.DataFrame, native_currency_code : str
                          ):

    total_sum = joined_df[ftypes.SpecialColumns.RCurrValue.get_col_name()].sum()

    def get_total_perc(row):
        val = row[ftypes.SpecialColumns.RCurrValue.get_col_name()]

        return val/total_sum
    
    category_df = pd.pivot_table(joined_df, values=ftypes.SpecialColumns.RCurrValue.get_col_name(), 
                                    index=[report_config.cat_column],
                                    aggfunc="sum", fill_value=0).copy()
    category_df[ftypes.SpecialColumns.RCatTotalPerc.get_col_name()] = category_df.apply(get_total_perc,axis=1)
    
    
    res_df = joined_df.copy()
    
    def get_cat_perc(row):
        cat = row[report_config.cat_column]
        val = row[ftypes.SpecialColumns.RCurrValue.get_col_name()]
        cat_val = category_df.loc[cat,ftypes.SpecialColumns.RCurrValue.get_col_name()]

        return val/cat_val


    res_df[ftypes.SpecialColumns.RCatPerc.get_col_name()] = res_df.apply(get_cat_perc,axis=1)
    res_df[ftypes.SpecialColumns.RTotalPerc.get_col_name()] = res_df.apply(get_total_perc,axis=1)

    def row_filter_fn(bitmask):
        def res_fn(row):
            val = row[ftypes.SpecialColumns.RCurrValue.get_col_name()]
            if val != 0.0 and not pd.isna(val):
                return True

            bm = util.default_df_val(row[ftypes.SpecialColumns.DJoinAllBitMask.get_col_name()],0)
            return (bm & bitmask) != 0
        
        return res_fn

    #we need to filter out empty rows that don't correspond to our report type. For capgains, we don't want empty divi
    #portfolio rows, since there are so many and its distracting. For divi, vic versa.
    res_df = res_df[res_df.apply(row_filter_fn(report_config.always_show_pick_bitmask),axis=1)]

    def get_cat_total_perc_for_df(row):
        cat = row[report_config.cat_column]
        cat_val = category_df.loc[cat][ftypes.SpecialColumns.RCurrValue.get_col_name()]

        return cat_val/total_sum

    # TODO 2.5 reenable this, using a different column per report or something...
    # we feed the data back into the main df, as well, so that the data page has all the data
    # joined_df[ftypes.SpecialColumns.RCatPerc.get_col_name()] = stocks_df[ftypes.SpecialColumns.RCatPerc.get_col_name()]
    # joined_df[ftypes.SpecialColumns.RTotalPerc.get_col_name()] = stocks_df[ftypes.SpecialColumns.RTotalPerc.get_col_name()]
    # joined_df[ftypes.SpecialColumns.RCatTotalPerc.get_col_name()] = joined_df.apply(get_cat_total_perc_for_df,axis=1)

    res_df.sort_values(by=report_config.column_order,inplace=True)

    res_df = res_df[[r[0] for r in report_config.columns]]

    res_df.rename(columns={ name : display_as for name,display_as,excel_format in report_config.columns}, inplace=True)

    def final_step_fn(writer):
        res_df.to_excel(writer, index=False, sheet_name=report_config.name)
        ws = writer.sheets[report_config.name]
        style_report_ws(ws)

        excel_formats = [r[2] for r in report_config.columns]
        update_number_formats(excel_formats,ws,res_df.shape[0],native_currency_code)

    return final_step_fn


def make_report_workbook(orig_joined_df : pd.DataFrame, holdings_df : pd.DataFrame, picks_df : pd.DataFrame, native_currency_code : str, 
                         rules_log : al.Log, config : ftypes.Config,output_file : str) -> pd.DataFrame:
    
    #PERF, this table is pretty large, but we don't want to go mucking with it here and then use it for something else later
    joined_df = orig_joined_df.copy()

    joined_df[ftypes.SpecialColumns.RTheme.get_col_name()] = joined_df[ftypes.SpecialColumns.RTheme.get_col_name()].fillna(NA_STR_NAME)
    joined_df[ftypes.SpecialColumns.RSector.get_col_name()] = joined_df[ftypes.SpecialColumns.RSector.get_col_name()].fillna(NA_STR_NAME)

    #make_portfolio_reports returns a function here because debugging while within a "with pd.ExcelWriter..." is a pain,
    #so we minimize the amount of code inside it
    report_writer_fn_list = [make_portfolio_reports(config, report_config, joined_df,holdings_df,picks_df,native_currency_code) for report_config in config.reports]
    
    # Export to Excel
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        for rw_fn in report_writer_fn_list:
            rw_fn(writer)

        def add_df(res_df, title, writer):
            res_df.to_excel(writer, index=False, sheet_name=title)
            ws = writer.sheets[title]
            style_report_ws(ws)

        add_df(holdings_df, HOLDINGS_WS_TITLE, writer)
        add_df(picks_df, PICK_WS_TITLE, writer)
        add_df(orig_joined_df, JOINED_DATA_WS_TITLE, writer)
        






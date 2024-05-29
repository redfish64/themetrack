from functools import partial
import pandas as pd
import ftypes
from openpyxl.styles import Font
import array_log as al

STOCKS_WS_TITLE = 'Securities Report'
THEMES_WS_TITLE = 'Themes Report'
HOLDINGS_WS_TITLE = 'Holdings Input Data'
PICK_WS_TITLE = 'Pick Input Data'
JOINED_DATA_WS_TITLE = 'Joined Data'
NA_THEME_NAME = '(none)'

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

def make_stock_report(df : pd.DataFrame, holdings_df : pd.DataFrame, picks_df : pd.DataFrame, native_currency_code : str, rules_log : al.Log, output_file : str) -> pd.DataFrame:
    COL_TO_REPORT_NAME = {
        ftypes.SpecialColumns.RCurrValue.get_col_name() : f"Value {native_currency_code}",
        ftypes.SpecialColumns.RExchange.get_col_name() : "Exchange",
        ftypes.SpecialColumns.RTicker.get_col_name() : "Ticker",
        ftypes.SpecialColumns.RTheme.get_col_name() : "Theme",
        ftypes.SpecialColumns.RThemePerc.get_col_name() : "% of Theme",
        ftypes.SpecialColumns.RTotalPerc.get_col_name() : "% of Total",
        ftypes.SpecialColumns.RThemeTotalPerc.get_col_name() : "% of Total",
    }

    COL_TO_EXCEL_TYPE = {
        ftypes.SpecialColumns.RCurrValue.get_col_name() : get_currency_format(native_currency_code),
        ftypes.SpecialColumns.RExchange.get_col_name() : ("@",len),
        ftypes.SpecialColumns.RTicker.get_col_name() : ("@",len),
        ftypes.SpecialColumns.RTheme.get_col_name() : ("@",len),
        ftypes.SpecialColumns.RThemePerc.get_col_name() : ("0.00%",partial(calc_num_len,1,2)),
        ftypes.SpecialColumns.RTotalPerc.get_col_name() : ("0.00%",partial(calc_num_len,1,2)),
        ftypes.SpecialColumns.RThemeTotalPerc.get_col_name() : ("0.00%",partial(calc_num_len,1,2)),
        ftypes.SpecialColumns.DRefreshedDate.get_col_name() : ("YYYY-MM-DD",lambda val: 4+3+3)
    }

    GENERIC_EXCEL_TYPE = ("@",generic_len)

    total_sum = df[ftypes.SpecialColumns.RCurrValue.get_col_name()].sum()

    def get_total_perc(row):
        val = row[ftypes.SpecialColumns.RCurrValue.get_col_name()]

        return val/total_sum

    df[ftypes.SpecialColumns.RTheme.get_col_name()] = df[ftypes.SpecialColumns.RTheme.get_col_name()].fillna(NA_THEME_NAME)

    themes_df = pd.pivot_table(df, values=ftypes.SpecialColumns.RCurrValue.get_col_name(), 
                                    index=[ftypes.SpecialColumns.RTheme.get_col_name()],
                                    aggfunc="sum", fill_value=0).copy()
    
    themes_df[ftypes.SpecialColumns.RThemeTotalPerc.get_col_name()] = themes_df.apply(get_total_perc,axis=1)
    
    STOCKS_DF_SORT = [
        ftypes.SpecialColumns.RTheme.get_col_name(),
        ftypes.SpecialColumns.RTicker.get_col_name(),
        ftypes.SpecialColumns.RExchange.get_col_name(),
    ]
    
    THEMES_DF_SORT = [
        ftypes.SpecialColumns.RTheme.get_col_name(),
    ]
    
    stocks_df = df[[
        ftypes.SpecialColumns.RTheme.get_col_name(),
        ftypes.SpecialColumns.RExchange.get_col_name(),
        ftypes.SpecialColumns.RTicker.get_col_name(),
        ftypes.SpecialColumns.RCurrValue.get_col_name()]].copy()
    
    def get_theme_perc(row):
        theme = row[ftypes.SpecialColumns.RTheme.get_col_name()]
        val = row[ftypes.SpecialColumns.RCurrValue.get_col_name()]
        theme_val = themes_df.loc[theme,ftypes.SpecialColumns.RCurrValue.get_col_name()]

        return val/theme_val


    stocks_df[ftypes.SpecialColumns.RThemePerc.get_col_name()] = stocks_df.apply(get_theme_perc,axis=1)
    stocks_df[ftypes.SpecialColumns.RTotalPerc.get_col_name()] = stocks_df.apply(get_total_perc,axis=1)

    def get_theme_total_perc_for_df(row):
        theme = row[ftypes.SpecialColumns.RTheme.get_col_name()]
        theme_val = themes_df.loc[theme][ftypes.SpecialColumns.RCurrValue.get_col_name()]

        return theme_val/total_sum

    # we feed the data back into the main df, as well, so that the data page has all the data
    df[ftypes.SpecialColumns.RThemePerc.get_col_name()] = stocks_df[ftypes.SpecialColumns.RThemePerc.get_col_name()]
    df[ftypes.SpecialColumns.RTotalPerc.get_col_name()] = stocks_df[ftypes.SpecialColumns.RTotalPerc.get_col_name()]
    df[ftypes.SpecialColumns.RThemeTotalPerc.get_col_name()] = df.apply(get_theme_total_perc_for_df,axis=1)

    def update_number_formats(orig_cols,ws,num_rows,always_use_generic=False):
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
            excel_type,max_len_fn = GENERIC_EXCEL_TYPE if always_use_generic else COL_TO_EXCEL_TYPE.get(oc, GENERIC_EXCEL_TYPE)
            max_len = len(col[0].value)
            for cell in col[1:num_rows+1]:
                cell.number_format = excel_type
                max_len = max(max_len_fn(cell.value),max_len)

            adjusted_width = (max_len + 2) * 1.2
            ws.column_dimensions[col[0].column_letter].width = adjusted_width      

    header_font = Font(bold=True, italic=True)

    def style_report_ws(ws):
        #Make header stylish
        for cell in ws[1]:
            cell.font = header_font


    # Export to Excel and make it purty
    with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
        #this will convert the index containing "Theme" to a regular column. We
        #do this so we can treat themes_df just like stocks_df. Otherwise we 
        #have to do a lot of special things.
        themes_df.reset_index(inplace=True) 

        stocks_df.sort_values(by=STOCKS_DF_SORT,inplace=True)
        themes_df.sort_values(by=THEMES_DF_SORT,inplace=True)

        orig_stock_df_cols = list(stocks_df.columns)
        stocks_df.rename(columns=COL_TO_REPORT_NAME, inplace=True)
        orig_theme_df_cols = list(themes_df.columns)
        themes_df.rename(columns=COL_TO_REPORT_NAME, inplace=True)

        def add_df(df,title,orig_cols=list(df.columns),always_use_generic_number_format=False):
            df.to_excel(writer, index=False, sheet_name=title)
            ws = writer.sheets[title]
            style_report_ws(ws)
            update_number_formats(orig_cols,ws,df.shape[0],always_use_generic=always_use_generic_number_format)

        add_df(stocks_df, STOCKS_WS_TITLE, orig_cols=orig_stock_df_cols)
        add_df(themes_df, THEMES_WS_TITLE, orig_cols=orig_theme_df_cols)
        add_df(holdings_df, HOLDINGS_WS_TITLE,always_use_generic_number_format=True)
        add_df(picks_df, PICK_WS_TITLE,always_use_generic_number_format=True)
        add_df(df, JOINED_DATA_WS_TITLE)

        






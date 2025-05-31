import re
import openpyxl as op
import util
import rules_parser
import util
import ftypes

OPTIONS_SHEETNAME = 'Options'
CUSTOM_RULES_SHEETNAME = 'Custom Rules'
SYSTEM_RULES_SHEETNAME = 'System Rules'


def trim_cols(data,end_col,start_col=0):
    def trim_it(row):
        return row[start_col:end_col]

    return map(trim_it, data)

def parse_option_group(fi,options_dict):
    data,at_eof,row_index = util.read_data(fi)

    used_options = {}

    def parse_option(name,rows,row_index):
        if(name not in options_dict):
            util.csv_error(row,row_index,0,f"No such option {name}")
        (required,fn) = options_dict[name]
        used_options[name] = True
        fn(rows,row_index)

    last_row_index = None
    last_name = None
    last_rows = None
    for data_ri,row in enumerate(data):
        if(row[0] == ''):
            if(last_name is not None):
                last_rows.append(row[1:])
        else:
            if(last_name is not None):
                parse_option(last_name,last_rows,last_row_index)
            last_name = row[0]
            last_rows = [row[1:]]
            last_row_index = row_index + data_ri

    parse_option(last_name,last_rows,last_row_index)

    for name,(required,fn) in options_dict.items():
        if(required and not used_options[name]):
            util.csv_error(data[0],row_index,0,"Option '{name}' is required but not present.") 

def parse_report_columns(rows,row_index):
    util.verify_header(row_index,rows[0][0:3],["Name","Display As","Excel Format"])

    cols = [(name,display_as,excel_format) for name,display_as,excel_format in trim_cols(rows[1:],3)]

    return cols

def parse_always_show_pick(rows,base_ri):
    total_bf = 0

    for row_ri,row in enumerate(rows):
        if(row[0] not in ftypes.SHORT_NAME_TO_PICK_TYPE):
            util.csv_error(row,base_ri + row_ri,1,f'Pick type must be one of {",".join(ftypes.SHORT_NAME_TO_PICK_TYPE.keys())}')
        bf = ftypes.PICK_TYPE_TO_BIT_FLAG[ftypes.SHORT_NAME_TO_PICK_TYPE[row[0]]]
        total_bf = (total_bf | bf)

    return total_bf


def parse_cat_report(fi):
    tr = ftypes.ReportConfig(name=None,columns=None,cat_column=None,column_order=None,sum_columns=[],always_show_pick_bitmask=0,is_cat_type=True)
    x = { 
        "Name" : (True,lambda rows,row_index : setattr(tr,'name',rows[0][0])),
        "Category" : (True,lambda rows,row_index : setattr(tr,'cat_column',rows[0][0])),
        "AlwaysShowPicks" : (True,lambda rows,row_index : setattr(tr,'always_show_pick_bitmask',parse_always_show_pick(rows,row_index))),
        "Columns" : (True,lambda rows,row_index : setattr(tr,'columns',parse_report_columns(rows,row_index))),
        "ColumnOrder" : (True,lambda rows,row_index : setattr(tr,'column_order',[r[0] for r in rows])),
        "SumColumns" : (False,lambda rows,row_index : setattr(tr,'sum_columns',[r[0] for r in rows])),
    }
    parse_option_group(fi,x)

    return tr

def parse_securities_report(fi):
    tr = ftypes.ReportConfig(name=None,columns=None,cat_column=None,column_order=None,sum_columns=[],always_show_pick_bitmask=0,is_cat_type=False)
    x = { 
        "Name" : (True,lambda rows,row_index : setattr(tr,'name',rows[0][0])),
        "Category" : (True,lambda rows,row_index : setattr(tr,'cat_column',rows[0][0])),
        "AlwaysShowPicks" : (True,lambda rows,row_index : setattr(tr,'always_show_pick_bitmask',parse_always_show_pick(rows,row_index))),
        "Columns" : (True,lambda rows,row_index : setattr(tr,'columns',parse_report_columns(rows,row_index))),
        "ColumnOrder" : (True,lambda rows,row_index : setattr(tr,'column_order',[r[0] for r in rows])),
        "SumColumns" : (False,lambda rows,row_index : setattr(tr,'sum_columns',[r[0] for r in rows])),
    }
    parse_option_group(fi,x)

    return tr


def parse_currency_formats(fi):
    (ri,header) = next(fi)

    util.verify_header(ri,header,["Types","Code","ExcelFormat"])
    data,at_eof,ri = util.read_data(fi)

    res = { code : excel_format for code,excel_format in trim_cols(data,3,1)}

    return res


def parse_options(options_csv_iter):
    fi = enumerate(util.extend_all_row_length(options_csv_iter,min_len=5))

    (ri,header) = next(fi)

    util.verify_header(ri,header,["Options",'','','','','Notes'])

    config = ftypes.Config(reports=[],currency=None,currency_formats=None)

    while(True):
        (ri,row) = util.skip_blank_lines(fi)

        if(row is None):
            break

        match(row[0]):
            case "ReportCurrency":
                config.currency = row[1]
            case "ThemeReport":
                config.reports.append(parse_cat_report(fi))
            case "SecuritiesReport":
                config.reports.append(parse_securities_report(fi))
            case "CurrencyFormat":
                config.currency_formats = parse_currency_formats(fi)

    def assert_option_present(val,name):
        if(val is None):
            util.error(f"{name} is required in Options file")

    assert_option_present(config.currency,"ReportCurrency")
    assert_option_present(config.currency_formats,"CurrencyFormat")

    def fix_special_vars_for_report(report : ftypes.ReportConfig):

        def replace_var(match):
            match match.group(1):
                case "ReportCurrency":
                    return config.currency
                case "CurrencyFormat":
                    return config.currency_formats[config.currency]
                case x:
                    util.error(f"Cannot understand variable ${{{x}}} in Options")

        def replace_vars(txt):
            ALL_VARS_PATTERN = re.compile(r'\$\{([a-zA-Z0-9 _-]+)\}')
            
            return ALL_VARS_PATTERN.sub(replace_var, txt)
        
        report.columns = [ (name,replace_vars(display_as),replace_vars(excel_format)) for name,display_as,excel_format in report.columns]

    for r in config.reports:
        fix_special_vars_for_report(r)

    return config


def parse_config_file(fp):
    wb = op.load_workbook(fp)
    system_rules = rules_parser.parse_override_file(util.read_standardized_csv(wb=wb,worksheet_name=SYSTEM_RULES_SHEETNAME), False)
    custom_rules = rules_parser.parse_override_file(util.read_standardized_csv(wb=wb,worksheet_name=CUSTOM_RULES_SHEETNAME), True)

    options_csv_iter = util.read_standardized_csv(wb=wb,worksheet_name=OPTIONS_SHEETNAME)

    config = parse_options(options_csv_iter)

    return config,custom_rules,system_rules    

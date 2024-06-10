import re
import openpyxl as op
from torch import fix_
import util
import rules_parser
import util
import ftypes

OPTIONS_SHEETNAME = 'Options'
CUSTOM_RULES_SHEETNAME = 'Custom Rules'


def trim_cols(data,end_col,start_col=0):
    def trim_it(row):
        return row[start_col:end_col]

    return map(trim_it, data)

def parse_report_columns(fi):
    (ri,header) = next(fi)

    util.verify_header(ri,header,["Columns","Name","Display As","Excel Format"])
    data,at_eof = util.read_data(fi)

    cols = { name : (display_as,excel_format) for name,display_as,excel_format in trim_cols(data,4,1)}

    return ftypes.ReportConfig(cols)

def parse_currency_formats(fi):
    (ri,header) = next(fi)

    util.verify_header(ri,header,["Types","Code","ExcelFormat"])
    data,at_eof = util.read_data(fi)

    res = { code : excel_format for code,excel_format in trim_cols(data,3,1)}

    return res


def parse_options(options_csv_iter):
    fi = enumerate(util.extend_all_row_length(options_csv_iter,min_len=5))

    (ri,header) = next(fi)

    util.verify_header(ri,header,["Options",'','','','','Notes'])

    config = ftypes.Config(None,None,None,None,None,None)

    while(True):
        (ri,row) = util.skip_blank_lines(fi)

        if(row is None):
            break

        match(row[0]):
            case "ReportCurrency":
                config.currency = row[1]
            case "CapexSecuritiesReport":
                config.capex_stocks_report = parse_report_columns(fi)
            case "CapexThemeReport":
                config.capex_theme_report = parse_report_columns(fi)
            case "DiviSecuritiesReport":
                config.divi_stocks_report = parse_report_columns(fi)
            case "DiviThemeReport":
                config.divi_theme_report = parse_report_columns(fi)
            case "CurrencyFormat":
                config.currency_format = parse_currency_formats(fi)

    def assert_option_present(val,name):
        if(val is None):
            util.error(f"{name} is required in Options file")

    assert_option_present(config.currency,"ReportCurrency")
    assert_option_present(config.capex_stocks_report,"CapexSecuritiesReport")
    assert_option_present(config.capex_theme_report,"CapexThemeReport")
    assert_option_present(config.divi_stocks_report,"DiviSecuritiesReport")
    assert_option_present(config.divi_theme_report,"DiviThemeReport")
    assert_option_present(config.currency_format,"CurrencyFormat")

    def fix_special_vars_for_report(report):

        def replace_var(match):
            match match.group(1):
                case "ReportCurrency":
                    return config.currency
                case "CurrencyFormat":
                    return config.currency_format[config.currency]
                case x:
                    util.error(f"Cannot understand variable ${{{x}}} in Options")

        def replace_vars(txt):
            ALL_VARS_PATTERN = re.compile(r'\$\{([a-zA-Z0-9 _-]+)\}')
            
            ALL_VARS_PATTERN.sub(replace_var, txt)

        for name,(display_as,excel_format) in report.columns.items():
            report.columns[name] = (replace_vars(display_as),replace_vars(excel_format))

    fix_special_vars_for_report(config.capex_stocks_report)
    fix_special_vars_for_report(config.capex_theme_report)
    fix_special_vars_for_report(config.divi_stocks_report)
    fix_special_vars_for_report(config.divi_theme_report)

    return config


def parse_config_file(fp):
    wb = op.load_workbook(fp)
    custom_rules = util.read_standardized_csv(wb=wb,worksheet_name=CUSTOM_RULES_SHEETNAME)
    custom_rules = rules_parser.parse_override_file(custom_rules)

    options_csv_iter = util.read_standardized_csv(wb=wb,worksheet_name=OPTIONS_SHEETNAME)

    config = parse_options(options_csv_iter)

    return config,custom_rules    

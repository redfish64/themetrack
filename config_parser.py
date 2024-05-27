import openpyxl as op
import util
import rules_parser

OPTIONS_SHEETNAME = 'Options'
CUSTOM_RULES_SHEETNAME = 'Custom Rules'

class Config:
    def __init__(self) -> None:
        self.currency = "USD"

def parse_config_file(fp):
    wb = op.load_workbook(fp)
    custom_rules = util.read_standardized_csv(wb=wb,worksheet_name=CUSTOM_RULES_SHEETNAME)
    custom_rules = rules_parser.parse_override_file(custom_rules)

    #TODO 1.5 parse config
    return Config(),custom_rules    

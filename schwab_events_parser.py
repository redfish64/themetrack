"""Parses an override excel or csv file
"""
import datetime
import sys

import util
from util import skip_blank_lines,verify_header,read_data

import ftypes
import re
import pandas as pd

SCHWAB_HEADERS = ['Date','Action','Symbol','Description','Quantity','Price','Fees & Comm','Amount']

SCHWAB_NUMERIC_HEADERS = ['Quantity','Price','Fees & Comm','Amount']

def extract_last_3_account_chars(filename):
    # Match the pattern between 'Individual_' and '_Transactions'
    match = re.search(r'Individual_XXX(.*?)_Transactions', filename)
    if match:
        account = match.group(1)
        return account[-3:]  # Return the last 3 characters
    else:
        return None



def parse_file(fp : str):
    acct_last3 = extract_last_3_account_chars(fp)

    fi = enumerate(util.extend_all_row_length(util.read_standardized_csv(fp),min_len=9))
    (ri,row) = next(fi)
    verify_header(ri,row,SCHWAB_HEADERS)

    all_rows = []
    while(True):
        (ri,row) = skip_blank_lines(fi)

        #at EOF
        if(row is None):
            break

        acct_name = row[0]
        (ri,row) = next(fi)

        (curr_table_rows,at_eof,ri) = read_data(fi)

        all_rows += curr_table_rows[0:-2]

        if(at_eof):
            break

    headers = SCHWAB_HEADERS+[ftypes.SpecialColumns.DAcctName.get_col_name()]

    res =  pd.DataFrame(all_rows,columns=headers)

    #schwab uses 'N/A' for some securities sometimes, so we replace it with None
    res[SCHWAB_NUMERIC_HEADERS] = res[SCHWAB_NUMERIC_HEADERS].replace('N/A', None)
    res[ftypes.SpecialColumns.DBrokerage.get_col_name()] = ftypes.BrokerageTypes.Schwab.name

    return res

if __name__ == '__main__':
    df = parse_file(sys.argv[1])

    print(df.to_csv())

"""Parses an override excel or csv file
"""
import datetime
import sys

import util
from util import skip_blank_lines,verify_header,read_data

import ftypes
import re
import pandas as pd

SCHWAB_HEADERS = ("Symbol,Description,Quantity,Price,Price Change %,Price Change $,Market Value,Day Change %,Day Change $,Cost Basis"
                 ",Gain/Loss %,Gain/Loss $,Ratings,Reinvest Dividends?,Capital Gains?,% Of Account,Security Type").split(",")

SCHWAB_NUMERIC_HEADERS = ['Quantity', 'Price', 'Price Change %',
       'Price Change $', 'Market Value', 'Day Change %', 'Day Change $',
       'Cost Basis', 'Gain/Loss %', 'Gain/Loss $', '% Of Account']




def parse_file(fp : str):
    fi = enumerate(util.extend_all_row_length(util.read_standardized_csv(fp),min_len=17))
    (ri,row) = next(fi)

    #first parse the date
    #Positions for CUSTACCS as of 02:07 AM ET, 04/03/2024
    (mm,dd,yyyy) = util.csv_assert_match(r'Positions for .*? as of .*, (\d\d)/(\d\d)/(\d\d\d\d)$', ri,0,row,"Can't parse date on first row")


    all_rows = []
    while(True):
        (ri,row) = skip_blank_lines(fi)

        #at EOF
        if(row is None):
            break

        acct_name = row[0]
        (ri,row) = next(fi)

        verify_header(ri,row,SCHWAB_HEADERS)

        (curr_table_rows,at_eof) = read_data(fi,acct_name)

        util.csv_assert(curr_table_rows[-2][0] == 'Cash & Cash Investments',row,ri-2,0,util.ErrorType.Error,"Table second to last row must be 'Cash & Cash Investments'")
        util.csv_assert(curr_table_rows[-1][0] == 'Account Total',row,ri-1,0,util.ErrorType.Error,"Table must end with 'Account Total'")

        all_rows += curr_table_rows[0:-2]

        if(at_eof):
            break

    headers = SCHWAB_HEADERS+[ftypes.SpecialColumns.DAcctName.get_col_name()]

    res =  pd.DataFrame(all_rows,columns=headers)

    #schwab uses 'N/A' for some securities sometimes, so we replace it with None
    res[SCHWAB_NUMERIC_HEADERS] = res[SCHWAB_NUMERIC_HEADERS].replace('N/A', None)
    res[ftypes.SpecialColumns.DBrokerage.get_col_name()] = ftypes.BrokerageTypes.Schwab.name
    res[ftypes.SpecialColumns.DRefreshedDate.get_col_name()] = datetime.date(int(yyyy),int(mm),int(dd))

    return res

#TODO 2 show cash
#TODO 2 show brokerage and allow user to specify fields of each report

if __name__ == '__main__':
    df = parse_file(sys.argv[1])

    print(df.to_csv())

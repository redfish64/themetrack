"""Parses an override excel or csv file
"""
import datetime
import sys

import util
from util import skip_blank_lines,verify_header,read_data

import ftypes
import re
import pandas as pd
from date_registry import DateRegistry

dr = DateRegistry()


dr.register("headers",None,['Symbol', 'Description', 'Qty (Quantity)', 'Price', 'Price Chng % (Price Change %)', 'Price Chng $ (Price Change $)', 
                  'Mkt Val (Market Value)', 'Day Chng % (Day Change %)', 'Day Chng $ (Day Change $)', 'Cost Basis', 'Gain % (Gain/Loss %)',
                  'Gain $ (Gain/Loss $)', 'Ratings', 'Reinvest?', 'Reinvest Capital Gains?', '% of Acct (% of Account)', 'Security Type']
)
dr.register("headers","2025-05-07",['Symbol', 'Description', 'Qty (Quantity)', 'Price', 'Price Chng $ (Price Change $)', 'Price Chng % (Price Change %)', 'Mkt Val (Market Value)', 'Day Chng $ (Day Change $)',
                  'Day Chng % (Day Change %)', 'Cost Basis', 'Gain $ (Gain/Loss $)', 'Gain % (Gain/Loss %)', 'Ratings', 'Reinvest?', 'Reinvest Capital Gains?', '% of Acct (% of Account)', 'Security Type']
)

dr.register("numeric_headers",None,['Qty (Quantity)', 'Price', 'Price Chng % (Price Change %)', 'Price Chng $ (Price Change $)', 
                  'Mkt Val (Market Value)', 'Day Chng % (Day Change %)', 'Day Chng $ (Day Change $)', 'Cost Basis', 'Gain % (Gain/Loss %)',
                  'Gain $ (Gain/Loss $)', '% of Acct (% of Account)']
)
dr.register("numeric_headers","2025-05-07",['Qty (Quantity)', 'Price', 'Price Chng % (Price Change %)', 'Price Chng $ (Price Change $)',
                  'Mkt Val (Market Value)', 'Day Chng % (Day Change %)', 'Day Chng $ (Day Change $)', 'Cost Basis', 'Gain % (Gain/Loss %)',
                  'Gain $ (Gain/Loss $)', '% of Acct (% of Account)'])


def parse_file_v1(fp : str):
    subdir_datestr = extract_subdir_datestr_for_file(fp)

    schwab_headers = dr.get("headers",subdir_datestr)
    schwab_numeric_headers = dr.get("numeric_headers",subdir_datestr)

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

        verify_header(ri,row,schwab_headers)

        (curr_table_rows,at_eof,ri) = read_data(fi,acct_name)

        util.csv_assert(curr_table_rows[-2][0] == 'Cash & Cash Investments',row,ri-2,0,util.ErrorType.Error,"Table second to last row must be 'Cash & Cash Investments'")
        util.csv_assert(curr_table_rows[-1][0] == 'Account Total',row,ri-1,0,util.ErrorType.Error,"Table must end with 'Account Total'")

        all_rows += curr_table_rows[0:-2]

        if(at_eof):
            break

    headers = schwab_headers+[ftypes.SpecialColumns.DAcctName.get_col_name()]

    res =  pd.DataFrame(all_rows,columns=headers)

    #schwab uses 'N/A' for some securities sometimes, so we replace it with None
    res[schwab_headers] = res[schwab_numeric_headers].replace('N/A', None)
    res[ftypes.SpecialColumns.DBrokerage.get_col_name()] = ftypes.BrokerageTypes.Schwab.name
    res[ftypes.SpecialColumns.DRefreshedDate.get_col_name()] = datetime.date(int(yyyy),int(mm),int(dd))

    return res

dr.register("parse_file",None,parse_file_v1)

def parse_file(fp):
    return dr.run("parse_file",util.extract_subdir_date_from_filepath(fp), fp)

#TODO 2 show cash
#TODO 2 show brokerage and allow user to specify fields of each report

if __name__ == '__main__':
    df = parse_file(sys.argv[1])

    print(df.to_csv())

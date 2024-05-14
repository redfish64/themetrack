"""Parses an override excel or csv file
"""
import datetime
import sys

import util
import ftypes
import re
import pandas as pd

SCHWAB_HEADERS = ("Symbol,Description,Quantity,Price,Price Change %,Price Change $,Market Value,Day Change %,Day Change $,Cost Basis"
                 ",Gain/Loss %,Gain/Loss $,Ratings,Reinvest Dividends?,Capital Gains?,% Of Account,Security Type").split(",")
def parse_file(fp : str):
    fi = enumerate(util.read_standardized_csv(fp,min_row_len=17))
    (ri,row) = next(fi)

    #first parse the date
    #Positions for CUSTACCS as of 02:07 AM ET, 04/03/2024
    (mm,dd,yyyy) = util.csv_assert_match(r'Positions for .*? as of .*, (\d\d)/(\d\d)/(\d\d\d\d)$', ri,0,row,"Can't parse date on first row")

    def skip_blank_lines(ri_row_enum) -> tuple[int, str]:
        """Will skip blanks rows until it finds one that has data. Any element that consists of empty string ('') is considered blank

        Args:
            ri_row_enum (iter[int,str]): an enum of tuples containing (row_index,row)

        Returns:
            (int,list[str]): (row_index,row) of first non-empty row, or (row_index,None) of final line, if reached EOF
        """
        row_index = 0

        for row_index, row in ri_row_enum:
            # Check if the row is non-empty (contains at least one non-empty string)
            if any(cell != '' for cell in row):
                return (row_index, row)
        
        # If no non-empty row was found, return last index with None
        return (row_index, None)

    def verify_header(ri,row : list[str],headers : list[str]):
        """Verifies that row matches the given header names or errors out
        """
        if(len(row) < len(headers) or row[0:len(headers)] != headers):
            util.csv_error(row,ri,len(row),f"Row doesn't match header, {','.join(headers)}")

    def read_data(ri_row_enum,*extra_constant_values):
        """reads a row from the enum. If it is not completely blank, and not at EOF, adds it to a list. 
           On blank, EOF, returns the resulting list. extra_constant_values are appended to every row 

        Args:
           ri_row_enum (_type_): an enum of tuples containing (row_index,row)

        Returns:
            _type_: Resulting list of data
        """
        row_index = 0

        data_list = []

        extra_constant_values = list(extra_constant_values)

        for row_index, row in ri_row_enum:
            # Check if the row is non-empty (contains at least one non-empty string)
            if all(cell == '' for cell in row):
                return (data_list,False)
            
            data_list.append(row + extra_constant_values)

        return (data_list,True)


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

    headers = SCHWAB_HEADERS+[ftypes.SpecialColumns.AcctName.get_col_name()]

    res =  pd.DataFrame(all_rows,columns=headers)

    res[ftypes.SpecialColumns.Brokerage.get_col_name()] = ftypes.BrokerageTypes.Schwab.name
    res[ftypes.SpecialColumns.RefreshedDate.get_col_name()] = datetime.date(int(yyyy),int(mm),int(dd))


if __name__ == '__main__':
    df = parse_file(sys.argv[1])

    print(df.to_csv())

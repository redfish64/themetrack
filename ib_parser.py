import argparse
import csv
from enum import Enum, auto
from util import error,warn,csv_assert,csv_error,csv_warning,ErrorType
import pandas as pd
import ftypes

class Table():
    def __init__(self,name,fields) -> None:
        self.name = name
        self.fields = fields
        self.rows = []

    def create_dataframe(self):
        def extend_or_truncate_list_to_length(lst_orig, length_wanted, fill_value=None):
            lst = lst_orig.copy()

            l = len(lst)
            if(l >= length_wanted):
                return lst[0:length_wanted]
            
            lst += [fill_value] * (length_wanted - l)

            return lst

        #convert the rows to columns        
        flen = len(self.fields)
        columns = [[] for x in range(0,flen)]
        for r in self.rows:
            r = extend_or_truncate_list_to_length(r,flen)
            for col,cell in zip(columns,r):
                col.append(cell)

        d = dict(zip(self.fields,columns))

        res = pd.DataFrame(d)

        res['D:TableType'] = self.name

        return res


def generic_parse(file):
    class IBRowType(Enum):
        Header = auto()
        Data = auto()
        SubTotal = auto()
        Total = auto()
        Notes = auto()
        MetaInfo = auto()

    class IBTableName(Enum):
        Disclosure = auto()

    tables = {}

    with open(file, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.reader(csvfile)

        def remove_blank_trailing_cells(row : list):
            while(row[-1] == ''):
                row.pop()

        for (row_index,row) in enumerate(reader):
            remove_blank_trailing_cells(row)
            table_name = row[0]
            row_type = row[1]
            
            if(table_name == IBTableName.Disclosure.name):
                pass
            elif(row_type == IBRowType.Header.name):
                fields = row[2:]
                t = Table(table_name,fields)

                
                if(table_name in tables):
                    #co: this is a common occurrence, no need to worry.
                    #csv_warning(row,row_index,0,"Table specified twice, both will be parsed")
                    pass
                else:
                    tables[table_name] = []

                tables[table_name].append(t)
            elif(row_type == IBRowType.Data.name):
                data = row[2:]
                table = tables[table_name][-1]
                if(len(fields) < len(data)):
                    csv_warning(row,row_index,None,"Number of fields is less than number of data values, ignoring extras")
                    while(len(data) < len(fields)):
                        data.append('')

                table.rows.append(data)
            elif(row_type == IBRowType.SubTotal.name):
                pass
            elif(row_type == IBRowType.Total.name):
                pass
            elif(row_type == IBRowType.Notes.name):
                pass
            elif(row_type == IBRowType.MetaInfo.name):
                pass
            elif(row_type == ''):
                pass
            else:
                csv_error(row,row_index,0,"Unrecognized row type")                

    return tables

def parse_holding_activity_and_trades(file):
    def join_dataframes(df1, df2, key, how='inner'):
        # Check for duplicates in both dataframes
        if df1[key].duplicated().any() or df2[key].duplicated().any():
            error(f"Duplicate keys found, {df1[key].duplicated() + df2[key].duplicated()}. Join requires unique keys in both dataframes.")
        
        # Perform the join
        return pd.merge(df1, df2, on=key, how=how)

    def create_dataframe_from_tables(tables_dict,table_name,required=True):
        if(not required and table_name not in tables_dict):
            return pd.DataFrame()
        tables_list = tables_dict[table_name]
        return pd.concat([x.create_dataframe() for x in tables_list])
    
    def remove_totals_in_data(df):
        if('Currency' in df):
            return df[~df['Currency'].str.startswith('Total')]
        return df

    #co: can be done in config
    # def break_out_stock_and_isin(df, column_name):
    #     df['Symbol'] = df[column_name].str.extract(r'^([^\(]+)\(')
    #     df['ISIN'] = df[column_name].str.extract(r'\(([^\)]+)\)')

    tables = generic_parse(file)

    op = create_dataframe_from_tables(tables,'Open Positions')
    fii = create_dataframe_from_tables(tables,'Financial Instrument Information')
    trades = create_dataframe_from_tables(tables,'Trades')
    dividends = remove_totals_in_data(create_dataframe_from_tables(tables,'Dividends',required=False)) # this is dividends before tax
    witholding_tax = remove_totals_in_data(create_dataframe_from_tables(tables,'Withholding Tax',required=False))
    fees = create_dataframe_from_tables(tables,'Fees',required=False)

    corp_act = create_dataframe_from_tables(tables,'Corporate Actions',required=False)
    fii.rename(columns={'Code':'FFICode'},inplace=True)

    #join open positions and ffi so we get more information on each stock owned
    holdings_res = pd.merge(op, fii, on=['Asset Category','Symbol'], how='inner',validate='1:1')
    holdings_res[ftypes.SpecialColumns.DBrokerage.get_col_name()] = ftypes.BrokerageTypes.InteractiveBrokers.name

    #join dividends, witholding_tax, and fees
    events_res = pd.concat([trades,dividends,witholding_tax,fees],ignore_index=True)
    events_res[ftypes.SpecialColumns.DBrokerage.get_col_name()] = ftypes.BrokerageTypes.InteractiveBrokers.name


    file_attrs = tables['Statement'][0].rows

    for name,val in file_attrs:
        holdings_res[name] = val

    return holdings_res,events_res

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        usage="%(prog)s [ib holding activity]...",
        description="parses and prints out stuff",
        exit_on_error=True,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("file", help="ib holdings activity file")

    conf = parser.parse_args()

    holdings_res,events_res = parse_holding_activity_and_trades(conf.file)

    print(holdings_res.to_csv())
    print(events_res.to_csv())




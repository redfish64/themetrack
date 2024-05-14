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

        return pd.DataFrame(d)


def generic_parse(file):
    class IBRowType(Enum):
        Header = auto()
        Data = auto()
        Total = auto()
        Notes = auto()

    tables = {}

    with open(file, newline='') as csvfile:
        reader = csv.reader(csvfile)

        def remove_blank_trailing_cells(row : list):
            while(row[-1] == ''):
                row.pop()

        for (row_index,row) in enumerate(reader):
            remove_blank_trailing_cells(row)
            table_name = row[0]
            row_type = row[1]
            
            if(row_type == IBRowType.Header.name):
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
            elif(row_type == IBRowType.Total.name):
                pass
            elif(row_type == IBRowType.Notes.name):
                pass
            else:
                csv_error(row,row_index,0,"Unrecognized row type")                

    return tables

def parse_holding_activity(file):
    def join_dataframes(df1, df2, key, how='inner'):
        # Check for duplicates in both dataframes
        if df1[key].duplicated().any() or df2[key].duplicated().any():
            error(f"Duplicate keys found, {df1[key].duplicated() + df2[key].duplicated()}. Join requires unique keys in both dataframes.")
        
        # Perform the join
        return pd.merge(df1, df2, on=key, how=how)

    def create_dataframe_from_tables(tables_dict,table_name):
        tables_list = tables_dict[table_name]
        return pd.concat([x.create_dataframe() for x in tables_list])


    tables = generic_parse(file)

    op = create_dataframe_from_tables(tables,'Open Positions')
    fii = create_dataframe_from_tables(tables,'Financial Instrument Information')
    fii.rename(columns={'Code':'FFICode'},inplace=True)

    #join open positions and ffi so we get more information on each stock owned
    res = pd.merge(op, fii, on=['Asset Category','Symbol'], how='inner',validate='1:1')

    res[ftypes.SpecialColumns.Brokerage.get_col_name()] = ftypes.BrokerageTypes.InteractiveBrokers.name

    file_attrs = tables['Statement'][0].rows

    for name,val in file_attrs:
        res[name] = val

    return res

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        usage="%(prog)s [ib holding activity]...",
        description="parses and prints out stuff",
        exit_on_error=True,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    parser.add_argument("file", help="ib holdings activity file")

    conf = parser.parse_args()

    res = parse_holding_activity(conf.file)

    print(res.to_csv())




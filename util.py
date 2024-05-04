import logging
import os
from enum import Enum, auto
import openpyxl as op


def get_code_file_path(file):
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Build the path to the file
    return os.path.join(script_dir, file)



class ErrorType(Enum):
    Warning = auto()
    Error = auto()

def system_msg(err_type,msg):
    if(err_type == ErrorType.Error):
        logging.error(msg)
        raise Exception(msg)
    elif(err_type == ErrorType.Warning):
        logging.warn(msg)

def error(msg):
    system_msg(ErrorType.Error,msg)

def warn(msg):
    system_msg(ErrorType.Warning,msg)

def csv_msg(row,row_index,col_index,err_type,desc):
    def adj_row_col(f):
        return f+1 if f is not None else "(none)"
    row_str = ",".join(row)
    system_msg(err_type,f"Row {adj_row_col(row_index)}, Col {adj_row_col(col_index)}: {desc} -- {row_str}")

def csv_assert(cond,row,row_index,col_index,err_type,desc):
    if(not cond):
        csv_msg(row,row_index,col_index,err_type,desc)

def csv_error(row,row_index,col_index,desc):
    csv_msg(row,row_index,col_index,ErrorType.Error,desc)
 
def csv_warning(row,row_index,col_index,desc):
    csv_msg(row,row_index,col_index,ErrorType.Warning,desc)
 
def csv_cell_standardize(c : str):
    """Converts None to '' and removes leading and trailing whitespace from strings
    """
    if(c is None):
        return ''
    return c.strip()

def read_standardized_csv(fp : str,min_row_len=0,worksheet_number=0):
    """Regardless of whether an excel spreadsheet or a csv, reads it like a csv file.
       Trims left and right whitespace of all cells.

       Args:
          min_row_len - specifies a minimum length for each row. Any row that is shorter
             than this will have cells containing '' appended to meet this minimum.
    """
    def extend_array_to_min_length(arr, min_len):
        # Calculate how many items need to be added
        additional_items = max(0, min_len - len(arr))
        
        # Extend the array with empty strings if needed
        arr.extend([""] * additional_items)
        
        return arr
    
    def remove_trailing_empty_cells(r):
        for i in range(len(r)-1,0,-1):
            c = csv_cell_standardize(r[i])
            if(c != ''):
                return list(r[0:i+1])
        return []
    
    def clean_csv_row(r):
        r = remove_trailing_empty_cells(r)
        r = [csv_cell_standardize(c) for c in r]
        r = extend_array_to_min_length(r,min_row_len)

        return r
        
    if(fp.endswith(".xlsx")):
        wb = op.load_workbook(fp)
        ws = wb.worksheets[worksheet_number]
        data = list(ws.iter_rows(values_only=True))
    elif(fp.endswith(".csv")):
        data = open(fp).read()
    else:
        error(f"don't know how to read {fp}")
    
    return map(clean_csv_row,data)

def enum_contains_name(enum_type, name):
    try:
        enum_type[name]
    except KeyError:
        return False
    return True

def csv_convert_to_enum(enum_obj : Enum, row, col_index, row_index):
    val = row[col_index]
    try:
        return enum_obj[val]
    except KeyError:
        csv_error(row,row_index,col_index,f"{val} not found in enum f{enum_obj.__name__}, values {", ".join([m.name for m in enum_obj])}")
        

import csv
from functools import partial
import logging
import os
from enum import Enum, auto
import re
import openpyxl as op
import pandas as pd
import sys


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

def csv_assert_match(regex, row_index, col_index, row, message):
    """Parses a cell using given regex. If doesn't match, errors out. Returns m.groups()
    """
    m = re.match(regex,row[col_index])
    if(m is None):
        csv_error(row,row_index,row_index,f"Can't match {regex}: {message}")

    return m.groups()

def csv_cell_standardize(c : str):
    """Converts None to '' and removes leading and trailing whitespace from strings
    """
    if(c is None):
        return ''
    
    return str(c).strip()

def extend_array_to_min_length(min_len,arr):
    # Calculate how many items need to be added
    additional_items = max(0, min_len - len(arr))
    
    # Extend the array with empty strings if needed
    arr.extend([""] * additional_items)
    
    return arr

def extend_all_row_length(fi,min_len):
    """Extends the row length of all csv rows to given min length by adding [""] to them

    Args:
        fi: iteration of arrays of strings

    Returns:
        iteration of arrays of strings
    """
    return map(partial(extend_array_to_min_length,min_len),fi)


def read_standardized_csv(fp : str = None,wb = None, worksheet_name=None):
    """Regardless of whether an excel spreadsheet or a csv, reads it like a csv file.
       Trims left and right whitespace of all cells.

       Args:
          fp - file path. Either fp or wb must be specified
          wb - excel workbook
          worksheet_name - if reading from a workbook, then the worksheet number to read.
                           Default is the first page

    """
    def remove_trailing_empty_cells(r):
        for i in range(len(r)-1,-1,-1):
            c = csv_cell_standardize(r[i])
            if(c != ''):
                return list(r[0:i+1])
        return []
    
    def clean_csv_row(r):
        r = remove_trailing_empty_cells(r)
        r = [csv_cell_standardize(c) for c in r]

        return r
        
    if(wb is not None or fp.endswith(".xlsx")):
        if(wb is None):
            wb = op.load_workbook(fp)
        if(worksheet_name is not None):
            ws = wb[worksheet_name]
        else:
            ws = wb.worksheets[0]
        data = list(ws.iter_rows(values_only=True))
    elif(fp.endswith(".csv")):
        fh = open(fp, newline='')
        data = csv.reader(fh)
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
        csv_error(row,row_index,col_index,f'{val} not found in enum f{enum_obj.__name__}, values {", ".join([m.name for m in enum_obj])}')
        
def get_df_row_val(row,name):
    try:
        v = row[name]
    except KeyError:
        return None
    
    if(pd.isna(v)):
        v = None

    return v

def get_installation_directory():
    """Returns the path of the directory of the program. This should even work if using pyinstaller
    TODO 2 test pyinstaller

    Returns:
        str: path
    """
    if hasattr(sys, '_MEIPASS'):
        return sys._MEIPASS
    return os.path.dirname(os.path.abspath(__file__))

def default_df_val(v,default_v):
    if(pd.isna(v)):
        return default_v
    return v


def filter_nan_from_dict(d):
    return {k: v for k, v in d.items() if not pd.isna(v)}
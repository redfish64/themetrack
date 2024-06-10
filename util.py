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
        Returns:
          iteration of lists where each list is a row
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

def row_matches(r1,r2):
    """Returns true if rows match. If one row is longer than the other, then items in the longer
       row will be matched against ''.
    """
    m = max(len(r1),len(r2))
    for i in range(0,m):
        c1 = r1[i] if i < len(r1) else ''
        c2 = r2[i] if i < len(r2) else ''
        if(c1 == c2):
            continue

        return False
    return True

def csv_assert_row_matches(row_index, row, match_row):
    """Matches row against match_row. If doesn't match, errors out
    """
    if(row_matches(row,match_row)):
        return
    
    csv_error(row,row_index,0,f"Must match {match_row}")

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
        csv_error(row,ri,len(row),f"Row doesn't match header, {','.join(headers)}")

def read_data(ri_row_enum,*extra_constant_values):
    """reads rows from the enum util the next row is completely blank, or at EOF.  
    Returns the resulting list. extra_constant_values are appended to every row 

    Args:
        ri_row_enum (_type_): an enum of tuples containing (row_index,row)

    Returns:
        list,bool: Resulting list of data and a boolean indicating if at EOF
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


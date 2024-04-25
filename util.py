import logging
import os
from enum import Enum, auto

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
 

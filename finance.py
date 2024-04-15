import os
from enum import Enum, auto
import argparse
import re
import sys
import util
import csvfsm
import pdb



def warning(str):
    print(str, file=sys.stderr)


def error(str):
    print(str, file=sys.stderr)
    raise Exception('Error',str)

def get_files_with_ext(directory):
    """Returns all files ending in given extension"""
    files = []
    
    for item in os.listdir(directory):
        item_path = os.path.join(directory, item)
        if os.path.isfile(item_path) and item_path.lower().endswith(".csv"):
            files.append(item_path)

    return files

def get_template_path(template_name):
    util.get_code_file_path(template_name)


parser = argparse.ArgumentParser(
    usage="%(prog)s [options] [directory of financial files]...",
    description="joins holdings files with recommendation files for analysis in a spreadsheet",
    exit_on_error=True,
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
parser.add_argument("finance_dir", help="directory containing financial files")

config = parser.parse_args()

csv_file_paths = get_files_with_ext(config.finance_dir)

FILE_PATH_FSM = "file_path.fsm"

file_path_template = csvfsm.read_template(get_template_path(FILE_PATH_FSM))

books = core.new_books()

for csv_fp in csv_file_paths:
    fp_data = csvfsm.parse_data(file_path_template,csv_fp)
 
    template_filename = get_template_filename_from_fp_data(fp_data)
    file_data_template = csvfsm.read_template(get_template_path(template_filename))

    file_data = csvfsm.parse_datafile(file_data_template,csv_fp)

    interpret_data(books,fp_data,file_data)

printer.print_books(books)


# def verify_fields(fields, *expected_fields):
#     if fields == expected_fields:
#         return
#     pdb.set_trace()
    
#     # Find missing or unexpected fields
#     missing_fields = set(expected_fields) - set(fields)
#     unexpected_fields = set(fields) - set(expected_fields)

#     errs = []
#     if missing_fields:
#         errs.append(f"Missing fields:{missing_fields}")
#     if unexpected_fields:
#         errs.append(f"Unexpected fields:{unexpected_fields}")

#     error("Fields don't match expected: "+(",".join(errs)))
    
# def read_big5(fn):
#     with open(fn, newline='') as csvfile:
#         r = csv.DictReader(csvfile)
#         h = r.next()

#         verify_fields(h,"Issue","Date","Theme","Name","Ticker")

#         return list(r)
    

# def get_data_maps(d):
#     capex_rows = []
#     holdings = []

#     for fn in os.listdir(d):
#         file_path = os.path.join(d, fn)
#         if not os.path.isfile(file_path):
#             continue
#         ft = get_filetype(fn)
#         if ft is None:
#             warning(f"Cannot determine type of file for {file_path}, ignoring"
#                     "...")
#             continue

#         if ft == FileCategory.Capex_Big5:
#             capex_rows = capex_rows + read_big5(file_path)
#         elif ft == FileCategory.Capex_ClosedPos:
#             capex_rows = capex_rows + read_closed_pos(file_path)
#         elif ft == FileCategory.Capex_CapGains:
#             capex_rows = capex_rows + read_cap_gains(file_path)
#         elif ft == FileCategory.Capex_IncPort:
#             capex_rows = capex_rows + read_inc_port(file_path)
#         elif ft == FileCategory.Capex_SkelPort:
#             capex_rows = capex_rows + read_skel_port(file_path)
#         elif ft == FileCategory.TDAmer:
#             holdings = holdings + read_tdamer(file_path)
#         elif ft == FileCategory.Canaccord:
#             holdings = holdings + read_canaccord(file_path)
#         elif ft == FileCategory.Schwab:
#             holdings = holdings + read_schwab(file_path)
#         elif ft == FileCategory.IB:
#             holdings = holdings + read_ib(file_path)
#         else:
#             error(f"Internal error, don't know about filetype {ft.name}")


# holdings,capex = get_data_maps(config.finance_dir)

# for h in holdings:
#     capex_rows = find_matching_capex(h,capex)
#     l = len(capex_rows)
#     if l > 1:
#         warning(f"Found multiple capex entries for {desc_holding(h)}: {','.join(map(desc_capex,capex_rows))}. Will divide allocation evenly between them.")

#         cl = len(capex_rows)
#         for c in capex_rows:
#             add_allocation(h,c,1./cl)

#         continue

#     if l == 0:
#         warning(f"No matching capex entry for {desc_holding(h)}, using theme {DEFAULT_THEME}")
#         add_allocation(h,default_c,1.)
#         continue

#     add_allocation(h,c,1.)

# for h in holdings:
#     print_holding(h)

    

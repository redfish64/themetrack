import csv
import os
from enum import Enum, auto
import argparse
import sys
import pdb



parser = argparse.ArgumentParser(
    usage="%(prog)s [options] [directory of financial files]...",
    description="prints out useful information",
    exit_on_error=True,
    formatter_class=argparse.ArgumentDefaultsHelpFormatter
)
parser.add_argument("finance_dir", help="directory containing financial files")

config = parser.parse_args()


class FileType(Enum):
    Capex_Big5 = auto()
    Capex_ClosedPos = auto()
    Capex_CapGains = auto()
    Capex_IncPort = auto()
    Capex_SkelPort = auto()
    Holdings_TDAmer = auto()
    Holdings_Canaccord = auto()
    Holdings_Schwab = auto()
    Holdings_IB = auto()


def get_filetype(fn):
    ft_prefix_map = {
        FileType.Capex_Big5: "capex_big5",
        FileType.Capex_ClosedPos: "capex_closed_pos",
        FileType.Capex_CapGains: "capex_cap_gains",
        FileType.Capex_IncPort: "capex_inc_port",
        FileType.Capex_SkelPort: "capex_skel_port",
        FileType.Holdings_TDAmer: "holdings_tdamer",
        FileType.Holdings_Canaccord: "holdings_canaccord",
        FileType.Holdings_Schwab: "holdings_schwab",
        FileType.Holdings_IB: "holdings_ib"
        }

    lfn = fn.lower()

    for e, fnp in ft_prefix_map.items():
        if lfn.startswith(fnp):
            return e

    return None


def warning(str):
    print(str, file=sys.stderr)


def error(str):
    print(str, file=sys.stderr)
    raise Exception('Error',str)


def verify_fields(fields, *expected_fields):
    if fields == expected_fields:
        return
    pdb.set_trace()
    
    # Find missing or unexpected fields
    missing_fields = set(expected_fields) - set(fields)
    unexpected_fields = set(fields) - set(expected_fields)

    errs = []
    if missing_fields:
        errs.append(f"Missing fields:{missing_fields}")
    if unexpected_fields:
        errs.append(f"Unexpected fields:{unexpected_fields}")

    error("Fields don't match expected: "+(",".join(errs)))
    
def read_big5(fn):
    with open(fn, newline='') as csvfile:
        r = csv.DictReader(csvfile)
        h = r.next()

        verify_fields(h,"Issue","Date","Theme","Name","Ticker")

        return list(r)
    

def get_data_maps(d):
    capex_rows = []
    holdings = []

    for fn in os.listdir(d):
        file_path = os.path.join(d, fn)
        if not os.path.isfile(file_path):
            continue
        ft = get_filetype(fn)
        if ft is None:
            warning(f"Cannot determine type of file for {file_path}, ignoring"
                    "...")
            continue

        if ft == FileType.Capex_Big5:
            capex_rows = capex_rows + read_big5(file_path)
        elif ft == FileType.Capex_ClosedPos:
            capex_rows = capex_rows + read_closed_pos(file_path)
        elif ft == FileType.Capex_CapGains:
            capex_rows = capex_rows + read_cap_gains(file_path)
        elif ft == FileType.Capex_IncPort:
            capex_rows = capex_rows + read_inc_port(file_path)
        elif ft == FileType.Capex_SkelPort:
            capex_rows = capex_rows + read_skel_port(file_path)
        elif ft == FileType.TDAmer:
            holdings = holdings + read_tdamer(file_path)
        elif ft == FileType.Canaccord:
            holdings = holdings + read_canaccord(file_path)
        elif ft == FileType.Schwab:
            holdings = holdings + read_schwab(file_path)
        elif ft == FileType.IB:
            holdings = holdings + read_ib(file_path)
        else:
            error(f"Internal error, don't know about filetype {ft.name}")


holdings,capex = get_data_maps(config.finance_dir)

for h in holdings:
    capex_rows = find_matching_capex(h,capex)
    l = len(capex_rows)
    if l > 1:
        warning(f"Found multiple capex entries for {desc_holding(h)}: {','.join(map(desc_capex,capex_rows))}. Will divide allocation evenly between them.")

        cl = len(capex_rows)
        for c in capex_rows:
            add_allocation(h,c,1./cl)

        continue

    if l == 0:
        warning(f"No matching capex entry for {desc_holding(h)}, using theme {DEFAULT_THEME}")
        add_allocation(h,default_c,1.)
        continue

    add_allocation(h,c,1.)

for h in holdings:
    print_holding(h)

    

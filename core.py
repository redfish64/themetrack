from enum import Enum, auto
import re

class FileCategory(Enum):
    Pick = auto()      # recommendations by newsletter
    Holding = auto()   # account holdings
    Mappings = auto()  # specifies relationships between holdings and picks if its not clear, 
                       # or not correctly auto associated


def get_filecat(fn):
    ft_prefix_map = {
        FileCategory.Pick: r"picks?",
        FileCategory.Holding: r"holdings?",
        FileCategory.Mappings: r"mappings?",
        }

    lfn = fn.lower()

    for e, fnp in ft_prefix_map.items():
        if re.match(fnp,lfn):
            return e

    return None


def new_books(fp_data,file_data):
    filecat(fp_data[])
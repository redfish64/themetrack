"""Parses an override excel or csv file
"""
from calendar import c
import openpyxl as op
import sys

from sympy import false

import util
import ftypes
import re
import pandas as pd

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
    
class MatchCondition:
    def __init__(self,name,val_str) -> None:
        self.name = name
        self.val_str = val_str

    def match(self,row):
        try:
            v = row[self.name]
        except KeyError:
            return (False,None)
        
        if(v == self.val_str):
            return (True,{})
        
class ReMatchCondition:
    def __init__(self,name,var_names,val_re) -> None:
        self.name = name
        self.var_names = var_names
        self.val_re = val_re

    def match(self,row):
        try:
            v = row[self.name]
        except KeyError:
            return (False,None)
        
        m = re.match(self.val_re,v)
        if(m):
            var_values = m.groups()
            return (True,dict(zip(self.var_names,var_values)))
        return (False,None)


def create_match_condition(name,val_str):
    m = re.match(r"^\$\w+(?:,\$\w+))*=(.*)$",val_str)
    if(m): #if a regular expression match, ex: $mkt,$sym=(.*):(.*)
        vars_str = m.group(1)
        regex = re.compile(m.group(2))

        # Split the string by commas to get individual variables
        vars_list = vars_str.split(',')

        # Remove the dollar sign from each variable
        vars_list = [var.strip('$') for var in vars_list]

        return ReMatchCondition(name,vars_list,regex)
    else:
        return MatchCondition(name,val_str)

class OverrideRule:
    def __init__(self, record_type) -> None:
        self.record_type = record_type
        self.match_conditions = []
        self.replacements = []

    def add_match_condition(self, match_name, match_value):
        """
        adds a condition for the rule to match before it is executed
        """
        self.match_conditions.append((match_name,match_value))

    def add_replacement(self, repl_name, repl_value):
        """
        adds a replacement action the rule is supposed to perform if it matched
        """
        #if there are multiple values
        m = re.match(r"m:(.*,.*)",repl_value)
        if(m):
            mult_values = m.group(1).split(",")
            repl_value = f"r:{"|".join(mult_values)}"

        self.replacements.append((repl_name,repl_value))


    def matches(self,df,index):
        for mc in self.match_conditions:
            if(not mc.matches(df.iloc[index])):
                return False
        
        return True
    
    def apply(self,df,index):
        for r_name,r_value in self.replacements:
            df.at[index,r_name] = r_value

def parse_override_file(fp : str):
    fi = enumerate(util.read_standardized_csv(fp,min_row_len=5))

    _,header = next(fi)
    if(not row_matches(['RecordType', 'Match', '', 'Replacement'],header[0:4])):
        util.csv_error(header,0,None,"Header must match \"FileType,Match,'',Replacement\"")

    rules = []
    current_rule = None
    for ri,row in fi:
        if(row[0] == ''):
            if(current_rule is None):
                util.csv_error(row,0,0,"Must specify a record type")            
        else :        
            record_type = util.csv_convert_to_enum(ftypes.RecordType,row,0,ri)
            current_rule = OverrideRule(record_type)
            rules.append(current_rule)
        
        match_name = row[1]
        match_value = row[2]
        repl_name = row[3]
        repl_value = row[4]

        if(match_name != ''):
            current_rule.add_match_condition(match_name, match_value)
        if(repl_name != ''):
            current_rule.add_replacement(repl_name, repl_value)

    return rules



def run_overrides(rules : list[OverrideRule], df : pd.DataFrame):
    for index in df.index:
        for r in rules:
            if(r.matches(df,index)):
                r.apply(df,index)


if __name__ == '__main__':
    parse_override_file(sys.argv[1])

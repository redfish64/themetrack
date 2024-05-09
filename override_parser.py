"""Parses an override excel or csv file
"""
from calendar import c
import math
from numpy import NaN
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

    def matches(self,row):
        v = util.get_df_row_val(row,self.name)
        
        return(v == self.val_str,{})
        
class ReMatchCondition:
    def __init__(self,name,var_names,val_re) -> None:
        self.name = name
        self.var_names = var_names
        self.val_re = val_re

    def matches(self,row):
        v = util.get_df_row_val(row,self.name)

        if(v is None):
            return (False,None)
        
        m = re.match(self.val_re,v)
        if(m):
            var_values = m.groups()
            return (True,dict(zip(self.var_names,var_values)))
        
        return (False,None)


def create_match_condition(name,val_str):
    m = re.match(r"^(\$\w+(?:,\$\w+)*)=(.*)$",val_str)
    if(m): #if a regular expression match, ex: $mkt,$sym=(.*):(.*)
        vars_str = m.group(1)

        regex_str = m.group(2)
        if(not regex_str.endswith('$')):
            regex_str += "$"

        regex = re.compile(regex_str)

        # Split the string by commas to get individual variables
        vars_list = vars_str.split(',')

        # Remove the dollar sign from each variable
        vars_list = [var.strip('$') for var in vars_list]

        return ReMatchCondition(name,vars_list,regex)
    else:
        return MatchCondition(name,val_str)

class OverrideRule:
    def __init__(self) -> None:
        self.match_conditions = []
        self.replacements = []

    def add_match_condition(self, match_name, match_value):
        """
        adds a condition for the rule to match before it is executed
        """
        self.match_conditions.append(create_match_condition(match_name,match_value))

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
        row = df.iloc[index]

        var_subs = {}
        for mc in self.match_conditions:
            (matches, match_var_subs) = mc.matches(row)
            if(not matches):
                return (False, {})
            
            var_subs.update(match_var_subs)
        
        return (True, var_subs)
    
    def apply(self,var_subs,df,index):
        def replace_var_sub(match):
            var_name = match.group(1)  # Extract the variable name from the match
            return var_subs.get(var_name, match.group(0))  # Return the value or the original string

        for r_name,r_value in self.replacements:
            updated_val = re.sub(r'\$\{(\w+)\}', replace_var_sub, r_value)
            df.at[index,r_name] = updated_val

def parse_match_columns(s : str):
    m = re.match(r'(\w+(?:,\w+))\s*=\s*(\w+(?:,\w+))$',s)
    if(m is None):
        return None
    holding_columns_str,pick_columns_str = m.groups()

    return holding_columns_str.split(','),pick_columns_str.split(',')

def parse_override_file(fp : str):
    fi = enumerate(util.read_standardized_csv(fp,min_row_len=4))

    #we allow the user to put some preamble stuff containing whatever they want before the main match/replacement table
    found_header = False
    for ri,row in fi:
        if(row_matches(['Match', '', 'Replacement'],row[0:3])):
            found_header = True
            break
    
    if(not found_header):
        util.csv_error('',0,None,"Header must match \"Match,'',Replacement\"")

    rules = []
    current_rule = None
    for ri,row in fi:
        #empty row indicates a new rule
        if(row == ['']*4):
            current_rule = None

        if(current_rule is None):
            current_rule = OverrideRule()
            rules.append(current_rule)
        
        match_name,match_value,repl_name,repl_value = row[0:4]

        #when a rule always matches, we allow the user to put a '*' to make it more humanly readable  
        if(match_name == '*'):
            match_name = ''

        if(repl_name == ftypes.assert_column_name("MatchColumns")):
            if(parse_match_columns(repl_value) is None):
                util.csv_error(row,ri,3,"MatchColumn values must be in the format "
                               "'[holding_column1],[holding_column2],...=[pick_column1],[pick_column2]...', Ex. 'Region,Ticker=Region,Ticker'")

        if(match_name != ''):
            current_rule.add_match_condition(match_name, match_value)
        if(repl_name != ''):
            current_rule.add_replacement(repl_name, repl_value)

    return rules



def run_overrides(rules : list[OverrideRule], df : pd.DataFrame):
    for index in df.index:
        for r in rules:
            (does_match,var_subs) = r.matches(df,index)
            if(does_match):
                r.apply(var_subs,df,index)


if __name__ == '__main__':
    parse_override_file(sys.argv[1])

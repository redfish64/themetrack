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
import array_log as al

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
    def __init__(self,row_index : int,name,val_str) -> None:
        self.row_index = row_index
        self.name = name
        self.val_str = val_str

    def matches(self,row):
        v = util.get_df_row_val(row,self.name)
        
        return(v == self.val_str,{})
        
class ReMatchCondition:
    def __init__(self,row_index : int, name,var_names,val_re) -> None:
        self.row_index = row_index
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

ALL_VARS_PATTERN = re.compile(r'\$\{([a-zA-Z0-9 _-]+)(?::([^}]+))?\}')

def create_match_condition(ri : int, name,val_str : str):
    if(val_str.startswith("r:")):
        is_re = True
        val_str = val_str[2:]
    else:
        is_re = False

    
    matches = re.findall(ALL_VARS_PATTERN,val_str)

    vars_list = [ n for n,_ in matches]

    # Function to replace each match with the variable's regular expression
    def replacement(match):
        regex = match.group(2)
        if(regex is None):
            regex = ".*"
        
        return f"({regex})"
        
    # Replace all matches in the text with the replacement function
    combined_regex = ALL_VARS_PATTERN.sub(replacement, val_str)
 
    if(vars_list != [] or is_re):
        return ReMatchCondition(ri,name,vars_list,combined_regex)
    else:
        return MatchCondition(ri, name,val_str)

def fixed_column(str):
    return str+"___FIXED___"

def is_fixed_column(s : str):
    return s.endswith("___FIXED___")

class OverrideRule:
    def __init__(self, ri : int) -> None:
        self.row_index = ri
        self.match_conditions = []
        self.replacements = []

    def add_match_condition(self, ri : int, match_name, match_value):
        """
        adds a condition for the rule to match before it is executed
        """
        self.match_conditions.append(create_match_condition(ri,match_name,match_value))

    def add_replacement(self, ri : int, repl_name, repl_value):
        """
        adds a replacement action the rule is supposed to perform if it matched
        """
        #if there are multiple values
        m = re.match(r"m:(.*,.*)",repl_value)
        if(m):
            mult_values = m.group(1).split(",")
            repl_value = f"r:{"|".join(mult_values)}"

        self.replacements.append((ri,repl_name,repl_value))


    def matches(self,df,index,log):
        row = df.iloc[index]

        var_subs = {}
        for mc in self.match_conditions:
            with al.add_log_context(log,{"match_condition_row_index" : mc.row_index }):
                (matches, match_var_subs) = mc.matches(row)
                if(not matches):
                    al.write_log(log,"matched.")
                    return (False, {})
                
                al.write_log(log,"did not match.")
                var_subs.update(match_var_subs)
        
        return (True, var_subs)
    
    def apply(self,var_subs,df,index, log, is_user_rule=False, fixed_columns = {}):
        """_summary_

        Args:
            var_subs (_type_): _description_
            df (_type_): _description_
            index (_type_): _description_
            is_user_rule (bool, optional): If true, the result of the rule cannot be changed by a non-user rule. Defaults to False.
            fixed_columns: columns that were set by a user rule, and so are fixed and cannot be changed by a system rule running afterwards
        """
        def replace_var_sub(match):
            var_name = match.group(1)  # Extract the variable name from the match
            return var_subs.get(var_name, match.group(0))  # Return the value or the original string

        for row_index,r_name,r_value in self.replacements:
            with al.add_log_context(log,{"replacement_row_index" : row_index,"r_name" : r_name,"r_value" : r_value}):
                if(r_name in fixed_columns and not is_user_rule):
                    al.write_log(log,f"{r_name} was modified by a user_rule, skipping")
                    next

                updated_val = re.sub(r'\$\{(\w+)\}', replace_var_sub, r_value)
                old_value = df.at[index,r_name] if r_name in df.columns else None
                if(is_user_rule or r_name not in fixed_columns):
                    if(old_value != updated_val):
                        al.write_log(log,f'Updating from "{old_value}" to "{updated_val}"')
                        df.at[index,r_name] = updated_val
                    if(is_user_rule):
                        al.write_log(log,f'Setting {r_name} as fixed column')
                        fixed_columns[r_name] = True
    
def parse_match_columns(s : str):
    m = re.match(r'([A-Za-z0-9: ]+(?:,[A-Za-z0-9: ]+))\s*=\s*([A-Za-z0-9: ]+(?:,[A-Za-z0-9: ]+))$',s)
    if(m is None):
        return None
    holding_columns_str,pick_columns_str = m.groups()

    return holding_columns_str.split(','),pick_columns_str.split(',')

def parse_override_file(fi) -> list[OverrideRule]:
    """parses a file containing rules to match and replace data values

    Args:
        fi: array of values, usually processed in the format returned by util.read_standardized_csv

    Returns:
        parsed rules
    """
    fi = enumerate(util.extend_all_row_length(fi,4))

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
            current_rule = OverrideRule(ri)
            rules.append(current_rule)
        
        match_name,match_value,repl_name,repl_value = row[0:4]

        #when a rule always matches, we allow the user to put a '*' to make it more humanly readable  
        if(match_name == '*'):
            match_name = ''

        if(repl_name == ftypes.SpecialColumns.RMatchColumns.get_col_name()):
            if(parse_match_columns(repl_value) is None):
                util.csv_error(row,ri,3,"MatchColumn values must be in the format "
                               "'[holding_column1],[holding_column2],...=[pick_column1],[pick_column2]...', Ex. 'Region,Ticker=Region,Ticker'")

        if(match_name != ''):
            current_rule.add_match_condition(ri,match_name, match_value)
        if(repl_name != ''):
            current_rule.add_replacement(ri,repl_name, repl_value)

    return rules


def run_rules(system_rules : list[OverrideRule], user_rules : list[OverrideRule], df : pd.DataFrame, log : al.Log):
    """Runs override rules against the data frame.

    Args:
        system_rules (list[OverrideRule]): These are rules that are run for every dataset and basically are hardcoded. 
          They are overrideable by user rules
        user_rules (list[OverrideRule]): These rules are for user exceptions, such as changing a ticker or an exchange to something that
          matches whats in Picks, etc. System rules will be run before and after all user rules. However system rules will never change
          the result of a user rule
        df (pd.DataFrame): Dataframe to update
    """

    for index in df.index:

        fixed_columns = {}
        
        def run_rules(rules : list[OverrideRule],log, is_user_rules):
            any_rule_matched = False

            for r in rules:
                with al.add_log_context(log, {"rule_row_index": r.row_index}):
                    (does_match,var_subs) = r.matches(df,index,log=log)
                    if(does_match):
                        al.write_log(log, "matched.")
                        r.apply(var_subs,df,index, is_user_rule=is_user_rules, fixed_columns=fixed_columns,log=log)
                        any_rule_matched = True
                    else:
                        al.write_log(log, "did not match.")
            
            return any_rule_matched

        with al.add_log_context(log, {"df_index" : index}):
            with al.add_log_context(log, {"rule_set": "system_rules pass 1"}):
                run_rules(system_rules,log, False)
            with al.add_log_context(log, {"rule_set": "user_rules"}):
                any_user_rules_matched = run_rules(user_rules,log, True)
            if(any_user_rules_matched):
                with al.add_log_context(log, {"rule_set": "system_rules pass 2"}):
                    run_rules(system_rules,log, False)


if __name__ == '__main__':
    parse_override_file(sys.argv[1])
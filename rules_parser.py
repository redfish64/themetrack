"""Parses an override excel or csv file
"""
from calendar import c
import math
from numpy import NaN
import openpyxl as op
import sys


import util
from util import row_matches
import ftypes
import re
import pandas as pd
import array_log as al

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
    def __init__(self, ri : int, is_user_rule) -> None:
        self.row_index = ri
        self.match_conditions = []
        self.replacements = []
        self.is_user_rule = is_user_rule

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
            repl_value = f"r:{'|'.join(mult_values)}"

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
    
    def apply(self,var_subs,df,index, log, fixed_columns = {}):
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
                if(r_name in fixed_columns and not self.is_user_rule):
                    al.write_log(log,f"{r_name} was modified by a user_rule, skipping")
                    continue

                updated_val = re.sub(r'\$\{(\w+)\}', replace_var_sub, r_value)
                old_value = df.at[index,r_name] if r_name in df.columns else None
                if(self.is_user_rule or r_name not in fixed_columns):
                    if(old_value != updated_val):
                        al.write_log(log,f'Updating from "{old_value}" to "{updated_val}"')
                        df.at[index,r_name] = updated_val
                    if(self.is_user_rule):
                        al.write_log(log,f'Setting {r_name} as fixed column')
                        fixed_columns[r_name] = True
    
def parse_match_columns(s : str):
    m = re.match(r'([A-Za-z0-9: ]+(?:,[A-Za-z0-9: ]+))\s*=\s*([A-Za-z0-9: ]+(?:,[A-Za-z0-9: ]+))$',s)
    if(m is None):
        return None
    holding_columns_str,pick_columns_str = m.groups()

    return holding_columns_str.split(','),pick_columns_str.split(',')

def parse_override_file(fi,is_user_rules) -> list[OverrideRule]:
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
            continue

        if(current_rule is None):
            current_rule = OverrideRule(ri,is_user_rules)
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

def get_match_name_list_sorted_by_usage(override_rules):
        match_name_to_count = {}
        for r in override_rules:
            for m in r.match_conditions:
                if(m.name in match_name_to_count):
                    match_name_to_count[m.name] += 1
                else:
                    match_name_to_count[m.name] = 1

        res = [(k, v) for k, v in match_name_to_count.items()]
        res.sort(key=lambda item: item[1], reverse=True)

        return [i[0] for i in res]


def merge_dicts(d1 : dict, d2 : dict, fn):
    d2_copy = d2.copy()
    for k,v in d1.items():
        if(k in d2_copy):
            d2_copy[k] = fn(d1[k],d2_copy.get(k,{}))
        else:
            d2_copy[k] = v

    return d2_copy


#TODO 2: When parsing rules, don't allow any rule to specify the same name twice in match or replacement.
# First, we haven't made FastOverrideRulesList to handle this. (We could do it, but it would be overly complicated
# and the user probably never needs to do this). Second, if this is happening, it is in all likelyhood a mistake
#TODO 2: also don't allow a rule to match the same var twice in different match conditions
class MatchGroup:
    def __init__(self,name) -> None:
        self.name = name
        self.val_to_ri_set = {} #rules that use a normal match cond
        self.re_mc_and_ri_set = [] #rules that use a regex match cond
        self.all_rules = set()  #all rules that are specified in this match condition

    def add_match_cond(self,mc,rule_index : int):
        if(mc.name != self.name):
            util.error("Internal error: added wrong match condition")
        
        self.all_rules.add(rule_index)

        if(isinstance(mc,ReMatchCondition)):
            for index,(re_mc,ri_dict) in enumerate(self.re_mc_and_ri_set):
                #if the regex match is identical to an existing one
                if(mc.val_re == re_mc.val_re and mc.var_names == re_mc.var_names):
                    ri_dict.add(rule_index)
                    return

            #no match so add a new one
            self.re_mc_and_ri_set.append((mc,{rule_index}))
            return
        
        #normal match conditon
        dict = self.val_to_ri_set.get(mc.val_str, None)
        if(dict is None):
            self.val_to_ri_set[mc] = {rule_index}
        
        self.val_to_ri_set[mc].add(rule_index)

    def filter_rules(self,row, existing_rules_to_var_values=None):
        #this function does an 'or' of self.val_to_ri_set, self.re_mc_and_ri_set, and self.passthrough
        #and then 'and's that with existing_rules_to_var_values if present, merging any var values

        val = row.get(self.name,'') #TODO 2 should we really use '' here? Probably need to chase down what
        #we do elsewhere for non existant columns and then make sure we all use the same thing in all cases

        #handle simple match conditions (no regex, and no match vars), by simply adding the rule indexes
        #that belong to the match for the 'or'
        or_res = { ri : {} for ri in self.val_to_ri_set.get(val,set())}

        #handle regex matches, with their own var values for the 'or'
        for re_mc,ri_set in self.re_mc_and_ri_set:
            #so not to run regex's for values that we will end up not using because they are filtered
            #already, we do a intersection ahead of time with existing_rules_to_var_values
            if(existing_rules_to_var_values): 
                ri_set = (ri_set & existing_rules_to_var_values.keys())
                
            #if there are no surviving existing rules then skip the regex
            if(ri_set == set()):
                continue

            #match the regex against the value
            is_match,curr_match_vars = re_mc.matches(row)
            if(not is_match):
                continue
            
            #matched, so add the curr_match_vars to every rule under the current match condition
            for ri in ri_set:
                or_res[ri] = curr_match_vars

        if(existing_rules_to_var_values):
            res = {}

            #now 'and' the result with existing rules
            for ek,ev in existing_rules_to_var_values.items():
                if(ek in or_res):
                    res[ek] = ev | or_res #note that we don't have to worry about conflicts, because no rule should specify the same variable twice
                    #in match conditions 
                elif(ek not in self.all_rules): # if the rule doesn't have this match condition at all
                    res[ek] = ev # just let it pass through
                #else we don't include it, since it was filtered out
        else:
            res = or_res

        return or_res        


class FastOverrideRulesList:
    def __init__(self, override_rules : list[OverrideRule]):
        """
        Speeds up override rules, by combining the match conditions so they only have to be run once,
        no matter how many rules use them.

        WARNING: No rule may specify the same name twice in the match conditions or this will produce
        inconsistent results.
        WARNING 2: No rule may specify the same match variable in more than one
        match condition, or inconsistent results may occur.
        """
        match_names = get_match_name_list_sorted_by_usage(override_rules)

        self.match_groups = [MatchGroup(n) for n in match_names]

        match_name_to_match_group = dict(zip(match_names,self.match_groups))

        self.always_exec_rule_indexes = []

        for ri,r in enumerate(override_rules):
            #if there are no conditions and should always run
            if(r.match_conditions == []):
                self.always_exec_rule_indexes.append(ri)
            else:
                for mc in r.match_conditions:
                    match_name_to_match_group[mc.name].add_match_cond(mc,ri)
            

    def filter_matching_rules(self,row):
        """
        filters rules to those that match the specified row. 
        Returns matching rules along with var values according to the regex matches
        """

        rules_to_var_values = None

        for mg in self.match_groups:
            rules_to_var_values = mg.filter_rules(row,rules_to_var_values)
        
        return rules_to_var_values


def create_forl(rules : list[OverrideRule]):
    return FastOverrideRulesList(rules)

def run_rules_fast(rules : list[OverrideRule], forl : FastOverrideRulesList, df : pd.DataFrame, log : al.Log):
    """Runs override rules against the data frame quickly

    Args:
        rules: rules to run
        forl : call create_forl()
        df (pd.DataFrame): Dataframe to update
    """
    for index in df.index:

        ri_to_var_values = forl.filter_matching_rules(df.iloc[index])

        fixed_columns = {}

        system_rules = []
        user_rules = []
        for ri,var_values in ri_to_var_values.items():
            r = rules[ri]
            if(r.is_user_rule):
                user_rules.append((ri,r,var_values))
            else:
                system_rules.append((ri,r,var_values))

        for ri in forl.always_exec_rule_indexes:
            r = rules[ri]
            if(r.is_user_rule):
                user_rules.append((ri,r,{}))
            else:
                system_rules.append((ri,r,{}))

        system_rules.sort(key=lambda x: x[0])
        user_rules.sort(key=lambda x: x[0])

        def run_rules(rules):
            for _,r,var_values in rules:
                r.apply(var_values,df,index, fixed_columns=fixed_columns,log=log)         

        run_rules(system_rules)
        run_rules(user_rules)
        run_rules(system_rules) #run system rules a second time so that any change to match conditions
        #from user_rules will propagate to the var variables for system rules
        

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

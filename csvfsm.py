#!/usr/bin/env python
#
# Copyright 2010 Google Inc. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#      http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied. See the License for the specific language governing
# permissions and limitations under the License.

# Tim E: Taken from Google's so-so TextFSM and converted to work with CSV files

"""Template based text parser.

This module implements a parser, intended to be used for converting
human readable text, such as command output from a router CLI, into
a list of records, containing values extracted from the input text.

A simple template language is used to describe a state machine to
parse a specific type of text input, returning a record of values
for each input entity.
"""

import argparse
import re
import textfsm
import csv
import os
from enum import Enum

FSM_TEMPLATE_NAME="fsm.tfsm"

FORMAT_FIELD='Format'
VALUE_FIELD='Valuu'
RULE_FIELD='Ruul'
MATCH_FIELD='Match'
LINE_ACTION_FIELD='LineAction'
RECORD_ACTION_FIELD='RecordAction'
NAME_FIELD='Name'
OPTIONS_FIELD='Options'
REGEX_FIELD='Regex'
NEXT_RULE_NAME_FIELD='NextRuleName'

DEFAULT_VALUE_REGEX='.*'
DEFAULT_VALUE_OPTIONS=[]
START_RULE='Start'

def get_code_file_path(file):
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Build the path to the file
    return os.path.join(script_dir, file)

def add_uniq_to_dict(d, key, value):
    if key in d:
        raise KeyError(f"Key '{key}' already exists.")
    d[key] = value

def add_to_dict_of_lists(d, key, value):
    if key not in d:
        d[key] = []
    d[key].append(value)

def get_required(dict, name):
    v = dict[name]
    if(not v):
        raise Exception(f"required field, {name} not filled in {dict}")
    
    return v

def parse_format_field(row):
    raise Exception("TBD") # TODO 3 Need to support format fields, I guess

class ValueOption(Enum):
    Filldown = 'Filldown'

class LineAction(Enum):
    Next = 'Next'
    Continue = 'Continue'
    Error = 'Error'

class RecordAction(Enum):
    NoRecord = 'NoRecord'
    Record = 'Record'
    Clear = 'Clear'
    Clearall = 'Clearall'

def parse_options(options_field):
    options=options_field.split(",")
    
    def get_option(o):
        return ValueOption[o]
    
    return map(get_option,options)

class ValueRegex:
    def __init__(self,name,options,regex) -> None:
        self.name = name
        self.options = options
        self.regex = regex

class ValueMatch:
    """The matched value, with the data, row/col and filename
    """
    def __init__(self,name : str, data : str, row_index : int = None, cell_index : int = None, filepath : str = None):
        self.name = name
        self.data = data
        self.row_index = row_index
        self.cell_index = cell_index
        self.filepath = filepath


class CellMatch():
    def __init__(self,regex : re.Pattern, value_names : list[str]) -> None:
        self.regex = regex
        self.value_names = value_names

    def matches(self, cell_str : str) -> dict[str,ValueMatch]:
        m = re.match(self.regex,cell_str)

        if(m is None):
            return None

        return {vn : ValueMatch(vn,vt) for vn,vt in zip(self.value_names,m.groups())}

class Rule:
    def __init__(self,rule_name : str,cell_matches : list[CellMatch] ,line_action : LineAction,record_action : RecordAction, next_rule_name : str) -> None:
        self.rule_name = rule_name
        self.cell_matches = cell_matches
        self.line_action = line_action
        self.record_action = record_action
        self.next_rule_name = next_rule_name

    def matches(self,row : list[str]) -> dict[str,ValueMatch]:
        row_value_matches = {}

        for cell_index,(cell_str,cell_match) in enumerate(zip(row,self.cell_matches)):
            value_matches = cell_match.matches(cell_str)
            if(value_matches is None): # failed match
                return None
            
            for vk,vm in value_matches.items():
                vm.cell_index = cell_index
            
            row_value_matches = row_value_matches | value_matches

        return row_value_matches
    
def parse_value_field(row) -> ValueRegex:
    try:
        name = get_required(row,NAME_FIELD)
        options = parse_options(row[OPTIONS_FIELD])
        regex = row[REGEX_FIELD]
        if(not regex):
            regex = DEFAULT_VALUE_REGEX

        return ValueRegex(name,options,regex)
    except Exception:
        raise Exception(f"Can't parse {row}")    
    
def parse_line_action(la):
    if(la == ''):
        return LineAction.Next
    return LineAction[la]
    
def parse_record_action(ra):
    if(ra == ''):
        return RecordAction.NoRecord
    return RecordAction[ra]
    
def split_by_commas(input_string):
    """
    Splits by commas, which can be escaped with a \\
    """
    # Temporarily replace '\\,' with a placeholder that is unlikely to be in the input
    placeholder = "\0"
    temp_string = input_string.replace("\\,", placeholder)
    
    # Split by commas not preceded by a backslash
    parts = re.split(r'(?<!\\),', temp_string)
    
    # Post-process parts to handle the placeholders and '\\'
    result = []
    for part in parts:
        # Replace the placeholder with ','
        part = part.replace(placeholder, ',')
        # Replace '\\' with '\'
        part = part.replace("\\\\", "\\")
        result.append(part)
        
    return result

def parse_rule_field_adding_to_values(row, values_map):
    """
    Parses a rule field and if it contains a reference to a value that is not defined, adds a default
    value to values_map.
    """

    VALUE_PATTERN = r'\${(\w+)}'

    def create_cell_match(match_str) -> CellMatch:
        def repl(match):
            name = match.group(1)

            #add to the names used in this particular cell
            names.append(name)

            existing_value = values_map.get(name)

            #if the value doesn't exist, create a default one for the convienence of the user
            if(existing_value is None):
                existing_value = ValueRegex(name,DEFAULT_VALUE_OPTIONS,DEFAULT_VALUE_REGEX)
                values_map[name] = existing_value

            return f"({existing_value.regex})"

        names = []

        regex_str = re.sub(VALUE_PATTERN, repl, match_str)

        return CellMatch(re.compile(regex_str),names)



    def split_match(match_field):
        cell_match_strs = split_by_commas(match_field)

        cell_matches = [create_cell_match(s) for s in cell_match_strs]
        return cell_matches

    rule_name = row[RULE_FIELD]
    full_match_str = row[MATCH_FIELD]
    line_action = parse_line_action(row[LINE_ACTION_FIELD])
    record_action = parse_record_action(row[RECORD_ACTION_FIELD])
    next_rule_name = row[NEXT_RULE_NAME_FIELD]

    if(next_rule_name and line_action == LineAction.Continue):
        raise Exception(f"can't have a next rule and a line action for {row}")
    
    if(not next_rule_name):
        next_rule_name = rule_name

    cell_matches=split_match(full_match_str)

    #check if a name is reused
    existing_names = {}
    for cm in cell_matches:
        for n in cm.value_names:
            if(n in existing_names):
                raise Exception(f"${{{n}}} is used twice")
            existing_names[n] = 1

    return Rule(rule_name,cell_matches,line_action,record_action,next_rule_name)

class CsvTemplate():
    def __init__(self,formats,value_regexs : list[ValueRegex], rules : dict[str,list[Rule]]) -> None:
        self.formats = formats
        self.value_regexs = value_regexs
        self.rules = rules

def read_template(template_filename):
    fsm_template = get_code_file_path(FSM_TEMPLATE_NAME)

    # Open the template file, and initialise a new TextFSM object with it.
    fsm = textfsm.TextFSM(open(fsm_template))

    with open(template_filename) as file:
        input_data = file.read()
    
    fsm_results = fsm.ParseTextToDicts(input_data)

    formats = {}
    value_regexs = {}
    rules = {}

    for row in fsm_results:
        if(row[FORMAT_FIELD]):
            format = parse_format_field(row)
            add_uniq_to_dict(formats, format.name, format)
        elif(row[VALUE_FIELD]):
            value_regex = parse_value_field(row)
            add_uniq_to_dict(value_regexs, value_regex.name, value_regex)
        elif(row[RULE_FIELD]):
            rule = parse_rule_field_adding_to_values(row, value_regexs)
            add_to_dict_of_lists(rules,rule.rule_name,rule)
        else:
            raise Exception(f"Internal error, can't understand row {row}")

    return CsvTemplate(formats,value_regexs,rules)

class State():
    def __init__(self,curr_rule_name : str,curr_values : dict[str,CellMatch],curr_filldown_values : dict[str,CellMatch]) -> None:
        self.curr_rule_name = curr_rule_name
        self.curr_values = curr_values 
        self.curr_filldown_values = curr_filldown_values
    

def parse_datafile(csv_template : CsvTemplate, file : str) -> list[dict[str,ValueMatch]]:
    state = State(START_RULE,{},{})

    results = []

    with open(file, newline='') as csvfile:
        reader = csv.reader(csvfile)

        start_rule_index = 0

        for (row_index,row) in enumerate(reader):
            curr_rules = csv_template.rules[state.curr_rule_name]
            for rule_index in range(start_rule_index,len(curr_rules)):
                curr_rule = curr_rules[rule_index]
                row_value_matches = curr_rule.matches(row)

                #if we matched
                if(row_value_matches is not None):
                    for vm in row_value_matches.values():
                        vm.row_index=row_index
                        vm.filepath=file
                    
                    state.curr_values = state.curr_values | row_value_matches
                    if(curr_rule.line_action == LineAction.Next):
                        start_rule_index = 0
                    elif(curr_rule.line_action == LineAction.Continue):
                        start_rule_index = rule_index
                    elif(curr_rule.line_action == LineAction.Error):
                        raise Exception(f"Error thrown at template rule {curr_rule.rule_name}, row {row_index}") #TODO 3 get the template line number somehow for this error message
                    else:
                        raise Exception()
                    
                    if(curr_rule.record_action == RecordAction.Clear):
                        state.curr_values = []
                    elif(curr_rule.record_action == RecordAction.Clear):
                        state.curr_values = []
                        state.curr_filldown_values = []
                    elif(curr_rule.record_action == RecordAction.Record):
                        results.append(state.curr_filldown_values | state.curr_values)
                    elif(curr_rule.record_action == RecordAction.NoRecord):
                        pass
                    else:
                        raise Exception()
                    
                    state.curr_rule_name = curr_rule.next_rule_name

    return results




            

if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        usage="%(prog)s [options] <template> <file>",
        description="prints data extracted from file using template",
        exit_on_error=True,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    
    parser.add_argument("template", help="Csv FSM template file, similar to TextFSM")
    parser.add_argument("file", help="Data file to process")

    config = parser.parse_args()

    csv_template = read_template(config.template)

    results = parse_datafile(csv_template,config.file)

    for i,r in enumerate(results):
        for k,v in r.items():            
            print(f"{i} {k}: {v.data}")



# print 'Header:'
# print fsm.header

# print 'Prefix             | Gateway(s)'
# print '-------------------------------'

# for row in fsm_results:
#   print '%-18.18s  %s' % (row[2], ', '.join(row[3]))

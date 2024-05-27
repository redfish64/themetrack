import re
from typing import Dict, Any

class Log:
    def __init__(self,filter : Dict[str,Any], turn_off = False):
        """_summary_

        Args:
            filter (Dict[str,Any]): filter of keys to values. Anything that doesn't match filter will not be matched
                    If a value is a re.Pattern, it will be regex matched
            turn_off (bool, optional): Turns off logging completely. Defaults to False.
        """
        self.logs = []
        self.context_stack = [{}]
        self.filter = filter
        self.turn_off = turn_off 

    def add_context(self, dict):
        # Add context to the current context
        new_context = self.context_stack[-1] | dict

        self.context_stack.append(new_context)

    def remove_context(self):
        # Remove the latest context
        if len(self.context_stack) > 1:
            self.context_stack.pop()

    def log_message(self, message):
        if(self.turn_off):
            return
        
        current_context = self.context_stack[-1]
        for k,v in self.filter.items():
            if(k not in current_context):
                return
            
            cv = current_context[k]

            if(isinstance(v, re.Pattern)):
                if(not re.match(v,cv)):
                    return
            elif(v != cv):
                return
            
        # Log a message with the current context
        self.logs.append((message,current_context))

    def get_logs(self):
        return self.logs


class add_log_context:
    def __init__(self, log, dict : dict):
        self.log = log
        self.dict = dict

    def __enter__(self):
        self.log.add_context(self.dict)

    def __exit__(self, exc_type, exc_value, traceback):
        self.log.remove_context()


def write_log(log, message):
    log.log_message(message)

if(__name__ == '__main__'):
    # Example usage
    log = Log()

    with add_log_context(log, "df_index", 1):
        write_log(log, "First message")
        with add_log_context(log, "row", 10):
            write_log(log, "Second message")
        write_log(log, "Third message")

    print(log.get_logs())

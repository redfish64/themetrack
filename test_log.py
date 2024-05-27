class Log:
    def __init__(self):
        self.logs = []
        self.context_stack = [{}]

    def add_context(self, key, value):
        # Add context to the current context
        new_context = self.context_stack[-1].copy()
        new_context[key] = value
        self.context_stack.append(new_context)

    def remove_context(self):
        # Remove the latest context
        if len(self.context_stack) > 1:
            self.context_stack.pop()

    def log_message(self, message):
        # Log a message with the current context
        current_context = self.context_stack[-1]
        self.logs.append({"message": message, "context": current_context})

    def get_logs(self):
        return self.logs


class add_log_context:
    def __init__(self, log, key, value):
        self.log = log
        self.key = key
        self.value = value

    def __enter__(self):
        self.log.add_context(self.key, self.value)

    def __exit__(self, exc_type, exc_value, traceback):
        self.log.remove_context()


def write_log(log, message):
    log.log_message(message)


# Example usage
log = Log()

with add_log_context(log, "df_index", 1):
    write_log(log, "First message")
    with add_log_context(log, "row", 10):
        write_log(log, "Second message")
    write_log(log, "Third message")

print(log.get_logs())
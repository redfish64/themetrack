import re

def replace_and_list_names(input_string, replacements):
    # Regular expression to match ${name} patterns
    pattern = r'\$\{([^}]+)\}'
    
    # Function to perform the replacement and track names
    def repl(match):
        name = match.group(1)  # Extract the name inside ${}
        names.append(name)  # Add to the list of names
        return replacements.get(name, match.group(0))  # Replace or keep original
    
    names = []  # To keep track of names in the order they appear
    # Use the sub function with repl as the replacement function
    replaced_string = re.sub(pattern, repl, input_string)
    
    return replaced_string, names

# Example usage
replacements_dict = {'apple': 'green', 'banana': 'yellow'}
input_str = "I ate ${apple} apples and ${banana} bananas."
replaced_str, names_list = replace_and_list_names(input_str, replacements_dict)

print("Replaced String:", replaced_str)
print("Names List:", names_list)
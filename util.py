import os

def get_code_file_path(file):
    # Get the directory of the current script
    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Build the path to the file
    return os.path.join(script_dir, file)


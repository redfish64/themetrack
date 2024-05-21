import argparse
import os
import subprocess
import platform

def open_directory(path):
    if platform.system() == "Windows":
        # Open directory in Windows File Explorer
        os.startfile(path)
    elif platform.system() == "Linux":
        # Open directory in Linux file manager
        subprocess.run(['xdg-open', path])
    else:
        print(f"Unsupported platform: {platform.system()}")

if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="opens external programs",
        exit_on_error=True,
        formatter_class=argparse.ArgumentDefaultsHelpFormatter
    )
    subparsers = parser.add_subparsers(title="commands", description="Available commands", help="Use `command -h` for more details", dest="command")

    parser_opendir = subparsers.add_parser('open_dir', help="Opens a directory in some weird gui way")
    parser_opendir.add_argument('dir', type=str,help="dir to open")
    parser_opendir.set_defaults(func=lambda args: open_directory(args.dir))

    args = parser.parse_args()

    # Call the appropriate function based on the command
    if args.command:
        args.func(args)
    else:
        parser.print_help()

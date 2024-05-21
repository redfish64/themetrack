import argparse
import shlex
import sys

def scrape(args):
    print(f"Scraping data from {args.source} and saving to {args.output}")

def create_reports(args):
    print(f"Creating {args.report_type} report from {args.input}")

def setup_argparse():
    parser = argparse.ArgumentParser(description="A CLI tool for scraping data and creating reports.")
    subparsers = parser.add_subparsers(title="commands", description="Available commands", help="Use `command -h` for more details", dest="command")
    
    # Subparser for the 'scrape' command
    parser_scrape = subparsers.add_parser('scrape', help="Scrape data from the specified source")
    parser_scrape.add_argument('--source', type=str, required=True, help="The data source to scrape from")
    parser_scrape.add_argument('--output', type=str, required=True, help="The file to save scraped data")
    parser_scrape.set_defaults(func=scrape)
    
    # Subparser for the 'create-reports' command
    parser_create_reports = subparsers.add_parser('create-reports', help="Create reports from the provided data")
    parser_create_reports.add_argument('--input', type=str, required=True, help="The input data file")
    parser_create_reports.add_argument('--report-type', type=str, choices=['pdf', 'html'], required=True, help="The type of report to generate")
    parser_create_reports.set_defaults(func=create_reports)
    
    return parser

def main():
    parser = setup_argparse()

    # Check if any command-line arguments were provided
    if len(sys.argv) > 1:
        # Parse command-line arguments
        args = parser.parse_args()
        if args.command:
            args.func(args)
        else:
            parser.print_help()
    else:
        # Enter interactive command loop
        while True:
            try:
                # Prompt the user for input
                user_input = input("Enter command: ")
                
                # Exit the loop if the user types 'exit' or 'quit'
                if user_input.lower() in {'exit', 'quit'}:
                    break
                
                # Split the input into arguments using shlex
                args = parser.parse_args(shlex.split(user_input))
                
                # Call the appropriate function based on the command
                if args.command:
                    args.func(args)
                else:
                    parser.print_help()
                    
            except Exception as e:
                print(f"Error: {e}")
                parser.print_help()

if __name__ == "__main__":
    main()
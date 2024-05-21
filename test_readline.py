import readline

def main():
    histfile = '.python_history'
    try:
        readline.read_history_file(histfile)
    except FileNotFoundError:
        pass

    while True:
        try:
            line = input('> ')
            if line == 'exit':
                break
            print(f'You entered: {line}')
        except EOFError:
            break

    readline.write_history_file(histfile)

if __name__ == '__main__':
    main()
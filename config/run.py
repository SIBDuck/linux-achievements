import la
import sys
import shlex
def start_cli():
    la.main()

def main():
    try:
        raw_input = shlex.join(sys.argv[1:]).strip()
        if not raw_input:
            start_cli()
            return
        la.parser.parse(raw_input, is_cli=False)
    except KeyboardInterrupt:
        return

if __name__ == "__main__":
    main()
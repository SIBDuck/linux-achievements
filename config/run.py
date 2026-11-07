import la
import sys
def start_cli():
    la.main()

def main():
    try:
        raw_input = " ".join(sys.argv[1:]).strip()
        if not raw_input:
            start_cli()
            return
        la.parser.parse(raw_input, is_cli=False)
    except KeyboardInterrupt:
        return

if __name__ == "__main__":
    main()
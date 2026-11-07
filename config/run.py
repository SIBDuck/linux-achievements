import la
import sys
def start_cli():
    la.main()

def main():
    raw_input = " ".join(sys.argv[1:]).strip()
    if not raw_input:
        start_cli()
        return
    la.Parser.parse(raw_input, is_cli=False)

if __name__ == "__main__":
    main()
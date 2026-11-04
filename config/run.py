import la
import sys
import variables as v
def start_cli():
    la.main()

def main():
    raw_input = " ".join(sys.argv[1:]).strip()
    if not raw_input:
        start_cli()
        return
    la.Parser.parse(raw_input)

if __name__ == "__main__":
    main()
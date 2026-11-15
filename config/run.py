import la
import sys
import shlex
import variables as v
def start_cli():
    la.main()


def main():
    try:
        la.init_ram_dir()
        raw_input = shlex.join(sys.argv[1:]).strip()
        if not raw_input:
            start_cli()
            sys.exit(0)
        ec = la.parser.parse(raw_input, is_cli=False)
        la.wh(raw_input)
        sys.exit(ec)
    except KeyboardInterrupt:
        sys.exit(130)



if __name__ == "__main__":
    main()
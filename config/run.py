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
            return
        la.parser.parse(raw_input, is_cli=False)
        la.wh(raw_input)
    except KeyboardInterrupt:
        return



if __name__ == "__main__":
    main()
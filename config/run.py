import la
import sys
import shlex
import variables as v
def start_cli():
    la.main()
def init_ram_dir():
    what_to_return = False
    for path in [v.PATH_LCMD, v.PATH_EDITOR, v.DAEMON_PID_PATH, v.LOG_FILE_PATH]:
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            path.touch()
            what_to_return = True
    return what_to_return

def main():
    try:
        init_ram_dir()
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
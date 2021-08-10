import os
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="subparser_name")

    pyuic_parser = subparsers.add_parser('pyuic')
    pyuic_parser.add_argument("--clear", action="store_true")
    count_parser = subparsers.add_parser('count')
    count_parser.add_argument(
        "--count-blank", action="store_true", dest="count_blank")
    setup_parser = subparsers.add_parser('setup')
    setup_parser.add_argument("--clear", action="store_true")
    copy_parser = subparsers.add_parser('copy')
    collect_parser = subparsers.add_parser('collect')
    clear_parser = subparsers.add_parser('clear')

    args = parser.parse_args()

    root = os.path.dirname(os.path.abspath(__file__))
    root = os.path.relpath(root)

    if args.subparser_name == "pyuic":
        from utils.pyuic import pyuic, clear
        if args.clear:
            clear(os.path.join(root, "Orbitool", "UI"))
        else:
            pyuic(os.path.join(root, "Orbitool", "UI"))
    elif args.subparser_name == "count":
        from utils.countCode import count
        count([os.path.join(root, "Orbitool")], root, args.count_blank)
    elif args.subparser_name == "collect":
        from utils.collect_code import collect
        collect(root, [os.path.join(root, "Orbitool"),
                os.path.join(root, "utils")], root)
    elif args.subparser_name == "setup":
        from utils.setup import main as setup, clear
        if args.clear:
            clear(root)
        else:
            setup(root)
    elif args.subparser_name == "copy":
        from utils.copyCode import copyTo
        copyTo(root)
    elif args.subparser_name == "clear":
        from utils.clear_temp import clear
        clear()

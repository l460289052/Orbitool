import os
import argparse

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    subparsers = parser.add_subparsers(dest="subparser_name")

    pyuic_parser = subparsers.add_parser('pyuic')
    count_parser = subparsers.add_parser('count')
    setup_parser = subparsers.add_parser('setup')
    copy_parser = subparsers.add_parser('copy')
    clear_parser = subparsers.add_parser('clear')

    args = parser.parse_args()

    root = os.path.dirname(os.path.abspath(__file__))
    root = os.path.relpath(root)

    if args.subparser_name == "pyuic":
        from utils.pyuic import pyuic
        pyuic(os.path.join(root, "Orbitool", "UI"))
    elif args.subparser_name == "count":
        from utils.countCode import count
        count([os.path.join(root,"Orbitool"), os.path.join(root, "utils")], root)
    elif args.subparser_name == "setup":
        from utils.setup import main as setup
        setup(root)
    elif args.subparser_name == "copy":
        from utils.copyCode import copy as copyCode
        pass
    elif args.subparser_name == "clear":
        from utils.clear_temp import clear
        clear()
        

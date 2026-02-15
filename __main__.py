from argparse import ArgumentParser, RawTextHelpFormatter
from sys import exit as sys_exit, stdin


class Details:
    byte_count = 0
    char_count = 0


def main() -> None:
    progname = "pywc"
    parser = ArgumentParser(
        progname,
        f"{progname} [OPTION]... [FILE]...\r\n{progname} [OPTION]... --files0-from=F",
        "Print  newline,  word, and byte counts for each FILE, and a total line if more than one FILE is specified.\r\n"
            "A word is a nonempty sequence of non white space delimited by white space characters or by start or end of input.\n\n"
            "With no FILE, or when FILE is -, read standard input.\n\n"
            "The options below may be used to select which counts are printed, always in the following order: newline, word, character, byte, maximum line length.",
        formatter_class=RawTextHelpFormatter)

    parser.add_argument("FILE", type=str, nargs="*", help="The file in question")
    parser.add_argument("-c", "--bytes", action="store_true", help="Print the byte counts")
    parser.add_argument("-m", "--chars", action="store_true", help="Print the character counts")
    
    args = parser.parse_args()
    
    # No FILE
    if not args.FILE:
        details = get_stdin_details()
        print(details.char_count)
        sys_exit(0)

    # FILE provided
    for path in args.FILE:
        if path == "-":
            details = get_stdin_details()
        else:
            try:
                details = get_file_details(path)
            except FileNotFoundError:
                print(f"{parser.prog}: {path}: No such file or directory")
                sys_exit(1)
            except IsADirectoryError:
                print(f"{parser.prog}: {path}: Is a directory")
                sys_exit(1)
            except PermissionError:
                print(f"{parser.prog}: {path}: Permission denied")
                sys_exit(1)
        print(details.char_count)


def get_file_details(path:str) -> Details:
    details = Details()
    with open(path, "r") as file:
        for line in file:
            for char in line:
                # BYTES
                details.byte_count += len(char.encode("utf-8"))
                # CHARS
                details.char_count += 1

    return details


def get_stdin_details() -> Details:
    details = Details()
    data = stdin.buffer.read()
    # BYTES
    details.byte_count += len(data)
    for _ in data:
        # CHARS
        details.char_count += 1

    return details


if __name__ == "__main__":
    main()

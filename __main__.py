from argparse import ArgumentParser, RawTextHelpFormatter
from sys import exit as sys_exit, stdin
from enum import Enum


class Details:
    byte_count = 0
    char_count = 0
    newline_count = 0
    max_line_length = 0
    word_count = 0


class State(Enum):
    LINES = 1
    WORDS = 2
    BYTES = 4
    CHARS = 8
    LENGTH = 16


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
    parser.add_argument("-l", "--lines", action="store_true", help="Print the newline counts")
    parser.add_argument("--files0-from", type=str, help="Read input from the files specified by NUL-terminated names in file F; If F is - then read names from standard input")
    parser.add_argument("-L", "--max-line-length", action="store_true", help="Print the maximum display width")
    parser.add_argument("-w", "--words", action="store_true", help="Print the word counts")

    args = parser.parse_args()

    state = get_state(args)
    
    # No FILE
    if not args.FILE + (get_files0_from(args.files0_from) if args.files0_from else []):
        details = get_stdin_details()
        print_report(state, details)
        sys_exit(0)

    # FILE provided
    for path in args.FILE + (get_files0_from(args.files0_from) if args.files0_from else []):
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
        print_report(state, details, path)


def get_file_details(path:str) -> Details:
    details = Details()
    with open(path, "r") as file:
        for line in file:
            line_length = 0
            is_word = False
            # LINES
            details.newline_count += 1
            for char in line:
                # BYTES
                details.byte_count += len(char.encode("utf-8"))
                # CHARS
                details.char_count += 1
                # LENGTH
                line_length += 1
                # WORDS
                if char.isspace():
                    if is_word:
                        details.word_count += 1
                    is_word = False
                else:
                    is_word = True

            if line_length > details.max_line_length:
                details.max_line_length = line_length - 1

            if is_word:
                details.word_count += 1

    return details


def get_stdin_details() -> Details:
    details = Details()
    data = stdin.buffer.read()
    line_length = 0
    is_word = False
    # BYTES
    details.byte_count += len(data)
    for byte in data:
        char = chr(byte)
        # LENGTH
        line_length += 1
        # CHARS
        details.char_count += 1
        # LINES
        if char == "\n":
            details.newline_count += 1
            line_length = 0
            if line_length > details.max_line_length:
                details.max_line_length = line_length

        if line_length > details.max_line_length:
            details.max_line_length = line_length

        # WORDS
        if char.isspace():
            if is_word:
                details.word_count += 1
            is_word = False
        else:
            is_word = True

    if is_word:
        details.word_count += 1

    return details


def get_files0_from(path) -> list[str]:
    with open(path, "r") as file:
        text = file.read()
        return [x for x in text.split("\0")]


def get_state(args) -> int:
    state = 0
    state |= args.lines * State.LINES.value
    state |= args.words * State.WORDS.value
    state |= args.chars * State.CHARS.value
    state |= args.bytes * State.BYTES.value
    state |= args.max_line_length * State.LENGTH.value

    return state or State.WORDS.value | State.LINES.value | State.BYTES.value


def print_report(state, details, path="") -> None:
    if state & State.LINES.value:
        print(f"{details.newline_count:4}", end="  ")
    if state & State.WORDS.value:
        print(f"{details.word_count:4}", end="  ")
    if state & State.CHARS.value:
        print(f"{details.char_count:4}", end="  ")
    if state & State.BYTES.value:
        print(f"{details.byte_count:4}", end="  ")
    if state & State.LENGTH.value:
        print(f"{details.max_line_length:4}", end="  ")
    print(path)


if __name__ == "__main__":
    main()

from argparse import ArgumentParser, RawTextHelpFormatter
from os import cpu_count
from sys import exit as sys_exit, stdin
from enum import Enum


class Details:
    byte_count = 0
    char_count = 0
    newline_count = 0
    max_line_length = 0
    word_count = 0

    def __add__(self, other):
        tmp = Details()
        tmp.byte_count = self.byte_count + other.byte_count
        tmp.char_count = self.char_count + other.char_count
        tmp.newline_count = self.newline_count + other.newline_count
        tmp.max_line_length = self.max_line_length + other.max_line_length
        tmp.word_count = self.word_count + other.word_count

        return tmp


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
    parser.add_argument("--total", choices=["auto", "always", "only", "never"], help="When to print a line with total counts; WHEN can be: auto, always, only, never", default="auto")

    args = parser.parse_args()

    state = get_state(args)
    file_list = args.FILE + (get_files0_from(args.files0_from) if args.files0_from else [])
    
    # TOTAL
    show_total = False
    if (args.total != "never" and len(file_list) > 1) or args.total == "always" or args.total == "only":
        show_total = True
    
    # No FILE
    if not file_list:
        details = get_stdin_details()
        if args.total != "only":
            print_report(state, details)
        if show_total:
            print_report(state, details, "total")
        sys_exit(0)

    # FILE provided
    total_details = Details()
    for path in file_list:
        if path == "-":
            details = get_stdin_details()
        else:
            try:
                details = get_file_details(path)
            except FileNotFoundError:
                print(f"{parser.prog}: {path}: No such file or directory")
                continue
            except IsADirectoryError:
                print(f"{parser.prog}: {path}: Is a directory")
                continue
            except PermissionError:
                print(f"{parser.prog}: {path}: Permission denied")
                continue
        if show_total:
            total_details = total_details + details
        if args.total != "only":
            print_report(state, details, path)
    if show_total:
        print_report(state, total_details, "total")


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

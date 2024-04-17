"""Check that GitHub issues (and PR) links match the number in Markdown link."""

import glob
import re
import sys

if __name__ == "__main__":
    p = re.compile(
        r"\[#(?P<number1>[0-9]+)\]"
        r"\(https://github\.com/"
        r"(?:[a-zA-Z0-9_-]+)/(?:[a-zA-Z0-9_-]+)/"
        r"(?:(?:issues)|(?:pull))/(?P<number2>[0-9]+)\)"
    )

    ret_code = 0

    for glob_pattern in sys.argv[1:]:
        for file in glob.glob(glob_pattern, recursive=True):
            with open(file) as f:
                for i, line in enumerate(f):
                    for m in p.finditer(line):
                        if m.group("number1") != m.group("number2"):
                            start, end = m.span()
                            print(f"{file}:{i}: ", line[start:end], file=sys.stderr)  # noqa: T201
                            ret_code = 1

    sys.exit(ret_code)

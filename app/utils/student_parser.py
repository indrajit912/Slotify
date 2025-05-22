# app/utils/student_parser.py
# Author: Indrajit Ghosh
# Created On: May 22, 2025
# 
from config import Config

def parse_enrolled_students(raw_data: str):
    """
    Parse a multiline string to extract (fullname, roll number) tuples.

    The roll number is identified by a known prefix such as 'rs_', 'bmat', 'mmat'.
    The division (any text after the roll number) is ignored.

    Args:
        raw_data (str): Multiline string with each line like 'Full Name   rollnumber   division'

    Returns:
        List[Tuple[str, str]]: List of (fullname, roll number) tuples
    """
    roll_prefixes = Config.ISI_ROLL_PREFIXES
    result = []

    for line in raw_data.strip().split('\n'):
        words = line.strip().split()
        for i, word in enumerate(words):
            if any(word.startswith(prefix) for prefix in roll_prefixes):
                fullname = ' '.join(words[:i])
                roll = word
                result.append((fullname, f"{roll.strip()}@isibang.ac.in"))
                break  # Found the roll number, no need to look further in this line

    return result


if __name__ == '__main__':
    print("Paste the multiline student list below. Enter an empty line to finish:\n")
    lines = []
    while True:
        line = input()
        if line.strip() == '':
            break
        lines.append(line)
    raw_text = '\n'.join(lines)

    students = parse_enrolled_students(raw_text)
    print("\nParsed students:\n")
    for fullname, email in students:
        print(f"{fullname} -> {email}")

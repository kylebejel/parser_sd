import re

def extract_tm(text):
    # can be expanded by appending regex for [int]..[int]..[int]
    # parenthises separate groups
    tm_pattern = re.compile("\[TM: ([0-9]{4}|[0-9]{5}) ([a-zA-Z]{2}|[a-zA-Z]{3})\] [A-Z] [0-9]")

    found_tm = tm_pattern.search(text)

    # more variables can be made for data values
    int_id = found_tm.group(1)
    name_id = found_tm.group(2)

    # loop through entries and extract info into variables, and then push to db (need to figure out schema)

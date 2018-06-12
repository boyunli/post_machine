import re

SUCCEED_STATUS = 1
FAILED_STATUS = 2

def trim(line):
    return re.sub('[\r\s]', '', line)


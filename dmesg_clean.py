#!/usr/bin/env python3

'''
This script helps to clean the dmesg printed by 'pr' macro, while keeping the original file for further investigation.
'''

import sys
import os

# Print usage and exit abnormally
def print_usage_and_exit(args):
    print("Usage:", args[0], "[input file]", "[-sb keep square backets]", "[-b keep brackets]")
    sys.exit(-1)

# Parse/get arguments
args = sys.argv.copy()
if len(args) < 2:
    print_usage_and_exit(args)

sb = False
if "-sb" in args:
    sb = True
    args.remove("-sb")

b = False
if "-b" in args:
    b = True
    args.remove("-b")

try:
    arg = args.pop(1)
except:
    print("Cannot parse log file path")
    print_usage_and_exit(args)
if not os.path.isfile(arg):
    print("Cannot access log file:", arg)
    print_usage_and_exit(args)
if not os.path.getsize(arg):
    print("Log file is empty:", arg)
    print_usage_and_exit(args)

if len(args) > 1:
    print("Unrecognized argument(s):", args[1:])
    print_usage_and_exit(args)

file = []
try:
    with open(arg) as infile:
        for line in infile:
            file.append(line)
except:
    print("Error opening file:", arg)
    print_usage_and_exit(args)

# Purge square brackets
if not sb:
    for l in range(0, len(file)):
        if file[l][0] != '[':
            continue
        for i in range(1, len(file)):
            if file[l][i] == ']':
                break
        file[l] = file[l][i + 2:]

# Purge brackets
if not b:
    for l in range(0, len(file)):
        if len(file[l]) < 2 or file[l][len(file[l]) - 2] != ')':
            continue
        for i in range(len(file[l]) - 3, -1, -1):
            if file[l][i] == '(':
                break
        if file[l][i:i + 4] != "(at ":
            continue
        file[l] = file[l][:i - 1] + '\n'

# Print to the terminal
for l in file:
    print(l, end="")

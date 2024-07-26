#!/usr/bin/env python3

'''
This script helps to clean the dmesg printed by 'pr' macro, while keeping the original file for further investigation.
'''

import sys
import os

# Print usage and exit abnormally
def print_usage_and_exit(args):
    print("Usage:", args[0], "[input file]", "[-o output file]", "[-sb keep square backets]", "[-b keep brackets]", "[-q quiet]")
    print("Cannot keep both (-sb and -b). Must have an output (not -q or -o).")
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

if sb and b:
    print_usage_and_exit(args)

out = None
if "-o" in args:
    try:
        out = args.pop(args.index("-o") + 1)
        args.remove("-o")
    except:
        print("Invalid output file")
        print_usage_and_exit(args)

q = False
if "-q" in args:
    q = True
    args.remove("-q")

if not out and q:
    print_usage_and_exit(args)

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
    print("Unrecognized argument(s):", args)
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
if not q:
    for l in file:
        print(l, end="")

# Write output file
if out:
    try:
        with open(out, "w") as outfile:
            for i in range(0, len(file)):
                outfile.write(file[i])
    except:
        print("Error writing file:", out)
        exit(-1)

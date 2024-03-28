#!/usr/bin/env python3

'''
This script evaulates the log file generated by the perf script.
It is useful when evaulating the PW latency statistics.

Usage:
File generated by perf script
Partitons, separated by comma, unit: runs
Exclusions, separated by comma, unit: run# (starting from #1, this affacts partitions)

Example:
chmod +x page_walk_counter.py
./page_walk_counter.py perf-always.log -p 3,3 -e 1 (Partitons: run 2,3,4; run 5,6,7; 1 excluded)
'''

import sys
import os
import statistics

'''
Print usage and exit abnormally. (Why python does not support goto?)

Args:
Arguments.

Returns:
-1 to the OS.
'''
def print_usage_and_exit(args):
    print("Usage:", args[0], "perf.log", "[-p partitions]", "[-e exclusions]")
    sys.exit(-1)

# Parse arguments and file loading
args = sys.argv.copy()
if len(args) < 2:
    print_usage_and_exit(args)

partition = []
if "-p" in args:
    try:
        arg = "(None)"
        arg = args.pop(args.index("-p") + 1)
        partition = [int(i) for i in arg.split(",")]
        args.remove("-p")
    except:
        print("Invalid partition argument:", arg)
        print_usage_and_exit(args)

exclusion = []
if "-e" in args:
    try:
        arg = "(None)"
        arg = args.pop(args.index("-e") + 1)
        exclusion = [int(i) for i in arg.split(",")]
        args.remove("-e")
    except:
        print("Invalid exclusion argument:", arg)
        print_usage_and_exit(args)

arg = args.pop(1)
if not os.path.isfile(arg):
    print("Invalid log file:", arg)

if len(args) > 1:
    print("Unrecognized argument(s):", args[1 :])
    print_usage_and_exit(args)

file = []
try:
    with open(arg) as infile:
        print("Loading...")
        for line in infile:
            file.append(line)
except:
    print("Error opening file")
    print_usage_and_exit(args)

valid_cols = ["dtlb_load_misses.walk_completed", "dtlb_load_misses.walk_pending", "dtlb_load_misses.walk_active",
              "dtlb_store_misses.walk_completed", "dtlb_store_misses.walk_pending", "dtlb_store_misses.walk_active",
              "itlb_misses.walk_completed", "itlb_misses.walk_pending", "itlb_misses.walk_active",
              "cycles:ukhHG"]

'''
Read a line in the perf file.

Args:
A line in the perf file.

Returns:
If the line contains valid data, return the 3 columns of interest plus CPU speed if available (len = 4)
If the line contains benchmark result, return the result (len = 1)
If the line is invalid, return an empty list (len = 0)
'''
def read_line(line):
    time = 0.0
    counts = 0
    col = 0
    speed = 0.0
    components = line.split(" ")
    if components[0] == "Took:":
        return [float(components[1].split("\n")[0])]
    if "GHz" in components:
        speed = float(components[components.index("GHz") - 1])
    for component in components:
        if component == "":
            continue
        try:
            if col == 0:
                time = float(component)
                col += 1
            elif col == 1:
                component = component.replace(",", "")
                counts = int(component)
                col += 1
            elif col == 2:
                if component in valid_cols:
                    return [time, counts, component, speed]
                else:
                    return []
        except:
            return []
    return []

'''
Calculate the page walk latency.

Args:
Counts of columns of interest from one run.

Returns:
Page walk latency.
'''
def get_pw_latency(event_counts):
    pending = event_counts[valid_cols.index("dtlb_load_misses.walk_pending")] +\
        event_counts[valid_cols.index("dtlb_store_misses.walk_pending")] +\
        event_counts[valid_cols.index("itlb_misses.walk_pending")]
    completed = event_counts[valid_cols.index("dtlb_load_misses.walk_completed")] +\
        event_counts[valid_cols.index("dtlb_store_misses.walk_completed")] +\
        event_counts[valid_cols.index("itlb_misses.walk_completed")]
    if not completed:
        print("Warning: divide by zero")
        return 0.0
    return pending / completed

'''
Get relative precentage with all available data.

Args:
Current data and all available data as numbers in a list.

Returns:
Relative precentages formatted as strings in a list.
'''
def get_relative(current, all):
    ret = []
    for i in all:
        ret += ['{:.3%}'.format((i - current) / current)]
    return ret

'''
Read one run in the perf file.

Args:
A line number in the perf file.

Returns:
A list contains the next line, runtime, PW latency, speed, eval time, from to last lines, and columns of interest, accumulated.
If the run is the last run, the line number will be 0.
If the run is not the last run, the line number will be the begining of the next run.
'''
def read_run(line_num):
    end_time = 0.0
    end_linenum = 0
    next_linenum = 0
    runtime = 0.0
    pw_latency = 0.0
    speed = 0.0
    speed_count = 0
    event_counts = [0] * len(valid_cols)
    for i in range(line_num, len(file) - 1):
        cols = read_line(file[i])
        if len(cols) == 4:
            if cols[0] >= end_time:
                end_time = cols[0]
                end_linenum = i
                event_counts[valid_cols.index(cols[2])] += cols[1]
                if cols[3]:
                    speed += cols[3]
                    speed_count += 1
            elif cols[0] < end_time:
                next_linenum = i
                break
        elif len(cols) == 1:
            if runtime != 0 and cols[0] != runtime:
                print("Warning: runtime differs in one run")
            runtime = cols[0]
    pw_latency = get_pw_latency(event_counts)
    return [next_linenum, runtime, pw_latency, speed / speed_count, end_time, line_num, end_linenum] + event_counts

# Evaluate all runs, record and print summaries.
line_num = 0
eval_count = 0
run_num = []
runtime = []
pw_latency = []
speed = []
stats = []
while True:
    this_stats = read_run(line_num)
    line_num, this_runtime, this_latency, this_speed = this_stats[0 : 4]
    if not this_runtime:
        print("Note: detected and omitted incomplete run after run #", eval_count, sep="")
    eval_count += 1
    if eval_count not in exclusion and this_runtime:
        runtime += [this_runtime]
        pw_latency += [this_latency]
        speed += [this_speed]
        stats += [this_stats[4 :]]
        run_num += [eval_count]
    if not line_num:
        break

for i in range(0, len(run_num)):
    print("")
    print("Run #", run_num[i], ", duration: ", stats[i][0], ", lines: ", stats[i][1] + 1, " -> ", stats[i][2] + 1, sep="")
    print("Runtime:", '{:.3f}'.format(runtime[i]))
    print("Relative runtime:", get_relative(runtime[i], runtime))
    print("Page walk latency:", '{:.3f}'.format(pw_latency[i]))
    print("Relative latency:", get_relative(pw_latency[i], pw_latency))
    print("Reference CPU speed:", '{:.3f}'.format(speed[i]), "GHz")
    print("Relative CPU speed:", get_relative(speed[i], speed))
    for j in range(3, len(stats[i])):
        print(valid_cols[j - 3], stats[i][j], sep=": ")

# Evaulate all partitions if supplied, print summaries.
partition_sum = sum(partition)
run_start = 0
run_end = 0
avg_runtime = []
avg_latency = []
avg_speed = []
if not len(partition) or partition_sum > len(run_num):
    print("")
    if len(partition):
        print("Warning: paritions are not applied because there are not enough runs to evaulate")
    print("Average runtime:", '{:.3f}'.format(statistics.mean(runtime)))
    print("Average page walk latency:", '{:.3f}'.format(statistics.mean(pw_latency)))
    print("Average CPU speed:", '{:.3f}'.format(statistics.mean(speed)), "GHz")
    print("")
    print("Note: all relative data are \"others compared to current\"")
    exit(0)
else:
    for i in range(0, len(partition)):
        run_end = run_start + partition[i]
        avg_runtime += [statistics.mean(runtime[run_start : run_end])]
        avg_latency += [statistics.mean(pw_latency[run_start : run_end])]
        avg_speed += [statistics.mean(speed[run_start : run_end])]
        run_start = run_end

run_start = 0
run_end = 0
for i in range(0, len(partition)):
    run_end = run_start + partition[i]
    print("")
    print("Partition #", i + 1, ", runs: ", run_num[run_start : run_end], sep="")
    print("Average runtime:", '{:.3f}'.format(avg_runtime[i]))
    print("Relative average runtime:", get_relative(avg_runtime[i], avg_runtime))
    print("Average page walk latency:", '{:.3f}'.format(avg_latency[i]))
    print("Relative page walk latency:", get_relative(avg_latency[i], avg_latency))
    print("Average CPU speed:", '{:.3f}'.format(avg_speed[i]), "GHz")
    print("Relative CPU speed:", get_relative(avg_speed[i], avg_speed))
    run_start = run_end

print("")
print("Note: all relative data are \"others compared to current\"")

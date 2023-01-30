import argparse
from datetime import datetime
import re
from pathlib import Path
import matplotlib.pyplot as plt
import os
import shutil


def main():
    parser = argparse.ArgumentParser(
        prog='iotop_parser',
        description='Parse the output from iotop into CSV')

    parser.add_argument('source', help="File containing the iotop output")
    args = parser.parse_args()

    if not Path(args.source).exists():
        print(f"ERROR: Cannot find path {args.source}")
        return

    if not os.path.exists('./output'):
        os.mkdir("./output")
    else:
        shutil.rmtree("./output")
        os.mkdir("./output")

    parse_results(args.source)


def parse_results(filepath):
    """
    Attempt to parse the output from iotop and generate graphs showing I/O for each process
    """
    print("Parsing results")

    results = {}

    timestamp = None
    with open(filepath, 'r') as file:
        for line in file:
            stripped = line.strip()

            # This line indicates a new set of data
            if stripped.startswith('Total DISK READ'):
                timestamp = get_timestamp(stripped)
                results[timestamp] = []
                continue

            if re.match('\d* .*', stripped):
                # Got a line containing data
                io_stats = get_io_stats(stripped)
                results[timestamp].append(io_stats)

    # Work out which processes were recorded, store in a set
    processes = set()
    for timestamp in results:
        for entry in results[timestamp]:
            if entry['command'] not in processes:
                processes.add(entry['command'])

    # Build final data set, including empty timestamps
    to_plot = {}

    for process in processes:
        to_plot[process] = {}
        for timestamp in results:
            # Get the data recorded at this timestamp
            data = results[timestamp]

            if len(data) == 0 or not any(d['command'] == process for d in data):
                # Either no data recorded at all at this timestamp or this processes reported
                # no IO
                to_plot[process][timestamp] = build_empty_result()
            else:
                # This process has data at this timestamp
                to_plot[process][timestamp] = [
                    d for d in data if d['command'] == process][0]

    # Build plots
    for process in processes:
        data_to_plot = to_plot[process]

        fig, ax = plt.subplots()

        timestamps = list(data_to_plot.keys())

        write = ax.plot(timestamps, [d['disk_write_kbps']
                for d in data_to_plot.values()], "-", color='tab:orange', label="Write KB/s")
        read = ax.plot(timestamps, [d['disk_read_kbps']
                for d in data_to_plot.values()], "-", color='tab:blue', label="Read KB/s")

        ax.set(xlabel='Timestamp', ylabel='KB/s',
               title=process)


        # Create a right-hand axis
        ax2 = ax.twinx()
        swapin = ax2.plot(timestamps, [d['swap_in_percent'] for d in data_to_plot.values()], "--", color="tab:green", label="Swap In %")
        io = ax2.plot(timestamps, [d['io_percent'] for d in data_to_plot.values()], "--", color="tab:purple", label="IO %")

        # Build a single legend with all lines
        lines = write+read+swapin+io
        labels = [l.get_label() for l in lines]

        ax.legend(lines, labels, loc=0)
        ax.set_ylim([0, None])

        ax2.set(ylabel='%')
        ax2.set_ylim([0, 100])

        ax.grid()

        filename = process
        if '/' in filename:
            filename = filename.replace('/', '_')

        fig.set_figwidth(15)
        fig.savefig(f"./output/{filename}.png", dpi=300)

    # # Re-organise dict based on process
    # process_data = {}

    # for timestamp in results:
    #     data = results[timestamp]

    #     for entry in data:
    #         if not process_data.get(entry['command']):
    #             process_data[entry['command']] = {}

    #         process_data[entry['command']][timestamp] = entry

    # # Create plots
    # fig, ax = plt.subplots()

    # timestamps = list(process_data['syslog-ng'])

    # data_points = []
    # for timestamp in timestamps:
    #     data_points.append(process_data['syslog-ng'][timestamp])

    # ax.plot(timestamps, [d['disk_write_kbps'] for d in data_points], label = 'Disk Write')
    # ax.plot(timestamps, [d['disk_read_kbps'] for d in data_points], label = 'Disk Read')

    # ax.set(xlabel='Timestamp', ylabel='KB/s',
    #    title='syslog-ng')
    # ax.legend()
    # ax.grid()

    # plt.show()

    return {}


def get_timestamp(line):
    match = re.match('^(Total DISK READ:.*\| )(.*)$', line)

    if match.group(2):
        date = datetime.strptime(match.group(2), '%a %b %d %H:%M:%S %Y')
        return date


def build_empty_result():
    stats = {}
    stats['pid'] = 0
    stats['prio'] = ""
    stats['user'] = ""
    stats['disk_read_kbps'] = 0.0
    stats['disk_write_kbps'] = 0.0
    stats['swap_in_percent'] = 0.0
    stats['io_percent'] = 0.0
    stats['command'] = ""

    return stats


def get_io_stats(line):
    stats = {}

    match = re.match(
        '(\d+)\s+(\w+\/\d)\s+([\w\d\-\.]*)\s+(\d+\.\d+) K\/s\s+(\d+\.\d+) K\/s (\d+\.\d+) % (\d+\.\d+) % ([a-zA-Z\-\_\w\/]*)', line)

    if not match:
        print(f"ERROR: Failed to parse line: {line}")
        return {}
    else:
        stats['pid'] = int(match.group(1))
        stats['prio'] = match.group(2)
        stats['user'] = match.group(3)
        stats['disk_read_kbps'] = float(match.group(4))
        stats['disk_write_kbps'] = float(match.group(5))
        stats['swap_in_percent'] = float(match.group(6))
        stats['io_percent'] = float(match.group(7))
        stats['command'] = match.group(8)

        return stats


if __name__ == "__main__":
    main()

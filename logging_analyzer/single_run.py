import argparse
import csv
import itertools
import os
from datetime import datetime, timedelta

try:
    from dateutil import parser as dateutil_parser
except:
    print('Error:', 'pip install python-dateutil')


def parse_perf_csv(perf_csv_path):
    '''
    [{key:value}]
    '''
    with open(perf_csv_path) as csvfile:
        csvreader = csv.DictReader(csvfile)
        return list(csvreader)


def prepare_db(db):
    def convert_db(db):
        for row in db:
            row['initial_timestamp'] = dateutil_parser.isoparse(row['initial_timestamp'])
            row['final_timestamp'] = dateutil_parser.isoparse(row['final_timestamp'])

    def append_latency_db(db):
        for row in db:
            row['latency'] = row['final_timestamp'] - row['initial_timestamp']

    convert_db(db)
    append_latency_db(db)


def print_row(row):
    modified_row = row.copy()
    modified_row['initial_timestamp'] = modified_row['initial_timestamp'].isoformat()
    modified_row['final_timestamp'] = modified_row['final_timestamp'].isoformat()
    print('Info:', *map(lambda kv: (str(kv[0]), str(kv[1])), modified_row.items()))


def group_by_time_interval_since_beginning(db, filter_func=None, interval_length=timedelta(seconds=1)):
    '''
    filter_func(row) returns false to ignore the row if filter_func is not None

    A list of groups, each group is defined to be
    having final_timestamp within [k, k+1] integer multiple of interval_length since the earliest initial_timestamp

    return [(len_after_first_group, rows)]
    sorted by len_after_first_group, and len_after_first_group is unique throughout the list
    rows are also sorted based on final_timestamp
    '''
    if filter_func is not None:
        db = list(filter(filter_func, db))

    if len(db) == 0:
        return

    # Base is set to be the earliest initial_timestamp
    first_timestamp = min(db, key=lambda row: row['initial_timestamp'])['initial_timestamp']
    print('Info:', 'first_timestamp:', first_timestamp)

    # Sort all rows by final_timestamp
    db = sorted(db, key=lambda row: row['final_timestamp'])
    grouped_by_sec = itertools.groupby(db, key=lambda row: int((row['final_timestamp']-first_timestamp)/interval_length))

    groups_of_rows = list()
    secs = list()
    for sec, rows in grouped_by_sec:
        groups_of_rows.append(sorted(rows, key=lambda row: row['final_timestamp']))
        secs.append(sec)

    return list(zip(secs, groups_of_rows))


def get_throughput(grouped_by_time_interval_since_beginning):
    '''
    Input should come from group_by_time_interval_since_beginning()

    return [(len_after_first_group, rows)]
    sorted by len_after_first_group, and len_after_first_group is unique throughout the list
    rows are also sorted based on final_timestamp

    return [(len_after_first_group, num_finished_within_the_interval)]
    '''
    return list(map(lambda id_rows: (id_rows[0], len(id_rows[1])), grouped_by_time_interval_since_beginning))


def init(parser):
    parser.add_argument('--log_dir', type=str, required=True, help='log file')


def main(args):
    perf_csv = os.path.join(args.log_dir, 'perf.csv')
    print('Info:', 'Analyzing', perf_csv)
    db = parse_perf_csv(perf_csv)
    prepare_db(db)

    # [(len_after_first_group, rows)]
    groupings = group_by_time_interval_since_beginning(db)
    print('Info:')
    print('Info:', 'Requests finished in each second after beginning')
    for (sec, group_of_rows) in groupings:
        print('Info:')
        print('Info:', sec)
        for row in group_of_rows:
            print_row(row)

    # Find the throughput for all time intervals since the beginning
    throughput = get_throughput(groupings)
    print('Info:')
    print('Info:', 'Throughput(#request_finished/sec) Trajectory')
    for item in throughput:
        print('Info:', item)

    # Find the peak throughput
    print('Info:')
    print('Info:', 'Peak throughput is', max(throughput, key=lambda kv: kv[1]))

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    init(parser)
    main(parser.parse_args())

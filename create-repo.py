#!/usr/bin/env python3

import argparse
import subprocess
import re
from csv import writer as csv_writer
from sys import argv
from os import path, mkdir
from shutil import rmtree

from openpyxl import load_workbook


def process_xlsx(args):
    commit_msg_regex = re.compile("\[master( \(root-commit\))? (.{7})\]")

    def _prepare_cmd(cmd):
        return "cd \"%s\"; %s" % (args['repo'], cmd)

    def _run(cmd):
        return subprocess.run(_prepare_cmd(cmd), shell=True, check=True, text=True, capture_output=True).stdout

    wb = load_workbook(args['grades'])
    report = open(args['output'], 'w')
    report_writer = csv_writer(report)
    report_writer.writerow(['First Name', 'Last Name', 'Email', 'Commit Hash'])

    if path.exists(args['repo']):
        rmtree(args['repo'])
    mkdir(args['repo'])
    _run("git init")

    try:
        for row in list(wb['Grades'].rows)[1:]:
            first_name = row[0].value
            last_name = row[1].value
            email = row[5].value
            commit_hash = commit_msg_regex.match(
                _run("git commit --allow-empty --allow-empty-message -m \"\" --author=\"%s %s <%s>\"" %
                     (first_name, last_name, email))
            ).group(2)
            report_writer.writerow([first_name, last_name, email, commit_hash])
    finally:
        wb.close()
        report.close()


def main():
    args_parser = argparse.ArgumentParser(
        prog="%s" % argv[0]
    )
    args_subparsers = args_parser.add_subparsers(description='operation type', required=True, dest='operation')
    parser_xlsx = args_subparsers.add_parser('xlsx', help='XLSX excel gradebook')
    parser_xlsx.add_argument('grades', type=str, help='address of XLSX gradebook')
    parser_xlsx.add_argument('repo', type=str, help='address of to-be-created git repository')
    parser_xlsx.add_argument('output', type=str, help='address of output CSV report')
    args = vars(args_parser.parse_args())
    globals()["process_%s" % args['operation']](args)


if __name__ == '__main__':
    main()

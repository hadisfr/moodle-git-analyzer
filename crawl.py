#!/usr/bin/env python3

import argparse
import re
import csv
import requests
from sys import argv
from shutil import copy2 as copy
from math import ceil


def get_students_list(addr):
    with open(addr, 'r') as f:
        reader = csv.DictReader(f)
        return {row['Commit Hash']: row for row in reader}


def set_students_list(addr, db, header):
    copy(addr, "%s~orig" % addr)
    with open(addr, 'w') as f:
        writer = csv.DictWriter(f, header)
        writer.writeheader()
        for row in db.values():
            writer.writerow(row)


def process_gitlab(path, list_addr):
    bucket = 100
    commits_url = "https://gitlab.com/%s/commits/master?limit=%s&offset=%%s" % (path, bucket)
    user_url = "https://gitlab.com/%s"
    commiters_regex = re.compile(
        "<li class=\"commit flex-row js-toggle-container\" id=\"commit-(.{8})\">\n" +
        "<div class=\"avatar-cell d-none d-sm-block\">\n" +
        "<a href=\"([^\"]*)\">"
    )
    user_created_at_regex = re.compile("<span class=\"middle-dot-divider\">\nMember since ([^>]*)\n</span>")
    db = get_students_list(list_addr)
    header = list(list(db.values())[0].keys())
    header.append('Gitlab Acconut')
    header.append('Gitlab Created at')
    for i in range(ceil(len(db) / bucket)):
        matches = commiters_regex.findall(requests.get(commits_url % (i * bucket)).text)
        for match in matches:
            if not match[1].startswith('mailto:'):
                username = match[1][1:]
                print(username)
                commit_hash = match[0]
                db[commit_hash[:7]]['Gitlab Acconut'] = username
                db[commit_hash[:7]]['Gitlab Created at'] = user_created_at_regex.findall(
                    requests.get(user_url % username).text
                )[0]
    set_students_list(list_addr, db, header)


def process_github(path, list_addr):
    pass


def main():
    args_parser = argparse.ArgumentParser(
        prog="%s" % argv[0]
    )
    args_parser.add_argument('site', choices=['gitlab', 'github'], help="online repo site")
    args_parser.add_argument('path', type=str, help="remote path")
    args_parser.add_argument('list', type=str, help="CSV list of students")
    args = vars(args_parser.parse_args())
    globals()["process_%s" % args['site']](args['path'], args['list'])


if __name__ == '__main__':
    main()

#!/usr/bin/env python3

import argparse
import re
import csv
import requests
from sys import argv, stderr
from shutil import copy2 as copy
from math import ceil
from time import sleep


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


def crawl_gitlab(path, list_addr):
    bucket = 100
    commits_url = "https://gitlab.com/%s/commits/master?limit=%s&offset=%%s" % (path, bucket)
    user_url = "https://gitlab.com/%s"
    user_projects_url = "https://gitlab.com/api/v4/users/%s/projects"
    user_contributions_url = "https://gitlab.com/users/%s/contributed.json"
    commiters_regex = re.compile(
        "<li class=\"commit flex-row js-toggle-container\" id=\"commit-(.{8})\">\n" +
        "<div class=\"avatar-cell d-none d-sm-block\">\n" +
        "<a href=\"([^\"]*)\">"
    )
    user_created_at_regex = re.compile("<span class=\"middle-dot-divider\">\nMember since ([^>]*)\n</span>")
    user_contributions_regex = re.compile("<a class=\"project\" href=\"([^\"]*)\">")

    db = get_students_list(list_addr)
    header = list(list(db.values())[0].keys())
    header.append('Gitlab Acconut')
    header.append('Gitlab Created at')
    header.append('Gitlab Personal Projects')
    header.append('Gitlab Contributions in Other\'s Projects')
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
                if '.' not in username:  # https://gitlab.com/gitlab-org/gitlab-ce/issues/51913
                    db[commit_hash[:7]]['Gitlab Personal Projects'] = requests.get(user_projects_url %
                                                                                   username).headers['X-Total']
                db[commit_hash[:7]]['Gitlab Contributions in Other\'s Projects'] = len(
                    user_contributions_regex.findall(
                        requests.get(user_contributions_url % username).json()['html']
                    )
                )
    set_students_list(list_addr, db, header)


def crawl_github(path, list_addr):
    def _api_call(url):
        while True:
            res = requests.get(url)
            if res.headers['X-RateLimit-Remaining']:
                return res
            else:
                print("Rate Limit Exceeded", file=stderr)
                sleep(3600)

    bucket = 100
    commits_url = "https://api.github.com/repos/%s/commits?per_page=%s&page=%%s" % (path, bucket)
    user_url = "https://github.com/%s"
    user_repositories_regex = re.compile("Repositories\n\ *<span class=\"Counter\">\n\ *([0-9]*)\n\ *</span>")
    user_stars_regex = re.compile("Stars\n\ *<span class=\"Counter\">\n\ *([0-9]*)\n\ *</span>")
    user_followers_regex = re.compile("Followers\n\ *<span class=\"Counter\">\n\ *([0-9]*)\n\ *</span>")
    user_followings_regex = re.compile("Following\n\ *<span class=\"Counter\">\n\ *([0-9]*)\n\ *</span>")

    db = get_students_list(list_addr)
    header = list(list(db.values())[0].keys())
    header.append('Github Acconut')
    header.append('Github Repositories')
    header.append('Github Stars')
    header.append('Github Followings')
    header.append('Github Followers')
    for i in range(ceil(len(db) / bucket)):
        commits = _api_call(commits_url % (i * bucket)).json()
        for commit in commits:
            if commit['author']:
                username = commit['author']['login']
                print(username)
                commit_hash = commit['sha']
                db[commit_hash[:7]]['Github Acconut'] = username
                user_page = requests.get(user_url % username).text
                db[commit_hash[:7]]['Github Repositories'] = user_repositories_regex.findall(user_page)[0]
                db[commit_hash[:7]]['Github Stars'] = user_stars_regex.findall(user_page)[0]
                db[commit_hash[:7]]['Github Followings'] = user_followings_regex.findall(user_page)[0]
                db[commit_hash[:7]]['Github Followers'] = user_followers_regex.findall(user_page)[0]
    set_students_list(list_addr, db, header)


def main():
    args_parser = argparse.ArgumentParser(
        prog="%s" % argv[0]
    )
    args_parser.add_argument('site', choices=['gitlab', 'github'], help="online repo site")
    args_parser.add_argument('path', type=str, help="remote path")
    args_parser.add_argument('list', type=str, help="CSV list of students")
    args = vars(args_parser.parse_args())
    globals()["crawl_%s" % args['site']](args['path'], args['list'])


if __name__ == '__main__':
    main()

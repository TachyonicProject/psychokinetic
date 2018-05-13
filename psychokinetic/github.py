# -*- coding: utf-8 -*-
# Copyright (c) 2018 Christiaan Frans Rademan.
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this
#   list of conditions and the following disclaimer.
#
# * Redistributions in binary form must reproduce the above copyright notice,
#   this list of conditions and the following disclaimer in the documentation
#   and/or other materials provided with the distribution.
#
# * Neither the name of the copyright holders nor the names of its
#   contributors may be used to endorse or promote products derived from
#   this software without specific prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS"
# AND ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE
# IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE
# ARE DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE
# LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR
# CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF
# SUBSTITUTE GOODS OR SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS
# INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY, WHETHER IN
# CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE)
# ARISING IN ANY WAY OUT OF THE USE OF THIS SOFTWARE, EVEN IF ADVISED OF
# THE POSSIBILITY OF SUCH DAMAGE.
from luxon.utils.http import Client
from luxon.utils.timezone import utc


def parse_repo(github_repo):
    repo = {}
    repo['name'] = github_repo['name']
    repo['description'] = github_repo['description']
    repo['clone_url'] = github_repo['clone_url']
    repo['git_url'] = github_repo['git_url']
    repo['ssh_url'] = github_repo['ssh_url']
    repo['html_url'] = github_repo['html_url']
    repo['created_at'] = utc(github_repo['created_at'])
    repo['updated_at'] = utc(github_repo['updated_at'])
    repo['pushed_at'] = utc(github_repo['pushed_at'])
    return repo


class GitHub(Client):
    def __init__(self, auth=None):
        super().__init__('https://api.github.com', auth=auth)

    def repos(self, user):
        github_repos = self.execute('GET', '/users/%s/repos' % user).json
        repos = []
        for github_repo in github_repos:
            repos.append(parse_repo(github_repo))
        return repos

    def repo(self, user, repo):
        github_repo = self.execute('GET', '/repos/%s/%s' % (user, repo,)).json
        return parse_repo(github_repo)

    def tags(self, user, repo):
        github_tags = self.execute('GET',
                                   '/repos/%s/%s/tags' % (user, repo,)).json
        tags = []
        for github_tag in github_tags:
            tags.append(github_tag['name'])
        return tags

    def branches(self, user, repo):
        github_branches = self.execute('GET',
                                       '/repos/%s/%s/branches' %
                                       (user, repo,)).json
        branches = []
        for github_branch in github_branches:
            branches.append(github_branch['name'])
        return branches

    def teams(self, user):
        headers = {'accept': 'application/vnd.github.inertia-preview+json'}
        github_teams = self.execute('GET',
                                    '/orgs/%s/teams' %
                                    user, headers=headers).json
        return github_teams

    def _events(self, user, repo):
        found_events = []
        github_events = self.execute('GET', '/repos/%s/%s/events' %
                                     (user, repo,)).json
        for github_event in github_events:
            found_events.append(github_event)

        return found_events

    def events(self, user, repo=None):
        github_repos = self.repos(user)
        found_events = []
        if repo is None:
            for github_repo in github_repos:
                repo = github_repo['name']
                found_events += self._events(user, repo)
        else:
            found_events = self._events(user, repo)

        return found_events

    def projects(self, user):
        projects = {}
        headers = {'accept': 'application/vnd.github.inertia-preview+json'}
        github_projects = self.execute('GET', '/orgs/%s/projects' % user,
                                       headers=headers).json
        for github_project in github_projects:
            id = github_project['id']
            name = github_project['name']
            projects[id] = {}
            projects[id]['name'] = name
            body = github_project['body']
            projects[id]['description'] = body
            state = github_project['state']
            html_url = github_project['html_url']
            projects[id]['url'] = html_url
            projects[id]['columns'] = []
            if state == 'open':
                github_columns = self.execute('GET',
                                              '/projects/%s/columns' % id,
                                              headers=headers).json
                for github_column in github_columns:
                    column = {}
                    projects[id]['columns'].append(column)

                    column_id = github_column['id']
                    column_name = github_column['name']
                    column['name'] = column_name
                    column['cards'] = []

                    github_cards = self.execute('GET',
                                                'projects/columns/%s/cards' %
                                                column_id,
                                                headers=headers).json
                    for github_card in github_cards:
                        card = {}
                        column['cards'].append(card)

                        note = github_card['note']
                        card['assignees'] = []
                        if 'content_url' in github_card:
                            content_url = github_card['content_url']
                            github_card_content = self.execute(
                                'GET',
                                content_url,
                                headers=headers
                            ).json
                            title = github_card_content['title']
                            card['title'] = title
                            body = github_card_content['body']
                            card['body'] = body
                            html_url = github_card_content['html_url']
                            card['html_url'] = html_url
                            assignees = github_card_content['assignees']
                            for assignee in assignees:
                                login = assignee['login']
                                card['assignees'].append(login)
                        else:
                            card['title'] = 'Note'
                            card['body'] = note
                            card['html_url'] = None

        return projects

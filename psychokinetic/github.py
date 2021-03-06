# -*- coding: utf-8 -*-
# Copyright (c) 2018-2020 Christiaan Frans Rademan <chris@fwiw.co.za>.
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
from luxon.utils.http import Client, parse_link_header


class GitHub(Client):
    def __init__(self, auth=None):
        super().__init__('https://api.github.com', auth=auth)

    def execute(self, method, url, headers={}, **kwargs):
        headers = headers.copy()
        response = super().execute(method, url, headers=headers, params=kwargs)
        if isinstance(response.json, list):
            responses = [] + response.json
            links = parse_link_header(response.headers.get('link'))
            if links.next is not None:
                responses += super().execute('GET',
                                             links.next[0]['link'],
                                             params=kwargs).json

            return responses

        return response.json

    def repos(self, user):
        github_repos = self.execute('GET', '/users/%s/repos' % user)
        repos = []
        for github_repo in github_repos:
            repos.append(github_repo)
        return repos

    def repo(self, user, repo):
        github_repo = self.execute('GET', '/repos/%s/%s' % (user, repo,))
        return github_repo

    def tags(self, user, repo):
        github_tags = self.execute('GET',
                                   '/repos/%s/%s/tags' % (user, repo,))
        return github_tags

    def branches(self, user, repo):
        github_branches = self.execute('GET',
                                       '/repos/%s/%s/branches' %
                                       (user, repo,))
        return github_branches

    def teams(self, user):
        headers = {'accept': 'application/vnd.github.inertia-preview+json'}
        github_teams = self.execute('GET',
                                    '/orgs/%s/teams' %
                                    user, headers=headers)
        return github_teams

    def team_members(self, team_id):
        headers = {'accept': 'application/vnd.github.inertia-preview+json'}
        github_teams = self.execute('GET',
                                    '/teams/%s/members' %
                                    team_id, headers=headers)
        return github_teams

    def user(self, username):
        headers = {'accept': 'application/vnd.github.inertia-preview+json'}
        github_teams = self.execute('GET',
                                    '/users/%s' %
                                    username, headers=headers)
        return github_teams

    def _events(self, user, repo):
        found_events = []
        github_events = self.execute('GET', '/repos/%s/%s/events' %
                                     (user, repo,))
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

    def commits(self, user, repo, **kwargs):
        return self.execute('GET', '/repos/%s/%s/commits' % (user,
                            repo, ), **kwargs)

    def projects(self, user):
        projects = {}
        headers = {'accept': 'application/vnd.github.inertia-preview+json'}
        github_projects = self.execute('GET', '/orgs/%s/projects' % user,
                                       headers=headers)
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
                                              headers=headers)
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
                                                headers=headers)
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
                            )
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

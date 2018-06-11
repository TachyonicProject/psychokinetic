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
import json

from psychokinetic.openstack.api.apibase import APIBase
from luxon.exceptions import FieldMissing


class IdentityV3(APIBase):

    def authenticate(self, username, password, domain):
        _token_url = self.client.keystone_url.rstrip('/') + '/auth/tokens'
        _password = {
            'user': {'name': username, 'domain': {'name': domain},
                     'password': password}}
        _identity = {'methods': ['password'], 'password': _password}
        _auth = {'identity': _identity}
        _login = json.dumps({'auth': _auth})

        _response = self.client.execute('POST', _token_url, data=_login)

        self.client._login_token = self.client['X-Auth-Token'] = \
        _response.headers['x-subject-token']


    def scope(self, domain=None, project_id=None, project_name=None):
        """Changes scope on Openstack Identity

        Args:
            Either specify the project ID or Name. Domain is only required
            in the case of Project Name, domain is not required for Project
            ID.

        """
        _token_url = self.client.keystone_url.rstrip('/') + '/auth/tokens'
        _identity = {'methods': ['token'],
                     'token': {'id': self.client._login_token}}
        _project = {}

        if domain:
            _project['domain'] = {'name': domain}
            self.client['domain_header'] = domain
        if project_id:
             _project['id'] = project_id
        elif project_name:
            if not domain:
                raise FieldMissing('domain', 'domain',
                                   'Scoping requires domain with Project Name')
            _project['name'] = project_name

        else:
            raise FieldMissing('project_id or project_name', 'Project',
                               'Scoping requires either Project ID or Name')

        _scope = {'project': _project}
        _auth = {'identity': _identity, 'scope': _scope}
        _login = json.dumps({'auth': _auth})

        _response = self.client.execute('POST', _token_url, data=_login)

        _catalog = _response.json['token']['catalog']
        self.client._scoped_token = self.client['X-Auth-Token'] = \
            _response.headers['x-subject-token']
        self.client['project_id_header'] = _response.json['token']['project'][
            'id']

        for c in _catalog:
            for e in c['endpoints']:
                if e['region'] == self.client.region:
                    if e['interface'] == 'internal':
                        self.client._user_endpoints[c['type']] = e['url']
                    elif e['interface'] == 'public':
                        self.client._public_endpoints[c['type']] = e['url']
                    elif e['interface'] == 'admin':
                        self.client._admin_endpoints[c['type']] = e['url']


    def unscope(self):
        """Unscope everything and go back to when we just had unscoped
        authentication.
        """
        self.client['X-Auth-Token'] = self.client._login_token
        self.client._scoped_token = None
        self.client._user_endpoints = {}
        self.client._public_endpoints = {}
        self.client._admin_endpoints = {}
        try:
            del self.client['project_id_header']
        except:
            pass
        try:
            del self.client['domain_header']
        except:
            pass

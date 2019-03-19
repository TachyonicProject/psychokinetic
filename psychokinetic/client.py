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
import multiprocessing

from luxon.utils.http import Client as HTTPClient
from luxon import g
from luxon.exceptions import TokenExpiredError
from luxon.helpers.cache import cache

from psychokinetic.objectstore.client import ObjectStore

lock = multiprocessing.Lock()


class Client(HTTPClient, ObjectStore):
    """Tachyonic RestApi Client.

    Client wrapped around RestClient using python requests.

    Provided for convienace to using RESTful API.

    Provides simple authentication methods and tracks endpoints.
    Keeps connection to specfici host, port open and acts like a singleton
    providing each thread continues request apabilities without reconnecting.

    Args:
        url (str): URL of Tachyonic main endpoint API.
        endpoint (str): Default End point to use for all calls. (optional)
        timeout (float/tuple): How many seconds to wait for the server to send
            data before giving up, as a float, or a (connect timeout, read
            read timeout) tuple. Defaults to (8, 2) (optional)
        auth (tuple): Auth tuple to enable Basic/Digest/Custom HTTP Auth.
            ('username', 'password' ) pair.
        verify (str/bool): Either a boolean, in which case it controls whether
            we verify the server's TLS certificate, or a string, in which case
            it must be a path to a CA bundle to use. Defaults to True.
            (optional)
        cert (str/tuple): if String, path to ssl client cert file (.pem). If
            Tuple, ('cert', 'key') pair.
    """
    def __init__(self, url=None, timeout=(2, 8),
                 auth=None, verify=True,
                 cert=None):
        super().__init__(url, timeout, auth, verify, cert)
        self._reauth = None
        self._regions = set([])

    def execute(self, method, uri, params=None,
                data=None, headers=None, endpoint=None,
                sort=None, limit=None, page=None, **kwargs):

        params = params or {}

        if limit is not None:
            params['limit'] = limit
        if page is not None:
            params['page'] = page
        if sort is not None:
            params['sort'] = page

        # Important for confederations etc..
        if endpoint == 'identity' and 'identity' not in self.endpoints:
            endpoint = None

        headers = headers or {}
        try:
            return super().execute(method, uri, params,
                                   data, headers, endpoint,
                                   default_endpoint_name='identity',
                                   **kwargs)
        except TokenExpiredError:
            with lock:
                if self._reauth:
                    self._reauth()
                    return super().execute(method, uri, params,
                                           data, headers, endpoint, **kwargs)
                else:
                    raise

    def collect_endpoints(self, region="Region1", interface='public'):
        response = cache(30, self.execute, 'GET', '/v1/endpoints',
                         headers=False)
        for endpoint in response.json['payload']:
            if endpoint['interface'] == interface:
                self._regions.add(endpoint['region'])
                if endpoint['region'] == region:
                    self.endpoints[endpoint['name']] = endpoint['uri']

    @property
    def regions(self):
        return sorted(list(self._regions))

    def config(self):
        self._url = g.app.config.get('identity', 'url')
        domain = g.app.config.get('identity', 'domain', fallback=None)
        username = g.app.config.get('identity', 'username', fallback=None)
        password = g.app.config.get('identity', 'password', fallback=None)
        tenant_id = g.app.config.get('identity', 'tenant_id', fallback=None)
        interface = g.app.config.get('identity', 'interface', fallback=None)
        region = g.app.config.get('identity', 'region', fallback=None)
        self.password(username, password, domain)
        self.scope(domain, tenant_id)
        self._reauth = self.config

    def password(self, username, password, domain=None):
        """Authenticate using credentials.

        Once authenticated execute will be processed using the context
        relative to user credentials.

        Args:
            username (str): Username.
            password (str): Password.
            domain (str): Name of domain for context.

        Returns authenticated result.
        """
        self._reauth = None
        auth_url = "/v1/token"

        if 'X-Auth-Token' in self:
            del self['X-Auth-Token']
        if 'X-Domain' in self:
            del self['X-Domain']
        if 'X-Tenant-Id' in self:
            del self['X-Tenant-Id']
        self.auth_token = None

        data = {
            "username": username,
            "domain": domain,
            "credentials": {
                "password": password
            }
        }

        response = self.execute("POST", auth_url, data=data,
                                endpoint='identity')

        if 'token' in response.json:
            self['X-Auth-Token'] = response.json['token']
            self.auth_token = response.json['token']
        if 'tenant_id' in response.json:
            self['X-Tenant-Id'] = response.json['tenant_id']
        if 'domain' in response.json:
            self['X-Domain'] = response.json['domain']

        return response

    def token(self, token):
        """Authenticate using Token.

        Once authenticated execute will be processed using the context
        relative to user credentials.

        Args:
            token (str): Token Key.
            domain (str): Name of domain for context.
            tenant_id (str): Tenant id for context. (optional)

        Returns authenticated result.
        """
        self._reauth = False

        auth_url = "/v1/token"

        if 'X-Auth-Token' in self:
            del self['X-Auth-Token']
        if 'X-Domain' in self:
            del self['X-Domain']
        if 'X-Tenant-Id' in self:
            del self['X-Tenant-Id']

        self.auth_token = token
        self['X-Auth-Token'] = token

        response = self.execute("GET", auth_url,
                                endpoint='identity')

        if 'token' in response.json:
            self['X-Auth-Token'] = response.json['token']
            self.auth_token = response.json['token']
        if 'tenant_id' in response.json:
            self['X-Tenant-Id'] = response.json['tenant_id']
        if 'domain' in response.json:
            self['X-Domain'] = response.json['domain']

        return response

    def extend(self):
        """Extend Token.
        """
        auth_url = "/v1/token"

        response = self.execute("PUT", auth_url,
                                endpooint='identity')

        return response

    def scope(self, domain, tenant_id=None):
        """Scope Token.
        """
        auth_url = "/v1/token"

        self['X-Domain'] = domain
        if tenant_id is not None:
            self['X-Tenant-Id'] = tenant_id
        elif 'X-Tenant-Id' in self:
            del self['X-Tenant-Id']

        scope = {}
        scope['domain'] = domain
        scope['tenant_id'] = tenant_id

        response = self.execute("PATCH", auth_url, data=scope,
                                endpooint='identity')

        if 'token' in response.json:
            self['X-Auth-Token'] = response.json['token']
        if 'tenant_id' in response.json:
            self['X-Tenant-Id'] = response.json['tenant_id']
        if 'domain' in response.json:
            self['X-Domain'] = response.json['domain']

        return response

    def set_context(self, auth_token, scope_token, domain, tenant_id):

        if 'X-Domain' in self:
            del self['X-Domain']
        if 'X-Tenant-Id' in self:
            del self['X-Tenant-Id']

        if auth_token is not None:
            self.auth_token = auth_token
            self['X-Auth-Token'] = self.auth_token

        if scope_token is not None:
            self['X-Auth-Token'] = scope_token

        if domain is not None:
            self['X-Domain'] = domain

        if tenant_id is not None:
            self['X-Tenant-Id'] = tenant_id

    def unscope(self):
        """Unscope Token.
        """
        self['X-Auth-Token'] = self.auth_token
        if 'X-Domain' in self:
            del self['X-Domain']
        if 'X-Tenant-Id' in self:
            del self['X-Tenant-Id']
        g.current_request.scope_token = None

    def new_endpoint(self, name, interface, region, uri):
        req = {}
        req['name'] = name
        req['interface'] = interface
        req['region'] = region
        req['uri'] = uri
        return self.execute('POST', '/v1/endpoint', req)

    def list_endpoints(self):
        return self.execute('GET', '/v1/endpoints')

    def delete_endpoint(self, id):
        return self.execute('DELETE', '/v1/endpoint/%s' % id)

    def user_domains(self):
        return self.execute('GET', '/v1/domains')

    def user_tenants(self, **kwargs):
        return self.execute('GET', '/v1/tenants', params=kwargs)

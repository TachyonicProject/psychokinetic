# -*- coding: utf-8 -*-
# Copyright (c) 2018 Dave Kruger.
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

class Contrail(Client):
    """Restclient to use on Contrail Implementation.

    Provide psychokinetic.Openstack obj to be used
    for login Authentication and/or scope change, and simply execute.

    Args:
        openstack(obj): psychokinetic.Openstac obj.
        url(str): URL of Contrail API.

    Example usage:

    .. code:: python

        os = Openstack(keystone_url='http://example:5000/v3')
        ct = Contrail(os, 'http://contrail-url:8082')
        ct.authenticate('admin','password','default')
        ct.scope(project_name="Customer1", domain="default")
        vns = ct.execute('GET','virtual-networks').json
    """

    def __init__(self, openstack, url):
        super().__init__()

        self._os_token = None
        self.os = openstack
        self.url = url

    def authenticate(self, user, passwd, domain=None):
        self.os.identity.authenticate(user, passwd, domain)
        self._os_token = self[
            'X-Auth-Token'] = self.os.identity.client._login_token

    def scope(self, domain=None, project_id=None, project_name=None):
        self.os.identity.scope(domain=domain, project_id=project_id,
                               project_name=project_name)
        self._os_token = self[
            'X-Auth-Token'] = self.os.identity.client._scoped_token

    def execute(self, method, uri, **kwargs):
        uri = self.url + '/' + uri.lstrip('/')
        return super().execute(method, uri, **kwargs)

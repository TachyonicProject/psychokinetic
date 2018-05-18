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
from psychokinetic.openstack.api.apibase import APIBase


class IdentityV3(APIBase):
    def authenticate(self, username, password, domain):
        # token = self.execute('POST', self.client.keystone_url)
        # endpoints = self.execute('GET', self.client.keystone_url)
        # self.client.login_token = token?
        # self.client['X-Auth-Token'] = token?
        # self.clients.user_endpoints = build endpoints based on client.region
        # & client.interface
        # However we will need all the admin endpoints too. Put them in
        # client.admin_endpoints... it needs to be there irrelevant of what
        # user selected.
        pass

    def scope(self, domain, project_id):
        # We have todo the same again process some endpoints might not be
        # availible for the scoped token.

        # token = self.execute('POST', self.client.keystone_url)
        # endpoints = self.execute('GET', self.client.keystone_url)
        # self.client.scoped_token = token?
        # self.client['X-Auth-Token'] = scoped_token?
        # self.clients.user_endpoints = build endpoints bbased on client.region &
        # client.interface
        # However we will need all the admin endpoints too. Put them in
        # client.admin_endpoints... it needs to be there irrelevant of what user
        # selected.

        # Now when scoping we also set the project_id and domain globally JUST
        # FOR HEADERS
        #self.client['project_id_header'] = project_id
        #self.client['domain_header'] = domain
        pass

    def unscope(self):
        # Unscope everything and go back to when we just had authenticate.
        # Remember to delete the headers.
        # This might be an issue with the HTTP Client in luxon. let me know I
        # can fix.
        pass

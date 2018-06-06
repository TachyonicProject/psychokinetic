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

from psychokinetic.openstack.api.identityv3 import IdentityV3
from psychokinetic.openstack.api.orchestrationv1 import OrchestrationV1
# from psychokinetic.openstack.api.networking2 import Networking2
# from psychokinetic.openstack.api.computev21 import Compute21
from psychokinetic.openstack.api.contrail4 import Contrail4
# from psychokinetic.openstack.api.contrail5 import Contrail5


class Openstack(Client):
    def __init__(self, keystone_url,
                 contrail_url=None,
                 region='RegionOne',
                 interface='public'):
        # The user should only be able to select interface public or internal.
        # Lower case it as well and lower the ones we get.

        super().__init__()
        self.keystone_url = keystone_url
        self.contrail_url = contrail_url

        # We store the login token here, it will also be placed in the global
        # HTTP client headers using Client[header] = value.
        # However we need a copy, since when using the identity.scope method
        # will change the header to the scoped token. If the user wishes to
        # use the 'scope' or 'unscope' method again on identity it will need
        # the original unscoped token.
        self._login_token = None

        # To keep track important dont remove... if user wishes to know current
        # environment information.
        self._scoped_token = None

        # Dictionary with key being 'type' ie image, metering, identity,
        # network, orchestration, volume, volume2, volumev3, etc.
        # The value being the url. Its not neccessary to store region,
        # interface, because its selected at Openstack client init.
        # The identity.authenticate method will populate these values.
        self._user_endpoints = {}
        # WE have to fill below ones anyways.
        self._admin_endpoints = {}
        self._public_endpoints = {}

        # The following interfadce, region is used to by identity.authenticate
        # to determine the endpoints that are stored above in
        # self.user_endpoints.
        self.interface = interface
        self.region = region

    @property
    def identity(self):
        return IdentityV3(self, 'identity')

    @property
    def orchestration(self):
        return OrchestrationV1(self, 'orchestration')

    @property
    def networking(self):
        # return Networking2(self, 'network')
        pass

    @property
    def compute(self):
        # return Compute21(self, 'compute')
        pass

    @property
    def contrail(self):
        return Contrail4(self)
        # return Contrail5(self)

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
from luxon import constants as const
from luxon.utils.http import Client
from psychokinetic.openstack.api.identityv3 import IdentityV3
from psychokinetic.openstack.api.networkv2 import NetworkV2
from psychokinetic.openstack.api.imagev2 import ImageV2
from psychokinetic.openstack.api.apibase import APIBase as OrchestrationV1
from psychokinetic.openstack.api.apibase import APIBase as ComputeV1
from psychokinetic.openstack.api.apibase import APIBase as VolumeV1
from psychokinetic.openstack.api.apibase import APIBase as VolumeV2
from psychokinetic.openstack.api.apibase import APIBase as VolumeV3
from psychokinetic.openstack.api.apibase import APIBase as ObjectStoreV1
from psychokinetic.openstack.api.apibase import APIBase as WorkloadsV1
from psychokinetic.openstack.api.apibase import APIBase as S3V1
from psychokinetic.openstack.api.apibase import APIBase as CloudformationV1
from psychokinetic.openstack.api.apibase import APIBase as MeteringV1

class Openstack(Client):
    """Restclient to use on Openstack Implementation.

    Log in and change scope with with Keystone, then execute on the chosen
    Service.

    Args:
        keystone_url(str): URL of Keystone API.
        region(str): Region of this Openstack implementation.
        interface(str): Which openstack interface to use - 'public', 'internal'
                        or 'admin'.

    Example usage:

    .. code:: python

        os = Openstack(keystone_url='http://example:5000/v3', region="RegionOne")
        os.identity.authenticate('admin','password','default')
        os.identity.scope(project_name="Customer1", domain="default")
        projects = os.identity.execute('GET','tenants').json

    """
    def __init__(self, keystone_url,
                 region='RegionOne',
                 interface='public'):
        # The user should only be able to select interface public or internal.
        # Lower case it as well and lower the ones we get.

        super().__init__()
        self['Content-Type'] = const.APPLICATION_JSON
        self.keystone_url = keystone_url

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
        # The identity.scope method will populate these values.
        self._user_endpoints = {}
        # We have to fill below ones anyways.
        self._admin_endpoints = {}
        self._public_endpoints = {}

        # The following interface, region is used to by identity.scope
        # to determine the endpoints that are stored above in endpoints.
        self.interface = interface
        self.region = region

    @property
    def identity(self):
        return IdentityV3(self, 'identity')

    @property
    def compute(self):
        return ComputeV1(self, 'compute')

    @property
    def orchestration(self):
        return OrchestrationV1(self, 'orchestration')

    @property
    def network(self):
        return NetworkV2(self, 'network')

    @property
    def volume(self):
        return VolumeV1(self, 'volume')

    @property
    def volumev2(self):
        return VolumeV2(self, 'volumev2')

    @property
    def volumev3(self):
        return VolumeV3(self, 'volumev3')

    @property
    def image(self):
        return ImageV2(self, 'image')

    @property
    def object_store(self):
        return ObjectStoreV1(self, 'object-store')

    @property
    def workloads(self):
        return WorkloadsV1(self, 'workloads')

    @property
    def s3(self):
        return S3V1(self, 's3')

    @property
    def cloudformation(self):
        return CloudformationV1(self, 'cloudformation')

    @property
    def metering(self):
        return MeteringV1(self, 'metering')

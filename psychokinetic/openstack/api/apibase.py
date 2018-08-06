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


class APIBase(object):
    """APIBase object.

    Openstack Endpoint Classes inherits this Base class.

    Args:
        client (obj): Some sort of psychokinetic.client obj.
        type (str): Openstack Endpoint Type: internal, public, or admin

    """

    def __init__(self, client, type):
        self._client = client
        self._type = type

    @property
    def client(self):
        """The psychokinetic.client obj passed for init.
        """
        return self._client

    @property
    def url(self):
        """Returns url for the given Region, interface and endpoint.
        """
        if self._client.interface == 'internal':
            _ep_interface = '_user_endpoints'
        else:
            _ep_interface = '_%s_endpoints' % self._client.interface

        if self._type in getattr(self._client, _ep_interface):
            return getattr(self._client, _ep_interface)[self._type]

        raise ValueError("No '%s' endpoint found" % self._type)

    def execute(self, method, uri='', **kwargs):
        """Executes the call on the given URI.

        Ags:
            method (str): String Method to use for API call.
            uri (str): URI to call.
            kwargs (kwargs): Additional keyword arguments

        Returns:
            Response object.
        """
        uri = self.url + '/' + uri
        return self.client.execute(method, uri, **kwargs)

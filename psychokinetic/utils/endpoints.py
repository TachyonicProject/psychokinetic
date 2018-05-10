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
from luxon.exceptions import NotFoundError

class Endpoints(object):
    interfaces = ( 'public', 'internal', 'admin' )
    def __init__(self, default_interface='public',
                 default_region='default'):

        self.default_region = default_region

        if default_interface not in self.interfaces:
            raise ValueError("Invalid interface for" +
                             " endpoint '%s'" % default_interface)

        self.default_interface = default_interface
        self.endpoints = {}
        self.regions = []

    def set(self, name, interface, region, uri):
        if interface not in self.interfaces:
            raise ValueError("Invalid interface for" +
                             " endpoint '%s'" % interface)

        if name not in self.endpoints:
            self.endpoints[name] = {}

        if interface not in self.endpoints[name]:
            self.endpoints[name][interface] = {}

        if region not in self.regions:
            self.regions.append(region)

        self.endpoints[name][interface][region] = uri

    def get(self, endpoint, interface=None, region=None):
        if interface is None:
            interface = self.default_interface

        if region is None:
            region = self.default_region

        if interface not in self.interfaces:
            raise NotFoundError("Invalid interface for endpoint '%s'" % interface)

        if endpoint in self.endpoints:
            if interface in self.endpoints[endpoint]:
                if region in self.endpoints[endpoint][interface]:
                    return self.endpoints[endpoint][interface][region]
                else:
                    raise NotFoundError("End point '%s' not" % endpoint +
                                     " found in region '%s'" % region)
            else:
                for interface in self.interfaces:
                    try:
                        return self.endpoints[endpoint][interface][region]
                    except KeyError:
                        pass
                raise NotFoundError("End point '%s' not" % endpoint +
                                 " found in region '%s'" % region)
        else:
            raise NotFoundError("End point not found '%s'" % endpoint)

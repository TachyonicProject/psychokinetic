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
import pickle
from types import GeneratorType

from luxon.utils.files import joinpath
from luxon.utils.http import Client as HTTPClient
from luxon import g


class ObjectStore(object):
    def _put_object(self, url, path,
                    file_object,
                    content_length,
                    content_type='text/plain; charset=utf-8',
                    md5hash=None,
                    timestamp=None):

        if content_length is None:
            raise ValueError('Require content_length')

        headers = {}
        if md5hash is not None:
            headers['X-MD5Hash'] = md5hash

        if timestamp is not None:
            headers['X-Timestamp'] = str(timestamp)

        url = url.rstrip('/') + '/v1/' + path.strip('/')

        return self.execute('PUT',
                            url,
                            data=file_object,
                            headers=headers,
                            content_length=content_length,
                            content_type=content_type)

    def _get_object(self, url, path):
        url = url.rstrip('/') + '/v1/' + path.strip('/')
        return self.stream('GET', url)

    def _unlink_object(self, url, path, timestamp):
        url = url.rstrip('/') + '/v1/' + path.strip('/')

        headers = {}
        if timestamp is not None:
            headers['X-Timestamp'] = str(timestamp)

        return self.execute('DELETE', url, headers=headers)

    def _object_metadata(self, url, path):
        url = url.rstrip('/') + '/v1/' + path.strip('/')
        return self.execute('HEAD', url)

    def storage_shards(self):
        return self.execute('GET', '/v1/shards', endpoint='katalog')

    def put_object(self,
                   tenant_id,
                   container,
                   name,
                   content,
                   content_length=None,
                   content_type=None,
                   etag=None,
                   raw=False):

        if raw is False:
            content = pickle.dumps(content)
            content_length = len(content)
            content_type = "application/python-pickle"
        else:
            if isinstance(content, bytes):
                content_length = len(content)
            elif isinstance(content, str):
                content = content.decode('utf-8')
                content_length = len(content)
                content_type = "text/plain; charset=utf-8"

        if content_length is None:
            raise ValueError('Require content_length keyword arguement')

        path = joinpath("/v1", tenant_id, container, name)

        headers = {}
        if etag is not None:
            headers['If-Match'] = etag

        return self.execute('PUT',
                            path,
                            data=content,
                            headers=headers,
                            content_length=content_length,
                            content_type=content_type,
                            endpoint='katalog')

    def get_object(self,
                   tenant_id,
                   container,
                   obj):
        path = joinpath("/v1", tenant_id, container, obj)
        sr = self.stream('GET', path, endpoint='katalog')
        sr.open()
        if sr.headers['Content-Type'].lower() == 'application/python-pickle':
            data = pickle.loads(sr.read())
            sr.close()
            return data
        else:
            return sr
        
    def unlink_object(self,
                      tenant_id,
                      container,
                      obj):
        path = joinpath("/v1", tenant_id, container, obj)

        return self.execute('DELETE', path, endpoint='katalog')

    def object_metadata(self,
                        tenant_id,
                        container,
                        obj):
        path = joinpath("/v1", tenant_id, container, obj)
        return self.execute('HEAD', path, endpoint='katalog')

    def list_objects(self,
                     tenant_id,
                     container):
        path = joinpath("/v1", tenant_id, container)
        return self.execute('GET', path, endpoint='katalog')

    def list_containers(self,
                        tenant_id):
        path = joinpath("/v1", tenant_id)
        return self.execute('GET', path, endpoint='katalog')

    def list_tenant_containers(self):
        return self.execute('GET', '/v1', endpoint='katalog')

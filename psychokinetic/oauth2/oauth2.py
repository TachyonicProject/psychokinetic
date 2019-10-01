# -*- coding: utf-8 -*-
# Copyright (c) 2019 David Kruger.
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
from requests_oauthlib import OAuth2Session

from luxon import g

from luxon.helpers.cache import cache


class OAuth2(OAuth2Session):
    """Restclient to use with OAuth2 BackendApplicationClient APIs.

    """
    def __init__(self, *args, section='oauth2', **kwargs):
        token_url = kwargs['token_url'] if 'token_url' in kwargs else None
        client_id = kwargs['client_id'] if 'client_id' in kwargs else None
        client_secret = kwargs[
            'client_secret'] if 'client_secret' in kwargs else None

        token_url = g.app.config.get(section, 'token_url', fallback=token_url)
        client_id = g.app.config.get(section, 'client_id', fallback=client_id)
        client_secret = g.app.config.get(section, 'client_secret',
                                         fallback=client_secret)

        from oauthlib.oauth2 import BackendApplicationClient

        self._backend_client = BackendApplicationClient(client_id=client_id)
        kwargs['client'] = self._backend_client
        self._oauth = OAuth2Session(*args, **kwargs)
        kwargs['token'] = cache(3600, self._oauth.fetch_token,
                                token_url=token_url,
                                client_id=client_id,
                                client_secret=client_secret)
        kwargs['client_id'] = client_id
        super().__init__(*args, **kwargs)

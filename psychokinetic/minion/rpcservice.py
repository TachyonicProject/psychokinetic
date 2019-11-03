# -*- coding: utf-8 -*-
# Copyright (c) 2019 Christiaan Frans Rademan.
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
from functools import partial

from luxon.core.networking.aio import async_send_pickle, async_recv_pickle

from psychokinetic.minion.baseservice import BaseComs, BaseService


class RPCBase(object):
    def ping(self, val):
        return val


class RPCClient(RPCBase):
    pass


class RPCServer(RPCBase):
    pass


class RPCComs(BaseComs):
    async def init(self):
        if self.server:
            self._methods = RPCServer()
        else:
            self._methods = RPCClient()

    async def channel_cb(self, reader, writer):
        resp = await async_recv_pickle(reader)
        if resp:
            try:
                method = getattr(self._methods, resp[0])
                val = await self.thread(
                    method,
                    *resp[1], **resp[2])
            except Exception as exception:
                val = exception

            await async_send_pickle(writer, val)
            writer.close()
        else:
            writer.close()

    async def connect_cb(self):
        pass
        #while True:
        #    print(await self.ping('bleh'))

    def __getattr__(self, method):
        return partial(self._rpc_call, method)

    async def _rpc_call(self, method, *args, **kwargs):
        reader, writer = await self.conn.channel()
        try:
            await async_send_pickle(writer, (method, args, kwargs,))
            val = await async_recv_pickle(reader)
            if isinstance(val, Exception):
                raise val
            return val
        finally:
            writer.close()


class RPCService(BaseService):
    COMS = RPCComs

# -*- coding: utf-8 -*-
# Copyright (c) 2019-2020 Christiaan Frans Rademan <chris@fwiw.co.za>.
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
import asyncio
from logging import getLogger


log = getLogger(__name__)


class Base(object):
    def __init__(self, service, processor, minion):
        self.service = service
        self.loop = asyncio.get_event_loop()
        self.server = processor.server
        self.thread = processor.thread
        self.minion = minion
        self.processor = processor
        self.proc = service.proc


class BaseComs(Base):
    async def init(self):
        # Connection is not yet established.
        pass

    async def channel_cb(self, reader, writer):
        # When channel is established from remote minion.
        pass

    async def connect_cb(self):
        # When connection is established.
        pass


class BaseProc(Base):
    async def start(self):
        # Service in process async loop. ie Syslog etc.
        pass

    async def conn(self, service):
        if not self.server:
            while True:
                try:
                    return await self.processor.get_server_connection(service)
                except ConnectionError:
                    await asyncio.sleep(1)
        else:
            raise ConnectionError('Only client to server' +
                                  ' connections availible')

    async def channel(self, service):
        if not self.server:
            conn = await self.conn(service)
            return await conn.channel()
        else:
            raise ConnectionError('Only client to server' +
                                  ' channels availible')


class BaseService(object):
    __version__ = None
    __description__ = None
    COMS = BaseComs
    PROC = BaseProc

    def __init__(self, minion):
        self.minion = minion
        self.server = minion.server
        self.ctx = {}
        self.init()
        self.proc = None

    def init(self):
        pass

    def coms(self, proccesor):
        # Returns object with channel_cb, connect_cb.
        if not self.proc:
            log.critical('Service not started %s' % self)
            return None
        return self.COMS(self, proccesor, self.minion)

    async def start(self, proccesor):
        # Service in process async loop. ie Syslog etc.
        self.proc = self.PROC(self, proccesor, self.minion)
        await self.proc.start()
        return self.proc

    def shutdown(self):
        pass

    @staticmethod
    def amq_on_channel_open(channel):
        pass

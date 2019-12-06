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
import concurrent.futures
from logging import getLogger
from multiprocessing import current_process

from luxon import g
from luxon.utils.system import switch
from luxon.core.logger import MPLogger
from luxon.core.networking.aio import (start_client,
                                       MultiplexConnection,
                                       async_send_pickle,
                                       async_recv_pickle)

log = getLogger(__name__)


class Proccessor(object):
    def __init__(self, minion, mplogger, services,
                 host='127.0.0.1', port=1983,
                 server_sock=None, ssl=None, **kwargs):

        self._mplogger = mplogger
        self._services = services
        self._minion = minion
        self._server_sock = server_sock
        self._host = host
        self._port = port
        self._ssl = ssl
        self._server_connections = {}

        self._kwargs = kwargs

        self._executor = None
        self._loop = None

    @property
    def server(self):
        if self._server_sock:
            return True
        return False

    def shutdown(self):
        if self._executor:
            self._executor.shutdown()
            self._executor = None

        self._loop = None

    async def get_server_connection(self, service):
        try:
            return self._server_connections[service]
        except KeyError:
            raise ConnectionError('No client connection') from None

    async def thread(self, call, *args, **kwargs):
        if self._executor and self._loop:
            return await self._loop.run_in_executor(
                self._executor,
                call,
                *args,
                **kwargs)
        else:
            raise Exception('Proccessor in shutdown')

    def run(self):
        MPLogger(current_process().name, self._mplogger.queue)

        # Switch from root to daemon user/group
        user = g.app.config.get('minion', 'user',
                                fallback="tachyonic")
        group = g.app.config.get('minion', 'group',
                                 fallback="tachyonic")
        switch(user, group)

        loop = self._loop = asyncio.get_event_loop()

        self._executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=128)
        loop.set_default_executor(self._executor)

        async def _connect_to(reader, writer, conn_type):
            await async_send_pickle(writer,
                                    {'conn_type': conn_type,
                                     'username': None,
                                     'password': None,
                                     'domain': None,
                                     'region': None})
            resp = await async_recv_pickle(reader)

            if 'error' in resp:
                raise Exception(resp['error'])

            return resp

        async def add_server_connection(service, conn):
            self._server_connections[service] = conn

        async def rm_server_connection(service):
            try:
                del self._server_connections[service]
            except KeyError:
                pass

        async def _handle_session(reader, writer, conn_type):
            handler = self._services[conn_type].coms(self)
            if not handler:
                writer.close()
                return
            await handler.init()

            loop = asyncio.get_event_loop()
            # Multiplex connection and run channel callback on request.
            conn = MultiplexConnection(handler.channel_cb,
                                       loop,
                                       reader,
                                       writer)
            handler.conn = conn

            if not self._server_sock:
                await add_server_connection(conn_type, conn)

            # Run connection handler init.
            # Run connection handler in thread.
            asyncio.ensure_future(handler.connect_cb())

            await conn._run()

            if not self._server_sock:
                await rm_server_connection(conn_type)

        async def _handle_connection(reader, writer):
            resp = await async_recv_pickle(reader)
            await async_send_pickle(writer, {'conn_type': resp['conn_type']})
            await _handle_session(reader, writer, resp['conn_type'])

        async def _handle_connect(reader, writer, conn_type=0):
            await _connect_to(reader, writer, conn_type)
            await _handle_session(reader, writer, conn_type)

        try:
            for service in self._services:
                loop.run_until_complete(
                    self._services[service].start(self))

            if self._server_sock:
                coro = asyncio.start_server(_handle_connection,
                                            sock=self._server_sock,
                                            ssl=self._ssl)
                loop.run_until_complete(coro)
            else:
                for service in self._services:
                    coro = start_client(_handle_connect,
                                        host=self._host,
                                        port=self._port,
                                        ssl=self._ssl,
                                        conn_type=service)
                    loop.run_until_complete(coro)

            loop.run_forever()
        except (KeyboardInterrupt, SystemExit):
            pass

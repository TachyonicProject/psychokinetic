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
import traceback
import asyncio
from logging import getLogger

import pika
from pika.adapters.asyncio_connection import AsyncioConnection as PikaConn


log = getLogger(__name__)


class AMQ(object):
    def __init__(self, channel_cb, host, *,  username=None,
                 password=None, virtualhost='/', port=5672, loop=None):
        self._channel_cb = channel_cb
        self._host = host
        self._username = username
        self._password = password
        self._virtualhost = virtualhost
        self._port = port
        self._loop = asyncio.get_event_loop()
        self._acked = 0
        self._nacked = 0
        self._published = 0

    def connect(self):
        asyncio.ensure_future(self._amq_connect(),
                              loop=self._loop)

    async def publish(self, exchange, routing_key, message):
        try:
            while True:
                # Important to prevent over_running memory.
                # Asyncio write buffer builds up on fast publishing.
                # This also helps us to prevent message loss.
                if self._unacked > 25:
                    await asyncio.sleep(0.005)
                    continue

                self._amq_channel.basic_publish(exchange,
                                                routing_key,
                                                message)
                self._unacked += 1
                return True
        except Exception:
            return False

    def consume(self, queue, callback, acks=True, consumer_tag=None):
        def callback_wrapper(ch, method, properties, body):
            try:
                if callback(ch, method, properties, body):
                    if acks:
                        ch.basic_ack(delivery_tag=method.delivery_tag)
                else:
                    if acks:
                        ch.basic_reject(delivery_tag=method.delivery_tag,
                                        requeue=False)
            except Exception as e:
                if acks:
                    ch.basic_reject(delivery_tag=method.delivery_tag,
                                    requeue=True)
                log.critical('%s\n%s\n%s' %
                             (str(e),
                              str(body),
                              str(traceback.format_exc(),)))

        try:
            self._amq_channel.basic_consume(queue,
                                            callback_wrapper,
                                            consumer_tag=consumer_tag)
            return True
        except Exception:
            return False

    async def _amq_connect(self, host='127.0.0.1', port=5672,
                           reconnect=False):
        self._acked = 0
        self._nacked = 0
        self._unacked = 0

        def connection_factory():
            amq_params = {
                'host': self._host,
                'port': self._port,
                'virtual_host': self._virtualhost
            }
            if self._username:
                amq_params = {**amq_params,
                              'credentials': pika.PlainCredentials(
                                  self._username,
                                  self._password)}

            params = pika.ConnectionParameters(**amq_params)

            return PikaConn(
                parameters=params, custom_ioloop=self._loop,
                on_open_callback=self._amq_on_connection_open,
                on_open_error_callback=self._amq_on_connection_open_error,
                on_close_callback=self._amq_on_connection_closed)

        if reconnect:
            await asyncio.sleep(5)

        while True:
            try:
                connection_factory()
                break
            except OSError as err:
                log.critical(err)
                await asyncio.sleep(5)

    def _amq_on_connection_open(self, connection):
        self._amq_connection = connection
        self._amq_connection.channel(
            on_open_callback=self._amq_on_channel_open)

    def _amq_on_connection_open_error(self, connection, err):
        asyncio.ensure_future(self._amq_connect(reconnect=True),
                              loop=self._loop)

    def _amq_on_connection_closed(self, connection, reason):
        self._amq_connection = None
        self._amq_channel = None
        asyncio.ensure_future(self._amq_connect(reconnect=True),
                              loop=self._loop)

    def _amq_on_channel_open(self, channel):
        channel.add_on_close_callback(
            self._amq_on_channel_closed)
        channel.confirm_delivery(self.on_delivery_confirmation)
        self._channel_cb(channel)
        self._amq_channel = channel

    def _amq_on_channel_closed(self, channel, reason):
        try:
            self._amq_connection.close()
        except Exception:
            pass
        self._amq_connection = None
        self._amq_channel = None

    def on_delivery_confirmation(self, method_frame):
        """Invoked by pika when RabbitMQ responds to a Basic.Publish RPC
        command, passing in either a Basic.Ack or Basic.Nack frame with
        the delivery tag of the message that was published. The delivery tag
        is an integer counter indicating the message number that was sent
        on the channel via Basic.Publish. Here we're just doing house keeping
        to keep track of stats and remove message numbers that we expect
        a delivery confirmation of from the list used to keep track of messages
        that are pending confirmation.
        :param pika.frame.Method method_frame: Basic.Ack or Basic.Nack frame
        """
        confirmation_type = method_frame.method.NAME.split('.')[1].lower()
        if confirmation_type == 'ack':
            self._acked += 1
            self._unacked -= 1
        elif confirmation_type == 'nack':
            self._nacked += 1
            self._unacked -= 1

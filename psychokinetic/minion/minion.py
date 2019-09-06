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
import os
import sys
import ssl
import time
import atexit
import socket
from logging import getLogger
from uuid import uuid4
from multiprocessing import (Process,
                             cpu_count,
                             Lock)

from luxon.core.app import App
from luxon.core.logger import MPLogger
from luxon.utils.unique import string_id
from luxon.utils.pkg import EntryPoints
from luxon.utils.system import require_root
from luxon.utils.daemon import GracefulKiller

from psychokinetic import metadata
from psychokinetic.minion.processor import Proccessor

log = getLogger(__name__)


class Interface(object):
    def __init__(self, minion):
        self._minion = minion

    def run_forever(self):
        self._minion._run_forever()


class Minion(object):
    def __init__(self, path, ini, pidfile, handlers, *args, **kwargs):
        self._pidfile = pidfile
        app = App('MINION', path=path, ini=ini, defaults=True)
        self._mplogger = None
        self._name = app.config.get('minion', 'name',
                                    fallback=socket.gethostname())
        self._server = app.config.getboolean('minion', 'server',
                                             fallback=False)
        self._host = app.config.get('minion', 'host', fallback='127.0.0.1')
        self._port = app.config.getint('minion', 'port', fallback=1983)
        self._cert = app.config.get('minion', 'ssl_cert', fallback=None)
        self._key = app.config.get('minion', 'ssl_key', fallback=None)

        if self._server and (self._key is None or self._cert is None):
            raise Exception('Require key and cert for Server')

        self._lock = Lock()
        self._listen_sock = None
        self._procs = []
        self._queues = None
        self._services = {}
        self._kwargs = kwargs
        self._handlers = handlers
        self._services = {}
        self._ephemeral_id = string_id()
        self._path = app.path
        self._id_file = app.path + '/agent_id.bin'
        self._id = self._minion_id()
        self._processors = []
        self._server_sock = None
        self._running = False
        GracefulKiller(self._killed)

    def _killed(self, signal):
        self._running = False
        raise SystemExit()

    @property
    def ephemeral_id(self):
        return self._ephemeral_id

    @property
    def id(self):
        return self._id

    @property
    def name(self):
        return self._name

    @property
    def path(self):
        return self._path

    @property
    def server(self):
        return self._server

    @property
    def type(self):
        return metadata.package

    @property
    def version(self):
        return metadata.version

    def _minion_id(self):
        try:
            with open(self._id_file, 'rb') as id_file:
                return id_file.read().decode('UTF-8')
        except FileNotFoundError:
            with open(self._id_file, 'wb+') as id_file:
                new_id = str(uuid4())
                id_file.write(new_id.encode('UTF-8'))
                return new_id

    def _write_pid(self):
        # Write PID File
        atexit.register(self._delete_pid)
        pid = str(os.getpid())
        with open(self._pidfile, 'w+') as pidfile:
            pidfile.write("%s\n" % pid)

    def _delete_pid(self):
        try:
            os.remove(self._pidfile)
        except FileNotFoundError:
            pass

    def __enter__(self):
        log.info('Starting Minion')

        if self._lock.acquire(False):
            self._write_pid()
            self._mplogger = MPLogger('__main__')
            self._mplogger.receive()

            if self._server:
                self._server_sock = socket.socket(socket.AF_INET,
                                                  socket.SOCK_STREAM)
                self._server_sock.setsockopt(socket.SOL_SOCKET,
                                             socket.SO_REUSEADDR, 1)
                self._server_sock.bind((self._host, self._port))
                self._server_sock.setblocking(False)
                self._server_sock.listen(65536)
            else:
                self._server_sock = None

            for handler in self._handlers:
                self._services[handler] = self._handlers[handler](self)

            if self._server:
                self._sc = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
                self._sc.check_hostname = False
                self._sc.load_cert_chain(self._cert,
                                         self._key)
            else:
                self._sc = ssl.create_default_context()
                self._sc.check_hostname = False
                if self._cert:
                    self._sc.load_verify_locations(self._cert)
                else:
                    self._sc.verify_mode = ssl.CERT_NONE

            for proc in range(cpu_count()):
                self._processors.append(Proccessor(self,
                                        self._mplogger,
                                        self._services,
                                        self._host,
                                        self._port,
                                        self._server_sock,
                                        self._sc,
                                        **self._kwargs))

                self._procs.append(Process(
                    target=self._processors[proc].run,
                    name='Proc%s' % proc,
                    daemon=True,
                    args=()))
        else:
            raise RuntimeError('Already running Minion')

        return Interface(self)

    def _run_forever(self):
        try:
            self._running = True
            for proc in self._procs:
                proc.start()
                log.info("Started Process '%s'" % proc.name)

            while self._running:
                for no, proc in enumerate(self._procs):
                    if not self._running:
                        break
                    if not proc.is_alive():
                        proc.join()
                        self._processors[no] = Proccessor(
                            self,
                            self._mplogger,
                            self._services,
                            self._host,
                            self._port,
                            self._server_sock,
                            self._sc,
                            **self._kwargs)
                        self._procs[no] = (Process(
                            target=self._processors[no].run,
                            name='Proc%s' % no,
                            daemon=True,
                            args=()))
                        self._procs[no].start()
                        log.critical("Process '%s' died," % proc.name +
                                     " restarted")
                time.sleep(5)

        except (KeyboardInterrupt, SystemExit):
            pass

    def __exit__(self, exception, message, traceback):
        log.info('Shutting down Minion')
        for proc in self._procs:
            log.info("Terminating Process '%s'" % proc.name)
            proc.terminate()

        if self._server_sock:
            self._server_sock.close()

        for service in self._services:
            self._services[service].shutdown()

        for processor in self._processors:
            processor.shutdown()

        self._processors = []
        self._mplogger.close()
        self._delete_pid()
        self._lock.release()


def main(argv):
    description = metadata.description + ' (Minion) ' + metadata.version
    print("%s\n" % description)

    try:
        require_root()
    except Exception as err:
        print(err)
        exit()

    if len(argv) < 2:
        print('Require minion root path as arguement')
        exit()

    path = os.path.abspath(argv[1])
    if not os.path.isdir(path):
        print("Invalid minion root path '%s'" % path)

    handlers = EntryPoints('tachyonic.minion.handlers')
    print("Handlers / EntryPoints")
    print("=" * 75)
    for handler in handlers:
        print(" %s = %s" % (handler, handlers[handler], ))
        print("     %s" % handlers[handler].__description__)
        print("     Version: %s" % handlers[handler].__version__)
    path = '/' + path.strip('/')
    print("=" * 75)

    with Minion(path,
                path + '/settings.ini',
                path + '/minion.pid',
                handlers) as m:
        m.run_forever()


def entry_point():
    """Zero-argument entry point for use with setuptools/distribute."""
    raise SystemExit(main(sys.argv))


if __name__ == '__main__':
    entry_point()

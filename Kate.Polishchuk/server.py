from __future__ import unicode_literals
# -*- coding: utf-8 -*-

"""
Small web-server on python

Author: Kate Polishchuk

To start this server you should execute: $ python server.py [port number]
Port number default value is 8090
"""

__author__ = 'kate'

import sys
import os, time
from os.path import relpath
import socket
import traceback
from datetime import datetime
from io import StringIO


class HTTPError(Exception):
    pass

class MyLogger:
    def writeRq1 (self, who, when):
        log = open('serverLog.txt', 'a')
        log.write(when)
        log.write(" [")
        (h, p) = who
        log.write(h)
        log.write(":")
        log.write(str(p))
        log.write("] ")
        log.close()
    def writeRq2 (self, what):
        log = open('serverLog.txt', 'a')
        log.write(what)
        log.write(" ")
        log.close()
    def writeRes (self, ans):
        log = open('serverLog.txt', 'a')
        log.write(ans + "\n")
        log.close()

def serve_static(url, root):
    cut = len(url)

    allowed_content_type = {
        ".html" : "text/html",
        ".htm" : "text/html",
        ".txt" : "text/plain",
        ".xml" : "text/xml",
        ".jpg" : "image/jpeg",
        ".png" : "image/png",
        ".gif" : "image/gif",
        ".mp3" : "audio/mpeg",
        ".zip" : "application/zip",
        ".gz" : "application/x-gzip",
        ".pdf" : "application/pdf",
        ".mpg" : "video/mpeg",
        ".py" : "text/plain"
    }

    DATE_RFC1123 = '%a, %d %b %Y %H:%I:%S GMT'

    def pattern(request):
        if request.code == 200:
            return request.url.startswith(url)
        return ''

    def handler(request):
        if request.code != 200:
            raise HTTPError(request.code)

        path = "%s/%s" % (root, request.url[cut:])

        if relpath(path).startswith('..'):
            raise HTTPError(404)

        try:
            stat = os.stat(path)
            if 'IF-MODIFIED-SINCE' in request.headers:
                try:
                    request_mtime = time.mktime(time.strptime(request.headers['IF-MODIFIED-SINCE'], DATE_RFC1123))
                    print request_mtime
                except ValueError:
                    request_mtime = None
                    print 'mtime value error'
                if request_mtime and request_mtime < stat.st_mtime:
                    return request.reply(304)

            mod_time = time.strftime(DATE_RFC1123, time.gmtime(stat.st_mtime))
            data = open(path).read()

        except (OSError, IOError) as err:
            if err.errno == 2:
                raise HTTPError(404)  # not found
            if err.errno == 13:
                raise HTTPError(404)  # no access
            if err.errno == 21:
                raise HTTPError(404)  # is a directory
            raise

        (head, ext) = os.path.splitext(path)
        if ext == ".py":
            try:

                buffer = StringIO()
                sys.stdout = buffer
                sys.stderr = buffer
                execfile(path)
                data = "\n".join(buffer.getValue())
                buffer.close()
                #stdout = os.popen("/usr/bin/python2.6 " + path, 'r')
                #if not stdout:
                #    data = 'empty stdout for program'
                #else:
                #    data = stdout.read()
                #    stdout.close()
            except Exception, e:

                raise HTTPError(500)
            finally:
                sys.stdout = sys.__stdout__
                sys.stderr = sys.__stderr__

        request.reply(body=data, code=200, content_type=allowed_content_type[ext], content_length=stat.st_size, last_modified=mod_time)

    return pattern, handler

def parse_http(data):
    try:
        lines = data.split('\r\n')
        query = lines[0].split(' ', 2)

        headers = {}
        pos = 0
        for pos, line in enumerate(lines[1:]):
            if not line.strip():
                break
            key, value = line.split(': ', 1)
            headers[key.upper()] = value

        body = None
        if pos:
            body = '\r\n'.join(lines[pos+2:])

        return query, headers, body
    except Exception, err:
        print traceback.format_exc(err)
        raise HTTPError(400)


def encode_http(query, body='', **headers):
    data = [" ".join(query)]

    headers = "\r\n".join("%s: %s" %
        ("-".join(part.title() for part in key.split('_')), value)
        for key, value in sorted(headers.iteritems()))

    if headers:
        data.append(headers)

    data.append('')

    if body:
        data.append(body)

    return "\r\n".join(data)

class Request(object):

    rqstatus = {
        200 : "OK",
        304 : "Not Modified",
        400 : "Bad request",
        404 : "Not found",
        418 : "I am a teapot",
        500 : "Internal server error"
    }

    def __init__(self, body, conn, code=200, method='GET', url=None, headers=None):
        self.method = method
        self.url = url
        self.headers = headers
        self.body = body
        self.conn = conn
        self.code = code

    def __str__(self):
        if self.method and self.url and self.headers:
            return "%s %s %r" % (self.method, self.url, self.headers)
        else:
            return "%d" % (self.code)

    def reply(self, code=None, content_type='text/plain', body='', **headers):
        if code != None:
            self.code = code

        if self.code == 200:
            headers.setdefault('content_type', content_type)
        else:
            headers.setdefault('content_type', 'text/plain')
            body = 'Error ' + str(self.code) + ': ' + self.rqstatus[self.code] + '\r\nThe original body :\r\n' + body

        headers.setdefault('server', 'KateServer')

        headers.setdefault('content_length', len(body))
        headers.setdefault('connection', 'close')
        headers.setdefault('date', datetime.now().ctime())

        logger = MyLogger()
        logger.writeRes(str(self.code))

        self.conn.send(encode_http(('HTTP/1.0', str(self.code), self.rqstatus[self.code]), body, **headers))
        self.conn.close()

class HTTPServer(object):
    def __init__(self, host='', port=8090):
        self.host = host
        self.port = port
        self.handlers = []

    def serve(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((self.host, self.port))
        sock.listen(0)

        try:
            while True:
                conn, address = sock.accept()
                self.on_connect(conn, address)
        except KeyboardInterrupt:
            sock.shutdown(socket.SHUT_RDWR)
            sock.close()
            print '\nServer shutdown'

    def on_connect(self, conn, address):
        log = MyLogger()
        try:
            log.writeRq1(address, datetime.now().ctime())
            data = conn.recv(1024)
            (method, url, protocol), headers, body = parse_http(data)
            log.writeRq2(url)
            self.on_request(Request(body, conn, 200, method, url, headers))
        except ValueError, exc:
            if data == '':
                log.writeRq2('Empty data')
            else:
                log.writeRq2(str(data))
            self.on_request(Request(traceback.format_exc(exc), conn, 400))
        except Exception, exc:
            self.on_request(Request(traceback.format_exc(exc), conn, 500))

    def on_request(self, request):
        print request
        if request.code != 200:
            return request.reply()
        try:
            for pattern, handler in self.handlers:
                if pattern(request):
                    handler(request)
                    return True
        except HTTPError as error:
            request.reply(error.args[0])
            return False
        except Exception as err:
            request.reply(500, traceback.format_exc(err))
            return False

        request.reply(404)

    def register(self, pattern, handler):
        self.handlers.append((pattern, handler))

if __name__ == '__main__':

    if len(sys.argv) > 1:
        port = int(sys.argv[1])
    else:
        port = 8090
    print port


    root = '.'
    server = HTTPServer(port=port)
    server.register(*serve_static('/', root))
    server.serve()
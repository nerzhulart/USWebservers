# -*- coding: utf-8 -*-
import sys

__author__ = 'kate'


import os, time
from os.path import relpath
import socket
import traceback
from datetime import datetime

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
        return request.url.startswith(url)

    def handler(request):
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

        except (OSError, IOError) as err:
            if err.errno == 2:
                raise HTTPError(404)  # not found
            if err.errno == 13:
                raise HTTPError(418)  # no access
            if err.errno == 21:
                raise HTTPError(418)  # is a directory
            raise

        (head, ext) = os.path.splitext(path)
        if ext == ".py":
            stdout = os.popen("/usr/bin/python2.6 " + path, 'r')
            if not stdout:
                data = 'empty stdout for program'
            else:
                data = stdout.read()
                stdout.close()
        else:
            data = open(path).read()

        request.reply(body=data, content_type=allowed_content_type[ext], content_length=stat.st_size, last_modified=mod_time)

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

	print data
	
    data.append('')

    if body:
        data.append(body)

    return "\r\n".join(data)

class Request(object):

    def __init__(self, method, url, headers, body, conn):
        self.method = method
        self.url = url
        self.headers = headers
        self.body = body
        self.conn = conn
        self.rqstatus = {
            200 : "OK",
            304 : "Not Modified",
            400 : "Bad request",
            404 : "Not found",
            418 : "I am a teapot",
            500 : "Internal server error"
        }
        self.code = 200

    def __str__(self):
        return "%s %s %r" % (self.method, self.url, self.headers)

    def reply(self, code=200, content_type='text/plain', body='', last_modified=datetime.now().ctime(), **headers):
        self.code = code
        if code == 200:
            headers.setdefault('content_type', content_type)
        else:
            headers.setdefault('content_type', 'text/plain')
            if code == 500:
                body = ["Error 500:" + self.rqstatus[code]].append(body)
            else:
                body = "Error " + str(code) + ": " + self.rqstatus[code]

        headers.setdefault('server', 'KateServer')

        headers.setdefault('content_length', len(body))
        headers.setdefault('connection', 'close')
        headers.setdefault('date', datetime.now().ctime())
        headers.setdefault('IF-MODIFIED-SINCE', last_modified)

        logger = MyLogger()
        logger.writeRes(str(code))

        self.conn.send(encode_http(('HTTP/1.0', str(code), self.rqstatus[code]), body, **headers))
        self.conn.close()

class HTTPServer(object):
    def __init__(self, host='localhost', port=8090):
        self.host = host
        self.port = port
        self.handlers = []

    def serve(self):
        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        sock.bind((self.host, self.port))
        sock.listen(5000)

        while True:
            conn, address = sock.accept()
            self.on_connect(conn, address)

    def on_connect(self, conn, address):
        log = MyLogger()
        try:
            log.writeRq1(address, datetime.now().ctime())
            (method, url, protocol), headers, body = parse_http(conn.recv(1024))
            log.writeRq2(url)
            self.on_request(Request(method, url, headers, body, conn))
        except HTTPError:
            log.writeRes('Bad request')
        except:
            raise

    def on_request(self, request):
        #print request
        
        try:
            for pattern, handler in self.handlers:
                if pattern(request):
                    handler(request)
                    return True
        except HTTPError as error:
            request.reply(error.args[0])
            return False
        except Exception as err:
            request.reply(500, traceback.format_exc())
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
  
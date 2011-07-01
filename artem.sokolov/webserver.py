#!/usr/bin/python -OO

# This is an example of a simple server written in python.
#
# You can use it as a usual web server (it supports some
# content types), and also for dynamic executing of python
# source files.
#
# Launching: "./webserver.py" (requires rights to execute) or
# "python webserver.py".
# Using: type localhost:8080 in your browser.

import socket
import re
import os
import email.utils
import sys
import StringIO
from datetime import datetime
from time import mktime
from common import safe_open_file, safe_close_file

HOST = "localhost"
PORT = 8080

ROOT_DIR = "./www"
SERVER_NAME = "Simple"

class WebServer:
    def __init__(self):
        self.file_path_regexp = re.compile('(?<=GET).*(?=HTTP)')
        self.socket = socket.socket()
        self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.socket.bind((HOST, PORT))
        self.log_file = safe_open_file('log.txt', 'w', 0, 'Could not open log file for writing. Terminated.')
        self.socket.listen(1)

    def __del__(self):
        safe_close_file(self, 'log_file')

    def start(self):
        while True:
            connected_socket, address = self.socket.accept()
            self.process_connection(connected_socket, address)

    def receive(self, socket):
        EOL = "\r\n"
        n_bytes = 4096
        buffer = socket.recv(n_bytes)
        if_modified_since = re.search('(?<=If-Modified-Since: ).*(?=\r\n)', buffer)
        if if_modified_since:
            if_modified_since = if_modified_since.group(0)
        result = buffer.split(EOL)[0]
        return result, if_modified_since

    def send_string(self, socket, data):
        bytes_to_send = len(data)
        while bytes_to_send > 0:
            sent_bytes = socket.send(data, bytes_to_send)
            if sent_bytes == -1:
                return False
            bytes_to_send -= sent_bytes
        return True

    def get_content_type(self, path):
        extension = path.split('.')[-1]
        return {
            'htm'   :   "text/html",
            'html'  :   "text/html",
            'txt'   :   "text/plain",
            'xml'   :   "text/xml",
            'jpeg'  :   "image/jpeg",
            'png'   :   "image/png",
            'gif'   :   "image/gif",
            'mp3'   :   "audio/mpeg",
            'zip'   :   "application/zip",
            'gz'    :   "application/x-gzip",
            'pdf'   :   "application/pdf",
            'avi'   :   "video/mpeg"
        }.get(extension, "text/html")

    def http_date(self, date_time):
        stamp = mktime(date_time.timetuple())
        return  email.utils.formatdate(
            timeval     = stamp,
            usegmt      = True
        )

    def parse_http_date(self, text):
        return datetime.strptime(text, '%a, %d %b %Y %H:%M:%S GMT')

    def make_header(self, mandatory, optional):
        header = "HTTP/1.1 " + {
            200 : "200 Ok",
            304 : "304 Not Modified",
            400 : "400 Bad Request",
            404 : "404 Not Found",
            500 : "500 Internal Server Error"
        }.get(mandatory['code'], "500 Internal Server Error") + "\n"
        if mandatory["code"] == 200 and mandatory["path"]:
            header += "Content-Type: " + self.get_content_type(mandatory["path"]) + "\n"
        if optional:
            for x in optional.keys():
                header += x + ": " + optional[x]
        header += "\n\n"
        return header

    def response(self, connected_socket, client_record, status, mandatory, data=None, optional=None):
        response = connected_socket.makefile('rw', 0)
        self.log_file.write(client_record + '\n')
        self.log_file.write('\t' + status + '\n')
        response.write(self.make_header(mandatory, optional))
        if data:
            response.write(data)
        else:
            response.write(status)
        response.close()

    def execute_file(self, resource):
        output = StringIO.StringIO()
        sys.stdout = output
        sys.stderr = output
        execfile(resource)
        data = '<br>'.join(output.getvalue().split())
        output.close()
        sys.stdout = sys.__stdout__
        sys.stderr = sys.__stderr__
        return data

    def process_connection(self, connected_socket, address):
        try:
            request, if_modified_since = self.receive(connected_socket)
            client_record = 'Got request from %s:%d "%s"' % (address[0], address[1], request)
            found = self.file_path_regexp.search(request)
            file_path = found.group(0).strip()
            if found:
                if file_path == '/':
                    file_path = '/index.html'
                resource = ROOT_DIR
                resource += file_path
                if file_path.split('.')[-1] == "py":
                    try:
                        data = self.execute_file(resource)
                        self.response(connected_socket, client_record, '200 OK', {"code": 200, "path": file_path}
                                      , "<html><body>" + data + "</body></html>")
                    except IOError:
                        self.response(connected_socket, client_record, '404 Not found', {"code": 404})
                    finally:
                        sys.stdout = sys.__stdout__
                        sys.stderr = sys.__stderr__
                else:
                    try:
                        f = open(resource, 'rb')
                        date_modified = datetime.fromtimestamp(os.path.getmtime(resource))
                        if if_modified_since and self.parse_http_date(if_modified_since) >= \
                                                 self.parse_http_date(self.http_date(date_modified)):
                            self.response(connected_socket, client_record, '304 Not Modified', {"code": 304})
                        else:
                            file_content = f.read()
                            self.response(connected_socket, client_record, '200 OK', {"code": 200, "path": file_path}
                                      , file_content, {"Last-Modified": self.http_date(date_modified)})
                        f.close()
                    except IOError:
                        self.response(connected_socket, client_record, '404 Not found', {"code": 404})
            else:
                self.response(connected_socket, client_record, '400 Bad Request', {"code": 400})
        except:
            self.response(connected_socket, client_record, '500 Internal Server Error', {"code": 500})
        finally:
            connected_socket.shutdown(socket.SHUT_RD)
            connected_socket.close()

web_server = WebServer()
web_server.start()




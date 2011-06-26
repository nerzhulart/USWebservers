#!/usr/bin/python -OO
import socket
import re
import os
from datetime import datetime
from time import mktime
import email.utils
import sys

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
        self.socket.listen(1)

    def start(self):
        while True:
            connected_socket, address = self.socket.accept()
            self.process_connection(connected_socket, address)

    def receive(self, socket):
        EOL = "\r\n"
        n_bytes = 4096
        buffer = socket.recv(n_bytes)
        #print buffer
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

    def make_header(self, mandatory, optional = None):
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

    def process_connection(self, connected_socket, address):
        response = connected_socket.makefile('rw', 0)
        try:
            request, if_modified_since = self.receive(connected_socket)
            print 'Got request from %s:%d "%s"' % (address[0], address[1], request)
            found = self.file_path_regexp.search(request)
            file_path = found.group(0).strip()
            if found:
                if file_path == '/':
                    file_path = '/index.html'
                resource = ROOT_DIR
                resource += file_path
                if file_path.split('.')[-1] == "py":
                    try:
                        output = open(ROOT_DIR + "/data", "w")
                        sys.stdout = output
                        sys.stderr = output
                        execfile(resource)
                        output.close()
                        sys.stdout = sys.__stdout__
                        sys.stderr = sys.__stderr__
                        rfile = open(ROOT_DIR + "/data", "r")
                        data = "<br>".join(rfile.readlines())
                        print "\t200 OK\n"
                        response.write(self.make_header({"code": 200, "path": file_path}))
                        response.write("<html><body>" + data + "</body></html>")
                    except IOError:
                        print "\t404 Not found\n"
                        response.write(self.make_header({"code": 404}))
                        response.write("404 Not Found")
                    finally:
                        sys.stdout = sys.__stdout__
                        sys.stderr = sys.__stderr__
                else:
                    try:
                        f = open(resource, 'rb')
                        date_modified = datetime.fromtimestamp(os.path.getmtime(resource))
                        date_modified_utc = datetime.utcfromtimestamp(os.path.getmtime(resource))
                        if if_modified_since and self.parse_http_date(if_modified_since) > self.parse_http_date(self.http_date(date_modified_utc)):
                            response.write(self.make_header({"code": 304}))
                        else:
                            print "\t200 OK\n"
                            response.write(self.make_header({"code": 200, "path": file_path},
                                                            {"Last-Modified": self.http_date(date_modified)}))
                            file_content = f.read()
                            response.write(file_content)
                        f.close()
                    except IOError:
                        print "\t404 Not found\n"
                        response.write(self.make_header({"code": 404}))
                        response.write("404 Not Found")
            else:
                print "\t400 Bad request\n"
                response.write(self.make_header({"code": 400}))
                response.write("400 Bad Request")
        except:
            print "\t500 - Internal Server Error\n"
            response.write(self.make_header({"code": 500}))
            response.write("500 - Internal Server Error")
        finally:
            connected_socket.shutdown(socket.SHUT_RD)
            response.close()
            connected_socket.close()

web_server = WebServer()
web_server.start()




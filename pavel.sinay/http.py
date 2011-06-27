#File implements wrapper of standard socket and low-level HTTP processor

import log
import processors

MSGLEN = 1024

class SmartSocket:
    def __init__(self, socket):
        self.sock = socket

    def send(self, msg):
        totalsent = 0
        while totalsent < len(msg):
            sent = self.sock.send(msg[totalsent:])
            if sent == 0:
                raise RuntimeError("socket connection broken")
            totalsent = totalsent + sent

    def receive(self):
        msg = ''
        chunk = MSGLEN * '0'
        while len(chunk) == MSGLEN:
            chunk = self.sock.recv(MSGLEN)
            msg = msg + chunk
        return msg


class HTTPProcessor:
    def __init__(self, socket):
        self.error_codes = {200: "OK", 500: "Internal server error", 400: "Bad request", 404: "Not Found"}
        self.code = 200
        try:
            self.smart_sock = SmartSocket(socket)
            self.msg = self.smart_sock.receive()
        except:
            self.code = 500
            self.send()
            return
        try:
            self.header = self.msg.split('\r\n\r\n')[0]
            self.body = self.msg.split('\r\n\r\n')[1]
            self.method = self.header.split(' ')[0]
            self.path = self.header.split(' ')[1]
            self.params = {}
        except:
            self.code = 400
            self.send()
            return
        processors.RequestProcessor(self)

    def send(self):
        if not (self.code in self.error_codes):
            self.code = 500
        self.code_str = self.error_codes[self.code]
        log.logger.info(str(self.code) + " " + self.code_str)
        self.params["Content-Length"] = str(len(self.body))
        self.msg = "HTTP/1.0 " + str(self.code) + " " + self.code_str + "\r\n"
        for i, j in self.params.iteritems():
            self.msg += i + ": " + j + "\r\n"
        self.msg += "\r\n" + self.body
        self.smart_sock.send(self.msg)
        self.smart_sock.sock.close()
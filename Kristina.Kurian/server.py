#!/usr/bin/python

# Program name - server.py
# Written by - Kristina P. Kurian (kristina.kurian06@gmail.com)
# Date and version No:  27.06.2011, ver. 1.0

# Description:
# Server.py is simply HTTP server. It support logging, standart status codes,
# standart content type, multi-threaded 

# Start:
# ./server.py [-h|--host=] host_name [-f|--file] log_file

# Options:
# [-h|--host] - host for connection, by default host is 8080
# [-f|--file] - file use for writing log, by default file is "log.txt"


import socket  
import signal  
import time   
import getopt 
import sys

class Server:
 content_type = { \
	"py" : "text/html; charset=utf-8", \
	"txt" : "text/plain; charset=utf-8", \
	"html" : "text/html; charset=utf-8", \
	"xml" : "text/xml; charset=utf-8", \
	"jpeg" : "image/jpeg", \
	"png" : "image/png", \
	"gif" : "image/gif", \
	"mp3" : "audio/mpeg", \
	"zip" : "application/zip", \
	"gzip" : "appliction/x-gzip", \
	"pdf" : "application/pdf", \
	"mpeg" : "video/mpeg" 
 }

 def __init__(self, port, filename):
     self.host = ''   
     self.port = port
     self.dir = 'page'
     self.filename = filename		
	
 def start_server(self):
     self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
     try: 
         self.socket.bind((self.host, self.port))

     except Exception as e:
         self.port = 8080

         try:
             print("Launching HTTP server on ", self.host, " ",self.port)
             self.socket.bind((self.host, self.port))

         except Exception as e:
             self.reset()
             sys.exit(1)

     print ("Server successfully started with port:", self.port)
     self.connect()

 def reset(self):
     try:
 	 s.socket.shutdown(socket.SHUT_RDWR)
     except Exception as e:
         print("ERROR: could not shut down the socket.", e)

 def check_state(self,  code):
     h = ''
     print code
     if (code == 200):
        h = 'HTTP/1.1 200 OK\n'
     elif(code == 304):
	h = 'HTTP/1.1 304 Not Modified\n' 	
     elif(code == 400):
        h = 'HTTP/1.1 400 Bad Request\n'
     elif(code == 404):
        h = 'HTTP/1.1 404 Not Found\n'
     elif(code == 500):
	h = 'HTTP/1.1 500 Internal Server Error\n'	

     current_date = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
     h += 'Date: ' + current_date +'\n' + 'Server: HTTP-Server\n' + 'Connection: close\n\n'  

     return h

 def connect(self):
     log_file = open(self.filename, "a")
     while True:
         self.socket.listen(10) 

         conn, addr = self.socket.accept()
 
         print("Got connection from:", addr)

         data = conn.recv(1024) 
         string = bytes.decode(data) 

         request_method = string.split(' ')[0]
         
         if (request_method == 'GET'):
             file_requested = string.split(' ')
             file_requested = file_requested[1] 
    		
             file_requested = file_requested.split('?')[0]  
     	     try:
	     	expansion = file_requested.split('.')[-1]
	     	if not Server.content_type.has_key(expansion):
			raise Exception("ERROR: Wrong Content Type")
	     	if expansion == "py":
			print ""
	     except Exception as e: 
		h = 'HTTP/1.1 400 Bad Request\n'

		current_date = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
     		h += 'Date: ' + current_date +'\n' + 'Server: Python-HTTP-Server\n' + 'Connection: close\n\n'  
   		log_file.write(h)			 
	
	     if (file_requested == '/'): 
                 file_requested = '/index.html' 
             
             file_requested = self.dir + file_requested
             print ("Opening page [",file_requested,"]")
	     try:
                 file_handler = open(file_requested,'rb')
                 if (request_method == 'GET'): 
                     response_content = file_handler.read()                        
                 file_handler.close()
                 
                 response_headers = self.check_state(200)
		 log_file.write(response_headers)			 
                 
             except Exception as e: 
		 response_headers = self.check_state(304)
                 if (request_method == 'GET'):
                    response_content = b"<html><body><p>Error 304: Not Modified</p><p>HTTP server</p></body></html>"
	
		 response_headers = self.check_state(400)
                 if (request_method == 'GET'):
                    response_content = b"<html><body><p>Error 400: Bad Request</p><p>HTTP server</p></body></html>"
	
                 
		 response_headers = self.check_state(404)
		 if (request_method == 'GET'):
                    response_content = b"<html><body><p>Error 404: File not found</p><p>HTTP server</p></body></html>"
		 
		 response_headers = self.check_state(500)
                 if (request_method == 'GET'):
                    response_content = b"<html><body><p>Error 500: Internal Server Error</p><p>HTTP server</p></body></html>"
		 
   		 log_file.write(response_headers)	
		
             server_response =  response_headers.encode() 
             if (request_method == 'GET'):
                 server_response +=  response_content  

             conn.send(server_response)
             print ("Closing connection.")
             conn.close()

         else:
             print("Unknown HTTP request method:", request_method)

def graceful_shutdown(sig, d):
    s.reset() 
    sys.exit(1)


signal.signal(signal.SIGINT, graceful_shutdown)
options, remainder = getopt.getopt(sys.argv[1:], 'h:f:', ['host=', 'file='])

host = 8080
log_file = "log.txt"
for opt, arg in options:
    if opt in ('-f', '--file'):
        log_file = arg
    elif opt in ('-h', '--host'):
        host = arg

print ("Starting server...")
s = Server(host, log_file) 
s.start_server() 

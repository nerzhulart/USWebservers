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

 def state200OK(self):
     mes = 'HTTP/1.1 200 OK\n'
     current_date = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
     mes += 'Date: ' + current_date +'\n' + 'Server: HTTP-Server\n' + 'Connection: close\n\n'  

     return mes

 def state304NotModified(self):
     mes = 'HTTP/1.1 304 Not Modified\n' 	
     current_date = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
     mes += 'Date: ' + current_date +'\n' + 'Server: HTTP-Server\n' + 'Connection: close\n\n'  

     return mes
 

 def state400BadRequest(self):
     mes = 'HTTP/1.1 400 Bad Request\n'
     current_date = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
     mes += 'Date: ' + current_date +'\n' + 'Server: HTTP-Server\n' + 'Connection: close\n\n'  

     return mes
 
 def state404NotFound(self):
     mes = 'HTTP/1.1 404 Not Found\n'
     current_date = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
     mes += 'Date: ' + current_date +'\n' + 'Server: HTTP-Server\n' + 'Connection: close\n\n'  

     return mes
 
 def state500InternalServerError(self):
     mes = 'HTTP/1.1 500 Internal Server Error\n'	
     current_date = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
     mes += 'Date: ' + current_date +'\n' + 'Server: HTTP-Server\n' + 'Connection: close\n\n'  

     return mes
 
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
             print("Trying to start server on ", self.host, " ",self.port)
             self.socket.bind((self.host, self.port))

         except Exception as e:
	     mes = self.state500InternalServerError()
	     print mes	
	     self.reset()
             sys.exit(1)

     print ("Server successfully started with port:", self.port)
     self.connect()

 def reset(self):
     try:
 	 s.socket.shutdown(socket.SHUT_RDWR)
     except Exception as e:
         print("ERROR: Problem with shut down socket appeared.", e)

 def connect(self):
     log_file = open(self.filename, "a")
     log_file.flush()	
     while True:
         self.socket.listen(10) 

         conn, addr = self.socket.accept()
 
         print("Got connection from:", addr)

         data = conn.recv(1024) 
         string = bytes.decode(data) 

         request_method = string.split(' ')[0]
         if (request_method == 'GET'):
             file_requested = string.split(' ')[1]
	     
	     try:
	     	expansion = file_requested.split('.')[-1]
	     	if not Server.content_type.has_key(expansion):
			raise Exception("ERROR: Wrong Content Type")
	     	
	     except Exception as e: 
		mes = self.state400BadRequest()
		log_file.write(mes)			 
		     
	     if expansion == "py":
		tmpfile = self.dir + file_requested
		
		from subprocess import Popen, PIPE
		command = "python " + tmpfile
		response_content = Popen(command, shell=True, stdin=PIPE, stdout=PIPE).stdout.read()	
               	response_headers = self.state200OK()
	 	log_file.write("Page: " + file_requested + "\n" + response_headers)			 
	     else:	
	     	if (file_requested == '/'): 
                	file_requested = '/index.html' 
             
             	file_requested = self.dir + file_requested
	     	print ("Opening page [",file_requested,"]")
	     	try:
                	file_handler = open(file_requested,'rb')
                 	
			response_content = file_handler.read()                        
                 	file_handler.close()
                 
                 	response_headers = self.state200OK()
		 	log_file.write("Page: " + file_requested + "\n" + response_headers)			 
             	except IOError as e:
			response_headers = self.state404NotFound()
			response_content = b"<html><body><p>Error 404: File not found</p><p>HTTP server</p></body></html>"
		 
   		 	log_file.write("Page: " + file_requested + "\n" + response_headers)	
    
             	except Exception as e: 
			response_headers = self.state400BadRequest()
                	response_content = b"<html><body><p>Error 400: Bad Request</p><p>HTTP server</p></body></html>"
		 
   			log_file.write("Page: " + file_requested + "\n" + response_headers)	
		
             server_response =  response_headers.encode() 
             server_response +=  response_content  

             conn.send(server_response)
             conn.close()

         else:
             mes = self.state400BadRequest()
	     log_file.write(mes)	

def shutdown(sig, d):
    s.reset() 
    sys.exit(1)


signal.signal(signal.SIGINT, shutdown)
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

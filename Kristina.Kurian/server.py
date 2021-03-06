#!/usr/bin/python

# Program name - server.py
# Written by - Kristina P. Kurian (kristina.kurian06@gmail.com)
# Date and version No:  27.06.2011, ver. 1.0

# Description:
# Server.py is simply HTTP server. It support logging, standart status codes,
# standart content type, multi-threaded 

# Start:
# ./server.py [-p|--port=] port_name [-f|--file=] log_file

# Options:
# [-p|--port=] - port for connection, by default port is 8080
# [-f|--file=] - file use for writing log, by default file is "log.txt"


import socket  
import signal
import datetime  
import time   
import getopt 
import sys

class Server:
 headers = {200:"OK", 304: "Not Modified", 400: "Bad Request", 404: "Not Found", 500: "Internal Server Error"}

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
 
 def processError(self, errorNumber):
     errorTitle = Server.headers[errorNumber]
     errorMessage = "<html><body><p>Error" + str(errorNumber) + ":" + errorTitle + "</p><p>HTTP server</p></body></html>"

     return errorMessage

 def check_state(self, number):
     title = Server.headers[number]
     mes = 'HTTP/1.1 ' + str(number) + ' ' + title + '\n'
     current_date = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
     mes += 'Date: ' + current_date +'\n' + 'Server: HTTP-Server\n' + 'Connection: close\n\n'  

     return mes	

 def __init__(self, port, filename):
     self.host = ''   
     self.port = int(port)
     self.dir = 'page'
     self.filename = filename		
	
 def start_server(self):
     self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
     try: 
	 print("Trying to start server on ", self.host, " ",self.port)
         self.socket.bind((self.host, self.port))

     except Exception as e:
	 print("Connect to specified port ", self.port, " is failed")        
 	 self.port = 8080
         try:
	     print("Trying to start server on ", self.host, " ",self.port)
             self.socket.bind((self.host, self.port))

         except Exception as e:
	     mes = self.check_state(500)
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
         
	 request = string.split("\r\n")
	 modified = [request for request in request if request.find("If-Modified-Since:") != -1]
	 modified_date = None
	 if modified != []:
	 	date = modified[0].partition(":")[2]
		modified_date = datetime.strptime(date, " %a, %d %b %Y %H:%M:%S GMT")
			
	 if (request_method == 'GET'):
             file_requested = string.split(' ')[1]
	     
	     try:
	     	expansion = file_requested.split('.')[-1]
	     	if not Server.content_type.has_key(expansion):
			raise Exception("ERROR: Wrong Content Type")
	     	
	     except Exception as e: 
		mes = self.check_state(400)
		log_file.write(mes)			 
		     
	     if expansion == "py":
		tmpfile = self.dir + file_requested
		
		from subprocess import Popen, PIPE
		command = "python " + tmpfile
		response_content = Popen(command, shell=True, stdin=PIPE, stdout=PIPE).stdout.read()	
               	response_headers = self.check_state(200)
	 	log_file.write("Page: " + file_requested + "\n" + response_headers)			 
	     else:	
	     	if (file_requested == '/'): 
                	file_requested = '/index.html' 
             
             	file_requested = self.dir + file_requested
	     	print ("Opening page [",file_requested,"]")
	     	try:
                	file_handler = open(file_requested,'rb')
                 	
			if modified_date:	
				dirname = os.getcwd() + file_requested
				file_modified_ts = os.path.getmtime(dirname)
				file_modified = datetime.fromtimestamp(file_modified_ts)
				if file_modified < modified_date:
					raise ValueError					
								
			response_content = file_handler.read()                        
                 	file_handler.close()
                 
                 	response_headers = self.check_state(200)
		 	log_file.write("Page: " + file_requested + "\n" + response_headers)			 
             	except IOError as e:
			response_headers = self.check_state(404)
			response_content = self.processError(404)

    		except ValueError:
			response_headers = self.check_state(300)
			response_content = self.processError(300)

             	except Exception as e: 
			response_headers = self.check_state(400)
                	response_content = self.processError(400)

		finally:
   			log_file.write("Page: " + file_requested + "\n" + response_headers)		
             server_response =  response_headers.encode() 
             server_response +=  response_content  

             conn.send(server_response)
             conn.close()

         else:
             mes = self.check_state(400)
	     log_file.write(mes)	

def shutdown(sig, d):
    s.reset() 
    sys.exit(1)


signal.signal(signal.SIGINT, shutdown)
options, remainder = getopt.getopt(sys.argv[1:], 'p:f:', ['port=', 'file='])

host = 8080
log_file = "log.txt"
for opt, arg in options:
    if opt in ('-f', '--file'):
        log_file = arg
    elif opt in ('-p', '--port'):
        host = arg

print ("Starting server...")
s = Server(host, log_file) 
s.start_server() 

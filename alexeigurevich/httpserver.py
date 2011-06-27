#!/usr/bin/python

"""
Small web-server on python

Author: Alexey Gurevich

To start this server you should execute:
$ python httpserver.py [log filename] [base path for server files]
"""

import socket
import datetime
import os
import sys

### server params
host = 'localhost'
port = 8080

### server default params (can be substituted by command line arguments)
log_filename = 'log.txt'
basepath = '.'

### timeformat
timeformat = '%Y-%m-%d %H:%M:%S'

### error headers
errorHeaders = {304: "Not Modified", 400: "Bad Request", 404: "Not Found", 500: "Internal Server Error"}

### MIMEs
mimes = {
	".html": "text/html", ".htm": "text/html", ".txt": "text/plain",
	".jpeg": "image/jpeg", ".jpg": "image/jpeg", ".gif": "image/gif", ".png": "image/png",
        ".mp3": "audio/mpeg", ".mpeg": "video/mpeg", ".avi": "video/mpeg",
        ".zip": "application/zip", ".gz": "application/x-gzip", ".pdf": "application/pdf",
        }

### this function creates error response message
def processError(errorNumber):
	errorTitle = '%d %s' % (errorNumber, errorHeaders[errorNumber])
	errorMessage = "HTTP/1.1 " + errorTitle + "\n\n<html><head><title>" + errorTitle + "</title></head> \
		<body><h3>" + errorTitle + "</h3></body></html>"
	return errorMessage, errorTitle

### this function processes requested file and returns response body and header or calls for processError function
def processFile(filename, mod_datetime):
	if filename == "/":
		filename = "/index.html"
	path = basepath + filename
	if os.path.exists(path) and os.path.isfile(path):
		inpfile = open(path, 'r')

		# check for 304 error
		if mod_datetime	!= None:
			file_mod_datetime = datetime.datetime.fromtimestamp(os.path.getmtime(path))
			if file_mod_datetime < mod_datetime:				
				return processError(304)

		ext = os.path.splitext(path)[1]
		mime = "text/plain"  # default value
		if mimes.get(ext) != None:
			mime = mimes[ext]
		
		header = "HTTP/1.1 200/OK "
		response = header + "Content-type: %s\r\n\r\n" % mime
		
		if ext == ".py":   # execute python script
			try:
				tmp = open("tmp", "w")
				sys.stdout = tmp
				sys.stderr = tmp
				execfile(path)
				tmp.close()
				tmp = open("tmp", "r")
				#response = header + "Content-type: text/html\r\n\r\n"
				response += "<html><head><title>Python file execution</title></head> \
					<body><h3>Execution results:</h3>" + tmp.read() + "</body></html>"				
			except:
				return processError(500)
			finally:			
				sys.stdout = sys.__stdout__
				sys.stderr = sys.__stderr__
				tmp.close()
				os.remove("tmp")
		else:
			response += inpfile.read()

		inpfile.close()		
		return response, header
	else:
		return processError(404)  # Not found
	
### this function processes requests and returns body and header of response 
def processRequest(request, mod_datetime):
	if request.startswith("GET"):
		requestParams = request.split(' ')		
		try:
			return processFile(requestParams[1], mod_datetime)
		except:
			return processError(500) # Internal Server Error
	else:
		return processError(400)	 # Bad Request


### socket initialization
c = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
c.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

c.bind((host, port))
c.listen(1)

if len(sys.argv) > 1:
	log_filename = sys.argv[1]
	if len(sys.argv) > 2:
		basepath = sys.argv[2]

### main execution cycle
while 1: 
	csock, caddr = c.accept() 	

	cfile = csock.makefile('rw', 0)
	request = cfile.readline().strip()
	tmp = cfile.readline()
# for testing error 304
#	tmp = "If-Modified-Since: 2011-06-27 02:07:27"
	mod_datetime = None
	while tmp.strip() != "":
		if tmp.split(':')[0] == "If-Modified-Since":			
			mod_datetime = datetime.datetime.strptime(tmp[len("If-Modified-Since:"):].strip(), timeformat)			
			break  
		tmp = cfile.readline()		

# getting response body and header
	response, header  = processRequest(request, mod_datetime)
	cfile.write(response)
	cfile.close() 
	
# logging
	logfile = open (log_filename,'a+')	
	logfile.write(
		"request from: " + caddr[0] +
		"\ntime: " + datetime.datetime.now().strftime(timeformat) + 
		"\nrequest: " + request +
		"\nresponse: " + header + "\n\n")
	logfile.close()

	csock.close() 

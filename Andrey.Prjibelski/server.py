#!/usr/bin/python -O

# This is very simple http server written on python.
# One can display basic content such as images, html pages, e.t.c.
# Also it you can run python script on it and see result as web page.
#
# To start server just run this file as "./server.py"
# If file appears to be non-executabe use "chmod +x server.py"
# (you need python to be installed on your computer)
# 
# Server will run on standart 8080 port.
# Type "http://localhost:8080/<filename>" in your browser to try it.
#
# (C) Andrey Prjibelski


import socket
import sys
import os
import datetime
from cStringIO import StringIO

#Log file
logFile = open("log.txt","a")

#Log message
def log(msg):
	logFile.write(str(datetime.datetime.now())+" "+msg+"\n")
	logFile.flush()

#Time format for 304
timeFormat = '%Y-%m-%d %H:%M:%S'

print "Server started"
log("Server started")

#HTTP request methods
HTTPMethods = ["OPTIONS", "GET", "HEAD", "PUT", "POST", "DELETE", "TRACE", "CONNECT"]

#Supported media type
contentType = {
       ".html": "text/html", ".htm": "text/html", ".txt": "text/plain",
       ".jpeg": "image/jpeg", ".jpg": "image/jpeg", ".gif": "image/gif", ".png": "image/png",
       ".mp3": "audio/mpeg", ".mpeg": "video/mpeg", ".avi": "video/mpeg",
       ".zip": "application/zip", ".gz": "application/x-gzip", ".pdf": "application/pdf",
       }

#Content header
def ContentHeader(content):
	return " Content-type: "+content+"\r\n\r\n"

#HTTP Status Codes
HTTPStatus = {
	200: "OK", 304: "Not Modified", 400: "Bad Request", 404: "Not Found", 405: "Method Not Allowed", 
	415: "Unsupported Media Type", 500: "Internal Server Error", 
	}


#Status text
def StatusText(code):
	return str(code)+" "+HTTPStatus[code]
		

#Status header
def StatusHeader(code):
	return "HTTP/1.1 "+StatusText(code)

#Status pages
def StatusPage(code, msg):
	log(StatusText(code)+" "+msg)
	title = StatusText(code)
	return StatusHeader(code)+"\n\n<html><head><title>"+title+"</title></head><body> \
	<h2>"+title+"</h2>"+msg+" \
	</body></html>"

#200
def HTTP200OK():
	log(StatusText(200))
	return StatusHeader(200)

#304
def HTTP304NotModified():
	log(StatusText(304))
	return StatusHeader(304)	

#400
def HTTP400BadRequest(query):
	return StatusPage(400, "Request "+query+" could not be understood by the server.")

#404
def HTTP404NotFound(fileName):
	return StatusPage(404, fileName+" cannot be found.")

#405
def HTTP405MethodNotAllowed(method):
	return StatusPage(405, "Used method "+method+" is not allowed. Available methods: <br> GET")

#415
def HTTP415UnsupportedMediaType(ext):
	return StatusPage(415, "Requested file seems to have unsupported extention "+ext+".")

#500
def HTTP500InternalError():
	return ErrorPage(500, "Internal server error occured.")


#Query ecexutor
def executeQuery(query, dateModified):
	queryList = query.split(' ')
	method = queryList[0].upper()
	if method == "GET":
		try:
			return openFile(queryList[1], dateModified)
		except IndexError:
			return HTTP400BadRequest(query)
	else :
		if method in HTTPMethods:
			return MethodNotAllowed(method)
		else:
			return HTTP400BadRequest(query)


#Try to open requested file
def openFile(fileName, dateModified):
	#Default is index.html
	if fileName == "/":
		fileName = "/index.html"

	#Get file extention
	ext = os.path.splitext(fileName)[1]

	if ext == ".py":
		#Python sctipt
		try:
			#Redirecting output
			bufferString = StringIO()
			sys.stdout = bufferString
			sys.stderr = bufferString
			#Executing
			execfile("."+fileName)

			return HTTP200OK()+ContentHeader(contentType.get(".html"))+"<html><head><title>"+fileName+"</title></head> \
			<body>"+"<br>".join(bufferString.getvalue().split("\n"))+"</body></html>"

		except IOError:
			return HTTP404NotFound(fileName)

		finally:
			#Returning output to its standart values
			sys.stdout = sys.__stdout__
			sys.stderr = sys.__stderr__

	else:
		#Get content type
		if contentType.get(ext) != None:
			content = contentType[ext]

		#If file in not python script, but format is supported
		try:
			inFile = open("."+fileName, "r")

			#Checking for 304
			if dateModified != None:
				if dateModified > datetime.datetime.fromtimestamp(os.path.getmtime(fileName)):
					return HTTP304NotModified()				

			if contentType.get(ext) == None:
				#Unsupported media type
				return HTTP415UnsupportedMediaType(ext)

			return HTTP200OK()+ContentHeader(content)+inFile.read()

		except IOError:
			return HTTP404NotFound(fileName)
		

#Host and port number
host = ''
port = 8080

#Creating sockets
serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM);
serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

		
#Binding socket
serverSocket.bind((host, port))
serverSocket.listen(1)

#Main server loop
try:
	while 1: 
		#Recieving request
		cSocket, cAddress = serverSocket.accept()
		dataFile = cSocket.makefile('rw', 0) 
		query = dataFile.readline().strip()

		#Finding "If-Modified-Since"
		dateModifiedStr = dataFile.readline()
		dateModified = None
		while dateModifiedStr.strip() != "":
			if dateModifiedStr.split(':')[0] == "If-Modified-Since":			
				dateModified = datetime.datetime.strptime(dateModifiedStr[len("If-Modified-Since:"):].strip(), timeFormat)			
				break  
			dateModifiedStr = dataFile.readline()	
		
		#Logging
		log("Request "+query+" from "+str(cAddress))
		#Executing query
		result = executeQuery(query, dateModified)
		#Sending data to client
		dataFile.write(result)

		dataFile.close() 
		cSocket.close()

except KeyboardInterrupt:
	pass
finally:
	print "Shutting down..."
	log("Server shutted down.")
	logFile.close()

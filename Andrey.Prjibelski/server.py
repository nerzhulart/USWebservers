#!/usr/bin/python -O

import socket
import sys

#HTTP request methods
HTTPMethods = ["OPTIONS", "GET", "HEAD", "PUT", "POST", "DELETE", "TRACE", "CONNECT"]

#HTTP headers
HTTPHeaderOK = "HTTP/1.1 200 OK\n\n"
HTTPHeaderBadRequest = "HTTP/1.1 400 Bad Request\n\n"
HTTPHeaderNotFound = "HTTP/1.1 404 Not Found\n\n"
HTTPHeaderMethodNotAllowed = "HTTP/1.1 405 Method Not Allowed\n\n"
HTTPHeaderUnsupported = "HTTP/1.1 415 Unsupported Media Type\n\n"
HTTPHeaderInternalError = "HTTP/1.1 500 Internal Server Error\n\n"


#Host and port number
host = ''
port = 8080

#Creating sockets
serverSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM);
serverSocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

#Error pages
#400
def HTTP400BadRequest(query):
	return HTTPHeaderBadRequest+"  \
	<html><head><title>400 Bad Request</title></head><body> \
	<h2>400 Bad Request</h2> \
	Request "+query+" could not be understood by the server.\
	<br></body></html>"

#404
def HTTP404NotFound(fileName):
	return HTTPHeaderNotFound+" \
	<html><head><title>404 Not Found</title></head> \
	<body><h2>404 Not Found</h2> \
	"+fileName+" cannot be found.<br>\
	</body></html>"

#405
def HTTP405MethodNotAllowed(method):
	return HTTPHeaderMethodNotAllowed+" \
	<html><head><title>405 Method Not Allowed</title></head> \
	<body><h2>405 Method Not Allowed</h2> \
	Used method "+method+" is not allowed. Available methods: <br> \
	GET <br></body></html>"

#415
def HTTP415UnsupportedMediaType(ext):
	return HTTPHeaderUnsupported+" \
	<html><head><title>415 Unsupported Media Type</title></head> \
	<body><h2>415 Unsupported Media Type</h2> \
	Requested file seems to have unsupported extention "+ext+". <br> \
	</body></html>"

#500
def HTTP500InternalError():
	return HTTPHeaderInternalError+" \
	<html><head><title>500 Internal Server Error</title></head> \
	<body><h2>500 Internal Server Error</h2> \
	Internal server error occured. <br> \
	</body></html>"


#Query ecexutor
def executeQuery(query):
	queryList = query.split(' ')
	method = queryList[0].upper()
	if method == "GET":
		try:
			return openFile(queryList[1])
		except IndexError:
			return HTTP400BadRequest(query)
	else :
		if method in HTTPMethods:
			return MethodNotAllowed(method)
		else:
			return HTTP400BadRequest(query)


#Try to open requested file
def openFile(fileName):
	#Default is index.html
	if fileName == "/":
		fileName = "/index.html"
	#Get file extention
	try:
		ext = fileName.rsplit('.', 1)[1]
	except IndexError:
		return HTTP415UnsupportedMediaType("")

	#If file in not python script, but format is supported
	if ext in ["txt", "htm", "html"]:
		try:
			inFile = open("."+fileName, "r")
			#Display text file prorely
			if ext == "txt":
				data = "<br>".join(inFile.readlines())
				return HTTPHeaderOK+"<html><head><title>"+fileName+"</title></head> \
				<body>"+data+"</body></html>"
			#Html displayed as is
			else:
				data = inFile.read()
				return HTTPHeaderOK+data
		except IOError:
			return HTTP404NotFound(fileName)
	else:
		#Python sctipt
		if ext == "py":
			try:
				#Redirecting output
				bufferFile = open("data", "w")
				sys.stdout = bufferFile
				sys.stderr = bufferFile
				#Executing
				execfile("."+fileName)
				bufferFile.close()
				#Reading data properly
				bufferFile = open("data", "r")
				data = "<br>".join(bufferFile.readlines())
				return HTTPHeaderOK+"<html><head><title>"+fileName+"</title></head> \
				<body>"+data+"</body></html>"
			except IOError:
				return HTTP404NotFound(fileName)
			finally:
				#Returning output to its standart values
				sys.stdout = sys.__stdout__
				sys.stderr = sys.__stderr__
		else:
			return HTTP415UnsupportedMediaType(ext)

		
#Binding socket
serverSocket.bind((host, port))
serverSocket.listen(1)

#Main server loop
while 1: 
	#Recieving request
	cSocket, cAddress = serverSocket.accept() 
	dataFile = cSocket.makefile('rw', 0) 
	query = dataFile.readline().strip()
	#Executing query
	result = executeQuery(query)
	#Sending data to client
	dataFile.write(result)
	dataFile.close() 
	cSocket.close()

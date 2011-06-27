"""
This is simple http server. It supports default file types,
basic response types and multithreading 

To run this server exec:
python  server.py <port_to_run_on>

Alice Afonina, 2011
"""
import socket
from datetime import datetime
import os
import sys
import re
import commands
import threading
import Queue

text = {
"200" : "OK",
"304" : "Not Modified",
"400" : "Bad Request",
"404" : "Not Found",
"500" : "Internal Server Error",
}

content = {
"" 		: "text/plain",
"txt" 	: "text/plain", 
"html" 	: "text/html",
"xml" 	: "text/xml",
"jpg" 	: "image/jpeg", 
"png" 	: "image/png",
"gif" 	: "image/gif",
"mpeg" 	: "video/mpeg",
"avi" 	: "video/mpeg",
"gz" 	: "application/x-gzip",
"zip" 	: "application/zip",
"pdf" 	: "application/pdf",
"mp3"	: "audio/mpeg"
}

def create_header(code, ext):
	return  "HTTP/1.1 """ + code + " " + text[code] + \
			"\nContent-Type:" + content[ext] + \
			"\n\n"
			
log_file = open("log.txt", "a+r")			
def log(addr, request, result):
	log_file.write(" ".join((str(datetime.now()), 
					":".join((addr[0], 
					str(addr[1]))),
					request, result)))
	log_file.write("\n")
	log_file.flush()
	  
class Processor(threading.Thread):
	def run(self):
		filename = ""
		while True:
			client, self.addr = clients.get()
			data = self.receive_message(client)
			try:
				request = str(data).split("\r\n")
				filename = request[0].split(" ")[1]
				modified = [x for x in request if x.find("If-Modified-Since:") != -1]
				modified_date = None
				if modified != []:
					date = modified[0].partition(":")[2]
					modified_date = datetime.strptime(date, " %a, %d %b %Y %H:%M:%S GMT")
			except:
				self.send_message(client, "", "400", "html")
			try:		
				dirname = os.getcwd() + filename
				if not os.path.exists(dirname):
					self.send_message(client, filename, "404", "html")
				else:
					with open(dirname, "r") as f:
						py_script_pattern = re.compile('.*py')
						if modified_date:	
							file_modified_ts = os.path.getmtime(dirname)
							file_modified = datetime.fromtimestamp(file_modified_ts)
							if file_modified < modified_date:
								self.send_message(client, filename, "304", "html", result)
								break
						if not py_script_pattern.match(filename): 
							result = "".join(f.readlines())
							filename_parts = filename.split(".")
							ext = filename_parts[len(filename_parts)-1]		
							self.send_message(client, filename, "200",  ext.lower(), result)
						else:
							result = commands.getoutput("python " + dirname)
							self.send_message(client, filename, "200", "txt", result)
			except:
				self.send_message(client, filename, "500", "html")				

	def receive_message(self, client):
		data = ""
		chunk_size = 2096
		while (1):
			chunk = client.recv(chunk_size)
			data += chunk
			if len(chunk) < chunk_size:
				break
		return data
		
	def send_message(self, client, request, code,  ext, result=None):
		header = create_header(code, ext)
		client.send(header)
		if not result:
			with open(code + ".html", "r") as f:
				result = "".join(f.readlines())		
		client.sendall(result)
		log(self.addr, request, code)
		client.close()
		
clients = Queue.Queue (0)	

def main():
	host = ''
	args = sys.argv		
	if len(args) < 1 or len(args) > 2:		
		print "Wrong number of arguments. No port selected. By default, server \n would be started on 6006 port."
		port = 6006
	else:
		port = args[1]			 
	s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
	s.bind((host, int(port)))
	s.listen(1)
	try:
		for i in range(3):
			Processor().start()
		while(1):
			clients.put(s.accept())
	except:
		print "Server Error"
		exit()
	finally:
		log_file.close()
		s.close()		
if __name__ == '__main__' :
  main()

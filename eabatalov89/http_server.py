#!/usr/bin/python2.6

# date: 06/27/2011
# mail: eabatalov89@gmail.com
# program: simple http server 
# language: python
# supported http codes: 500, 404, 400, 304, 200
# supported mymetypes: below in ext_cont_type dictionary
# scripts: executes python scripts (executes and passes stdout to client) with no GET\POST parameters
# this means no interaction between server and python code.
# command line args: port to listen on all intefaces, log file
# ------------------------Features--------------------------------
# single-threaded 
# starts from init() function
# processes request by checking each potential http error
# if no such, returns requested content or 304 Not Modified

import sys
import socket
import re
from datetime import datetime
import time
import os
import email.utils as eut
import subprocess
import StringIO

lsn_port = 8080
lsn_host = ''
lsn_socket = None
log_file_name = "stdout"
log_file = None

req_file_ext = None
req_file_path = None
req_modif_since = None
req_file_name = None

ext_cont_type = { \
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
"mpeg" : "video/mpeg" }

err_code_description = {
500 : "Internal Server Error",
404: "Not Found",
400: "Bad Request",
304: "Not Modified",
200: "Ok"
}


def parse_request(req_str):
   global req_file_path
   global req_file_ext
   global req_modif_since
   global req_file_name
   match_file = re.search("GET /(\w+)\.(\w+)", req_str)
   if match_file:
      req_file_path = ""
      req_file_name = match_file.group(1)
      req_file_ext = match_file.group(2) 
   else:
      req_file_ext = "html"
      req_file_path = ""
      req_file_name = "index"
   match_ifmod = re.search("If-Modified-Since: (.*)", req_str)
   if not match_ifmod:
      req_modif_since = None
   else:
      req_modif_since = match_ifmod.group(1).strip()
   
   print req_file_path
   print req_file_name
   print req_file_ext

def req_file():
   return "./" + req_file_path + req_file_name + "." + req_file_ext
 

def generate_response(code, log_msg):
   print >>log_file, datetime.now(), " ", str(code), " ", log_msg
   log_file.flush()
   return "HTTP/1.1 " + str(code) + " " + err_code_description[code]  + "\nServer: PyPyPyPyPyPyPy\n|"

def internal_error(exception):
   return generate_response(500, str(exception))


def bad_request(req_str):
   if (not req_file_ext) or (not req_file_name):
      return generate_response(400, "No file specified  \n" + req_str)
   else: 
      return None


def not_found(req_str):
   if os.path.exists(req_file()):
      return None
   else: 
      return generate_response(404, req_file())


def not_modified(req_str):
   if req_modif_since:
      last_modif = eut.formatdate(os.path.getmtime( req_file() ), usegmt = True).strip()
      if last_modif == req_modif_since:
         return generate_response(304, req_file())
      else: return None
   else: return None


def handle_file():
   if not ext_cont_type.has_key(req_file_ext):
      return generate_response(400, "MIME type not supported: " + req_file())
   header = generate_response(200, req_file())
   header += "Content-Type: " + ext_cont_type[req_file_ext] + "\n"
   if req_file_ext == "py":
      std_out = StringIO.StringIO()
      sys.stdout = std_out
      execfile(req_file())
      sys.stdout = sys.__stdout__
      body = std_out.getvalue()
      std_out.close()
   else:
      f = open(req_file(), "r")
      body = f.read()
      f.close()

   last_modif = eut.formatdate(os.path.getmtime(req_file()), usegmt = True)
   header += "Content-Length: " + str(len(body)) + "\n"
   header +="Last-Modified: " + last_modif + "\n"
   header += "Connection: close"
   return header + "\n\n" + body

def process(req_str):
#   try:
      parse_request(req_str)

      print >>log_file, "INCOMING HTTP REQUEST:"
      print >>log_file, req_str
      
      resp = bad_request(req_str)
      if resp: return resp

      resp = not_found(req_str)
      if resp: return resp

      resp = not_modified(req_str)
      if resp: return resp

      resp = handle_file()
      if resp: return resp

      return BAD_REQUEST_STR
#   except:
#      return internal_error(str(sys.exc_info()[0]))

def finalize():
   if lsn_socket:
      lsn_socket.close()
   if log_file:
      log_file.close()

def init():
   global lsn_port
   global lsn_socket
   global lsn_host
   global log_file
   global log_file_name

   print "Console args: ", sys.argv
   if (len(sys.argv) > 1):
       lsn_port = int(sys.argv[1])
   if (len(sys.argv) > 2): 
      log_file_name = sys.argv[2]
      log_file = open(log_file_name, "a")
   else:
      log_file = sys.stdout

   print "logging to file ", log_file_name
   print >>log_file, "starting http server..."
   lsn_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
   print >>log_file, "binding to all interfaces at ", lsn_port, " port"
   lsn_socket.bind((lsn_host, lsn_port))
   print >>log_file, "starting listening..."
   lsn_socket.listen(10)
   print >>log_file, "server ready"
   while 1:
      cl_socket, cl_addr = lsn_socket.accept()
      print >>log_file, "connection accepted from ", cl_addr
      data = cl_socket.recv(4096)
      response = process(data)
      cl_socket.send(response)
      cl_socket.close()
    
# main:
try:
   init()
except KeyboardInterrupt:
   print >>log_file, "exiting by keyboard interrupt"
finally:   
   finalize()

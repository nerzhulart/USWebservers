# /usr/bin/python2.6
import sys
import socket
import re
from datetime import datetime
import time
import os
import email.utils as eut
import subprocess

lsn_port = 8080
lsn_host = ''
lsn_socket = None
log_file_name = "stdout"
log_file = None

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

def internal_error():
   print >>log_file, datetime.now(), " 500 Internal Server Error - ", sys.exc_info()[0]
   return """HTTP/1.1 500 Internal Server Error
Server: PyPyPyPyPyPyPy
connection: close"""

BAD_REQUEST_STR = """HTTP/1.1 400 Bad Request
Server: PyPyPyPyPyPyPy
connection: close"""

def bad_request(req_str):
   #match_enc = re.search("Accept-Charset: .*utf-8.*", req_str) 
   #match_file = re.search("(GET|POST) /(\w+)\.(\w+)", req_str)
   #if (not match_enc) or (not match_file):
   #   print >>log_file, datetime.now(), " 400 Bad Request - Client Browser Doesnt support utf-8 encoding \n", req_str
   #   return BAD_REQUEST_STR
   #else: 
   return None

def not_found(req_str):
   match_file = re.search("(GET|POST) /(\w+)\.(\w+)", req_str)
   req_file_path = match_file.group(2)
   req_ext = match_file.group(3) 
   if os.path.exists("./" + req_file_path + "." + req_ext):
      return None
   else: 
      print >>log_file, datetime.now(), " 404 Not Found - file: ", "./" + req_file_path + "." + req_ext
      return """HTTP/1.1 404 Not Found
Server: PyPyPyPyPyPyPy
connection: close"""

def not_modified(req_str):
   match_ifmod = re.search("If-Modified-Since: (.*)", req_str)
   if not match_ifmod: return None
   else:
      match_file = re.search("(GET|POST) /(\w+)\.(\w+)", req_str)
      req_file_path = match_file.group(2)
      req_ext = match_file.group(3) 
      last_modif = eut.formatdate(os.path.getmtime( "./" + req_file_path + "." + req_ext), usegmt = True).strip()
      req_last_modif = match_ifmod.group(1).strip()
      if last_modif == req_last_modif:
         print >>log_file, datetime.now(), " 304 Not Modified - file: ", "./" + req_file_path + "." + req_ext
         return """HTTP/1.1 304 Not Modified
Server: PyPyPyPyPyPyPy
connection: close"""
      else: return None

def handle_file(req_str):
   header = """HTTP/1.1 200 OK
Server: PyPyPyPyPyPyPy
"""
   match_file = re.search("(GET|POST) /(\w+)\.(\w+)", req_str)
   req_file_path = match_file.group(2)
   req_ext = match_file.group(3) 
   req_file = req_file_path + "." + req_ext

   if not ext_cont_type.has_key(req_ext):
      return BAD_REQUEST_STR
   header += "Content-Type: " + ext_cont_type[req_ext] + "\n"
   if req_ext == "py":
      std_out = os.popen("/usr/bin/python2.6 " + req_file)
      if not std_out:
         return internal_error()
      else:
         body = std_out.read()
         std_out.close()
   else:
      f = open(req_file, "r")
      body = f.read()
      f.close()

   last_modif = os.path.getmtime(req_file)
   last_modif_fmt = eut.formatdate(last_modif, usegmt = True)
   
   header += "Content-Length: " + str(len(body)) + "\n"
   header +="Last-Modified: " + last_modif_fmt + "\n"
   header += "Connection: close"

   print >>log_file, datetime.now(), "\n", header
   return header + "\n\n" + body

def process(req_str):
   try:
      print >>log_file, "INCOMING HTTP REQUEST:"
      print >>log_file, req_str
      
      resp = bad_request(req_str)
      if resp: return resp

      resp = not_found(req_str)
      if resp: return resp

      resp = not_modified(req_str)
      if resp: return resp

      resp = handle_file(req_str)
      if resp: return resp

      return BAD_REQUEST_STR
   except:
      return internal_error()

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
      log_file = open(log_file_name, "w")
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

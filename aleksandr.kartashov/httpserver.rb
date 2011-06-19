#!/usr/bin/ruby

require 'socket'
require 'time'

# --------------------------------------------------------------------------------

iface = "127.0.0.1"
port  = 8080
log_file = "http.log"

# --------------------------------------------------------------------------------

mimes = {
  "html" => "text/html",
  "xml" => "text/xml",
  "jpg" => "image/jpeg",
  "jpeg" => "image/jpeg",
  "png" => "image/png",
  "gif" => "image/gif",
  "mpg" => "audio/mpeg",
  "zip" => "application/zip",
  "gz" => "application/x-gzip",
  "pdf" => "application/pdf"
}

at_cache = { }

# --------------------------------------------------------------------------------

class BadRequest < RuntimeError
end

class HttpRequest
  def initialize(lines)
    m = /GET \/(.+) HTTP/.match(lines[0])

    if m != nil
      @resource = m.captures[0]
    else
      @resource = nil
    end

    if @resource == nil
      raise BadRequest
    end

    m = /(.+)\?(.+)/.match(@resource)
    if m != nil
      @resource = m.captures[0]
      @params = m.captures[1]
    else
      @params = nil
    end
      
    @headers = { }

    for i in 1..(lines.size - 1)
      cap = /(.+?):\s*(.+)/.match(lines[i])
      @headers[cap[1]] = cap[2]
    end
  end

  def headers
    @headers
  end

  def path
    @resource
  end

  def params
    @params
  end
end


class HttpResponse
  def initialize
    @headers = { "Connection" => "close" }
    @code = "200 OK"
  end

  def headers 
    @headers
  end

  def headers=(v)
    @headers = v
  end

  def code
    @code
  end

  def code=(v) 
    @code = v
  end

  def content=(v)
    @content = v
    @headers["Content-Length"] = @content.size.to_s
  end

  def mime=(v)
    @mime = v
    @headers["Content-Type"] = @mime
  end

  def write(stream)
    s = "HTTP/1.0 #{@code}\r\n"

    for header, value in @headers
      s += header + ": " + value + "\r\n"
    end

    stream.write s + "\r\n"
    
    if @content != nil
      stream.write @content
    end
  end
end


class Log 
  def initialize(log_fp)
    @log = File.new log_fp, "w"
  end

  def write(message)
    @log.write "[#{Time.now}] #{message}\n"
  end
end

# --------------------------------------------------------------------------------
# Program entry

server = TCPServer.new iface, port
log    = Log.new log_file

while remote = server.accept
  rem_addr = remote.addr
  client = "#{rem_addr[2]} (#{rem_addr[3]})"
  log.write "Accepted connection from #{client}"

  stat = 0
  req = []
  line = ""
  
  # read until an empty line
  while stat != 2
    rd = remote.read(1)
    b = rd[0]
    
    if b != 0xD
      if b == 0xA
        case
          when stat == 0 then stat = 1; req = req + [line]; line = ""
          when stat == 1 then stat = 2
        end
      else
        stat = 0
        line = line + b.chr
      end      
    end
  end

  res = HttpResponse.new

  begin
    req = HttpRequest.new(req)
    ext = /\.(.+)$/.match(req.path).captures[0]

    log.write "Requested #{req.path} by #{client}"

    if ext != "rb"
      # reply with a local file

      mime = mimes[ext]
      if mime == nil
        mime = "text/plain"
      end 
  
      f = File.new(req.path)
      res.mime = mime

      # last modification control
      mt = req.headers["If-Modified-Since"]
      if mt != nil
        if Time.parse(mt) >= f.mtime
          res.code = "304 Not modified"
        else
          res.content = f.read
        end
      else
        res.content = f.read
      end

      res.headers["Last-Modified"] = f.mtime.to_s

    else
      # run a Ruby program and reply with its stdout
      pipe = nil

      if req.params != nil
        pipe = IO.popen("ruby " + req.path + " " + req.params.sub("&", " "), "w+")
      else 
        pipe = IO.popen("ruby " + req.path, "w+")
      end

      pipe.close_write
      res.content = pipe.read
      pipe.close_read
    end

  rescue BadRequest => e
    res.code = "400 Bad request"
    res.mime = "text/html"
    res.content = "<html><head><title>Bad request</title></head><body>Bad request</body></html>"
    
  rescue Errno::ENOENT => e
    res.code = "404 Not found"
    res.mime = "text/html"
    res.content = "<html><head><title>Path not found</title></head><body>Not found: #{req.path}</body></html>"

  rescue Exception => e
    res.code = "500 Internal server error"
    res.mime = "text/html"
    res.content = "<html><head><title>Internal server error</title></head><body>Internal server error</body></html>"

    e.display
    puts e.backtrace
    puts e.class
  end

  res.write remote
  log.write "Responded with #{res.code} to #{client}"
  
  remote.close
end


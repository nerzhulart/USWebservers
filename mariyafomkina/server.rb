#!/usr/bin/env ruby

# To make it work:
# $: apt-get install ruby ruby-dev rubygems sqlite3 sqlite3-dev
# $: gem install activerecord sqlite3
require 'socket'
require './logger.rb'

module SPbAU
  class Server
    def initialize
      require './settings.rb'
      @logger = SampleLogger.new
      @server = TCPServer.new(@@host, @@port)
      @content_by_ext = { 
        ".html"   => "text/html",
        ".htm"    => "text/html", 
        ".txt"    => "text/plain",
        ".xml"    => "text/xml",
        ".xsl"    => "text/xml",
        ".jpeg"   => "image/jpeg",
        ".jpg"    => "image/jpeg",
        ".png"    => "image/png",
        ".gif"    => "image/gif",
        ".mp3"    => "audio/mpeg",
        ".zip"    => "application/zip",
        ".gzip"   => "application/x-gzip",
        ".pdf"    => "application/pdf",
        ".mp4"    => "video/mpeg",
        ".mpeg"   => "video/mpeg",
        ".avi"    => "video/mpeg", 
        ".erb"    => "text/html"
      }
      @content_by_ext.default = "text/plain"
    end

    def listen
      loop do
        session = @server.accept
        Thread.start(session) do |session|
          proceed(session)
          session.close
        end
      end
    end

    def proceed(session)
      begin
        args = Hash.new
        request = session.gets
        line = session.gets
        while line.strip != ''
          line.gsub(/(.*):(.*)/) do |str|
            args[$1.strip] = $2.strip
          end
          line = session.gets
        end
        p args
        hostname = nil
        filename = nil
        version = nil
        ip = session.peeraddr[3]
        request.gsub(/GET\s*http:\/\/([^\s]+?)\/([^\s]*)\s*HTTP\/(\d*\.\d*)/) do |str|
          hostname = $1
          filename = $2
          version = $3
        end      
        if filename == nil
          request.gsub(/GET\s*\/([^\s]*)\s*HTTP\/(\d*\.\d*)/) do |str|
            filename = $1
            version = $2
          end
          hostname = args["Host"] 
        end
        if filename == nil 
          content = File.open('./400.html', "r").read
          session.print("HTTP/1.1 400 Bad Request\nServer: #{@@server_name}\n")
          session.print("Content-type: text/html\n\n#{content}")
          @logger.write(ip, filename, 400)
          return
        end
        filename = @@root + filename
        ext = File.extname(filename)
        content_type = @content_by_ext[ext]
        if !File.exists?(filename)
          content = File.open('./404.html', "r").read
          session.print("HTTP/1.1 404 Not Found\nServer: #{@@server_name}\n")
          session.print("Content-type: text/html\n\n#{content}")
          @logger.write(ip, filename, 404)
          return
        end
        time = args["If-Modified-Since"]
        if !time.nil?
          if Time.parse(time) > File.mtime(filename) 
            session.print("HTTP/1.1 304 Not Modified\nServer: #{@@server_name}\n\n")
            @logger.write(ip, filename, 304)
            return
          end 
        end
        if ext == ".erb"
          pipe = IO.popen("eruby #{filename}", "rb")
          content = pipe.read
        else
          content = File.open(filename, "rb").read
        end
        session.print("HTTP/#{version} 200 OK\nServer: #{@@server_name}\n")
        session.print("Content-type: #{content_type}\n\n#{content}")
        @logger.write(ip, filename, 200)
      rescue
        session.print("HTTP/1.1 500 Internal Server Error\n")
        session.print("Server: #{@@server_name}\n\n")
        @logger.write(ip, filename, 500)
      end
    end
  end
end

server = SPbAU::Server.new
server.listen

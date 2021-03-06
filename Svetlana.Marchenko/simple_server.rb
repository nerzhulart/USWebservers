=begin
  Author: Svetlana Marchenko
  This is simple web server that can serve requests for some content types (txt, html, css, ruby files, images, css etc). 
  It has logging support.
  Multi-thread mechanism.
  http status codes (200, 400, 404, 500) support.
  No https.
  
  command for server start:
    ruby simple_server.rb [path to the base folder]
=end

$:.unshift(File.expand_path("./"))

require 'socket'
require 'generator'


def writeIntoLog(message)
  logStr =  "\n#{message}"
  $log.puts logStr if $log != nil
  $stderr.puts logStr if $log != nil
end

class HttpServer
  def initialize(session, request, basePath)
    @session = session
    @request = request
    @basePath = basePath
    @status = {
      200=>"OK",
      304=>"Modified",
      400=>"Bad_Request",
      404=>"Not_Found",
      500=>"Internal_Server_Error"
      }
    @contentTypes = {
      ".html"=>"text/html",
      ".htm" =>"text/html",
      ".txt" =>"text/plain",
      ".rb"  =>"text/plain",
      ".jpeg"=>"image/jpeg",
      ".jpg" =>"image/jpeg",
      ".gif" =>"image/gif",
      ".bmp" =>"image/bmp",
      ".png" =>"image/png",
      ".xml" =>"text/xml",
      ".mpg" =>"video/mpeg",
      ".zip" =>"application/zip",
      ".pdf" =>"application/pdf",
      ".mp3" =>"audio/mpeg"
      }
    @contentTypes.default = "unknown/unknown"
  end

  def getFullPath()
    fileName = nil
    if @request =~ /GET .* HTTP.*/
      fileName = @request.gsub(/GET /, '').gsub(/ HTTP.*/, '')
    end
    fileName = fileName.strip
    unless fileName == nil
      fileName = @basePath + fileName
      fileName = File.expand_path(fileName, @defaultPath)
    end
    fileName << "/index.html" if  File.directory?(fileName)
    return fileName
  end

  def serve()
    @fullPath = getFullPath()
    begin
      contentType = getContentType(@fullPath)
      if File.exist?(@fullPath) and File.file?(@fullPath)
	if @fullPath.index(@basePath) == 0 
	  header = generateHeader(200, @status[200], contentType)
	  writeIntoLog(generateLogMessage(@session, 200, @status[200], contentType))
	  @session.print header
	  ext = File.extname(@fullPath)
	  if ext == ".rb"
	    @session.print `ruby #{@fullPath}`
	  else
	    getFileContent(@fullPath)
	  end
	else #endif fullPath starts with basePath
	  @session.print generateHeader(400, @status[400], @contentTypes[".html"])
	  @session.print generateErrorPage(400, @status[400])
	  writeIntoLog(generateLogMessage(@session, 400, @status[400], contentType))
	end
      else #endif File.exist
	@session.print generateHeader(404, @status[404], @contentTypes[".html"])
	@session.print generateErrorPage(404, @status[404])
	print "file not found \n"
	writeIntoLog(generateLogMessage(@session, 404, @status[404], contentType))
      end
    ensure
      @session.close
    end
  end

  def getFileContent(path)
    contentFile = IO.read(path)
    @session.print contentFile
  end
  

  def getContentType(path)
    ext = File.extname(path)
    @contentTypes[ext]
  end
end

#======================================



if (ARGV.length > 0)
	basePath = File.expand_path(ARGV[0])
else
	basePath = File.expand_path("./")
end

$server = TCPServer.new('127.0.0.1', 9090)
logfile = basePath + "/log.txt"
$log = File.open(logfile, "a")
$log.sync = true

loop do
  session = $server.accept
  request = session.gets
  logStr =  "#{session.peeraddr[2]} (#{session.peeraddr[3]}) "
  logStr += Time.now.localtime.strftime("%Y/%m/%d %H:%M:%S")
  logStr += " #{request}"
  writeIntoLog(logStr)

  Thread.start(session, request) do |session, request|
    HttpServer.new(session, request, basePath).serve()
  end
end
$log.close

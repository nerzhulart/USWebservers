require 'socket'

def writeIntoLog(message)
  logStr =  "\n\n\n\n\n\n#{message}"
  $log.puts logStr if $log != nil
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
			print "#{contentType}"
			if (contentType != "error")
	      if File.exist?(@fullPath) and File.file?(@fullPath)
					if @fullPath.index(@basePath) == 0 
							okMessage = "HTTP/1.1 200/OK\r\nServer: Simple Http Server On Ruby\r\nContent-type: #{contentType}\r\n\r\n"
							writeIntoLog(okMessage)
				  		@session.print okMessage
							ext = File.extname(@fullPath)
							if ext == ".rb"
								@session.print `ruby #{@fullPath}` 
							else
								printFileContent(@fullPath)
							end
					else #endif fullPath starts with basePath
						handleError(400, @status[400])
					end
  	    else #endif File.exist
					handleError(404, @status[404])
  	    end
			else #endif error content type
				handleError(500, @status[500])
			end  
    ensure
      @session.close
    end
  end

	def printFileContent(path)
		src = File.open(path, "rb")
   	while (not src.eof?)
     	buffer = src.read(256)
     	@session.write(buffer)
   	end
   	src.close
   	src = nil
	end

	def handleError(status, message)
		command = "ruby error.rb #{status} #{message}"
		@session.print `#{command}`
	end

  def getContentType(path)

    ext = File.extname(path)
		case ext
			when ".html"
				return "text/html"
			when ".htm"
				return "text/html"
			when ".txt"
				return "text/plain"
			when ".css"
				return "text/css"
			when ".jpeg"
				return "image/jpeg"
			when ".jpg"
				return "image/jpeg"
			when ".gif"
				return "image/gif"
			when ".bmp"
				return "image/bmp"
			when ".xml"
				return "text/xml"
			when ".rb"
				return "text/plain"
			else
				return "error"
		end
  end
end

#======================================



if (ARGV.length > 0)
	basePath = ARGV[0]
else
	basePath = "/home/lana/Study/unix"
end

server = TCPServer.new('127.0.0.1', 9090)
logfile = basePath + "/log.txt"
$log = File.open(logfile, "a")

loop do
  session = server.accept
  request = session.gets
  logStr =  "#{session.peeraddr[2]} (#{session.peeraddr[3]})\n"
  logStr += Time.now.localtime.strftime("%Y/%m/%d %H:%M:%S")
  logStr += "\n#{request}"
  logStr += "\nbase path #{basePath}\n"
  writeIntoLog(logStr)

  Thread.start(session, request) do |session, request|
    HttpServer.new(session, request, basePath).serve()
  end
end
$log.close

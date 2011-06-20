#This is a simple implementaion of HTTP server
#Usage: server <path_to_docs> <port>

require 'socket'
class HttpServer
    @session
    @request
    @requestParams
    @basePath
    ServerName = "Nerzhul Web Server"
    ResponseCodes = {
        200 => "HTTP/1.1 200/OK",
        304 => "HTTP/1.1 304/Not Modified",
        400 => "HTTP/1.1 400/Bad Request",
        404 => "HTTP/1.1 404/Not Found",
        500 => "HTTP/1.1 500/Internal Server Error"
    }
    MimeTypes = {
        ".html" => "text/html",
        ".htm" => "text/html",
        ".txt" => "text/plain",
        ".css" => "text/css",
        ".jpeg" => "image/jpeg",
        ".jpg" => "image/jpeg",
        ".gif" => "image/gif",
        ".bmp" => "image/bmp",
        ".bmp" => "image/bmp",
        ".rb" => "text/html",
        ".xml" => "text/xml",
        ".xsl" => "text/xml",
        ".mp3" => "audio/mpeg",
        ".ogg" => "audio/mpeg",
        ".zip" => "application/zip",
        ".gz" => "application/x-gzip",
        ".pdf" => "application/pdf",
        ".mp4" => "video/mpeg",
        ".avi" => "video/mpeg",
        ".mpeg" => "video/mpeg"
    }
    MimeTypes.default = "text/html"

    def initialize(session, request, requestParams, basePath)
        @session = session
        @request = request
        @requestParams = requestParams
        @basePath = basePath
    end

    def getFullPath()
        fileName = nil
        if @request =~ /GET .* HTTP.*/
            fileName = @request.gsub(/GET /, '').gsub(/ HTTP.*/, '')
        else
            return nil
        end
        fileName = fileName.strip
        unless fileName == nil
            fileName = @basePath + fileName
            fileName = File.expand_path(fileName, @basePath)
            fileName.gsub!('/', '\\')
        end
        fileName << "\\index.html" if  File.directory?(fileName)
        return fileName
    end

    def processRequest()
        log("Request from #{@session.peeraddr[2]} : #{@request.strip}")
        responseHead = ""
        responseBody = ""
        responseCode = 0
        begin
            @fullPath = getFullPath()
            file = nil
            if @fullPath.nil?
                responseCode = 400

            elsif if File.exist?(@fullPath) and File.file?(@fullPath)
                      if @fullPath.index(@basePath) == 0
                          contentType = getContentType(@fullPath)
                          fileContent = nil
                          userTime = nil
                          ifModifiedAttr = false
                          if @requestParams.key?("If-Modified-Since")
                              dateStr = @requestParams["If-Modified-Since"]
                              userTime = DateTime.parse(dateStr)
                              ifModifiedAttr = true
                          end
                          file = File.open(@fullPath, "rb")
                          modifiedTime = file.mtime

                          if ifModifiedAttr and (modifiedTime < userTime.to_time)
                              responseCode = 304
                          else
                              responseCode = 200
                              responseBody = "Content-type: #{contentType}\r\n\r\n"
                          end
                          if File.extname(@fullPath) == ".rb"
                              fileContent = `ruby #{@fullPath}`
                          else
                              fileContent = file.read
                          end
                          responseBody += fileContent
                          file.close
                          file = nil
                      else
                          responseCode = 404
                      end
                  else
                      responseCode = 404
                  end
            end
        rescue
            responseCode = 500
        ensure
            responseHead = "#{ResponseCodes[responseCode]}\r\nServer: #{ServerName}\r\n"
            response = responseHead + responseBody + "\r\n"
            @session.print response
            log "Response for #{@session.peeraddr[2]}: #{ResponseCodes[responseCode]}"
            file.close unless file == nil
            @session.close
        end
    end

    def getContentType(path)
        ext = File.extname(path)
        type = MimeTypes[ext]
        if  type == nil
            type = "text/html"
        end
        type
    end
end

def log(message)
    logStr = "#{Time.now}: #{message}"
    puts logStr
    logFile = File.open($logFileName, "a+")
    logFile.puts logStr unless logFile == nil
    logFile.close
end

if ARGV.length != 2
    puts "Usage: server <path_to_docs> <port>"
    exit()
end
documentRoot = ARGV[0]
port = ARGV[1]
server = TCPServer.new('127.0.0.1', port)
$logFileName = documentRoot + "\\log.txt"


loop do
    session = server.accept
    request = session.gets

    requestParams = Hash.new
    tmp = session.gets
    while tmp.strip != ""
        curParams = tmp.split(':', 2)
        requestParams[curParams[0]] = curParams[1]
        tmp = session.gets
    end

    Thread.start(session, request, requestParams) do |session, request, requestParams|
        HttpServer.new(session, request, requestParams, documentRoot).processRequest()
    end
end
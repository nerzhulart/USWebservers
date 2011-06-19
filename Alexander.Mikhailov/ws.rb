require 'socket'
require 'time'

$hostname = '127.0.0.1'
$port = 80
$serverName = "AXL's server"
$workdir = File.expand_path('.')

# Log without any formatting, except \n at the EOL
def log_raw(message)
	print message + "\n"
end

# Formats message as "HH:MM:SS message"
def log(message)	
	log_raw(Time.now.strftime("%H:%M:%S: #{message}"))
end

# Main client processing function
def serveClient(session) 
	request = session.gets
	fullRequest = request
	ln = ''
	condition = nil
	while ln != "\r\n"
		ln = session.gets
		fullRequest += ln
		m = /If-Modified-Since: (.+)/.match(ln)
		if m != nil
			condition = Time.parse(m.captures[0])
			break
		end
	end
	
	m = /GET (\/.+) HTTP/.match(request)
	return sendError(session, "400 Bad Request") if m == nil
	
	fileName = m.captures[0].strip
	
	begin
		return if fileName == "/favicon.ico"
		
		fileName = "/index.html" if fileName.empty?
		fileName = $workdir + fileName
		
		if File.exist?(fileName) and File.file?(fileName) 
			return serveFile(fileName, session, condition)
		else
			return sendError(session, "404 Not Found")
		end
	rescue
		return sendError(session, "500 Internal Server Error")
	ensure
		session.close
	end
end


def sendError(session, error) 
	header = createHeader({'code' => error}, {})
	msg = header + "<h1> Error #{error} </h1>"
	session.print msg
	log("#{error} send to: " + session.addr[3])
end


def createHeader(mandatory, optional)
	header = ''
	header += "HTTP/1.1 " + mandatory['code'] + "\n"
	header += "Server: " + $serverName + "\n"
	header += "Content-Type: " + mandatory['content-type'] + "\n" if mandatory['content-type'] != nil
	optional.each do |v|
		header += v[0] + ": " + v[1] + "\n"
	end
	header += "\n"
end

def getContentType(path)
    ext = File.extname(path)
    return "text/html"          if ext == ".html" or ext == ".htm"
    return "text/plain"         if ext == ".txt"
    return "text/xml"           if ext == ".xml"
	return "image/jpeg"         if ext == ".jpeg" or ext == ".jpg"
	return "image/png"          if ext == ".png"
	return "image/gif"          if ext == ".gif"
	return "audio/mpeg"         if ext == ""
	return "application/zip"    if ext == ".zip"
	return "application/x-gzip" if ext == ".gz"
	return "application/pdf"    if ext == ".pdf"
	return "video/mpeg"         if ext == ""
	return "text/css"           if ext == ".css"
	return "text/html"          if ext == ".rb"
    return "text/plain"
end

def serveFile(path, session, ifdate) 	
	if ifdate != nil 
		time = File.mtime(path)
		if ifdate >= time
			header = createHeader({'code'=>'304 Not modified'}, {'Last-Modified'=>time.httpdate})
			session.print header
			return
		end
	end
	
	header = createHeader({'code'=>'200 Ok', 'content-type'=>getContentType(path)}, {'Last-Modified'=>File.mtime(path).httpdate})
	
	ext = File.extname(path)
	if ext == ".rb"
		pipe = IO.popen("ruby " + path, "w+")
		session.print header
		pipe.close_write
		session.print pipe.read
		pipe.close_read
		return
	end
	
	session.print header
	
	file = File.open(path, "rb")
    while (not file.eof?)
		buffer = file.read(256)
		session.print buffer
    end
    file.close
end

#Starting server
server = TCPServer.new($hostname, $port)
log_raw(Time.now.strftime("%d.%m.%Y %H:%M:%S #{$serverName} started"))

#loop {
	session = server.accept
	serveClient(session)
#}

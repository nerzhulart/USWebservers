=begin
  Author: Svetlana Marchenko
  This is augxillary file with functions for headers (for response) and html code (for error pages) generating.
=end

def generateHeader(status, message, contentType)
  header = "HTTP/1.1 #{status}/#{message}\r\nServer: Simple Http Server On Ruby\r\nContent-type: #{contentType}\r\n\r\n"
  header
end

def generateLogMessage(session, status, message, contentType)
	logStr  = "#{session.peeraddr[2]} (#{session.peeraddr[3]}) "
	logStr += Time.now.localtime.strftime("%Y/%m/%d %H:%M:%S")
	logStr += " HTTP/1.1 #{status}/#{message} Content-type: #{contentType}"
	logStr
end

def generateErrorPage(status, message)
  htmlText = "  
  <!DOCTYPE html>
  <html>
  <head>
  <meta charset=\"utf-8\" />
  <title>Error</title>
  </head>
  <body>"

  htmlText += "#{status}\n #{message}"

  htmlText += "
  </body>
  </html>"
  htmlText
  
end

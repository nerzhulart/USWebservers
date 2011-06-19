status = ARGV[0]
message = ARGV[1]

print "HTTP/1.1 #{status}/#{message}\r\nServer: Simple Http Server On Ruby\r\nContent-type: text/html\r\n\r\n"

htmlText = <<EOF
<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8" />
<title>Error</title>
</head>
<body>

EOF

htmlText += "#{status}\n #{message}"

htmlText += <<EOF

</body>
</html>
EOF

print "#{htmlText}"


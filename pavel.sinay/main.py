# Main file of the program.
# Opening server socket, accepting connections, waiting for user interrupt.


import socket
import http
import select
import sys
import log

port = 8080

serversocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
serversocket.bind((socket.gethostname(), port))
serversocket.listen(5)
serversocket.setblocking(0)

input = [serversocket,sys.stdin]
running = True
log.logger.info("Starting server")
while running:
    inputready,outputready,exceptready = select.select(input,[],[])

    for s in inputready:
        if s == serversocket:
            (clientsocket, address) = serversocket.accept()
            http.HTTPProcessor(clientsocket)
        else:
            cmd = sys.stdin.readline()
            if cmd== "exit\n":
                running = False
            else:
                print "enter 'exit' to stop the server"

serversocket.close()
log.logger.info("EXIT")


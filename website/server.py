import socketserver
import sys

from python import http
import requestParsing

class TCPHandler(socketserver.BaseRequestHandler):

    def handle(self):
        recieved_data = self.request.recv(1024)
        print(self.client_address[0] + " is sending data")
        print("----")
        print(recieved_data.decode())
        print("\n\n")
        sys.stdout.flush()

        header_end = "\r\n\r\n".encode() # convert end of of header mark to bytes

        data = []

        if recieved_data.find(header_end) != -1:
            data = recieved_data.split(header_end, 1) # use it to separate request
        else:
            data = [recieved_data, b'']

        # only decode header
        header = data[0].decode().split("\r\n")


        request_line = header[0].split(" ")
        if request_line[0] == "GET":
            if request_line[1] == '/':
                response = http.html_header("website/index.html")
                self.request.sendall(response)
            
            elif request_line[1].find(".html") != -1:
                fname = "website" + request_line[1]
                response = http.html_header(fname)
                self.request.sendall(response)

            elif request_line[1].find(".js") != -1:
                fname = "website" + request_line[1]
                response = http.js_header(fname)
                self.request.sendall(response)

            elif request_line[1].find(".css") != -1:
                fname = "website" + request_line[1]
                response = http.css_header(fname)
                self.request.sendall(response)
            
            elif request_line[1].find("/images/") != -1:
                fname = "website" + request_line[1]
                f_type = fname.split(".")[1]
                response = http.image_header(fname, f_type)
                self.request.sendall(response)
            
            else:
                response = http.not_found()
                self.request.sendall(response)
        else:
            postData = requestParsing.parseRequest(self, header, recieved_data)
            if postData != ():
                response = http.byteResponse(postData)
                self.request.sendall(response)
            



if __name__ == '__main__':
    host = "localhost"
    port = 8000

    server = socketserver.ThreadingTCPServer((host, port), TCPHandler)
    server.serve_forever()
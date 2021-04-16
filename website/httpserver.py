import http.server
import socketserver

PORT = 8000
HOST = "localhost"

def readFile(filename, type):
    fileContent = None
    file = open(filename, "r") if type == "str" else open(filename, "rb")
    fileContent = file.read()
    return fileContent

def pathLocation(path, self):
    if path == '/':
        response = readFile("website/index.html", "str")
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(response)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(response.encode())

    elif path.find(".html") != -1:
        response = readFile("website" + path, "str")
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(response)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(response.encode())

    elif path.find(".js") != -1:
        response = readFile("website" + path, "str")
        self.send_response(200)
        self.send_header("Content-Type", "text/javascript")
        self.send_header("Content-Length", str(len(response)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(response.encode())
        
    elif path.find(".css") != -1:
        response = readFile("website" + path, "str")
        self.send_response(200)
        self.send_header("Content-Type", "text/css")
        self.send_header("Content-Length", str(len(response)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(response.encode())
        
    elif path.find("/images/") != -1:
        response = readFile("website" + path, "bytes")
        imageType = path.split(".")[1]
        self.send_response(200)
        self.send_header("Content-Type", "image/" + imageType)
        self.send_header("Content-Length", str(len(response)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(response)

    else:
        self.send_response(404)
        self.end_headers()


class server(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        path = self.path
        response = pathLocation(path, self)
        return response


    def do_POST(self):
        path = self.path
        length = int(self.headers.get("Content-Length"))
        isMultipart = self.header.isMultipart()
        boundary = self.headers.get_boundary()
        body = self.rfile.read(length)


with socketserver.ThreadingTCPServer((HOST, PORT), server) as httpd:
    print("serving at port", PORT)
    httpd.serve_forever()

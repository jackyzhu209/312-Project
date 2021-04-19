import http.server
import socketserver
import cgi
import pymongo

PORT = 8000
HOST = "localhost"
mongoclient = pymongo.MongoClient("mongodb://localhost:27017/")
storedUsers = mongoclient["users"]
profiles = storedUsers["profiles"]

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

#if login query, checks credentials, if insert, checks if username exists and if not insert to DB
def entryQuery(qtype, entry):    
    if qtype == "login":
        if profiles.count_documents({"name": entry["name"], "pwd": entry["pwd"]}) != 0:
            return True
    elif qtype == "insert":
        if profiles.count_documents({"name": entry["name"]}) == 0:
            profiles.insert(json.dumps(entry))
            return True
    elif qtype == "online":
        onlineUsers = []
        account = profiles.find()
        for users in account:
            if json.loads(users[online]):
                onlineUsers.append(users)
        return onlineUsers
    return False
            

class server(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        path = self.path
        response = pathLocation(path, self)
        return response


    def do_POST(self):        
        path = self.path
        length = int(self.headers.get("Content-Length"))
        isMultipart = True if "multipart/form-data" in self.headers.get("Content-Type") else False
        if isMultipart:
            boundary = {'boundary': self.headers.get_boundary().encode()}
            data = cgi.parse_multipart(self.rfile, boundary)
            if path == "/enternewuser":
                name = data["enternewuser"]
                pwd = data["enternewpass"]
                entry = {"name": name, "pwd": pwd}
                inserted = entryQuery("insert", entry) #deal with front end warning depending on the boolean value, false means username already exists and cannot be duplicated
            elif path == "/loginuser":
                name = data["loginusername"]
                pwd = data["loginuserpass"]
                entry = {"name": name, "pwd": pwd, "online": True}
                exists = entryQuery("login", entry) #deal with front end warning depending on the boolean value, false means credentials dont exist or are wrong
            elif path == "/uploadproject":            
                image = data["enterprojectname"]
                pDesc = data["comment"]
                pName = data["uploadprojectimage"]
        


with socketserver.ThreadingTCPServer((HOST, PORT), server) as httpd:
    print("serving at port", PORT)
    httpd.serve_forever()

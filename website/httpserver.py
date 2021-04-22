import http.server
import socketserver
import cgi
import pymongo
import json

PORT = 8000
HOST = "0.0.0.0"
mongoclient = pymongo.MongoClient("mongo")
storedUsers = mongoclient["users"]
profiles = storedUsers["profiles"]
projects = storedUsers["projects"]

postFormat = '<div class="post"><hr>Project Name: Project1<b style="position:relative; left: 480px;">Rating: 7 <button style="background-color:green">&#x1F44D;</button><button style="background-color:red">&#x1F44E;</button></b><br><img src="../images/test.png" style="width:400px;height:200px;"><br>Description:<br>Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.<br><br><small>By: User1</small></div>'

def readFile(filename, type):
    filename = filename.replace("%20", " ")
    fileContent = None
    file = open(filename, "r") if type == "str" else open(filename, "rb")
    fileContent = file.read()
    return fileContent

def loadProjects():
    DBprojects = []
    for project in projects.find():
        DBprojects.append(project)
    return DBprojects

def replaceFormat(project):
    projectLine = postFormat.replace("Project Name: Project1", "Project Name: " + project["name"])
    projectLine = projectLine.replace("Description:<br>Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.", "Description:<br>" + project["desc"])
    projectLine = projectLine.replace('src="../images/test.png"', 'src="../images/projectImages/' + project["img"] + '"')
    return projectLine

def pathLocation(path, self):
    if path == '/':
        response = readFile("index.html", "str")
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(response)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(response.encode())

    elif path.find(".html") != -1: #make conditional statement for project.html, helper function to look thru all entries in projects database and populate placeholder with such entries
        response = readFile(path[1:], "str")
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("Content-Length", str(len(response)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        if path == "/html/projects.html":
            for projects in loadProjects():
                response = response.replace('<div class="projectlist">', '<div class="projectlist">' + replaceFormat(projects))
            self.wfile.write(response.encode())
        else:
            self.wfile.write(response.encode())

    elif path.find(".js") != -1:
        response = readFile(path[1:], "str")
        self.send_response(200)
        self.send_header("Content-Type", "text/javascript")
        self.send_header("Content-Length", str(len(response)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(response.encode())
        
    elif path.find(".css") != -1:
        response = readFile(path[1:], "str")
        self.send_response(200)
        self.send_header("Content-Type", "text/css")
        self.send_header("Content-Length", str(len(response)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(response.encode())
        
    elif path.find("/images/") != -1:
        response = readFile(path[1:], "bytes")
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

def sendRedirect(self, path):
    self.send_response(301)
    self.send_header("Location", path)
    self.end_headers()


#if login query, checks credentials, if insert, checks if username exists and if not insert to DB
def entryQuery(qtype, entry):    
    if qtype == "login":
        if profiles.count_documents({"name": entry["name"], "pwd": entry["pwd"]}) != 0:
            return True
    elif qtype == "insert":
        if profiles.count_documents({"name": entry["name"]}) == 0:
            profiles.insert_one(entry)
            return True
    elif qtype == "online":
        onlineUsers = []
        account = profiles.find()
        for users in account:
            if json.loads(users["online"]):
                onlineUsers.append(users)
        return onlineUsers
    elif qtype == "upload":
        projects.insert_one(entry)
        return True
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
            if path == "/enternewuser":
                data = cgi.parse_multipart(self.rfile, boundary)
                name = data["enternewuser"]
                pwd = data["enternewpass"]
                entry = {"name": name, "pwd": pwd}
                inserted = entryQuery("insert", entry) #deal with front end warning depending on the boolean value, false means username already exists and cannot be duplicated
                if inserted:
                    sendRedirect(self,"/html/login.html")
                else:
                    response = "Username Is Taken"
                    self.send_response(200)
                    self.send_header("Content-Type", "text/plain")
                    self.send_header("Content-Length", str(len(response)))
                    self.send_header("X-Content-Type-Options", "nosniff")
                    self.end_headers()
                    self.wfile.write(response)
            elif path == "/loginuser":
                data = cgi.parse_multipart(self.rfile, boundary)
                name = data["loginusername"]
                pwd = data["loginuserpass"]
                entry = {"name": name, "pwd": pwd, "online": True}
                exists = entryQuery("login", entry) #deal with front end warning depending on the boolean value, false means credentials dont exist or are wrong
                if exists:                    
                    sendRedirect(self, "/html/projects.html")
                else:
                    response = "Login Information Is Incorrect"
                    self.send_response(200)
                    self.send_header("Content-Type", "text/plain")
                    self.send_header("Content-Length", str(len(response)))
                    self.send_header("X-Content-Type-Options", "nosniff")
                    self.end_headers()
                    self.wfile.write(response)
            elif path == "/uploadproject": #parse manually for filename, add to database, redirect to project.html | associated filename with project index number, write file to directory (images/projectImages/filename)
                fileData = self.rfile.read(length)
                fileData = fileData.split(b'--' + self.headers.get_boundary().encode())
                nameSection = fileData[1].split(b'\r\n\r\n')[1].strip(b'\r\n').decode()
                descSection = fileData[2].split(b'\r\n\r\n')[1].strip(b'\r\n').decode()     
                imageSection = fileData[3].split(b'\r\n\r\n')
                imageName = imageSection[0].split(b'\r\n')[1].split(b'filename=')[1].strip(b'"').decode()
                imageData = imageSection[1]
                with open("images/projectImages/" + imageName, "wb") as imageFile:
                    imageFile.write(imageData)
                entry = {"name": nameSection, "desc": descSection, "img": imageName}
                entryQuery("upload", entry)
                sendRedirect(self, "/html/projects.html")

                
        


with socketserver.ThreadingTCPServer((HOST, PORT), server) as httpd:
    print("serving at port", PORT)
    httpd.serve_forever()

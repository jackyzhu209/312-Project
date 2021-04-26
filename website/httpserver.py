import http.server
import socketserver
import cgi
import pymongo
import json
import bcrypt
import secrets
from datetime import datetime, timedelta
import helperFunction as helper


PORT = 8000
HOST = "0.0.0.0"
mongoclient = pymongo.MongoClient("mongo")
storedUsers = mongoclient["users"]

user_accounts = storedUsers["user_accounts"]
projects = storedUsers["projects"]
online_users = storedUsers["online"]

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

def give_403():
    self.send_response(403)
    self.send_header("Content-Type", "text/plain")
    self.send_header("Content-Length", "20")
    self.end_headers()
    self.wfile.write(b"Error 403: Forbidden")
def give_404():
    self.send_response(404)
    self.send_header("Content-Type", "text/plain")
    self.send_header("Content-Length", "20")
    self.end_headers()
    self.wfile.write(b"Error 404: Not Found")




def postPathing(self, path, length, isMultipart, boundary):
    if isMultipart:
        boundary = {'boundary': self.headers.get_boundary().encode(), "CONTENT-LENGTH": length}            
        if path == "/enternewuser":
            data = cgi.parse_multipart(self.rfile, boundary)
            name = data["enternewuser"]
            pwd = data["enternewpass"]
            repwd = data["confirmnewpass"]
            entry = {"name": name, "pwd": pwd}
            # inserted = entryQuery("insert", entry) #deal with front end warning depending on the boolean value, false means username already exists and cannot be duplicated

            if pwd != rePwd:
                self.serve_htmltext_and_goto(None,'<h1>The passwords do not match. Please try again.</h1><br><h2>Returning in 5 seconds...</h2>', '/', 5)
                return            
            if name == pwd:
                self.serve_htmltext_and_goto(None,'<h1>You cant pick a password equal to your username. Please try again.</h1><br><h2>Returning in 5 seconds...</h2>', '/', 5)
                return
            if user_accounts.find_one({"account": name}) != None:
                name = name.replace('&','&amp').replace('<','&lt').replace('>','&gt')
                self.serve_htmltext_and_goto(None,'<h1>The account name ['+name+'] is already in use. Please try again.</h1><br><h2>Returning in 5 seconds...</h2>', '/', 5)
                return
            if len(pwd.decode()) < 8:
                self.serve_htmltext_and_goto(None,'<h1>The password did not meet the required length(>=8). Please try again.</h1><br><h2>Returning in 5 seconds...</h2>', '/', 5)
                return
            
            pass_salt = bcrypt.gensalt()
            hashed_pass = bcrypt.hashpw(new_pass, pass_salt)
            hashed_token =  bcrypt.hashpw(str(secrets.token_hex(16)).encode(), pass_salt)
            new_account = {
                    'account': name,                    
                    'pass'   : hashed_pass,
                    'token'  : hashed_token,
                    'bio'    : 'Empty bio'
                }
            user_accounts.insert_one(new_account)
            new_username = name.replace('&','&amp').replace('<','&lt').replace('>','&gt')
            self.serve_htmltext_and_goto(None,'<h1>Account created: '+new_username+'</h1><br><h2>Returning in 5 seconds...</h2>', '/', 5)


        elif path == "/loginuser":
            data = cgi.parse_multipart(self.rfile, boundary)
            name = data["loginusername"]
            pwd = data["loginuserpass"]
                        
            retrieved_account = user_accounts.find_one({"account": login_username})
            
            if retrieved_account == None:
                name = name.replace('&','&amp').replace('<','&lt').replace('>','&gt')
                self.serve_htmltext_and_goto(None,'<h1>Login failed: The account['+login_username+'] does not exist. Please try again.</h1><br><h2>Returning in 5 seconds...</h2>', '/', 5)
                return

            retrieved_pass = retrieved_account['pass']

            if not bcrypt.checkpw(pwd, retrieved_account):
                login_username = name.replace('&','&amp').replace('<','&lt').replace('>','&gt')
                login_pass = pwd.replace('&','&amp').replace('<','&lt').replace('>','&gt')
                self.serve_htmltext_and_goto(None,'<h1>Login failed: The password['+login_pass+'] is incorrect for the account['+login_username+']. Please try again.</h1><br><h2>Returning in 5 seconds...</h2>', '/', 5)
                return

            retrieved_token = retrieved_account['token']

            '''NOTE: Accounts stay logged in for up to 10 minutes of idle time, timer is reset upon any recieved request'''
            online_users.create_index("date", expireAfterSeconds=600)
            new_online_user = {
                                    'account':login_username,
                                    'date':datetime.utcnow()
                                }
            online_users.insert_one(new_online_user)
        
            login_username = name.replace(b'&',b'&amp').replace(b'<',b'&lt').replace(b'>',b'&gt')
            self.serve_htmltext_and_goto(retrieved_token,'<h1>You successfully logged in as: '+login_username+'</h1><br><h2>Returning in 5 seconds...</h2>', '/', 5)

        elif path == "/uploadproject": #parse manually for filename, add to database, redirect to project.html | associated filename with project index number, write file to directory (images/projectImages/filename)
            fileData = self.rfile.read(length)
            fileData = fileData.split(b'--' + self.headers.get_boundary().encode())
            
            project_name = fileData[1].split(b'\r\n\r\n')[1].strip(b'\r\n').decode()
            project_description = fileData[2].split(b'\r\n\r\n')[1].strip(b'\r\n').decode()
            
            imageSection = fileData[3].split(b'\r\n\r\n')
            image_path = imageSection[0].split(b'\r\n')[1].split(b'filename=')[1].strip(b'"').decode()
            image_path = "images/projectImages/" + image_path
            imageData = imageSection[1]

            #Make sure user submitted an image, give a 403 error otherwise
            '''NOTE: currently image uploads only work properly with jpegs'''
            if helper.get_mimetype(filename)[0:5] != b'image':
                self.give_403()
                return

            # store image data in "images/projectImages/"
            with open(image_path, "wb") as imageFile:
                imageFile.write(imageData)
            
            #Default username if project is submitted without being logged in, THOUGH this shouldnt ever occur
            username = "Anonymous"

            # get session token and check
            user_token = None
            cookie = self.headers.get("Cookie")
            if cookie != None:
                cookies = helper.parse_cookies(cookie)
                user_token = cookies.get("session-token", None)
            
            if user_token != None:
                retrieved_account = user_accounts.find_one({"token": user_token})
                if retrieved_account != None:
                    username = retrieved_account['account'].replace('&','&amp').replace('<','&lt').replace('>','&gt')
            
            #Create a dictionary for this post submission, formatted for the db
            project_post = {
                                "account":username,
                                "projectname":project_name,
                                "projectdescription":project_description,
                                "imagepath":image_path,
                                "rating":'0'
                            }
            # add post to db
            projects.insert_one(project_post)

            sendRedirect(self, "/html/projects.html")

        elif path == "/updatebio":
            data = cgi.parse_multipart(self.rfile, boundary)
            # get bio text
            newbio = data["biotext"]

            #Get all cookies into a list, extract the session token cookie if present
            '''NOTE: Currently there is only one cookie, the session token one'''
            user_token = None
            account_name = None
            cookie = self.headers.get("Cookie")
            if cookie != None:
                cookies = helper.parse_cookies(cookie)
                user_token = cookies.get("session-token", None)
            
            if user_token != None:
                retrieved_account = user_accounts.find_one({"token": user_token})
                if retrieved_account != None:
                    retrieved_account['bio'] = newbio
                    user_accounts.save(retrieved_account)
                else:
                    self.give_403()
            self.sendRedirect("html/profile.html")
        
        else:
            self.give_404



class server(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        path = self.path
        response = pathLocation(path, self)
        return response


    def do_POST(self):        
        path = self.path
        length = int(self.headers.get("Content-Length"))
        isMultipart = True if "multipart/form-data" in self.headers.get("Content-Type") else False
        

                
        


with socketserver.ThreadingTCPServer((HOST, PORT), server) as httpd:
    print("serving at port", PORT)
    httpd.serve_forever()

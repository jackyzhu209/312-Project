import http.server
import socketserver
import cgi
import pymongo
import json
import bcrypt
import secrets
import hashlib
import base64
from datetime import datetime, timedelta
import helperFunction as helper

SOCKET_GUID = b'258EAFA5-E914-47DA-95CA-C5AB0DC85B11'
TEXT_FRAME = 1
OPCODE_MASK = 0b00001111
PAYLOAD_LEN_MASK = 0b01111111
FIRST_BYTE_TEXT_FRAME = b'\x81'
SECOND_BYTE_LEN126 = b'\x7E'
SECOND_BYTE_LEN127 = b'\x7F'
FRAME_LEN_NO_METADATA = 1010


projects_list = []

PORT = 8000
HOST = "0.0.0.0"
localHost = "mongodb://localhost:27017"
mongoclient = pymongo.MongoClient(localHost)
storedUsers = mongoclient["users"]

user_accounts = storedUsers["user_accounts"]
projects = storedUsers["projects"]
online_users = storedUsers["online"]
#new_online_user = storedUsers["timeout"]

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
        projectHTML = helper.gen_project_post_html_asbytes(project["account"], project["projectname"], project["projectdescription"], project["imagepath"], project["rating"])
        DBprojects.append(projectHTML)
    return DBprojects

def replaceFormat(project):
    projectLine = postFormat.replace("Project Name: Project1", "Project Name: " + project["name"])
    projectLine = projectLine.replace("Description:<br>Lorem ipsum dolor sit amet, consectetur adipiscing elit, sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.", "Description:<br>" + project["desc"])
    projectLine = projectLine.replace('src="../images/test.png"', 'src="../images/projectImages/' + project["img"] + '"')
    return projectLine

def serve_htmltext_and_goto(self, token, text, link, time):
    if link != None:
        text += '<meta http-equiv="refresh" content="'+str(time)+'; url='+link+'" />'
    self.send_response(200)
    self.send_header("Content-Type", "text/html")
    self.send_header("X-Content-Type-Options", "nosniff")
    if token != None:
        self.send_header("Set-Cookie", "session-token=" + token + "; Max-Age=600")
    self.send_header("Content-Length", str(len(text)))
    self.end_headers()
    self.wfile.write(text.encode())


'''
Open a file at filepath(string) in bytes, get the mimetype and then serve it.
Return true if successful otherwise serve a 404 & return false.
Checks files for various html template placeholders, replaces them with data if encountered
Perform tasks specific to username(bytes) if it's not None
Return True on success, else False
'''
def serve_file(self, filepath, username)->bool:
    #queriedaccount example -> localhost:8000/html/profile.html?user=somename
    queriedaccount = None
    #session token is later retrieved and used to reset log out timer
    token = None
    if '?user=' in filepath:
        queriedaccount = filepath.split('?user=')[1]
        filepath = filepath.split('?user=')[0]
        
    #Open file, get content
    try:
        f = open(filepath, 'rb')
    except:
        give_404(self)
        return False
    b = f.read()
    #Get mimetype, serve 403 if filetype not in mimetypes dictionary
    mimetype = helper.get_mimetype(filepath)
    if mimetype == None:
        give_403(self)
        return False
    
    projectslist = b''
    for project in projects_list:
        projectslist += project     
    b = b.replace(b'{{projectslist}}',projectslist)
    
    #Get all usernames in database, make the the html for the frontend, insert if placeholder found
    alluserslist = b''
    for item in user_accounts.find():
        alluserslist += helper.gen_user_list_segment(item['account'].encode())
    b = b.replace(b'{{alluserslist}}', alluserslist)
    
    #Same as above but only for currently online users
    onlineuserslist = b''
    for item in online_users.find():
        onlineuserslist += helper.gen_user_list_segment(item['account'].encode())
    b = b.replace(b'{{onlineuserslist}}', onlineuserslist)

    #Show login status if username exists otherwise dont, and hide anything with the {{hideornot}} placeholder
    if username != None:
        b = b.replace(b'{{loggedin_temp}}', b'Currently logged in as: '+ username.encode())
        b = b.replace(b'{{username_placeholder}}', username.encode())
    else:
        b = b.replace(b'{{loggedin_temp}}', b'')
        b = b.replace(b'{{hideornot}}',b'hidden')
        '''NOTE: can currently comment this^ line out for testing purposes, but final version would have that line active'''
    
    #If an account profile was not queried and the user is not logged in, hide certain frontend data
    if queriedaccount == None and username == None:
        b = b.replace(b'{{userbio}}',b'')
        b = b.replace(b'{{hideifnotthisuser}}', b'hidden')

    #else if a profile wasnt queried but a user name is supposedly logged in, make sure that account exists
    #and refresh their session cookie and online status if so
    elif queriedaccount == None and username != None:
        #get queried account's bio and replace placeholder with it
        retrieved_account = user_accounts.find_one({"account": username})
        if retrieved_account == None:
            self.serve_htmltext_and_goto(self, None,'<h1>That username does not exist. Please try again.</h1><br><h2>Returning in 5 seconds...</h2>', '/html/users.html', 5)
            return
        userbio = helper.gen_user_bio_html(username,retrieved_account['bio'])
        b = b.replace(b'{{userbio}}',userbio)
        #account login status refresh
        token = helper.parse_cookies(self.headers.get("Cookie")).get("session-token", None)
        account_to_refresh = online_users.find_one({"account": username})
        account_to_refresh['date'] = datetime.utcnow()
        online_users.save(account_to_refresh)

    #if an account is queried(and exists), show their profile page and hide the bio updater form   
    elif queriedaccount != None:
        retrieved_account = user_accounts.find_one({"account": queriedaccount.encode()})
        if retrieved_account == None:
            self.serve_htmltext_and_goto(self, None,'<h1>That username does not exist. Please try again.</h1><br><h2>Returning in 5 seconds...</h2>', '/html/users.html', 5)
            return
        userbio = helper.gen_user_bio_html(queriedaccount.encode(),retrieved_account['bio'])
        b = b.replace(b'{{userbio}}',userbio)
        b = b.replace(b'{{hideifnotthisuser}}', b'hidden')
    
    
    #Create appropriate response
    self.send_response(200)
    self.send_header('Content-Type', mimetype)
    self.send_header('X-Content-Type-Options', 'nosniff')    
    #reset session cookie to another 10 minutes
    if username != None and token != None:
        self.send_header('Set-Cookie', 'session-token=' + token + '; Max-Age=600')
        
    self.send_header('Content-Length', str(len(b)))
    self.end_headers()
    self.wfile.write(b)
    
    #Close file and send response
    f.close()
    return True


# looks at token and gets username
def get_username(self):
    username = None

    # get session token and check username
    user_token = None
    cookie = self.headers.get("Cookie")
    if cookie != None:
        cookies = helper.parse_cookies(cookie)
        user_token = cookies.get("session-token", None)

    if user_token != None:
        retrieved_account = user_accounts.find_one({"token": hashlib.sha256(user_token.encode()).hexdigest()})
        if retrieved_account != None:
            username = retrieved_account['account'].replace('&','&amp').replace('<','&lt').replace('>','&gt')
    
    #loop through all instances and do bcrypt.checkpw on the retrieved token and the 

    return username

def handleSocket(self):
    socket_key = self.headers.get("Sec-WebSocket-Key").encode() + SOCKET_GUID
    base64_socket_key = base64.b64encode(hashlib.sha1(socket_key).digest())
    
    response = b'HTTP/1.1 101 Switching Protocols\r\n'
    response += b'Connection: Upgrade\r\n'
    response += b'Upgrade: websocket\r\n'
    response += b'Sec-WebSocket-Accept: ' + base64_socket_key + b'\r\n\r\n'
    self.request.sendall(response)

    # keep track of sockets
    self.active_sockets.append(self.request)
    account_name = get_username(self)
    if account_name != None:
        self.dm_sockets[account_name] = self.request

    socket_data = b' '
    while socket_data:
        #Try receiving data, break loop on any exception
        try:
            socket_data = self.request.recv(1024)
        except:
            break
        
        #Get the opcode
        opcode = None
        if socket_data:
            opcode = socket_data[0] & OPCODE_MASK
        
        #if its a text frame(do nothing otherwise)
        if opcode == TEXT_FRAME and account_name != None:
            msg_type = None
            #get payload length
            payload_len = socket_data[1] & PAYLOAD_LEN_MASK
            
            #Self explanatory: get data from the packets as defined for the three payload sizes
            if payload_len < 126:
                masking_key = socket_data[2:6]
                payload_data = socket_data[6:(6 + payload_len)]
                
            elif payload_len == 126:
                payload_len = int.from_bytes(socket_data[2:4], byteorder='big', signed=False)
                masking_key = socket_data[4:8]
                if (FRAME_LEN_NO_METADATA - payload_len) < 0:
                    socket_data += self.request.recv(65536)
                payload_data = socket_data[8:(8 + payload_len)]
                
            elif payload_len == 127:
                payload_len = int.from_bytes(socket_data[2:10], byteorder='big', signed=False)
                masking_key = socket_data[10:14]
                socket_data += self.request.recv(payload_len)
                payload_data = socket_data[14:(14 + payload_len)]
            
            #Decode payload with the masking key
            decoded_payload = b''
            for idx, byte in enumerate(payload_data):
                decoded_payload += (byte ^ masking_key[idx % 4]).to_bytes(1, byteorder='big', signed=False)
                
            #Remove html from payload
            decoded_payload = decoded_payload.replace(b'&',b'&amp').replace(b'<',b'&lt').replace(b'>',b'&gt')
            
            #Start the outgoing payload
            outgoing_payload = None
            #if websocket was used to rate project
            if b'"projectname"' in decoded_payload:
                msg_type = "rating"

                #Extract project name and the value to be added to the rating (1 or -1)
                project_name = helper.extract_segment(decoded_payload, b'"projectname":"',b'","addedvalue"')
                added_value = int(helper.extract_segment(decoded_payload, b'"addedvalue":',b'}').decode())
                
                #Get the project by name and update it with a +1 or -1
                project_to_rate = projects.find_one({"projectname": project_name.decode()}) #change this
                project_to_rate['rating'] = new_rating = str(int(project_to_rate['rating']) + added_value)
                projects.save(project_to_rate)
                
                #Refresh the projects_list list
                projects_list.clear()
                for item in projects.find():
                    formatted_project_post_html = helper.gen_project_post_html_asbytes(item['account'], item['projectname'], item['projectdescription'], item['imagepath'], item['rating'])
                    projects_list.append(formatted_project_post_html)
                
                #Set up outgoing payload for project rating
                outgoing_payload = b'{"projectname":"'+project_name+b'","updatedvalue":'+new_rating.encode()+b'}'
            
            #else if websocket was used to send message
            elif b'"chatmessage"' in decoded_payload:
                msg_type = "dm"
                #Extract the various data
                msg_sender = None
                sender_token = helper.extract_segment(decoded_payload, b'"sender":"',b'","recipient"')
                msg_recipient = helper.extract_segment(decoded_payload, b'"recipient":"',b'","chatmessage"')
                chat_message = helper.extract_segment(decoded_payload, b'"chatmessage":"',b'"}')
                
                #Fine the account this message was sent from based on the token given
                #if no account was found give them the name "Anonymous" THOUGH this shouldnt ever occur
                msg_sender = b'Anonymous'
                retrieved_account = user_accounts.find_one({"token": hashlib.sha256(sender_token).hexdigest()})
                if retrieved_account != None:
                    msg_sender = retrieved_account['account'].encode()
                
                #set up outgoing payload for a message
                outgoing_payload = b'{"sender":"'+msg_sender+b'","recipient":"'+msg_recipient+b'","chatmessage":"'+chat_message+b'"}'
            
            #Set up outgoing frame as required for different sized payloads
            payload_len = len(outgoing_payload)
            outgoing_frame = FIRST_BYTE_TEXT_FRAME
            if payload_len < 126:
                outgoing_frame += payload_len.to_bytes(1, byteorder='big', signed=False)
                
            elif payload_len >= 65536:
                outgoing_frame += SECOND_BYTE_LEN127
                outgoing_frame += payload_len.to_bytes(8, byteorder='big', signed=False)
                
            elif payload_len >= 126:
                outgoing_frame += SECOND_BYTE_LEN126
                outgoing_frame += payload_len.to_bytes(2, byteorder='big', signed=False)
            outgoing_frame += outgoing_payload
            
            if msg_type == "rating":
                #Send outgoing frame to all connected sockets(includes itself)
                for socket in self.active_sockets:
                    socket.sendall(outgoing_frame)
            elif msg_type == "dm":
                #Send dms only to the sockets for the two members, and only bother if they're online
                if msg_sender.decode() in self.dm_sockets:
                    self.dm_sockets[msg_sender.decode()].sendall(outgoing_frame)
                if msg_recipient.decode() in self.dm_sockets and msg_sender != msg_recipient:
                    self.dm_sockets[msg_recipient.decode()].sendall(outgoing_frame)
                            
    #remove this socket on socket close           
    self.active_sockets.remove(self.request)        
    self.dm_sockets.pop(account_name, None)


def pathLocation(path, self):    
    path = path.replace("%20", " ")
    if path == '/':
        username = get_username(self)
        serve_file(self, './index.html', username)

    elif path.find(".html") != -1: #make conditional statement for project.html, helper function to look thru all entries in projects database and populate placeholder with such entries
        username = get_username(self)
        serve_file(self, './' + path[1:], username)

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
        if path[1:5] == "html":
            response = readFile(path[6:], "bytes")
        else:
            response = readFile(path[1:], "bytes")
        imageType = path.split(".")[1]
        self.send_response(200)
        self.send_header("Content-Type", "image/" + imageType)
        self.send_header("Content-Length", str(len(response)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(response)
    elif path == "/logout":
        if get_username(self) != None:
            online_users.delete_many({"account" : get_username(self)})
        helper.logout(self, helper.parse_cookies(self.headers.get("Cookie")).get("session-token", None),'<h1>You have logged out.</h1><br><h2>Returning in 3 seconds...</h2>', '/', 3)
    elif path == "/websocket":
        handleSocket(self)
    else:
        self.send_response(404)
        self.end_headers()

def sendRedirect(self, path):
    self.send_response(301)
    self.send_header("Location", path)
    self.end_headers()

def give_403(self):
    self.send_response(403)
    self.send_header("Content-Type", "text/plain")
    self.send_header("Content-Length", "20")
    self.end_headers()
    self.wfile.write(b"Error 403: Forbidden")
def give_404(self):
    self.send_response(404)
    self.send_header("Content-Type", "text/plain")
    self.send_header("Content-Length", "20")
    self.end_headers()
    self.wfile.write(b"Error 404: Not Found")




def postPathing(self, path, length, isMultipart):
    if isMultipart:
        boundary = {'boundary': self.headers.get_boundary().encode(), "CONTENT-LENGTH": length}            
        if path == "/enternewuser":
            data = cgi.parse_multipart(self.rfile, boundary)
            name = data["enternewuser"][0]
            pwd = data["enternewpass"][0]
            rePwd = data["confirmnewpass"][0]
            entry = {"name": name, "pwd": pwd}
            # inserted = entryQuery("insert", entry) #deal with front end warning depending on the boolean value, false means username already exists and cannot be duplicated

            if pwd != rePwd:
                serve_htmltext_and_goto(self,None,'<h1>The passwords do not match. Please try again.</h1><br><h2>Returning in 5 seconds...</h2>', '/', 5)
                return            
            if name == pwd:
                serve_htmltext_and_goto(self, None,'<h1>You cant pick a password equal to your username. Please try again.</h1><br><h2>Returning in 5 seconds...</h2>', '/', 5)
                return
            if user_accounts.find_one({"account": name}) != None:
                name = name.replace('&','&amp').replace('<','&lt').replace('>','&gt')
                serve_htmltext_and_goto(self, None,'<h1>The account name ['+name+'] is already in use. Please try again.</h1><br><h2>Returning in 5 seconds...</h2>', '/', 5)
                return
            if len(pwd) < 8:
                serve_htmltext_and_goto(self, None,'<h1>The password did not meet the required length(>=8). Please try again.</h1><br><h2>Returning in 5 seconds...</h2>', '/', 5)
                return
            
            pass_salt = bcrypt.gensalt()
            hashed_pass = bcrypt.hashpw(pwd.encode(), pass_salt)            
            new_account = {
                    'account': name,                    
                    'pass'   : hashed_pass,
                    'token'  : bcrypt.hashpw(secrets.token_urlsafe(16).encode(), pass_salt),
                    'bio'    : 'Empty bio'
                }
            user_accounts.insert_one(new_account)
            new_username = name.replace('&','&amp').replace('<','&lt').replace('>','&gt')
            serve_htmltext_and_goto(self, None,'<h1>Account created: '+new_username+'</h1><br><h2>Returning in 5 seconds...</h2>', '/', 5)

        elif path == "/loginuser":
            data = cgi.parse_multipart(self.rfile, boundary)
            name = data["loginusername"][0]
            pwd = data["loginuserpass"][0]
                        
            retrieved_account = user_accounts.find_one({"account": name})
            
            if retrieved_account == None:
                name = name.replace('&','&amp').replace('<','&lt').replace('>','&gt')
                serve_htmltext_and_goto(self, None,'<h1>Login failed: The account['+name+'] does not exist. Please try again.</h1><br><h2>Returning in 5 seconds...</h2>', '/', 5)
                return

            retrieved_pass = retrieved_account['pass']

            if not bcrypt.checkpw(pwd.encode(), retrieved_pass):
                login_username = name.replace('&','&amp').replace('<','&lt').replace('>','&gt')
                login_pass = pwd.replace('&','&amp').replace('<','&lt').replace('>','&gt')
                serve_htmltext_and_goto(self, None,'<h1>Login failed: The password['+pwd+'] is incorrect for the account['+pwd+']. Please try again.</h1><br><h2>Returning in 5 seconds...</h2>', '/', 5)
                return

            token = secrets.token_urlsafe(16)
            tokenHashed = hashlib.sha256(token.encode()).hexdigest()
            user_accounts.update({'account' : name}, {"$set": {'token': tokenHashed}})

            '''NOTE: Accounts stay logged in for up to 10 minutes of idle time, timer is reset upon any recieved request'''
            online_users.create_index("date", expireAfterSeconds=600)
            new_online_user = {
                                    'account':name,
                                    'date':datetime.utcnow()
                                }
            online_users.insert_one(new_online_user)
        
            login_username = name.replace('&','&amp').replace('<','&lt').replace('>','&gt')
            serve_htmltext_and_goto(self, token,'<h1>You successfully logged in as: '+name+'</h1><br><h2>Returning in 5 seconds...</h2>', '/', 5)

        elif path == "/uploadproject": #parse manually for filename, add to database, redirect to project.html | associated filename with project index number, write file to directory (images/projectImages/filename)
            fileData = self.rfile.read(length)
            fileData = fileData.split(b'--' + self.headers.get_boundary().encode())
            
            project_name = fileData[1].split(b'\r\n\r\n')[1].strip(b'\r\n').decode()
            project_name = project_name.replace('&','&amp').replace('<','&lt').replace('>','&gt')
            project_description = fileData[2].split(b'\r\n\r\n')[1].strip(b'\r\n').decode()
            project_description = project_description.replace('&','&amp').replace('<','&lt').replace('>','&gt')
            
            imageSection = fileData[3].split(b'\r\n\r\n')
            image_path = imageSection[0].split(b'\r\n')[1].split(b'filename=')[1].strip(b'"').decode()
            image_path = "images/projectImages/" + image_path
            imageData = imageSection[1]

            #Make sure user submitted an image, give a 403 error otherwise
            '''NOTE: currently image uploads only work properly with jpegs'''
            if helper.get_mimetype(image_path)[0:5] != 'image':
                give_403(self)
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
                retrieved_account = user_accounts.find_one({"token": hashlib.sha256(user_token.encode()).hexdigest()})
                if retrieved_account != None:
                    username = retrieved_account['account'].replace('&','&amp').replace('<','&lt').replace('>','&gt')
            
            #Create a dictionary for this post submission, formatted for the db
            project_post = {
                                "account":username,
                                "projectname":project_name,
                                "projectdescription":project_description,
                                "imagepath":"../" + image_path,
                                "rating":'0'
                            }
            # add post to db
            projects.insert_one(project_post)

            formatted_project_post_html = helper.gen_project_post_html_asbytes(username, project_name, project_description, image_path, '0')
                
            #Add this html to the projects_list list
            projects_list.append(formatted_project_post_html)

            sendRedirect(self, "/html/projects.html")

        elif path == "/updatebio":
            data = cgi.parse_multipart(self.rfile, boundary)
            # get bio text
            newbio = data["biotext"][0]

            #Get all cookies into a list, extract the session token cookie if present
            '''NOTE: Currently there is only one cookie, the session token one'''
            user_token = None
            account_name = None
            cookie = self.headers.get("Cookie")
            if cookie != None:
                cookies = helper.parse_cookies(cookie)
                user_token = cookies.get("session-token", None)
            
            if user_token != None:
                retrieved_account = user_accounts.find_one({"token": hashlib.sha256(user_token.encode()).hexdigest()})
                if retrieved_account != None:
                    retrieved_account['bio'] = newbio
                    user_accounts.save(retrieved_account)
                else:
                    give_403(self)
            sendRedirect(self, "html/profile.html")
        
        else:
            give_404(self)



class server(http.server.SimpleHTTPRequestHandler):
    active_sockets = []
    dm_sockets = {}
    def do_GET(self):
        path = self.path
        response = pathLocation(path, self)
        return response


    def do_POST(self):        
        path = self.path
        length = int(self.headers.get("Content-Length"))
        isMultipart = True if "multipart/form-data" in self.headers.get("Content-Type") else False
        postPathing(self, path, length, isMultipart)
        

                
        


with socketserver.ThreadingTCPServer((HOST, PORT), server) as httpd:
    print("serving at port", PORT)
    httpd.serve_forever()

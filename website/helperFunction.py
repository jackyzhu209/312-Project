#Simple mapping of file extensions to html content types(as bytes)
mimetypes = {
    'txt'  : 'text/plain; charset=utf-8',
    'text' : 'text/plain',
    'html' : 'text/html',
    'js'   : 'text/javascript',
    'css'  : 'text/css',
    'png'  : 'image/png',
    'jpg'  : 'image/jpeg',
    'jpeg' : 'image/jpeg',
}

#Use the mimetypes dictionary to match file extensions to some known types, else return None
#If the extension doesnt exist as a key in our dictionary, then we likely never want to serve that file anyways(example:server.py)
def get_mimetype(filepath)->bytes:
    chunks = filepath.split('.')
    if chunks[-1] in mimetypes:
        return mimetypes[chunks[-1]]
    else:
        return None


# used to turn cookies into a dictionary
def parse_cookies(cookie):
    cookies = {}
    cookie_list = cookie.split("; ")

    # keys and values are split on 
    for c in cookie_list:
        kv_pair = c.split("=")
        cookies.update({kv_pair[0]: kv_pair[1]})
    return cookies


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
        self.give_404()
        return False
    b = f.read()
    #Get mimetype, serve 403 if filetype not in mimetypes dictionary
    mimetype = helper.get_mimetype(filepath)
    if mimetype == None:
        self.give_403()
        return False
    
    #Show login status if username exists otherwise dont, and hide anything with the {{hideornot}} placeholder
    if username != None:
        b = b.replace(b'{{loggedin_temp}}', b'Currently logged in as: '+username)
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
        retrieved_account = db.user_accounts.find_one({"account": username})
        if retrieved_account == None:
            self.serve_htmltext_and_goto(None,'<h1>That username does not exist. Please try again.</h1><br><h2>Returning in 5 seconds...</h2>', '/html/users.html', 5)
            return
        userbio = helper.gen_user_bio_html(username,retrieved_account['bio'])
        b = b.replace(b'{{userbio}}',userbio)
        #account login status refresh
        token = retrieved_account['token']
        account_to_refresh = db.online_users.find_one({"account": username})
        account_to_refresh['date'] = datetime.utcnow()
        db.online_users.save(account_to_refresh)
    #if an account is queried(and exists), show their profile page and hide the bio updater form   
    elif queriedaccount != None:
        retrieved_account = db.user_accounts.find_one({"account": queriedaccount.encode()})
        if retrieved_account == None:
            self.serve_htmltext_and_goto(None,'<h1>That username does not exist. Please try again.</h1><br><h2>Returning in 5 seconds...</h2>', '/html/users.html', 5)
            return
        userbio = helper.gen_user_bio_html(queriedaccount.encode(),retrieved_account['bio'])
        b = b.replace(b'{{userbio}}',userbio)
        b = b.replace(b'{{hideifnotthisuser}}', b'hidden')
    
    #Get all html for submitted projects, insert if placeholder found
    projectslist = b''
    for project in projects_list:
        projectslist += project     
    b = b.replace(b'{{projectslist}}',projectslist)
    
    #Get all usernames in database, make the the html for the frontend, insert if placeholder found
    alluserslist = b''
    for item in db.user_accounts.find():
        alluserslist += helper.gen_user_list_segment(item['account'])
    b = b.replace(b'{{alluserslist}}', alluserslist)
    
    #Same as above but only for currently online users
    onlineuserslist = b''
    for item in db.online_users.find():
        onlineuserslist += helper.gen_user_list_segment(item['account'])
    b = b.replace(b'{{onlineuserslist}}', onlineuserslist)
    
    #Create appropriate response
    self.response = b'HTTP/1.1 200 OK\r\n'
    self.response += b'Content-Type: '+mimetype+b'\r\n'
    self.response += b'X-Content-Type-Options: nosniff\r\n'
    #reset session cookie to another 10 minutes
    if username != None and token != None:
        self.response += b'Set-Cookie: session-token=' + token + b'; Max-Age=600\r\n'
        
    self.response += b'Content-Length: ' + str(len(b)).encode() + b'\r\n\r\n'
    self.response += b
    
    #Close file and send response
    f.close()
    self.request.sendall(self.response)
    return True

#generates the project post html given the parameters
def gen_project_post_html_asbytes(user_name, project_name, project_description, image_path, rating)->bytes:
    html = b'<div class="post"><hr>Project Name: '
    html += project_name.encode() + b'<b style="position:relative; left: 480px;"><div id="'+project_name.encode()+b'">Rating: '+rating.encode()+b'</div> <button onclick="rateProject(1,'
    html += b'\''+project_name.encode()+b'\')" style="background-color:green">&#x1F44D;</button><button onclick="rateProject(-1,'
    html += b'\''+project_name.encode()+b'\')" style="background-color:red">&#x1F44E;</button></b><br>'
    html += b'<img src="'+image_path.encode()+b'" style="width:400px;height:200px;"><br>'
    html += b'Description:<br>'+project_description.encode()
    html += b'<br><br><small>By: '+user_name.encode()+b'</small></div>'
    return html

#Used to generate html bytes for the frontend users lists nodes, also allows clicking user name to see their profile
def gen_user_list_segment(username)->bytes:
    html = b'<li><a href="./profile.html?user='+username+b'">'+username+b'</a><button id="'+username+b'" class="messagebutton" onclick="openChat(this.id)">Message</button></li>'
    return html

#Gen html as bytes for user bio
def gen_user_bio_html(username, text)->bytes:
    html = b'<p>'+username.encode()+b's bio:<br>'+text.encode()+b'</p>'
    return html

def extract_segment(bytestream, left_delim, right_delim)->bytes:
    return bytestream.split(left_delim,1)[1].split(right_delim,1)[0]
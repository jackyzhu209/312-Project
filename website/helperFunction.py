from datetime import datetime, timedelta
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

def logout(self, token, text, link, time):
        if link != None:
            text += '<meta http-equiv="refresh" content="'+str(time)+'; url='+link+'" />'
        self.send_response(200)
        self.send_header("Content-Type", "text/html")
        self.send_header("X-Content-Type-Options", "nosniff")
        if token != None:
            self.send_header("Set-Cookie", "session-token=deleted; path=/; expires=" + str(datetime.utcnow()) + "Max-Age=-1")
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
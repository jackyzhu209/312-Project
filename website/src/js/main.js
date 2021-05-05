// Establish a WebSocket connection with the server
const socket = new WebSocket('ws://' + window.location.host + '/websocket');

// Call evaluateData on data received
socket.onmessage = evaluateData;

//Send a message from the current user to the @'d used
//used token cookie as sender name, deciphered to a username in the backend
function sendMessage() {
   const chatTarget = document.getElementById("chatTarget").innerHTML.replace("<h1>","").replace("</h1>","").replace("Chat@","");
   const chatBox = document.getElementById("chat-comment");
   const chatSender = getCurrentSessionToken()
   const comment = chatBox.value;
   this_user = document.getElementById("current_user").innerHTML;
   chatBox.value = "";
   chatBox.focus();
   if(comment !== "") {
      socket.send(JSON.stringify({'sender':chatSender,'recipient':chatTarget,'chatmessage':comment}));
   }
}

//Rate a project up one or down one point, useless unless logged in
function rateProject(value, projectname) {
	socket.send(JSON.stringify({'projectname': projectname, 'addedvalue': value}));
}

//Called whenever a message is sent, received or when a project is rated.
//The data within the socket json is used to id what the socket was used for
function evaluateData(message) {
   const socketData = JSON.parse(message.data);
   let chat = document.getElementById('chat');

   //If it was used to rate a project
   if(socketData['projectname'] != null){
      projectname = socketData['projectname'];
      if(projectname.includes("&lt;/")){
         //this is done to account for some weird error that happens when someone used html in their project name
         projectname = projectname.replaceAll("&lt;","<").replaceAll("&gt;",">").replaceAll("&amp;","&");
      }
	   editted_rating = document.getElementById(projectname);
	   editted_rating.innerHTML =  "Rating: " + socketData['updatedvalue']
   }
   //if a message was sent/received
   //Creates a div containing the message. Clicking the message allows you to @ that user(only @'d users see your message)
   else if(socketData['chatmessage'] != null){
   		//Sent
	   	this_user = document.getElementById("current_user").innerHTML;
	   	if(this_user == socketData['sender']){
	   		chat.innerHTML += "<div onclick=\"openChat(\'"+socketData['recipient']+"\')\">"+"@" + socketData['recipient'] + ": " + socketData['chatmessage'] + '<br></div>';
   			openChat(socketData['recipient']);
   		}
   		//received
   		else if(this_user == socketData['recipient']){
   			chat.innerHTML += "<div onclick=\"openChat(\'"+socketData['sender']+"\')\">"+ socketData['sender'] + ": " + socketData['chatmessage'] + '<br></div>';
   			openChat(socketData['sender']);	
   		}
   }

}

//Straight forward functions to open/close the chat box(technically hiding/showing it) and one to get
//the session token cookie
function openChat(user_id) { 
	document.getElementById("dmBox").style.display = "block";
	document.getElementById("chatTarget").innerHTML = "<h1>Chat@"+user_id+"</h1>";
}

function closeChat() {
	document.getElementById("dmBox").style.display = "none";
}

function getCurrentSessionToken() {
	return document.cookie.split("session-token=")[1].split(";")[0]
}

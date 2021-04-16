function openChat(user_id) {
	document.getElementById("dmBox").style.display = "block";
	document.getElementById("chatTarget").innerHTML = "<h1>Chat@"+user_id+"</h1>";
}

function closeChat() {
	document.getElementById("dmBox").style.display = "none";
}
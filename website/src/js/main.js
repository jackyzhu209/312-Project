function openChat(user_id) {
	document.getElementById("dmBox").style.display = "block";
	document.getElementById("chatTarget").innerHTML = "<h1>Chat@"+user_id+"</h1>";
}

function closeChat() {
	document.getElementById("dmBox").style.display = "none";
}

function incrementVote() {
	document.getElementById("increment").click();
	var count = parseInt($(".count", this).text());

	if(this.hasClass("up")) {
		var count = count + 1;
		
		(".count", this).text(count);     
	} else {
		var count = count - 1;
		(".count", this).text(count);     
	}
}

function decrementVote() {
	document.getElementById("increment").click();
	var count = parseInt($("~ .count", this).text());

	if(this.hasClass("up")) {
		var count = count + 1;
		
		(".count", this).text(count);     
	} else {
		var count = count - 1;
		(".count", this).text(count);     
	}
}

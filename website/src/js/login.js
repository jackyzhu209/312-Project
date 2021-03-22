// Get the modal
var modal_forgotPass = document.getElementById("modal_forgotPass");
var modal_createAccount = document.getElementById("modal_createAccount");

// Get the button that opens the modal
var link_forgotPass = document.getElementById("forgotPass");
var link_createAccount = document.getElementById("createAccount");

// Get the <span> element that closes the modal
var span_forgotPass = document.getElementsByClassName("close")[0];
var span_createAccount = document.getElementsByClassName("close")[1];

// When the user clicks on the button, open the modal
link_forgotPass.onclick = function() {
  modal_forgotPass.style.display = "block";
}
link_createAccount.onclick = function() {
  modal_createAccount.style.display = "block";
}

// When the user clicks on <span> (x), close the modal
span_forgotPass.onclick = function() {
  modal_forgotPass.style.display = "none";
}
span_createAccount.onclick = function() {
  modal_createAccount.style.display = "none";
}

// When the user clicks anywhere outside of the modal, close it
window.onclick = function(event) {
  if (event.target == modal_forgotPass) {
    modal_forgotPass.style.display = "none";
  }
  if (event.target == modal_createAccount) {
    modal_createAccount.style.display = "none";
  }
}

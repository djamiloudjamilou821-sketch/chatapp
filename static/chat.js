var socket = io();

/* =========================
   ONLINE USER SYSTEM
========================= */
socket.emit("user_online", {
    username: CURRENT_USER
});

socket.on("update_users", function(users) {
    document.getElementById("online").innerHTML =
        "🟢 Online: " + users.join(", ");
});


/* =========================
   SEND MESSAGE
========================= */
function sendMessage() {
    let msg = document.getElementById("message").value;

    if (msg.trim() === "") return;

    socket.emit("send_message", {
        sender: CURRENT_USER,
        receiver: CHAT_USER,
        message: msg
    });

    document.getElementById("message").value = "";
}


/* =========================
   RECEIVE MESSAGE
========================= */
socket.on("receive_message", function(data) {
    let chat = document.getElementById("chat");

    let div = document.createElement("div");

    if (data.sender === CURRENT_USER) {
        div.className = "msg me";
    } else {
        div.className = "msg other";
    }

    div.innerHTML = data.message;

    chat.appendChild(div);

    chat.scrollTop = chat.scrollHeight;
});


/* =========================
   TYPING SYSTEM
========================= */
let typingTimeout;

document.addEventListener("DOMContentLoaded", function() {

    let input = document.getElementById("message");

    input.addEventListener("input", function() {

        socket.emit("typing", {
            sender: CURRENT_USER,
            receiver: CHAT_USER
        });

        clearTimeout(typingTimeout);

        typingTimeout = setTimeout(() => {
            socket.emit("stop_typing", {
                sender: CURRENT_USER,
                receiver: CHAT_USER
            });
        }, 1000);
    });

});


socket.on("typing", function(data) {
    document.getElementById("typing").innerHTML =
        "✍ " + data.sender + " is typing...";
});

socket.on("stop_typing", function() {
    document.getElementById("typing").innerHTML = "";
});


/* =========================
   SEEN SYSTEM (BASIC)
========================= */
socket.emit("seen", {
    user: CURRENT_USER,
    chat_with: CHAT_USER
});

let startX;

document.addEventListener("touchstart", e => {
    startX = e.touches[0].clientX;
});

document.addEventListener("touchend", e => {
    let endX = e.changedTouches[0].clientX;

    if (startX - endX > 80) {
        console.log("swipe left");
    }
});
from typing import Annotated

from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from starlette.responses import HTMLResponse

from .settings import settings

from .api import router as api_router
from .exceptions import add_custom_exception_handlers
from ..backend import Backend, get_backend

app = FastAPI()
app.include_router(api_router)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
add_custom_exception_handlers(app)

@app.get('/auth', response_class=HTMLResponse)
async def auth():
    return f"""
    <html>
    <head><title>Login</title></head>
    <body>
        <h2>Login</h2>
        <form id="loginForm">
            <input type="email" id="email" placeholder="Email" required><br>
            <input type="password" id="password" placeholder="Password" required><br>
            <button type="submit">Login</button>
        </form>
        <script>
            document.getElementById("loginForm").onsubmit = async function(event) {{
                event.preventDefault();
                const formData = new FormData();
                formData.append("username", document.getElementById("email").value);
                formData.append("password", document.getElementById("password").value);
                const response = await fetch("{settings.MAIN_URL_HTTP}/api/v1/login", {{
                    method: "POST",
                    body: formData,
                    credentials: "include"  // Allows cookies to be set
                }}).then(async response => {{
                    if (response.ok) {{
                        let responseJson = await response.json();
                        localStorage.setItem('user_id', responseJson.id)
                        localStorage.setItem('user_name', responseJson.name)
                        window.location.href = "{settings.MAIN_URL_HTTP}/";
                    }} else {{
                        alert("Login failed");
                    }}
                }});
            }};
        </script>
    </body>
    </html>
    """

@app.get('/', response_class=HTMLResponse)
async def main():
    return f"""
    <!DOCTYPE html>
    <html>
        <head>
            <title>Chat</title>
            <style>
                #messages {{
                    max-height: 300px; /* Set a maximum height */
                    overflow-y: scroll; /* Enable vertical scrolling */
                    padding-right: 10px; /* Adjust padding to avoid overlap with scrollbar */
                    border: 1px solid #ccc; /* Thin light gray border around the messages window */
                    border-radius: 4px; /* Optional: rounded corners for the border */
                }}

                #messages::-webkit-scrollbar {{
                    width: 8px; /* Set width of the scrollbar */
                }}

                #messages::-webkit-scrollbar-track {{
                    background: #f1f1f1; /* Color of the track */
                }}

                #messages::-webkit-scrollbar-thumb {{
                    background: #888; /* Color of the scrollbar thumb */
                    border-radius: 4px; /* Rounded corners for the thumb */
                }}

                #messages::-webkit-scrollbar-thumb:hover {{
                    background: #555; /* Darker color when hovering */
                }}
            </style>
        </head>
        <body>
            <h1>WebSocket Chat</h1>
            <h3 id="cur_user_display"></h3>
            <button id="logout" style="display: none;" onclick="logout()">Logout</button>

            <h3>All Chats ← just for debug, so does not reload automatically using ws</h3>
            <button onclick="fetchAllChats()">Reload</button>
            <ul id="allChats"></ul>

            <h3>Your Chats</h3>
            <ul id="userChats"></ul>

            <h3>Open Chat</h3>

            <form action="" onsubmit="loadChat(event, this)">
                <input type="number" id="chat_id" inputmode="numeric" placeholder="Chat ID" required/>
                <button>Open Chat</button>
            </form>

            <h3>Create Chat</h3>

            <form action="" onsubmit="createChat(event, this)">
                <input type="text" id="chat_name" placeholder="Chat Name" required/>
                <select id="chat_type">
                    <option value="group">Group</option>
                    <option value="private">Private</option>
                </select>
                <button>Create Chat</button>
            </form>

            <h3>Join chat</h3>

            <form action="" onsubmit="joinChat(event, this)">
                <input type="number" id="chat_id" inputmode="numeric" placeholder="Chat ID" required/>
                <button>Join Chat</button>
            </form>

            <div id="messageContainer" style="display: none;">
                <h3>Invite to current chat</h3>
    
                <form action="" onsubmit="inviteToChat(event, this)">
                    <input type="number" id="user_id" inputmode="numeric" placeholder="User ID" required/>
                    <button>Invite to chat</button>
                </form>
                
                <h3>Current Chat ID: <span id="currentChatDisplay">None</span></h3>
                <button onclick="leaveChat()">Leave Chat</button>
                <h3>Send Message</h3>

                <form action="" onsubmit="sendMessage(event, this)">
                    <input type="text" id="messageText" autocomplete="off" required/>
                    <button>Send</button>
                </form>
                <ul id='messages'>
                </ul>
            </div>

            <script>
                var ws = new WebSocket("{settings.MAIN_URL_WS}/api/v1/ws");
                var currentChatId = null;
                var userChatsArray = []
                var allChatsArray = []
                fetchAllChats();
                fetchUserChats();
                toggleLogoutButton();

                function currentUserId() {{
                    const userId = localStorage.getItem('user_id');
                    return userId ? parseInt(userId, 10) : null;
                }}

                function renderChats() {{
                    let userChats = document.getElementById("userChats");
                    userChats.innerHTML = "";

                    userChatsArray.forEach(chat => {{
                        let item = document.createElement("li");
                        item.textContent = "ID: " + chat.id + ", Unread: " + chat.unread + ", Users: " + chat.users;
                        userChats.appendChild(item);
                    }});
                }}

                function leaveChat() {{
                    fetchWithErrorHandling(`{settings.MAIN_URL_HTTP}/api/v1/chat/leave?chat_id=${{currentChatId}}`, {{
                            method: "POST"
                        }})
                }};

                function fetchAllChats() {{
                    fetchWithErrorHandling(`{settings.MAIN_URL_HTTP}/api/v1/chat/get_all`)
                        .then(response => response.json())
                        .then(data => {{                        
                            let allChats = document.getElementById("allChats");
                            allChats.innerHTML = "";
                            data.forEach(chat => {{
                                let item = document.createElement("li");
                                item.textContent = chat.name + " (ID: " + chat.id + ")";
                                allChats.appendChild(item);
                            }});
                        }});
                }};

                function fetchUserChats() {{
                    fetchWithErrorHandling(`{settings.MAIN_URL_HTTP}/api/v1/chat/get_user_chats`)
                        .then(response => response.json())
                        .then(data => {{
                            data.forEach(chat => {{
                                let chat_obj = {{ id: chat.id, unread: 0, users: [] }};
                
                                let unreadPromise = fetchWithErrorHandling(
                                    `{settings.MAIN_URL_HTTP}/api/v1/message/get_user_unread?chat_id=${{chat.id}}&user_id=${{currentUserId()}}`
                                )
                                    .then(response => response.text())
                                    .then(unread_num => {{
                                        chat_obj.unread = parseInt(unread_num, 10);
                                    }});
                
                                let usersPromise = fetchWithErrorHandling(
                                    `{settings.MAIN_URL_HTTP}/api/v1/chat/get_chat_users?chat_id=${{chat.id}}`
                                )
                                    .then(response => response.json())
                                    .then(users => {{
                                        chat_obj.users = users.map(user => user.id);
                                    }});
                
                                Promise.all([unreadPromise, usersPromise]).then(() => {{
                                    userChatsArray.push(chat_obj);
                                    userChatsArray.sort((a, b) => a.id - b.id);
                                    renderChats();
                                }});
                            }});
                        }});
                }};

                function createChat(event, form) {{
                    event.preventDefault();
                    var name = form.chat_name.value
                    var type = form.chat_type.value
                    fetchWithErrorHandling(`{settings.MAIN_URL_HTTP}/api/v1/chat/create`, {{
                        method: "POST",
                        headers: {{ "Content-Type": "application/json" }},
                        body: JSON.stringify({{ name: name, type: type }})
                    }});
                }};

                function inviteToChat(event, form) {{
                    event.preventDefault();
                    var userId = form.user_id.value;
                    fetchWithErrorHandling(`{settings.MAIN_URL_HTTP}/api/v1/chat/invite?chat_id=${{currentChatId}}&user_id=${{userId}}`, {{
                        method: "POST"
                    }});
                }};

                function joinChat(event, form) {{
                    event.preventDefault();
                    var chatId = form.chat_id.value;
                    fetchWithErrorHandling(`{settings.MAIN_URL_HTTP}/api/v1/chat/join?chat_id=${{chatId}}`, {{
                        method: "POST"
                    }})
                }};

                function loadChat(event, form) {{
                    event.preventDefault();
                    chat_id = parseInt(form.chat_id.value, 10)
                    if (!chat_id) return;

                    fetchWithErrorHandling(`{settings.MAIN_URL_HTTP}/api/v1/message/get_chat_messages?chat_id=${{chat_id}}`)
                    .then(response => response.json())
                    .then(messagesData => {{
                        return fetchWithErrorHandling(`{settings.MAIN_URL_HTTP}/api/v1/chat/user_progress?chat_id=${{chat_id}}&user_id=${{currentUserId()}}`)
                        .then(response => response.text())
                        .then(userRead => ({{messagesData, userRead}}))
                    }}).then( ({{messagesData, userRead}}) => {{
                        return fetchWithErrorHandling(`{settings.MAIN_URL_HTTP}/api/v1/chat/progress?chat_id=${{chat_id}}`)
                        .then(response => response.text())
                        .then(totalProgressData => ({{messagesData, userRead, totalProgressData}}));
                    }})
                    .then( ({{ messagesData, userRead, totalProgressData }}) => {{
                        let messages = document.getElementById("messages");
                        messages.innerHTML = "";
                        messagesData.messages.slice().reverse().forEach(msg => {{
                            var message = constructMessage(msg.id, msg.chat_id, msg.user_id, msg.content)
                            messages.appendChild(message)
                        }});
                        currentChatId = chat_id
                        userReadMessages(parseInt(userRead, 10))
                        othersReadMessages(parseInt(totalProgressData, 10))
                        document.getElementById("currentChatDisplay").textContent = currentChatId;
                        toggleMessageForm()
                    }});
                }}

                function constructMessage(id, chat_id, user_id, content) {{
                    var message = document.createElement('li')
                    message.parsedData = {{
                        "id": id,
                        "chat_id": chat_id,
                        "user_id": user_id,
                        "content": content
                    }}

                    var content = document.createTextNode("" + user_id + ": " + content);

                    var readByOthersWrapper = document.createElement('span');
                    readByOthersWrapper.classList.add('read-by-others-wrapper');
                    readByOthersWrapper.textContent = `✓`;

                    var checkboxWrapper = document.createElement('span');
                    checkboxWrapper.classList.add('checkbox-wrapper');
                    checkboxWrapper.textContent = `( I've read this : `;
                    var checkbox = document.createElement('input')
                    checkbox.type = 'checkbox'
                    checkbox.onclick = function () {{ sendProgress(chat_id, id) }}
                    checkboxWrapper.appendChild(checkbox);
                    var closingBracket = document.createElement('span');
                    closingBracket.textContent = ` )`;
                    checkboxWrapper.appendChild(closingBracket);

                    message.appendChild(content)
                    let spacer = document.createTextNode("\u00A0\u00A0\u00A0");
                    if (message.parsedData.user_id === currentUserId()) {{
                        message.appendChild(spacer);
                        message.appendChild(readByOthersWrapper);
                    }} else {{
                        message.appendChild(spacer);
                        message.style.backgroundColor = "lightblue"
                        message.appendChild(checkboxWrapper);
                    }}

                    return message
                }};

                ws.onmessage = function(event) {{
                    var parsed = JSON.parse(event.data)
                    var messages = document.getElementById('messages')
                    if (parsed.type === "message") {{
                        if (parsed.chat_id === currentChatId) {{
                            var message = constructMessage(parsed.message_id, parsed.chat_id, parsed.user_id, parsed.content)
                            messages.appendChild(message)
                        }}
                        if (parsed.user_id != currentUserId()) {{
                            let chat_counter = userChatsArray.find(chat => chat.id === parsed.chat_id);
                            if (chat_counter) {{
                                chat_counter.unread += 1
                                renderChats()
                            }}
                        }}
                    }} else if (parsed.type === "new_user") {{
                        if (parsed.user_id === currentUserId()) {{
                            let chat_obj = {{ id: parsed.chat_id, unread: 0, users: [] }};

                            fetchWithErrorHandling(`{settings.MAIN_URL_HTTP}/api/v1/chat/get_chat_users?chat_id=${{parsed.chat_id}}`)
                                .then(response => response.json())
                                .then(users => {{
                                    chat_obj.users = users.map(user => user.id);
                                    userChatsArray.push(chat_obj);
                                    userChatsArray.sort((a, b) => a.id - b.id);
                                    renderChats();
                                }});
                        }} else {{
                            let chat_counter = userChatsArray.find(chat => chat.id === parsed.chat_id);
                            if (chat_counter) {{
                                chat_counter.unread += 1
                                chat_counter.users.push(parsed.user_id)
                                chat_counter.users.sort((a, b) => a - b)
                                renderChats()
                            }}
                            if (parsed.chat_id === currentChatId) {{
                                var message = constructMessage(parsed.message_id, parsed.chat_id, parsed.user_id, parsed.content)
                                messages.appendChild(message);
                            }}
                        }}
                    }} else if (parsed.type === "user_left") {{
                        if (parsed.user_id === currentUserId()) {{
                            let index = userChatsArray.findIndex(chat => chat.id === parsed.chat_id);
                            if (index !== -1) {{
                                userChatsArray.splice(index, 1);
                            }}
                            renderChats()
                            if (parsed.chat_id === currentChatId) {{
                                document.getElementById("currentChatDisplay").textContent = "None";
                                toggleMessageForm()
                            }}
                        }} else {{
                            let chat_counter = userChatsArray.find(chat => chat.id === parsed.chat_id);
                            if (chat_counter) {{
                                chat_counter.unread += 1
                                let index = chat_counter.users.findIndex(id => id === parsed.user_id);
                                if (index !== -1) {{
                                    chat_counter.users.splice(index, 1);
                                }}
                                renderChats()
                            }}
                            if (parsed.chat_id === currentChatId) {{
                                var message = constructMessage(parsed.message_id, parsed.chat_id, parsed.user_id, parsed.content)
                                messages.appendChild(message);
                            }}
                        }}
                    }} else if (parsed.type === "chat_progress") {{
                        if (parsed.chat_id != currentChatId) return;
                        othersReadMessages(parsed.last_read_message_id);
                    }} else if (parsed.type === "user_progress") {{
                        if (parsed.user_id === currentUserId()) {{
                            fetchWithErrorHandling(`{settings.MAIN_URL_HTTP}/api/v1/message/get_user_unread?chat_id=${{parsed.chat_id}}&user_id=${{parsed.user_id}}`)
                            .then(response => response.text())
                            .then(unread_num => {{
                                let chat_counter = userChatsArray.find(chat => chat.id === parsed.chat_id);
                                chat_counter.unread = parseInt(unread_num, 10)
                                renderChats()
                            }})
                            if (parsed.chat_id === currentChatId) {{
                                userReadMessages(parsed.last_read_message_id)
                            }}
                        }}
                    }}
                }};

    			function userReadMessages(lastReadMessageId) {{
                    var messages = document.getElementById('messages').children;
                    for (let msg of messages) {{
                        if (msg.parsedData.user_id != currentUserId() &&
                            parseInt(msg.parsedData.id, 10) <= lastReadMessageId) {{
    							var checkboxWrapper = msg.querySelector('.checkbox-wrapper');
    							if (checkboxWrapper) {{
    								msg.removeChild(checkboxWrapper);
    							}}
    							msg.style.backgroundColor = ""
                        }}
                    }}
                }};

                function othersReadMessages(lastReadMessageId) {{
                    var messages = document.getElementById('messages').children;
                    for (let msg of messages) {{
                        if (msg.parsedData.id <= lastReadMessageId &&
                            msg.parsedData.user_id === currentUserId()) {{
                                var readByOthersWrapper = msg.querySelector('.read-by-others-wrapper');
                                if (readByOthersWrapper) {{
                                    readByOthersWrapper.textContent = `✓✓`;
                                }}
                        }}
                    }}
                }};

                function sendMessage(event, form) {{
                    event.preventDefault();

                    var chatId = currentChatId;
                    var messageText = form.messageText.value;

                    if (!chatId || !messageText) return;

                    var message = {{
                        type: "message",
                        chat_id: parseInt(chatId, 10),
                        content: messageText
                    }};

                    ws.send(JSON.stringify(message))
                }};
                function sendProgress(chat_id, message_id) {{                
                    var progressMessage = {{
                        type: "user_progress",
                        chat_id: chat_id,
                        "last_read_message_id": message_id
                    }};

                    ws.send(JSON.stringify(progressMessage));
                }};
                async function fetchWithErrorHandling(url, options = {{}}) {{
                    try {{
                        let response = await fetch(url, options);
                        if (response.ok) {{
                            return response;
                        }}

                        if (response.status === 401) {{
                            let refreshResponse = await fetch('{settings.MAIN_URL_HTTP}/api/v1/login/refresh', {{
                                method: "POST"
                            }})

                            if (refreshResponse.ok) {{
                                if (ws && ws.readyState === WebSocket.CLOSED) {{
                                    ws = new WebSocket("{settings.MAIN_URL_WS}/api/v1/ws");
                                }}
                                response = await fetch(url, options);
                                if (response.ok) {{
                                    return response;
                                }}
                            }}

                            window.location.href = '{settings.MAIN_URL_HTTP}/auth';
                            throw new Error('Redirecting to login screen due to failed authentication.');
                        }}

                        let responseText = await response.text();
                        throw new Error(`Error ${{response.status}}: ${{responseText}}`);

                    }} catch (error) {{
                        console.error(error);
                        alert(error);
                        throw error;
                    }}
                }};

                function toggleMessageForm() {{
                    let chatDisplay = document.getElementById("currentChatDisplay").textContent;
                    let messageContainer = document.getElementById("messageContainer");

                    messageContainer.style.display = chatDisplay === "None" ? "none" : "block";
                }}

                function toggleLogoutButton() {{
                    let userId = localStorage.getItem('user_id');
                    let logoutButton = document.getElementById("logout");
                    logoutButton.style.display = userId ? "block" : "none";
                    var cur_user_display = document.getElementById('cur_user_display')
                    cur_user_display.textContent = userId ? `You are user #${{userId}}` : ''
                }}
                
                async function logout() {{
                    const response = await fetch('{settings.MAIN_URL_HTTP}/api/v1/logout', {{ method: 'POST' }});
                    try {{
                        ws.close();
                    }} catch (error) {{
                        console.error('Error closing WebSocket:', error);
                    }}
                    window.location.href = '{settings.MAIN_URL_HTTP}/auth';
                }}
            </script>
        </body>
    </html>
    """

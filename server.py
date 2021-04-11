from aiohttp import web
routes = web.RouteTableDef()

from rtcbot import Websocket, getRTCBotJS

ws = None # Websocket connection to the robot

ws_List = list()

@routes.get("/ws/{key}")
async def wsKey(request):
    global ws_List
    key = request.match_info['key']
    print(key)
    ##Check if key already exist in ws_List
    socket = Websocket(request)
    ws_Dic = {
        "key": key,
        "socket": socket
    }
    ws_List.append(ws_Dic)
    print(socket)
    print("Robot Connected")
    await socket
    print(socket)
    print("Robot disconnected")
    ##Delete ws_Dic form ws_List
    ws_List = deleteList(ws_List, key)
    return socket.ws

def deleteList(in_List, in_Key):
    ot_List = in_List.copy()
    for item in in_List:
        if item["key"] == in_Key:
            ot_List.remove(item)
    return ot_List

def checkSocket(in_List, in_Key):
    ot_socket = None
    for item in in_List:
        if item["key"] == in_Key:
            ot_socket = item["socket"]
    return ot_socket

@routes.post("/connect/{key}")
async def connectKey(request):
    global ws_List
    key = request.match_info['key']
    #Find socket in ws_List using key
    socket = checkSocket(ws_List, key)
    if socket is None:
        raise web.HTTPInternalServerError()
    clientOffer = await request.json()
    socket.put_nowait(clientOffer)
    robotResponse = await socket.get()
    return web.json_response(robotResponse)

@routes.get("/ws")
async def websocket(request):
    global ws
    ws = Websocket(request)
    print("Robot Connected")
    await ws  # Wait until the websocket closes
    print("Robot disconnected")
    return ws.ws

# Called by the browser to set up a connection
@routes.post("/connect")
async def connect(request):
    global ws
    if ws is None:
        raise web.HTTPInternalServerError()
    clientOffer = await request.json()
    # Send the offer to the robot, and receive its response
    ws.put_nowait(clientOffer)
    robotResponse = await ws.get()
    return web.json_response(robotResponse)

# Serve the RTCBot javascript library at /rtcbot.js
@routes.get("/rtcbot.js")
async def rtcbotjs(request):
    return web.Response(content_type="application/javascript", text=getRTCBotJS())

@routes.get("/main")
async def index(request):
    return web.Response(
        content_type="text/html",
        text="""
    <html>
        <head>
            <title>RTCBot: Remote Video</title>
            <script src="/rtcbot.js"></script>
        </head>
        <body style="text-align: center;padding-top: 30px;">
            <video autoplay playsinline muted controls></video>
            <p>
            Open the browser's developer tools to see console messages (CTRL+SHIFT+C)
            </p>
            <script>
                var conn = new rtcbot.RTCConnection();

                conn.video.subscribe(function(stream) {
                    document.querySelector("video").srcObject = stream;
                });

                async function connect() {
                    let offer = await conn.getLocalDescription();

                    // POST the information to /connect
                    let response = await fetch("/connect/key1", {
                        method: "POST",
                        cache: "no-cache",
                        body: JSON.stringify(offer)
                    });

                    await conn.setRemoteDescription(await response.json());

                    console.log("Ready!");
                }
                connect();

            </script>
        </body>
    </html>
    """)

async def cleanup(app=None):
    global ws
    if ws is not None:
        c = ws.close()
        if c is not None:
            await c

async def cleanup2(app=None):
    global ws_List
    for item in ws_List:
        if item["socket"] is not None:
            c = item["socket"].close()
            if c is not None:
                await c

app = web.Application()
app.add_routes(routes)
app.on_shutdown.append(cleanup)
app.on_shutdown.append(cleanup2)
web.run_app(app,host='127.0.0.1', port=8085)

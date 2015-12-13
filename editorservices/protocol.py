import json
from .logger import log

# Message Type Information

class MessageType:
    Unknown = 0
    Request = 1
    Event = 2

def request(methodName):
    def decorator(requestClass):
        requestClass.__type = MessageType.Request
        requestClass.__method = methodName
        return requestClass
    return decorator

def event(methodName):
    def decorator(eventClass):
        eventClass.__type = MessageType.Event
        eventClass.__method = methodName
        return eventClass
    return decorator

# Message Read/Write Methods

class MessageEncoder(json.JSONEncoder):
    def default(self, obj):
        return obj.__dict__

ContentLengthHeaderString = "Content-Length: "

def write_message(message, id, inputStream):
    messageObject = {"jsonrpc": "2.0"}
    messageObject["params"] = message
    messageObject["method"] = message.__class__.__method
    messageType = message.__class__.__type

    messageTypeName = "UNKNOWN"
    if messageType is MessageType.Request:
        messageObject["id"] = id
        messageTypeName = "request"
    else:
        messageTypeName = "event"

    log.debug("Sending %s '%s':\n%s",
              messageTypeName,
              messageObject["method"],
              json.dumps(messageObject,
                         sort_keys=True,
                         indent=4,
                         cls=MessageEncoder,
                         separators=(',', ': ')))

    jsonString = json.dumps(messageObject, cls=MessageEncoder)
    jsonBytes = bytearray(jsonString, 'utf-8')
    headerString = ContentLengthHeaderString + str(len(jsonBytes)) + "\r\n\r\n"

    inputStream.write(bytes(headerString, 'ascii'))
    inputStream.write(jsonBytes)
    inputStream.flush()

def read_message(outputStream):
    headerStringBytes = outputStream.readline()
    if headerStringBytes == None:
        log.error("Language Server terminated unexpectedly!")

    headerString = headerStringBytes.decode('ascii')
    if headerString.startswith(ContentLengthHeaderString):
        # Read the following newline
        if outputStream.readline() == None:
            log.error("Language Server terminated unexpectedly!")

        contentLengthStr = headerString[len(ContentLengthHeaderString):].strip()
        messageJson = outputStream.read(int(contentLengthStr))

        if messageJson == None:
            log.error("Language Server terminated unexpectedly!")

        return json.loads(messageJson.decode('utf-8'))

    else:
        #print "Expected Content-Length header!"
        return None



def commandStart(text, window, inferredVoiceCommand):
    if text == "command":
        inferredVoiceCommand.linebuilder = "command "
    elif (text == "start" and inferredVoiceCommand.linebuilder == "command ") \
            or text == "command start":
        window['Command-Start'].Update(value=True)
        inferredVoiceCommand.linebuilder = ""


def commandLine(text, window, inferredVoiceCommand):
    if text == "line":
        inferredVoiceCommand.linebuilder = "line "
    elif (inferredVoiceCommand.linebuilder == "line "
          and (text == "one" or text == "two" or text == "three" or text == "four")):
        window['Line'].Update(value=True)
        inferredVoiceCommand.line = inferredVoiceCommand.linebuilder + text
    elif text == "line one" \
            or text == "line two" \
            or text == "line three" \
            or text == "line four":
        window['Line'].Update(value=True)
        inferredVoiceCommand.line = text

def commandCommand(text, window, inferredVoiceCommand):
    if text == "transmit":
        window['Command'].Update(value=True)
        inferredVoiceCommand.command = text
    elif text == "receive":
        window['Command'].Update(value=True)
        inferredVoiceCommand.command = text


def commandStop(text, window, inferredVoiceCommand):
    window['Command-Stop'].Update(value=True)
    if inferredVoiceCommand.line == "line one":
        if inferredVoiceCommand.command == "transmit":
            window['Line1-rx'].Update(value=True)
        elif inferredVoiceCommand.command == "receive":
            window['Line1-rxtx'].Update(value=True)
    elif inferredVoiceCommand.line == "line two":
        if inferredVoiceCommand.command == "transmit":
            window['Line2-rx'].Update(value=True)
        elif inferredVoiceCommand.command == "receive":
            window['Line2-rxtx'].Update(value=True)
    elif inferredVoiceCommand.line == "line three":
        if inferredVoiceCommand.command == "transmit":
            window['Line3-rx'].Update(value=True)
        elif inferredVoiceCommand.command == "receive":
            window['Line3-rxtx'].Update(value=True)
    elif inferredVoiceCommand.line == "line four":
        if inferredVoiceCommand.command == "transmit":
            window['Line4-rx'].Update(value=True)
        elif inferredVoiceCommand.command == "receive":
            window['Line4-rxtx'].Update(value=True)


def commandCancel(text, window, inferredVoiceCommand):
    window['Command-None'].Update(value=True)
    inferredVoiceCommand.reset()
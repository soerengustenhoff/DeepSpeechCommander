
class InferredVoiceCommand:
    line = ""
    command = ""
    command_builder = ""
    reverse_command_builder = ""

    def reset_all(self):
        self.line = ""
        self.command = ""
        self.command_builder = ""
        self.reverse_command_builder = ""

    def reset_builders(self):
        self.command_builder = ""
        self.reverse_command_builder = ""


def voice_command_builder():
    voice_commands = []

    # Word for command, used to start and stop the command tree
    voice_commands.append("command")

    # Words for start
    voice_commands.append("start")

    # Words for stop
    voice_commands.append("stop")
    voice_commands.append("complete")

    # Words for aborting voice command tree
    voice_commands.append("cancel")
    voice_commands.append("abort")

    # Words for rx
    voice_commands.append("transmit")
    voice_commands.append("listen")

    # Words for rx/tx
    voice_commands.append("receive")
    voice_commands.append("speak")

    # Words for the line
    voice_commands.append("line")

    # Words for line numbers
    voice_commands.append("one")
    voice_commands.append("first")
    voice_commands.append("two")
    voice_commands.append("second")
    voice_commands.append("three")
    voice_commands.append("third")
    voice_commands.append("four")
    voice_commands.append("fourth")

    return voice_commands


def command_start_logic(text, window, inferred_voice_command):
    if text == "command":
        inferred_voice_command.command_builder = "command "
        return True

    if (text == "start" and inferred_voice_command.command_builder == "command ") \
            or text == "command start":
        window['Command-Start'].Update(value=True)
        inferred_voice_command.command_builder = ""
        return True


def command_start(text, window, inferred_voice_command):
    if command_start_logic(text, window, inferred_voice_command):
        inferred_voice_command.reset_builders()


def command_line_logic(text, window, inferred_voice_command: InferredVoiceCommand):
    if text == "line":
        inferred_voice_command.command_builder = "line "
        if inferred_voice_command.reverse_command_builder != "":
            inferred_voice_command.reverse_command_builder += text
            text = inferred_voice_command.reverse_command_builder
        else:
            return True

    if (inferred_voice_command.command_builder == "line "
            and (text == "one" or text == "two" or text == "three" or text == "four")):
        window['Line'].Update(value=True)
        inferred_voice_command.line = inferred_voice_command.command_builder + text
        return True

    if text == "first" \
            or text == "second" \
            or text == "third" \
            or text == "forth":
        inferred_voice_command.reverse_command_builder = text + " "

    if text == "first line":
        text = "line one"

    if text == "second line":
        text = "line two"

    if text == "third line":
        text = "line three"

    if text == "forth line":
        text = "line four"

    if text == "line one" \
            or text == "line two" \
            or text == "line three" \
            or text == "line four":
        window['Line'].Update(value=True)
        inferred_voice_command.line = text
        return True


def command_line(text, window, inferred_voice_command):
    if command_line_logic(text, window, inferred_voice_command):
        inferred_voice_command.reset_builders()


def command_command_logic(text, window, inferred_voice_command):
    if text == "receive" \
            or text == "listen":
        window['Command'].Update(value=True)
        inferred_voice_command.command = text
        return True

    if text == "transmit" \
            or text == "speak":
        window['Command'].Update(value=True)
        inferred_voice_command.command = text
        return True


def command_command(text, window, inferred_voice_command):
    if command_command_logic(text, window, inferred_voice_command):
        inferred_voice_command.reset_builders()


def command_stop_run_command(window, inferred_voice_command):
    if inferred_voice_command.line == "line one":
        if inferred_voice_command.command == "transmit":
            window['Line1-rx'].Update(value=True)
            return True
        elif inferred_voice_command.command == "receive":
            window['Line1-rxtx'].Update(value=True)
            return True
    elif inferred_voice_command.line == "line two":
        if inferred_voice_command.command == "transmit":
            window['Line2-rx'].Update(value=True)
            return True
        elif inferred_voice_command.command == "receive":
            window['Line2-rxtx'].Update(value=True)
            return True
    elif inferred_voice_command.line == "line three":
        if inferred_voice_command.command == "transmit":
            window['Line3-rx'].Update(value=True)
            return True
        elif inferred_voice_command.command == "receive":
            window['Line3-rxtx'].Update(value=True)
            return True
    elif inferred_voice_command.line == "line four":
        if inferred_voice_command.command == "transmit":
            window['Line4-rx'].Update(value=True)
            return True
        elif inferred_voice_command.command == "receive":
            window['Line4-rxtx'].Update(value=True)
            return True

    return False


def command_stop_logic(text, window, inferred_voice_command):
    if text == "command":
        inferred_voice_command.command_builder = "command "
        return False

    if (inferred_voice_command.command_builder == "command " and text == "stop") \
            or text == "command stop":
        return command_stop_run_command(window, inferred_voice_command)

    if (inferred_voice_command.command_builder == "command " and text == "complete") \
            or text == "command complete":
        return command_stop_run_command(window, inferred_voice_command)


def command_stop(text, window, inferred_voice_command):
    if command_stop_logic(text, window, inferred_voice_command):
        window['Command-Ready'].Update(value=True)
        inferred_voice_command.reset_builders()
        return


def command_cancel_check(text, window, inferred_voice_command):
    if text == "command cancel" \
            or text == "cancel command"\
            or text == "command abort"\
            or text == "abort command":
        window['Command-Ready'].Update(value=True)
        inferred_voice_command.reset_all()

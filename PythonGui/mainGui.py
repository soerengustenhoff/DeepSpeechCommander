import PySimpleGUI as sg
import os.path
import deepSpeechHandler
import deepSpeechModels
import voiceOperationHelper

import time
import logging
from datetime import datetime
import threading
import collections
import queue
import os
import deepspeech
import numpy as np
import pyaudio
import wave
import webrtcvad
from halo import Halo
from scipy import signal

import json
import sys
import subprocess
import shlex
import threading

try:
    from shhlex import quote
except ImportError:
    from pipes import quote

logging.basicConfig(level=20)
lock = threading.Lock()


#def convert_samplerate(audio_path, desired_sample_rate):
#    sox_cmd = 'sox {} --type raw --bits 16 --channels 1 --rate {} --encoding signed-integer --endian little --compression 0.0 --no-dither - '.format(
#        quote(audio_path), desired_sample_rate)
#    try:
#        output = subprocess.check_output(shlex.split(sox_cmd), stderr=subprocess.PIPE)
#    except subprocess.CalledProcessError as e:
#        raise RuntimeError('SoX returned non-zero status: {}'.format(e.stderr))
#    except OSError as e:
#        raise OSError(e.errno,
#                      'SoX not found, use {}hz files or install it: {}'.format(desired_sample_rate, e.strerror))
#
#    return desired_sample_rate, np.frombuffer(output, np.int16)


class TranscriptedWord:
    confidence = -99.999
    text = ""


class InferredWord:
    confidence = 0
    text = ""


class InferredVoiceCommand:
    line = ""
    command = ""
    linebuilder = ""

    def reset(self):
        self.line = ""
        self.command = ""
        self.linebuilder = ""


inferredVoiceCommand = InferredVoiceCommand()
voiceCommands = ["command", "start", "stop", "cancel", "receive", "transmit", "line", "one", "two", "three", "four"]

def DistinguishVoiceOperation(transcriptedWords, window):
    #voiceCommands = ["command", "start", "stop", "cancel", "recieve", "transmit", "line", "one", "two", "three", "four"]

    inferredWord = InferredWord()
    inferredWord.inferred_str = ""

    for transcriptedWord in transcriptedWords:
        checkTranscriptWord = transcriptedWord.text.split(' ')
        for text in checkTranscriptWord:
            if text in voiceCommands:
#                with lock:
#                    window['-DEEPSPEECH-out-'].print("Recognized: %s with confidence %.3f \n \n \n" % (transcriptedWord.text, transcriptedWord.confidence))
                if inferredWord.inferred_str == "":
                    inferredWord.inferred_str += text
                elif inferredWord.inferred_str == text:
                    pass
                else:
                    inferredWord.inferred_str += " " + text

                if checkTranscriptWord and text == checkTranscriptWord[-1]:
                    inferredWord.confidence = transcriptedWord.confidence
                    with lock:
                        window['-DEEPSPEECH-out-'].print(
                            "Recognized: %s with confidence %.3f \n " % (
                                inferredWord.inferred_str, inferredWord.confidence))
                    return inferredWord.inferred_str
            else:
                inferredWord.inferred_str = ""
                inferredWord.confidence = 0
                break

#    with lock:
#        window['-DEEPSPEECH-out-'].print("Did not understand your command, please try again \n ")

    return inferredWord.inferred_str


def handleVoiceOperation(text, window):
    with lock:
        if window['Command-None'].get():
            voiceOperationHelper.commandStart(text, window, inferredVoiceCommand)
        elif window['Command-Start'].get():
            voiceOperationHelper.commandLine(text, window, inferredVoiceCommand)
        elif window['Line'].get():
            voiceOperationHelper.commandCommand(text, window, inferredVoiceCommand)
        elif window['Command'].get() and text == "command stop":
            voiceOperationHelper.commandStop(text, window, inferredVoiceCommand)
        elif text == "command cancel":
            voiceOperationHelper.commandCancel(text, window, inferredVoiceCommand)
    return


def handleVoiceOperationOld(text, window):
    with lock:
        if text == "command start" and window['Command-None'].get():
            window['Command-Start'].Update(value=True)
        elif text == "line one" \
                or text == "line two" \
                or text == "line three" \
                or text == "line four" \
                and window['Command-Start'].get():
            window['Line'].Update(value=True)
            inferredVoiceCommand.line = text
        elif text == "transmit" \
                or text == "receive"\
                and window['Line'].get():
            window['Command'].Update(value=True)
            inferredVoiceCommand.command = text
        elif text == "command stop" and window['Command'].get():
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
        elif text == "command cancel":
            window['Command-None'].Update(value=True)
            inferredVoiceCommand.reset()
    return


def handleMetadata(text, window):
    transcriptedWords = []

    transcripts = text.transcripts
    for transcript in transcripts:
        transcriptedWord = TranscriptedWord()
        transcriptedWord.confidence = transcript.confidence
        for token in transcript.tokens:
            transcriptedWord.text += token.text
        transcriptedWords.append(transcriptedWord)

    text = DistinguishVoiceOperation(transcriptedWords, window=window)
    handleVoiceOperation(text, window=window)
    return text


def runMicrophone(dataModel: deepSpeechModels.deepSpeechDataModel, window):

    dataModel.vad_audio = deepSpeechModels.VADAudio(aggressiveness=ARGS.vad_aggressiveness,
                                                    device=ARGS.device,
                                                    input_rate=ARGS.rate,
                                                    file=ARGS.file)
    with lock:
        window['-DEEPSPEECH-out-'].print("Listening (ctrl-C to exit)...\n")

    frames = dataModel.vad_audio.vad_collector()

    # Stream from microphone to DeepSpeech using VAD
    spinner = None
    if not ARGS.nospinner:
        spinner = Halo(spinner='line')
    stream_context = dataModel.model.createStream()
    wav_data = bytearray()
    for frame in frames:
        if frame is not None:
            if spinner: spinner.start()
            logging.debug("streaming frame")
            stream_context.feedAudioContent(np.frombuffer(frame, np.int16))
            if ARGS.savewav: wav_data.extend(frame)
        else:
            if spinner: spinner.stop()
            logging.debug("end utterence")
            if ARGS.savewav:
                dataModel.vad_audio.write_wav(
                    os.path.join(ARGS.savewav, datetime.now().strftime("savewav_%Y-%m-%d_%H-%M-%S_%f.wav")), wav_data)
                wav_data = bytearray()
            text = handleMetadata(stream_context.finishStreamWithMetadata(50), window=window)
            if ARGS.keyboard:
                from pyautogui import typewrite
                typewrite(text)
            stream_context = dataModel.model.createStream()


def init():
    sg.theme('Dark Blue 3')  # please make your windows colorful

    layout = [[sg.T('Command progress'),
               sg.Radio('No input', "RADIOCOMMAND", default=True, key='Command-None'),
               sg.Radio('Start', "RADIOCOMMAND", key='Command-Start'),
               sg.Radio('Line selected', "RADIOCOMMAND", key='Line'),
               sg.Radio('Command', "RADIOCOMMAND", key='Command'),
               sg.Radio('Stop', "RADIOCOMMAND", key='Command-Stop')],
              [sg.T('Line 1'),
               sg.Radio('Off', "Line1", default=True, key='Line1-Off'),
               sg.Radio('Tx', "Line1", key='Line1-rx'),
               sg.Radio('Tx/Rx', "Line1", key='Line1-rxtx')],
              [sg.T('Line 2'),
               sg.Radio('Off', "Line2", default=True, key='Line2-Off'),
               sg.Radio('Tx', "Line2", key='Line2-rx'),
               sg.Radio('Tx/Rx', "Line2", key='Line2-rxtx')],
              [sg.T('Line 3'),
               sg.Radio('Off', "Line3", default=True, key='Line3-Off'),
               sg.Radio('Tx', "Line3", key='Line3-rx'),
               sg.Radio('Tx/Rx', "Line3", key='Line3-rxtx')],
              [sg.T('Line 4'),
               sg.Radio('Off', "Line4", default=True, key='Line4-Off'),
               sg.Radio('Tx', "Line4", key='Line4-rx'),
               sg.Radio('Tx/Rx', "Line4", key='Line4-rxtx')],
              [sg.Multiline('Welcome\n', autoscroll=True, size=(100, 20), key='-DEEPSPEECH-out-')]
              ]

    window = sg.Window('Window Title', layout).Finalize()

    dataModel = deepSpeechModels.deepSpeechDataModel()
    deepSpeechHandler.init(args=ARGS, dataModel=dataModel)

    x = threading.Thread(target=runMicrophone, args=(dataModel,window), daemon=True)
    x.start()

    while True:  # Event Loop
        event, values = window.read()
        print(event, values)
        if event == sg.WIN_CLOSED or event == 'Exit':

            break

    window.close()


if __name__ == "__main__":
    DEFAULT_SAMPLE_RATE = 44100

    import argparse

    parser = argparse.ArgumentParser(description="Stream from microphone to DeepSpeech using VAD")

    parser.add_argument('-v', '--vad_aggressiveness', type=int, default=3,
                        help="Set aggressiveness of VAD: an integer between 0 and 3, 0 being the least aggressive about filtering out non-speech, 3 the most aggressive. Default: 3")
    parser.add_argument('--nospinner', action='store_true',
                        help="Disable spinner")
    parser.add_argument('-w', '--savewav',
                        help="Save .wav files of utterences to given directory")
    parser.add_argument('-f', '--file',
                        help="Read from .wav file instead of microphone")

    parser.add_argument('-m', '--model', required=True,
                        help="Path to the model (protocol buffer binary file, or entire directory containing all standard-named files for model)")
    parser.add_argument('-s', '--scorer',
                        help="Path to the external scorer file.")
    parser.add_argument('-d', '--device', type=int, default=None,
                        help="Device input index (Int) as listed by pyaudio.PyAudio.get_device_info_by_index(). If not provided, falls back to PyAudio.get_default_device().")
    parser.add_argument('-r', '--rate', type=int, default=DEFAULT_SAMPLE_RATE,
                        help=f"Input device sample rate. Default: {DEFAULT_SAMPLE_RATE}. Your device may require 44100.")
    parser.add_argument('-k', '--keyboard', action='store_true',
                        help="Type output through system keyboard")
    ARGS = parser.parse_args()
    if ARGS.savewav: os.makedirs(ARGS.savewav, exist_ok=True)
    init()

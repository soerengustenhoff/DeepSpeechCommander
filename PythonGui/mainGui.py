import PySimpleGUI as sg
import os.path
import deepSpeechHandler
import deepSpeechModels

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

try:
    from shhlex import quote
except ImportError:
    from pipes import quote

logging.basicConfig(level=20)



def convert_samplerate(audio_path, desired_sample_rate):
    sox_cmd = 'sox {} --type raw --bits 16 --channels 1 --rate {} --encoding signed-integer --endian little --compression 0.0 --no-dither - '.format(
        quote(audio_path), desired_sample_rate)
    try:
        output = subprocess.check_output(shlex.split(sox_cmd), stderr=subprocess.PIPE)
    except subprocess.CalledProcessError as e:
        raise RuntimeError('SoX returned non-zero status: {}'.format(e.stderr))
    except OSError as e:
        raise OSError(e.errno,
                      'SoX not found, use {}hz files or install it: {}'.format(desired_sample_rate, e.strerror))

    return desired_sample_rate, np.frombuffer(output, np.int16)


def words_from_candidate_transcript(metadata):
    word = ""
    word_list = []
    word_start_time = 0
    # Loop through each character
    for i, token in enumerate(metadata.tokens):
        # Append character to word if it's not a space
        if token.text != " ":
            if len(word) == 0:
                # Log the start time of the new word
                word_start_time = token.start_time

            word = word + token.text
        # Word boundary is either a space or the last character in the array
        if token.text == " " or i == len(metadata.tokens) - 1:
            word_duration = token.start_time - word_start_time

            if word_duration < 0:
                word_duration = 0

            each_word = dict()
            each_word["word"] = word
            each_word["start_time"] = round(word_start_time, 4)
            each_word["duration"] = round(word_duration, 4)

            word_list.append(each_word)
            # Reset
            word = ""
            word_start_time = 0

    return word_list


def metadata_json_output(metadata):
    json_result = dict()
    json_result["transcripts"] = [{
        "confidence": transcript.confidence,
        "words": words_from_candidate_transcript(transcript),
    } for transcript in metadata.transcripts]
    return json.dumps(json_result, indent=2)


class TranscriptedWord:
    confidence = -99.999
    text = ""


class InferedWord:
    confidence = 0
    text = ""


def handleVoiceOperation(transcriptedWords=[], window=None):
    voiceCommands = ["command", "start", "stop", "recieve", "transmit", "line", "one", "two", "three", "four"]

    inferedWord = InferedWord()
    inferedWord.infered_str = ""

    for transcriptedWord in transcriptedWords:
        checkTranscriptWord = transcriptedWord.text.split(' ')
        for text in checkTranscriptWord:
            if text in voiceCommands:
#                with lock:
#                    window['-DEEPSPEECH-out-'].print("Recognized: %s with confidence %.3f \n \n \n" % (transcriptedWord.text, transcriptedWord.confidence))
                if inferedWord.infered_str == "":
                    inferedWord.infered_str += text
                elif inferedWord.infered_str == text:
                    pass
                else:
                    inferedWord.infered_str += " " + text

                if checkTranscriptWord and text == checkTranscriptWord[-1]:
                    inferedWord.confidence = transcriptedWord.confidence
                    with lock:
                        window['-DEEPSPEECH-out-'].print(
                            "Recognized: %s with confidence %.3f \n " % (
                            inferedWord.infered_str, inferedWord.confidence))
                    return inferedWord.infered_str
            else:
                inferedWord.infered_str = ""
                inferedWord.confidence = 0
                break

#    with lock:
#        window['-DEEPSPEECH-out-'].print("Did not understand your command, please try again \n ")

    return inferedWord.infered_str


def handleMetadata(text, window):
    transcriptedWords = []

    transcripts = text.transcripts
    for transcript in transcripts:
        transcriptedWord = TranscriptedWord()
        transcriptedWord.confidence = transcript.confidence
        for token in transcript.tokens:
            transcriptedWord.text += token.text
        transcriptedWords.append(transcriptedWord)

    text = handleVoiceOperation(transcriptedWords, window=window)
    return text

import threading
lock = threading.Lock()
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

    layout = [[sg.T('Line 1'),
               sg.Radio('Off', "RADIO1", default=True, key='RADIO1-Off'),
               sg.Radio('Tx', "RADIO1", key='RADIO1-tx'),
               sg.Radio('Tx/Rx', "RADIO1", key='RADIO1-rxtx')],
              [sg.T('Line 2'),
               sg.Radio('Off', "RADIO2", default=True, key='RADIO2-Off'),
               sg.Radio('Tx', "RADIO2", key='RADIO2-tx'),
               sg.Radio('Tx/Rx', "RADIO2", key='RADIO2-rxtx')],
              [sg.T('Line 3'),
               sg.Radio('Off', "RADIO3", default=True, key='RADIO3-Off'),
               sg.Radio('Tx', "RADIO3", key='RADIO3-tx'),
               sg.Radio('Tx/Rx', "RADIO3", key='RADIO3-rxtx')],
              [sg.T('Line 4'),
               sg.Radio('Off', "RADIO4", default=True, key='RADIO4-Off'),
               sg.Radio('Tx', "RADIO4", key='RADIO4-tx'),
               sg.Radio('Tx/Rx', "RADIO4", key='RADIO4-rxtx')],
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

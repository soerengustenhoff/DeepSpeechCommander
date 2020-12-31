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


class TranscribedWord:
    confidence = -99.999
    text = ""


class InferredWord:
    confidence = 0
    text = ""


inferredVoiceCommand = voiceOperationHelper.InferredVoiceCommand()
voiceCommands = voiceOperationHelper.voice_command_builder()


def distinguish_voice_operation(transcriptedWords, window):
    inferred_word = InferredWord()
    inferred_word.inferred_str = ""

    for transcribed_word in transcriptedWords:
        check_transcribed_word = transcribed_word.text.split(' ')
        for text in check_transcribed_word:
            if text in voiceCommands:
                if inferred_word.inferred_str == "":
                    inferred_word.inferred_str += text
                elif inferred_word.inferred_str == text:
                    pass
                else:
                    inferred_word.inferred_str += " " + text

                if check_transcribed_word and text == check_transcribed_word[-1]:
                    inferred_word.confidence = transcribed_word.confidence
                    with lock:
                        window['-DEEPSPEECH-out-'].print(
                            "Recognized: %s with confidence %.3f \n " % (
                                inferred_word.inferred_str, inferred_word.confidence))
                    return inferred_word.inferred_str
            else:
                inferred_word.inferred_str = ""
                inferred_word.confidence = 0
                break

    return inferred_word.inferred_str


def handle_voice_operation(text, window):
    if text == "":
        return

    with lock:
        if window['Command-Ready'].get():
            voiceOperationHelper.command_start(text, window, inferredVoiceCommand)
        elif window['Command-Start'].get():
            voiceOperationHelper.command_line(text, window, inferredVoiceCommand)
        elif window['Line'].get():
            voiceOperationHelper.command_command(text, window, inferredVoiceCommand)
        elif window['Command'].get():
            voiceOperationHelper.command_stop(text, window, inferredVoiceCommand)

        voiceOperationHelper.command_cancel_check(text, window, inferredVoiceCommand)

    return


def handle_metadata(text, window):
    transcribed_words = []

    transcripts = text.transcripts
    for transcript in transcripts:
        transcribed_word = TranscribedWord()
        transcribed_word.confidence = transcript.confidence
        for token in transcript.tokens:
            transcribed_word.text += token.text
        transcribed_words.append(transcribed_word)

    text = distinguish_voice_operation(transcribed_words, window=window)
    handle_voice_operation(text, window=window)
    return text


def run_microphone(data_model: deepSpeechModels.DeepSpeechDataModel, window):

    data_model.vad_audio = deepSpeechModels.VADAudio(aggressiveness=ARGS.vad_aggressiveness,
                                                     device=ARGS.device,
                                                     input_rate=ARGS.rate,
                                                     file=ARGS.file)
    with lock:
        window['-DEEPSPEECH-out-'].print("Listening (ctrl-C to exit)...\n")

    frames = data_model.vad_audio.vad_collector()

    # Stream from microphone to DeepSpeech using VAD
    spinner = None
    if not ARGS.nospinner:
        spinner = Halo(spinner='line')
    stream_context = data_model.model.createStream()
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
                data_model.vad_audio.write_wav(
                    os.path.join(ARGS.savewav, datetime.now().strftime("savewav_%Y-%m-%d_%H-%M-%S_%f.wav")), wav_data)
                wav_data = bytearray()
            text = handle_metadata(stream_context.finishStreamWithMetadata(50), window=window)
            if ARGS.keyboard:
                from pyautogui import typewrite
                typewrite(text)
            stream_context = data_model.model.createStream()


def init():
    sg.theme('Dark Blue 3')  # please make your windows colorful

    layout = [[sg.T('Command progress'),
               sg.Radio('Ready for input', "RADIOCOMMAND", default=True, key='Command-Ready'),
               sg.Radio('Start', "RADIOCOMMAND", key='Command-Start'),
               sg.Radio('Line selected', "RADIOCOMMAND", key='Line'),
               sg.Radio('Command', "RADIOCOMMAND", key='Command')],
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

    data_model = deepSpeechModels.DeepSpeechDataModel()
    deepSpeechHandler.init(args=ARGS, data_model=data_model)

    x = threading.Thread(target=run_microphone, args=(data_model, window), daemon=True)
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

import PySimpleGUI as sg
import os.path

def main():
    import PySimpleGUI as sg

    sg.theme('Dark Blue 3')  # please make your windows colorful

    layout = [[sg.Text('Your typed chars appear here:'), sg.Text(size=(12, 1), key='-OUTPUT-')],
              [sg.Input(key='-IN-')],
              [sg.Button('Show'), sg.Button('Exit')],
              [sg.T('Line 1'),
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
              [sg.Multiline('Welcome', autoscroll=True, size=(100, 20), key='-DEEPSPEECH-')]
              ]

    window = sg.Window('Window Title', layout)

    while True:  # Event Loop
        event, values = window.read()
        print(event, values)
        if event == sg.WIN_CLOSED or event == 'Exit':
            break
        if event == 'Show':
            # change the "output" element to be the value of "input" element
            window['-OUTPUT-'].update(values['-IN-'])

    window.close()

if __name__ == "__main__":
    main()


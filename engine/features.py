import sys
import os
import re
import shlex
import sqlite3
import struct
import subprocess
import time
import webbrowser
from playsound import playsound
import eel
import pyaudio
import pyautogui
import pywhatkit as kit
import pvporcupine
import requests
from engine.command import speak
from engine.config import ASSISTANT_NAME
from engine.helper import extract_yt_term, remove_words
from hugchat import hugchat

# Add the directory containing the 'engine' module to the Python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

con = sqlite3.connect("jarvis.db")
cursor = con.cursor()

@eel.expose
def playAssistantSound():
    music_dir = "www\\assets\\audio\\start_sound.mp3"
    playsound(music_dir)

def openCommand(query):
    query = query.replace(ASSISTANT_NAME, "").replace("open", "").strip().lower()
    if query:
        try:
            cursor.execute('SELECT path FROM sys_command WHERE name = ?', (query,))
            results = cursor.fetchall()

            if results:
                speak(f"Opening {query}")
                os.startfile(results[0][0])
            else:
                cursor.execute('SELECT url FROM web_command WHERE name = ?', (query,))
                results = cursor.fetchall()

                if results:
                    speak(f"Opening {query}")
                    webbrowser.open(results[0][0])
                else:
                    speak(f"Opening {query}")
                    try:
                        os.system(f'start {query}')
                    except:
                        speak("Command not found")
        except Exception as e:
            speak("Something went wrong")
            print(e)

def PlayYoutube(query):
    search_term = extract_yt_term(query)
    try:
        # Check internet connection
        requests.get("https://google.com")
        speak(f"Playing {search_term} on YouTube")
        kit.playonyt(search_term)
    except requests.ConnectionError:
        speak("Error while connecting to the Internet. Make sure you are connected to the Internet!")

def hotword():
    porcupine = None
    paud = None
    audio_stream = None
    try:
        # Pre-trained keywords    
        porcupine = pvporcupine.create(keywords=["spark", "alexa"])
        paud = pyaudio.PyAudio()
        audio_stream = paud.open(rate=porcupine.sample_rate, channels=1, format=pyaudio.paInt16, input=True, frames_per_buffer=porcupine.frame_length)

        # Loop for streaming
        while True:
            keyword = audio_stream.read(porcupine.frame_length)
            keyword = struct.unpack_from("h" * porcupine.frame_length, keyword)

            # Processing keyword comes from mic 
            keyword_index = porcupine.process(keyword)

            # Checking first keyword detected for not
            if keyword_index >= 0:
                print("Hotword detected")

                # Pressing shortcut key win+j
                pyautogui.keyDown("win")
                pyautogui.press("j")
                time.sleep(2)
                pyautogui.keyUp("win")

    except Exception as e:
        print(e)
    finally:
        if porcupine is not None:
            porcupine.delete()
        if audio_stream is not None:
            audio_stream.close()
        if paud is not None:
            paud.terminate()

def findContact(query):
    words_to_remove = [ASSISTANT_NAME, 'make', 'a', 'to', 'phone', 'call', 'send', 'message', 'whatsapp', 'video']
    query = remove_words(query, words_to_remove).strip().lower()

    try:
        cursor.execute("SELECT mobile_no FROM contacts WHERE LOWER(name) LIKE ? OR LOWER(name) LIKE ?", ('%' + query + '%', query + '%'))
        results = cursor.fetchall()

        if results:
            mobile_number_str = str(results[0][0])
            if not mobile_number_str.startswith('+91'):
                mobile_number_str = '+91' + mobile_number_str

            return mobile_number_str, query
        else:
            speak('Contact not found')
            return 0, 0
    except Exception as e:
        speak('An error occurred while searching contacts')
        print(e)
        return 0, 0

def whatsApp(mobile_no, message, flag, name):
    if flag == 'message':
        target_tab = 12
        jarvis_message = f"Message sent successfully to {name}"
    elif flag == 'call':
        target_tab = 7
        message = ''
        jarvis_message = f"Calling {name}"
    else:
        target_tab = 6
        message = ''
        jarvis_message = f"Starting video call with {name}"

    # Encode the message for URL
    encoded_message = shlex.quote(message)

    # Construct the URL
    whatsapp_url = f"whatsapp://send?phone={mobile_no}&text={encoded_message}"

    # Construct the full command
    full_command = f'start "" "{whatsapp_url}"'

    try:
        # Check internet connection
        requests.get("https://google.com")
        subprocess.run(full_command, shell=True)
        time.sleep(5)
        subprocess.run(full_command, shell=True)
        pyautogui.hotkey('ctrl', 'f')
        for _ in range(target_tab):
            pyautogui.hotkey('tab')
        pyautogui.hotkey('enter')
        speak(jarvis_message)
    except requests.ConnectionError:
        speak("Error while connecting to the Internet. Make sure you are connected to the Internet!")
    except Exception as e:
        speak("An error occurred while sending WhatsApp message")
        print(e)

def chatBot(query):
    user_input = query.lower()
    chatbot = hugchat.ChatBot(cookie_path=r"engine\cookies.json")
    id = chatbot.new_conversation()
    chatbot.change_conversation(id)
    try:
        response = chatbot.chat(user_input)
        print(response)
        speak(response)
        return response
    except requests.ConnectionError:
        speak("Error while connecting to the Internet. Make sure you are connected to the Internet!")
    except Exception as e:
        speak("An error occurred while chatting")
        print(e)

def makeCall(name, mobileNo):
    mobileNo = mobileNo.replace(" ", "")
    speak(f"Calling {name}")
    command = f'adb shell am start -a android.intent.action.CALL -d tel:{mobileNo}'
    os.system(command)

def sendMessage(message, mobileNo, name):
    from engine.helper import replace_spaces_with_percent_s, goback, keyEvent, tapEvents, adbInput
    message = replace_spaces_with_percent_s(message)
    mobileNo = replace_spaces_with_percent_s(mobileNo)
    speak("Sending message")
    goback(4)
    time.sleep(1)
    keyEvent(3)
    # Open SMS app
    tapEvents(136, 2220)
    # Start chat
    tapEvents(819, 2192)
    # Search mobile number
    adbInput(mobileNo)
    # Tap on name
    tapEvents(601, 574)
    # Tap on input
    tapEvents(390, 2270)
    # Enter message
    adbInput(message)
    # Send message
    tapEvents(957, 1397)
    speak(f"Message sent successfully to {name}")
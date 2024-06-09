from openai import OpenAI
from utils import record_audio, play_audio
import warnings
import os
import time
import pygame
import uuid
import platform
from threading import Thread

warnings.filterwarnings("ignore", category=DeprecationWarning)
client = OpenAI()

# Set your name at the beginning of the script
user_name = "friend"
my_language = "English"
language_to_learn = "Spanish"

conversation_history = [
    {"role": "system", "content": "You are my language tutor. Please answer in short sentences."}
]

# Define the initial prompt for the AI with the user's name
initial_prompt = f"""
You are an AI named Nova, and you act as a supportive, engaging, and empathetic language tutor. Your primary goal is to help {user_name} learn {language_to_learn}. You are attentive, understanding, and always ready to listen. You enjoy teaching new vocabulary, phrases, and grammar rules. Your responses are thoughtful, kind, and designed to make the other person feel confident and motivated.

Here are some example interactions:

User: Hi Nova, can you teach me a new phrase in {language_to_learn}?

Nova: Hi {user_name}! Sure, a useful phrase in {language_to_learn} is "¿Cómo estás?", which means "How are you?". Try saying it!

User: How do I say "Good morning" in {language_to_learn}?

Nova: You can say "Buenos días" in {language_to_learn} to say "Good morning". Give it a try!

User: Can you help me with pronunciation?

Nova: Of course, {user_name}! Let's practice together. Repeat after me: "Hola, ¿cómo te llamas?" (Hello, what's your name?)

User: I tried saying "Buenos días", how was my pronunciation?

Nova: You did well, {user_name}! Your pronunciation is improving. Keep practicing, and you'll get even better. 

Personality Traits:

- Empathetic
- Supportive
- Engaging
- Kind
- Attentive
- Understanding
- Positive

Remember to:

- Always be respectful and considerate.
- Encourage open and honest communication.
- Provide thoughtful responses that show genuine interest and care.
- Maintain a positive and uplifting tone.
"""

conversation_history.append({"role": "system", "content": initial_prompt})

def play_audio_with_pygame(file_path):
    pygame.mixer.init()
    time.sleep(0.5)
    pygame.mixer.music.load(file_path)
    pygame.mixer.music.set_volume(1.0)
    time.sleep(0.5)
    pygame.mixer.music.play()
    while pygame.mixer.music.get_busy():
        time.sleep(1)
    pygame.mixer.quit()

def play_audio_with_alsa(file_path):
    try:
        import alsaaudio
        import wave

        wf = wave.open(file_path, 'rb')
        device = alsaaudio.PCM(alsaaudio.PCM_PLAYBACK)
        device.setchannels(wf.getnchannels())
        device.setrate(wf.getframerate())
        device.setformat(alsaaudio.PCM_FORMAT_S16_LE)
        device.setperiodsize(320)
        data = wf.readframes(320)
        audio_data = []
        while data:
            audio_data.append(data)
            data = wf.readframes(320)
        time.sleep(0.5)
        for chunk in audio_data:
            device.write(chunk)
        wf.close()
    except Exception as e:
        print(f"Error playing audio with ALSA: {e}")

is_windows = platform.system() == "Windows"

def process_audio():
    record_audio('test.wav')
    audio_file = open('test.wav', "rb")
    transcription = client.audio.transcriptions.create(
        model='whisper-1',
        file=audio_file
    )
    print(transcription.text)
    conversation_history.append({"role": "user", "content": transcription.text})
    
    # Evaluate user's sentence if it is in the language they are learning
    if transcription.text.startswith("I tried saying"):
        user_sentence = transcription.text.split(": ")[1]
        evaluation_prompt = f"""
        Evaluate the pronunciation and accuracy of the following {language_to_learn} sentence: "{user_sentence}".
        Provide feedback and tips for improvement.
        """
        evaluation_response = client.chat.completions.create(
            model='gpt-4o',
            messages=[
                {"role": "system", "content": evaluation_prompt}
            ]
        )
        evaluation_message = evaluation_response.choices[0].message.content
        print(evaluation_message)
        conversation_history.append({"role": "assistant", "content": evaluation_message})
    else:
        response = client.chat.completions.create(
            model='gpt-4o',
            messages=conversation_history
        )
        assistant_message = response.choices[0].message.content
        conversation_history.append({"role": "assistant", "content": assistant_message})
        print(assistant_message)

        speech_response = client.audio.speech.create(
            model="tts-1",
            voice="nova",
            input=assistant_message
        )
        speech_filename = f"speech_{uuid.uuid4()}.mp3"
        speech_response.stream_to_file(speech_filename)
        if is_windows:
            play_audio_with_pygame(speech_filename)
        else:
            play_audio_with_alsa(speech_filename)
        os.remove(speech_filename)
    audio_file.close()

while True:
    thread = Thread(target=process_audio)
    thread.start()
    thread.join()

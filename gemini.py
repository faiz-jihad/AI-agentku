# ==================== JARVIS FINAL - ASISTEN AI LENGKAP ====================
# Fitur: Gemini AI, Spotify, PowerPoint, Suara Cowok/Cewek, Website, Wikipedia

from google import genai
from google.genai import types
import pyttsx3
import webbrowser
import smtplib
import random
import speech_recognition as sr
import wolframalpha
import wikipediaapi as wikipedia
import datetime
import os
import sys
import json
import subprocess
import requests
from typing import Dict, List, Any, Optional
import re
import time
import threading
from gtts import gTTS
import pygame
import tempfile
import logging
import urllib.parse
import win32com.client
import pythoncom
import keyboard
import glob

# ==================== KONFIGURASI ====================
class Config:
    MAX_HISTORY = 50
    VOICE_RATE = 180
    VOICE_VOLUME = 0.9
    LISTEN_TIMEOUT = 5

# ==================== API KEYS ====================
GEMINI_API_KEY = "AIzaSyBTleQ1UB2X7BOLC6nSbKXoIosrGR9yL1Y"
WOLFRAM_ALPHA_ID = 'V388XY-YEUE7YTQKW'

# ==================== INISIALISASI GEMINI CLIENT ====================
try:
    client = genai.Client(api_key=GEMINI_API_KEY)
    print("✓ Gemini Client initialized")
except Exception as e:
    print(f"❌ Error initializing Gemini: {e}")
    client = None

# ==================== CEK MODEL GEMINI ====================
def check_available_models():
    if not client:
        return []
    try:
        models = client.models.list()
        print("\n📋 Model Gemini yang tersedia:")
        gemini_models = []
        for model in models:
            model_name = model.name.replace('models/', '')
            if 'gemini' in model_name.lower():
                gemini_models.append(model_name)
                print(f"  - {model_name}")
        return gemini_models
    except Exception as e:
        print(f"❌ Error checking models: {e}")
        return []

AVAILABLE_MODELS = check_available_models()
PREFERRED_MODELS = ["gemini-1.5-flash", "gemini-1.5-pro", "gemini-2.0-flash-exp"]

MODEL_NAME = None
for preferred in PREFERRED_MODELS:
    if preferred in AVAILABLE_MODELS:
        MODEL_NAME = preferred
        break

if not MODEL_NAME and AVAILABLE_MODELS:
    MODEL_NAME = AVAILABLE_MODELS[0]
if not MODEL_NAME:
    MODEL_NAME = 'gemini-2.0-flash-exp'
    print(f"⚠️ Menggunakan model default: {MODEL_NAME}")

print(f"\n✅ Menggunakan model Gemini: {MODEL_NAME}")

# ==================== WOLFRAM ALPHA ====================
try:
    wolfram_client = wolframalpha.Client(WOLFRAM_ALPHA_ID)
    print("✓ Wolfram Alpha terhubung")
except Exception as e:
    print(f"⚠️ Error Wolfram Alpha: {e}")
    wolfram_client = None

# ==================== SETUP LOGGING ====================
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger("JarvisFinal")

# ==================== SPOTIFY CONTROLLER ====================
# ==================== SPOTIFY CONTROLLER (UNTUK APLIKASI DESKTOP) ====================
class SpotifyController:
    """Kelas untuk mengontrol Spotify Desktop App"""
    
    def __init__(self):
        self.is_running = False
        self.spotify_path = self.find_spotify_path()
        self.spotify_uri_scheme = "spotify:"  # URI scheme untuk Spotify
        
    def find_spotify_path(self):
        """Mencari lokasi instalasi Spotify desktop"""
        
        # Path Spotify Anda (WindowsApps)
        user_path = r"C:\Users\LENOVO\AppData\Local\Microsoft\WindowsApps\Spotify.exe"
        
        if os.path.exists(user_path):
            print(f"✓ Spotify Desktop ditemukan di: {user_path}")
            return user_path
        
        # Path umum lainnya
        common_paths = [
            os.path.expandvars(r"%APPDATA%\Spotify\Spotify.exe"),
            os.path.expandvars(r"%LOCALAPPDATA%\Spotify\Spotify.exe"),
            r"C:\Program Files\Spotify\Spotify.exe",
            r"C:\Program Files (x86)\Spotify\Spotify.exe",
        ]
        
        for path in common_paths:
            if os.path.exists(path):
                print(f"✓ Spotify Desktop ditemukan di: {path}")
                return path
        
        print("⚠️ Spotify Desktop tidak ditemukan")
        return None
    
    def open_spotify_app(self):
        """Membuka aplikasi Spotify desktop"""
        try:
            if self.spotify_path and os.path.exists(self.spotify_path):
                # Buka aplikasi Spotify
                os.startfile(self.spotify_path)
                self.is_running = True
                time.sleep(3)  # Tunggu Spotify terbuka
                return True, "Membuka aplikasi Spotify"
            else:
                # Fallback ke web
                webbrowser.open('https://open.spotify.com')
                return True, "Spotify desktop tidak ditemukan, membuka web version"
        except Exception as e:
            return False, f"Gagal membuka Spotify: {e}"
    
    def play_song_in_app(self, song_name):
        """Memutar lagu langsung di aplikasi Spotify desktop"""
        try:
            # Pastikan Spotify berjalan
            if not self.is_running:
                self.open_spotify_app()
            
            # Format pencarian untuk Spotify URI
            # spotify:search:lagu
            search_uri = f"spotify:search:{urllib.parse.quote(song_name)}"
            
            # Buka di aplikasi Spotify melalui URI
            webbrowser.open(search_uri)
            time.sleep(2)  # Tunggu hasil pencarian
            
            # Tekan Enter untuk memutar lagu pertama
            keyboard.press_and_release('enter')
            
            return True, f"Memutar {song_name} di aplikasi Spotify"
        except Exception as e:
            # Fallback ke web
            webbrowser.open(f"https://open.spotify.com/search/{urllib.parse.quote(song_name)}")
            return True, f"Mencari {song_name} di Spotify Web"
    
    def play_playlist_in_app(self, playlist_name, playlist_id):
        """Memutar playlist di aplikasi Spotify"""
        try:
            playlist_uri = f"spotify:playlist:{playlist_id}"
            webbrowser.open(playlist_uri)
            time.sleep(2)
            
            # Klik play
            keyboard.press_and_release('enter')
            
            return True, f"Memutar playlist {playlist_name}"
        except:
            webbrowser.open(f"https://open.spotify.com/playlist/{playlist_id}")
            return True, f"Membuka playlist {playlist_name} di web"
    
    def control_playback(self, command):
        """Kontrol pemutaran (play/pause/next/prev)"""
        try:
            if command == "play":
                keyboard.press_and_release('space')
                return "Memutar"
            elif command == "pause":
                keyboard.press_and_release('space')
                return "Menjeda"
            elif command == "next":
                keyboard.press_and_release('ctrl+right')
                return "Lagu berikutnya"
            elif command == "previous":
                keyboard.press_and_release('ctrl+left')
                return "Lagu sebelumnya"
            elif command == "volume_up":
                for _ in range(5):
                    keyboard.press_and_release('ctrl+up')
                return "Volume naik"
            elif command == "volume_down":
                for _ in range(5):
                    keyboard.press_and_release('ctrl+down')
                return "Volume turun"
        except:
            return None
        
# ==================== POWERPOINT CONTROLLER ====================
class PowerPointController:
    """Kelas untuk mengontrol PowerPoint"""
    
    def __init__(self):
        self.application = None
        self.presentation = None
        self.slide_index = 0
        self.total_slides = 0
        self.is_connected = False
        self.ppt_running = False
        self.slide_show = None
        self.slide_show_window = None
        self.use_com = True
        
    def connect_to_powerpoint(self):
        """Connect ke PowerPoint"""
        try:
            pythoncom.CoInitialize()
            self.application = win32com.client.GetActiveObject("PowerPoint.Application")
            self.is_connected = True
            print("✓ Terhubung ke PowerPoint")
            
            if self.application.Presentations.Count > 0:
                self.presentation = self.application.ActivePresentation
                self.total_slides = self.presentation.Slides.Count
                print(f"✓ Presentation aktif: {self.total_slides} slide")
                
                if self.application.SlideShowWindows.Count > 0:
                    self.slide_show = self.application.SlideShowWindows(1)
                    self.slide_show_window = self.slide_show.View
                    self.ppt_running = True
                    self.slide_index = self.slide_show.View.CurrentShowPosition
            return True
        except Exception as e:
            print(f"❌ Error: {e}")
            return False
    
    def next_slide(self):
        if not self.ppt_running:
            return False
        try:
            self.slide_show_window.Next()
            self.slide_index = self.slide_show_window.CurrentShowPosition
            return True
        except:
            return False
    
    def previous_slide(self):
        if not self.ppt_running:
            return False
        try:
            self.slide_show_window.Previous()
            self.slide_index = self.slide_show_window.CurrentShowPosition
            return True
        except:
            return False
    
    def start_slideshow(self):
        if not self.presentation:
            return False
        try:
            self.slide_show = self.presentation.SlideShowSettings.Run()
            self.slide_show_window = self.slide_show.View
            self.ppt_running = True
            self.slide_index = 1
            return True
        except:
            return False
    
    def end_slideshow(self):
        if not self.slide_show:
            return False
        try:
            self.slide_show.Exit()
            self.ppt_running = False
            return True
        except:
            return False

# ==================== VOICE HANDLER ====================
class VoiceHandler:
    def __init__(self):
        self.recognizer = sr.Recognizer()
        self.setup_microphone()
        self.setup_tts()
        self.setup_pygame()
        self.voice_enabled = True
        self.listening = False
        self.use_google_voice = True
        self.voice_gender = "male"
    
    def setup_microphone(self):
        try:
            self.microphone = sr.Microphone()
            with self.microphone as source:
                print("✓ Microphone berhasil diinisialisasi")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
        except Exception as e:
            print(f"⚠️ Error microphone: {e}")
            self.microphone = None
    
    def setup_tts(self):
        try:
            self.tts_engine = pyttsx3.init('sapi5')
            self.set_voice_properties()
        except:
            try:
                self.tts_engine = pyttsx3.init()
                self.set_voice_properties()
            except Exception as e:
                print(f"⚠️ Error TTS: {e}")
                self.tts_engine = None
    
    def setup_pygame(self):
        try:
            pygame.mixer.init()
        except:
            pass
    
    def set_voice_properties(self):
        if not self.tts_engine:
            return
        try:
            self.tts_engine.setProperty('rate', Config.VOICE_RATE)
            self.tts_engine.setProperty('volume', Config.VOICE_VOLUME)
            
            voices = self.tts_engine.getProperty('voices')
            selected_voice = None
            
            if self.voice_gender == "male":
                male_keywords = ['male', 'man', 'david', 'mark']
                for voice in voices:
                    if any(k in voice.name.lower() for k in male_keywords):
                        selected_voice = voice
                        break
            else:
                female_keywords = ['female', 'woman', 'zira', 'hazel']
                for voice in voices:
                    if any(k in voice.name.lower() for k in female_keywords):
                        selected_voice = voice
                        break
            
            if not selected_voice and voices:
                selected_voice = voices[0]
            
            if selected_voice:
                self.tts_engine.setProperty('voice', selected_voice.id)
                print(f"✓ Suara: {selected_voice.name}")
        except:
            pass
    
    def set_voice_gender(self, gender):
        if gender in ['male', 'cowok', 'pria']:
            self.voice_gender = "male"
            self.set_voice_properties()
            return "Suara cowok aktif"
        elif gender in ['female', 'cewek', 'wanita']:
            self.voice_gender = "female"
            self.set_voice_properties()
            return "Suara cewek aktif"
        return "Pilih male/female"
    
    def speak_google(self, text):
        if not self.voice_enabled:
            return
        clean_text = re.sub(r'[*_`#]', '', text)
        print(f'🤖 [Google] {clean_text}')
        try:
            tts = gTTS(text=clean_text, lang='id', slow=False)
            with tempfile.NamedTemporaryFile(delete=False, suffix='.mp3') as f:
                temp_filename = f.name
            tts.save(temp_filename)
            pygame.mixer.music.load(temp_filename)
            pygame.mixer.music.play()
            while pygame.mixer.music.get_busy():
                pygame.time.wait(100)
            pygame.mixer.music.unload()
            os.unlink(temp_filename)
        except:
            self.speak_pyttsx3(text)
    
    def speak_pyttsx3(self, text):
        if not self.voice_enabled or not self.tts_engine:
            print(f'🤖 {text}')
            return
        clean_text = re.sub(r'[*_`#]', '', text)
        print(f'🤖 [Lokal] {clean_text}')
        try:
            if len(clean_text) > 500:
                parts = self.split_text(clean_text, 500)
                for part in parts:
                    self.tts_engine.say(part)
                    self.tts_engine.runAndWait()
            else:
                self.tts_engine.say(clean_text)
                self.tts_engine.runAndWait()
        except:
            pass
    
    def speak(self, text):
        if self.use_google_voice:
            try:
                requests.get("http://www.google.com", timeout=3)
                self.speak_google(text)
            except:
                self.speak_pyttsx3(text)
        else:
            self.speak_pyttsx3(text)
    
    def split_text(self, text, max_length):
        sentences = re.split(r'[.!?]+', text)
        parts = []
        current = ""
        for s in sentences:
            s = s.strip()
            if not s:
                continue
            if len(current) + len(s) < max_length:
                current += s + ". "
            else:
                if current:
                    parts.append(current)
                current = s + ". "
        if current:
            parts.append(current)
        return parts

# ==================== SPEECH RECOGNITION ====================
def listen_command(timeout=5) -> str:
    r = sr.Recognizer()
    try:
        with sr.Microphone() as source:
            print("\n🎤 Listening...")
            r.pause_threshold = 1
            r.adjust_for_ambient_noise(source, duration=0.5)
            audio = r.listen(source, timeout=timeout, phrase_time_limit=10)
        
        print("🔄 Processing...")
        
        try:
            query = r.recognize_google(audio, language='id-ID')
            print(f'👤 User (ID): {query}')
            return query.lower()
        except:
            query = r.recognize_google(audio)
            print(f'👤 User: {query}')
            return query.lower()
                
    except sr.WaitTimeoutError:
        return ""
    except Exception as e:
        print(f"❌ Error: {e}")
        return ""

# ==================== LINK GENERATOR ====================
class LinkGenerator:
    @staticmethod
    def generate_youtube_link(query):
        return f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
    
    @staticmethod
    def generate_google_search(query):
        return f"https://www.google.com/search?q={urllib.parse.quote(query)}"
    
    @staticmethod
    def generate_google_maps(query):
        return f"https://www.google.com/maps/search/{urllib.parse.quote(query)}"

# ==================== GEMINI AGENT ====================
class GeminiAgent:
    def __init__(self, voice_handler):
        self.client = client
        self.model = MODEL_NAME
        self.voice = voice_handler
        self.conversation_history = []
        self.max_history = Config.MAX_HISTORY
        self.link_gen = LinkGenerator()
    
    def generate_response(self, user_input: str) -> Dict[str, Any]:
        self.conversation_history.append({"role": "user", "content": user_input})
        
        response = {"text": "", "link": None, "action": None}
        
        if 'youtube' in user_input:
            video = user_input.replace('buka', '').replace('video', '').replace('youtube', '').strip()
            response["link"] = self.link_gen.generate_youtube_link(video)
            response["text"] = f"Mencari {video} di YouTube"
            response["action"] = "open_link"
        elif 'cari' in user_input or 'search' in user_input:
            search = user_input.replace('cari', '').replace('search', '').strip()
            response["link"] = self.link_gen.generate_google_search(search)
            response["text"] = f"Mencari {search} di Google"
            response["action"] = "open_link"
        elif 'maps' in user_input or 'peta' in user_input:
            location = user_input.replace('maps', '').replace('peta', '').strip()
            response["link"] = self.link_gen.generate_google_maps(location)
            response["text"] = f"Membuka peta {location}"
            response["action"] = "open_link"
        else:
            system_prompt = f"""Kamu adalah Jarvis, asisten AI yang ramah. 
            Jawab dalam bahasa Indonesia.
            Recent: {self.format_history()}"""
            
            full_prompt = f"{system_prompt}\n\nUser: {user_input}\nAssistant:"
            
            try:
                gemini_response = self.client.models.generate_content(
                    model=self.model,
                    contents=full_prompt,
                    config=types.GenerateContentConfig(temperature=0.7)
                )
                response["text"] = gemini_response.text
                response["action"] = "speak"
            except Exception as e:
                response["text"] = f"Maaf, error: {str(e)}"
                response["action"] = "speak"
        
        self.conversation_history.append({"role": "assistant", "content": response["text"]})
        return response
    
    def format_history(self) -> str:
        return "\n".join([f"{m['role']}: {m['content'][:50]}..." for m in self.conversation_history[-3:]])

# ==================== FUNGSI UTAMA ====================
def greet_user():
    h = datetime.datetime.now().hour
    if h < 12:
        return 'Selamat pagi'
    elif h < 18:
        return 'Selamat siang'
    else:
        return 'Selamat malam'

def process_commands(query: str, voice: VoiceHandler, 
                    ppt: PowerPointController = None,
                    spotify: SpotifyController = None):
    
    # ===== SPOTIFY  =====
    if spotify and ('spotify' in query or 'musik' in query or 'lagu' in query or 'play' in query):
    
    # Buka aplikasi Spotify
        if 'buka spotify' in query or 'open spotify' in query:
            success, msg = spotify.open_spotify_app()
        voice.speak(msg)
        return True
    
    # Putar lagu
    elif 'play' in query or 'putar' in query:
        # Ekstrak judul lagu
        song = query.replace('play', '').replace('putar', '').replace('lagu', '').replace('musik', '').strip()
        
        if song:
            voice.speak(f"Memutar {song} di aplikasi Spotify")
            # Panggil fungsi khusus untuk app
            success, msg = spotify.play_song_in_app(song)
            voice.speak(msg)
        else:
            # Jika hanya "play" tanpa judul, buka Spotify app
            spotify.open_spotify_app()
        return True
    
    # Cari lagu (LANGSUNG DI APP!)
    elif 'cari lagu' in query or 'search lagu' in query:
        song = query.replace('cari lagu', '').replace('search lagu', '').strip()
        if song:
            voice.speak(f"Mencari {song} di aplikasi Spotify")
            webbrowser.open(f"spotify:search:{urllib.parse.quote(song)}")
        return True
    
    # Playlist Indonesia (LANGSUNG DI APP!)
    elif 'playlist indonesia' in query or 'lagu indonesia' in query:
        voice.speak("Memutar playlist Indonesia")
        spotify.play_playlist_in_app("Indonesia", "37i9dQZF1DX4o1oenSJRJd")
        return True
    
    # Top 50 Indonesia
    elif 'top 50' in query or 'trending' in query:
        voice.speak("Memutar Top 50 Indonesia")
        spotify.play_playlist_in_app("Top 50", "37i9dQZF1DXdPec7aLTmlC")
        return True
    
    # Kontrol pemutaran (untuk Spotify app)
    elif 'pause' in query or 'jeda' in query:
        result = spotify.control_playback("pause")
        voice.speak(result or "Menjeda musik")
        return True
    
    elif 'play' in query and len(query) < 10:  # "play" saja tanpa judul
        result = spotify.control_playback("play")
        voice.speak(result or "Memutar")
        return True
    
    elif 'next' in query or 'skip' in query or 'berikutnya' in query:
        result = spotify.control_playback("next")
        voice.speak(result or "Lagu berikutnya")
        return True
    
    elif 'previous' in query or 'kembali' in query:
        result = spotify.control_playback("previous")
        voice.speak(result or "Lagu sebelumnya")
        return True
    
    elif 'volume up' in query or 'volume naik' in query:
        result = spotify.control_playback("volume_up")
        voice.speak(result or "Volume naik")
        return True
    
    elif 'volume down' in query or 'volume turun' in query:
        result = spotify.control_playback("volume_down")
        voice.speak(result or "Volume turun")
        return True
    
    # ===== POWERPOINT COMMANDS =====
    if ppt and ppt.use_com:
        if 'jarvis konek' in query:
            if ppt.connect_to_powerpoint():
                voice.speak("Terhubung ke PowerPoint")
            else:
                voice.speak("Gagal terhubung")
            return True
        elif 'jarvis maju' in query:
            if ppt.next_slide():
                voice.speak(f"Slide {ppt.slide_index}")
            else:
                voice.speak("Gagal")
            return True
        elif 'jarvis mundur' in query:
            if ppt.previous_slide():
                voice.speak(f"Slide {ppt.slide_index}")
            else:
                voice.speak("Gagal")
            return True
        elif 'jarvis mulai' in query:
            if ppt.start_slideshow():
                voice.speak("Memulai presentasi")
            else:
                voice.speak("Gagal")
            return True
        elif 'jarvis akhir' in query:
            if ppt.end_slideshow():
                voice.speak("Mengakhiri")
            else:
                voice.speak("Gagal")
            return True
    
    # ===== VOICE GENDER =====
    if 'suara cowok' in query:
        voice.speak(voice.set_voice_gender("male"))
        return True
    if 'suara cewek' in query:
        voice.speak(voice.set_voice_gender("female"))
        return True
    
    # ===== WEBSITES =====
    websites = {
        'youtube': 'https://youtube.com',
        'google': 'https://google.com',
        'gmail': 'https://gmail.com',
        'facebook': 'https://facebook.com',
        'instagram': 'https://instagram.com',
        'twitter': 'https://twitter.com',
        'github': 'https://github.com'
    }
    
    for site, url in websites.items():
        if f'buka {site}' in query or f'open {site}' in query:
            voice.speak(f'Membuka {site}')
            webbrowser.open(url)
            return True
    
    # ===== TIME =====
    if 'jam berapa' in query or 'time' in query:
        now = datetime.datetime.now().strftime('%H:%M')
        voice.speak(f'Sekarang jam {now}')
        return True
    
    # ===== WIKIPEDIA =====
    if 'apa itu' in query or 'siapa itu' in query:
        topic = query.replace('apa itu', '').replace('siapa itu', '').strip()
        try:
            result = wikipedia.summary(topic, sentences=2)
            voice.speak(result)
        except:
            voice.speak(f"Tidak menemukan {topic}")
        return True
    
    # ===== WOLFRAM =====
    if 'hitung' in query or 'calculate' in query:
        if wolfram_client:
            try:
                res = wolfram_client.query(query)
                answer = next(res.results).text
                voice.speak(f"Hasil: {answer}")
            except:
                voice.speak("Tidak bisa menghitung")
        return True
    
    # ===== EXIT =====
    if any(k in query for k in ['bye', 'exit', 'keluar', 'dadah']):
        voice.speak('Sampai jumpa!')
        return 'exit'
    
    return False

# ==================== MAIN PROGRAM ====================
def main():
    voice = VoiceHandler()
    gemini = GeminiAgent(voice)
    ppt = PowerPointController()
    spotify = SpotifyController()
    
    print("\n" + "="*90)
    print("🤖 JARVIS FINAL - ASISTEN AI LENGKAP")
    print("="*90)
    print(f"Model Gemini: {MODEL_NAME}")
    print("\n🎵 SPOTIFY:")
    print("  • 'buka spotify'    • 'play [lagu]'    • 'pause/next'")
    print("\n📊 POWERPOINT:")
    print("  • 'jarvis konek'    • 'jarvis maju'    • 'jarvis mundur'")
    print("\n🎤 SUARA:")
    print("  • 'suara cowok'      • 'suara cewek'")
    print("\n🌐 WEBSITE:")
    print("  • 'buka youtube'     • 'buka google'    • 'buka gmail'")
    print("\n📚 LAINNYA:")
    print("  • 'apa itu [topik]'  • 'jam berapa'     • 'hitung [rumus]'")
    print("="*90 + "\n")
    
    voice.set_voice_gender("male")
    voice.speak(f"Halo! Saya Jarvis. {greet_user()}!")
    
    if spotify.spotify_path:
        print(f"✓ Spotify siap")
    if ppt.use_com:
        print("✓ PowerPoint siap")
    
    while True:
        try:
            print("\n🎤 Perintah (Enter untuk voice):")
            use_voice = input("> ").strip()
            
            if use_voice == "":
                query = listen_command(timeout=5)
            else:
                query = use_voice.lower()
                print(f"👤 User: {query}")
            
            if not query:
                continue
            
            result = process_commands(query, voice, ppt, spotify)
            
            if result == 'exit':
                break
            elif result == True:
                pass
            else:
                print("🤖 Gemini...")
                response = gemini.generate_response(query)
                
                if response["action"] == "open_link" and response["link"]:
                    print(f"🔗 {response['link']}")
                    voice.speak(response["text"])
                    webbrowser.open(response["link"])
                else:
                    voice.speak(response["text"])
            
        except KeyboardInterrupt:
            voice.speak("Sampai jumpa!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            voice.speak("Error, coba lagi")

if __name__ == "__main__":
    main()
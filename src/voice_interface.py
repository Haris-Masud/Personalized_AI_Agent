# voice_interface.py

import os
import speech_recognition as sr
import tempfile
import time
import pygame
from gtts import gTTS

class VoiceInterface:
    def __init__(self, output_dir="generated_audio"):
        # Create output directory if it doesn't exist
        self.output_dir = output_dir
        os.makedirs(self.output_dir, exist_ok=True)
        
        # Initialize recognizer and microphone
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Initialize pygame for audio playback
        pygame.init()
        pygame.mixer.init()
        
        # For adaptive listening
        self.energy_threshold = 300  # Default energy threshold
        
        # Initialize first with ambient noise adjustment
        with self.microphone as source:
            print("Calibrating microphone...")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            self.energy_threshold = self.recognizer.energy_threshold * 1.2
            print(f"Energy threshold set to: {self.energy_threshold}")

    def text_to_speech_and_play(self, text, lang='en'):
        """Convert text to speech and play it immediately"""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix='.mp3', delete=False) as temp_file:
            temp_filename = temp_file.name
        
        # Generate speech
        tts = gTTS(text=text, lang=lang, slow=False)
        tts.save(temp_filename)
        
        # Play the audio
        pygame.mixer.music.load(temp_filename)
        pygame.mixer.music.play()
        
        # Wait for playback to finish
        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)
        
        # Clean up
        pygame.mixer.music.unload()
        os.unlink(temp_filename)
    
    def listen_from_mic_adaptive(self, min_silence_duration=4):
        """
        Improved adaptive listening function that better handles continuous speech
        and properly terminates after detecting silence.
        
        This version uses a single microphone context to prevent the 
        "already inside a context manager" error.
        """
        all_text = []
        speech_detected = False
        last_speech_time = 0
        current_time = time.time()
        listening_start_time = current_time
        
        print("Listening...")
        
        # Use a single microphone context
        with self.microphone as source:
            # Initial ambient noise adjustment
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            self.recognizer.energy_threshold = self.energy_threshold
            
            # Main listening loop
            while True:
                try:
                    # Listen with a timeout to allow for checking conditions
                    # Use a shorter timeout that's long enough to detect speech
                    # but short enough to regularly check for silence
                    audio = self.recognizer.listen(source, timeout=3.0, phrase_time_limit=10.0)
                    
                    # Try to recognize the speech
                    text = self.recognizer.recognize_google(audio)
                    if text:
                        print(f"Recognized: {text}")
                        all_text.append(text)
                        speech_detected = True
                        last_speech_time = time.time()
                        
                        # Check for terminate command immediately
                        if "bye" in " ".join(all_text).lower():
                            print("Terminate call command detected")
                            return " ".join(all_text)
                
                except sr.WaitTimeoutError:
                    # No speech detected during the timeout period
                    current_time = time.time()
                    
                    # If we've detected speech and now have silence for the minimum duration
                    if speech_detected and (current_time - last_speech_time >= min_silence_duration):
                        print(f"Detected {min_silence_duration}s silence after speech, finishing...")
                        return " ".join(all_text)
                    
                    # If we haven't detected any speech for a long time, provide feedback
                    if not speech_detected and (current_time - listening_start_time > 10):
                        print("No speech detected, continuing to listen...")
                        # Reset the start time to avoid repeated messages
                        listening_start_time = current_time
                
                except sr.UnknownValueError:
                    print("Speech detected but not recognized")
                    # If we've previously detected valid speech and silence has been long enough, finish listening.
                    if speech_detected and (time.time() - last_speech_time >= min_silence_duration):
                        print(f"Detected {min_silence_duration}s silence after speech, finishing...")
                        return " ".join(all_text)
                    if not speech_detected and (current_time - listening_start_time > 10):
                        print("No speech detected, continuing to listen...")
                        # Reset the start time to avoid repeated messages
                        listening_start_time = current_time
                    # Still update timestamp as speech was detected
                    # if speech_detected:
                    #     last_speech_time = time.time()



                
                except sr.RequestError as e:
                    print(f"Error with speech recognition service: {e}")
                    time.sleep(1)  # Avoid rapid retries on service failure
                
                except Exception as e:
                    print(f"Unexpected error in listen_from_mic_adaptive: {e}")
                    time.sleep(1)

    def listen_from_mic(self, timeout=5):
        """Legacy method - Listen to microphone input and return transcribed text"""
        with self.microphone as source:
            print("Adjusting for ambient noise...")
            self.recognizer.adjust_for_ambient_noise(source, duration=1)
            
            try:
                print("Listening...")
                audio = self.recognizer.listen(source, timeout=timeout)
                return self.recognizer.recognize_google(audio)
            except sr.WaitTimeoutError:
                return ""
            except sr.UnknownValueError:
                print("Could not understand audio")
                return ""
            except sr.RequestError as e:
                print(f"Recognition error: {e}")
                return ""

    def clear_audio_files(self):
        """Remove all generated audio files"""
        for filename in os.listdir(self.output_dir):
            file_path = os.path.join(self.output_dir, filename)
            try:
                if os.path.isfile(file_path):
                    os.unlink(file_path)
            except Exception as e:
                print(f"Error deleting {file_path}: {e}")


# voice_interface.py

import os
import pyaudio
import wave
import struct
import webrtcvad
import time
from collections import deque


class ImprovedVoiceInterface:
    def __init__(self):
        # Audio parameters
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000  # Sample rate required by webrtcvad
        self.CHUNK_DURATION_MS = 30  # Duration of each chunk in milliseconds
        self.CHUNK_SIZE = int(self.RATE * self.CHUNK_DURATION_MS / 1000)  # Chunk size in samples
        self.SILENCE_THRESHOLD = 500  # Audio level threshold to detect silence
        self.SILENCE_DURATION = 1.0  # Duration of silence to consider speech ended (seconds)
        
        # Initialize VAD
        self.vad = webrtcvad.Vad(3)  # Aggressiveness level 3 (0-3)
        
        # Initialize PyAudio
        self.audio = pyaudio.PyAudio()
        
        # Create a directory for temporary audio files if it doesn't exist
        os.makedirs("temp_audio", exist_ok=True)
        
    def clear_audio_files(self):
        """Clear temporary audio files"""
        for file in os.listdir("temp_audio"):
            if file.endswith(".wav"):
                os.remove(os.path.join("temp_audio", file))
    
    def calculate_energy(self, data):
        """Calculate audio energy using struct instead of audioop"""
        # Convert bytes to short integers
        shorts = struct.unpack(f"{len(data)//2}h", data)
        
        # Calculate RMS energy
        sum_squares = sum(s*s for s in shorts)
        return int((sum_squares / len(shorts)) ** 0.5) if shorts else 0
    
    def listen_from_mic_with_vad(self):
        """Listen from microphone with Voice Activity Detection"""
        print("Listening...")
        
        # Open stream
        stream = self.audio.open(
            format=self.FORMAT,
            channels=self.CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK_SIZE
        )
        
        # Variables for VAD
        frames = []
        is_speech = False
        silent_chunks = 0
        silent_chunks_threshold = int(self.SILENCE_DURATION * 1000 / self.CHUNK_DURATION_MS)
        
        # Buffer for storing audio context before speech detection
        pre_speech_buffer = deque(maxlen=10)  # Store ~300ms of audio before speech starts
        
        try:
            # Main listening loop
            while True:
                data = stream.read(self.CHUNK_SIZE, exception_on_overflow=False)
                pre_speech_buffer.append(data)
                
                # Check if this chunk contains speech
                try:
                    is_current_chunk_speech = self.vad.is_speech(data, self.RATE)
                except Exception as e:
                    # If VAD fails, fall back to energy-based detection
                    energy = self.calculate_energy(data)
                    is_current_chunk_speech = energy > self.SILENCE_THRESHOLD
                
                # State machine for speech detection
                if not is_speech and is_current_chunk_speech:
                    # Speech just started
                    is_speech = True
                    silent_chunks = 0
                    # Include the pre-speech buffer to capture the beginning of speech
                    frames.extend(list(pre_speech_buffer))
                    print("Speech detected, recording...")
                    
                elif is_speech:
                    # Continue recording
                    frames.append(data)
                    
                    # Check for silence
                    if not is_current_chunk_speech:
                        silent_chunks += 1
                        if silent_chunks >= silent_chunks_threshold:
                            # Enough silence has passed, end recording
                            print("Speech ended")
                            break
                    else:
                        # Reset silence counter
                        silent_chunks = 0
                
                # If we've been recording for too long, stop
                if is_speech and len(frames) > 1000:  # ~30 seconds
                    print("Maximum recording time reached")
                    break
                    
            # Close stream
            stream.stop_stream()
            stream.close()
            
            # If we didn't record any speech, return None
            if len(frames) == 0 or not is_speech:
                return None
            
            # Save audio to file
            audio_file = os.path.join("temp_audio", f"recording_{int(time.time())}.wav")
            self._save_audio(frames, audio_file)
            
            # Transcribe audio
            transcription = self._transcribe_audio(audio_file)
            return transcription
            
        except Exception as e:
            print(f"Error in voice recording: {e}")
            if 'stream' in locals() and stream.is_active():
                stream.stop_stream()
                stream.close()
            return None
    
    def _save_audio(self, frames, file_path):
        """Save audio frames to a WAV file"""
        wf = wave.open(file_path, 'wb')
        wf.setnchannels(self.CHANNELS)
        wf.setsampwidth(self.audio.get_sample_size(self.FORMAT))
        wf.setframerate(self.RATE)
        wf.writeframes(b''.join(frames))
        wf.close()
    
    def _transcribe_audio(self, audio_file):
        """Transcribe audio file using an API or local model"""
        try:
            # Use SpeechRecognition library with Google's API
            import speech_recognition as sr
            recognizer = sr.Recognizer()
            
            with sr.AudioFile(audio_file) as source:
                audio_data = recognizer.record(source)
                
                try:
                    result = recognizer.recognize_google(audio_data)
                    print(f"Google Speech Recognition result: {result}")
                    return result
                except sr.UnknownValueError:
                    print("Google Speech Recognition could not understand audio")
                    return "I couldn't understand that."
                except sr.RequestError as e:
                    print(f"Could not request results from Google Speech Recognition service; {e}")
                    return "Sorry, my speech recognition service is currently unavailable."
                    
        except Exception as e:
            print(f"Transcription error: {e}")
            return "I couldn't understand that."
    
    def text_to_speech_and_play(self, text):
        """Convert text to speech and play it"""
        # You can use your existing TTS code here
        pass
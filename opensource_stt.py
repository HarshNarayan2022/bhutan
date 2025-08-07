"""
Open Source Speech-to-Text using Vosk
Memory-optimized for 512MB deployments
"""
import os
import json
import wave
import tempfile
import subprocess
from typing import Optional, Dict, Any
import vosk
import soundfile as sf

class OpenSourceSTT:
    def __init__(self):
        self.model = None
        self.model_path = None
        self.rec = None
        self._initialize_model()
    
    def _initialize_model(self):
        """Initialize Vosk model with memory optimization"""
        try:
            # Check if we should skip STT in free tier mode
            if os.environ.get('SKIP_AI_MODELS') == '1' or os.environ.get('MEMORY_MODE') == 'free_tier':
                print("🔧 Skipping Vosk STT model loading - running in free tier mode")
                return
            
            # Try to use a lightweight Vosk model
            model_dir = "/tmp/vosk-model"
            
            # Check if model exists locally
            if not os.path.exists(model_dir):
                print("📥 Downloading lightweight Vosk model...")
                # Use a small English model (about 40MB)
                model_url = "https://alphacephei.com/vosk/models/vosk-model-small-en-us-0.15.zip"
                
                try:
                    import urllib.request
                    import zipfile
                    
                    # Download model
                    zip_path = "/tmp/vosk-model.zip"
                    urllib.request.urlretrieve(model_url, zip_path)
                    
                    # Extract model
                    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                        zip_ref.extractall("/tmp/")
                    
                    # Find the extracted model directory
                    for item in os.listdir("/tmp/"):
                        if item.startswith("vosk-model-small-en-us"):
                            os.rename(f"/tmp/{item}", model_dir)
                            break
                    
                    # Clean up
                    os.remove(zip_path)
                    print("✅ Vosk model downloaded and extracted")
                    
                except Exception as e:
                    print(f"⚠️ Failed to download Vosk model: {e}")
                    return
            
            # Initialize Vosk model
            if os.path.exists(model_dir):
                vosk.SetLogLevel(-1)  # Reduce logging
                self.model = vosk.Model(model_dir)
                print("✅ Vosk STT model loaded successfully")
            else:
                print("⚠️ Vosk model directory not found")
                
        except Exception as e:
            print(f"⚠️ Failed to initialize Vosk STT: {e}")
            self.model = None
    
    def is_available(self) -> bool:
        """Check if STT is available"""
        return self.model is not None
    
    def convert_audio_format(self, input_path: str, output_path: str) -> bool:
        """Convert audio to WAV format required by Vosk"""
        try:
            # Use soundfile to convert audio
            data, samplerate = sf.read(input_path)
            
            # Ensure mono and 16kHz for optimal Vosk performance
            if len(data.shape) > 1:
                data = data.mean(axis=1)  # Convert to mono
            
            # Resample to 16kHz if needed
            if samplerate != 16000:
                # Simple resampling (for production, use proper resampling)
                import numpy as np
                from scipy import signal
                
                # Calculate resampling ratio
                ratio = 16000 / samplerate
                new_length = int(len(data) * ratio)
                data = signal.resample(data, new_length)
                samplerate = 16000
            
            # Save as WAV
            sf.write(output_path, data, samplerate, format='WAV')
            return True
            
        except Exception as e:
            print(f"Audio conversion error: {e}")
            # Fallback: try using ffmpeg if available
            try:
                cmd = [
                    'ffmpeg', '-i', input_path, 
                    '-ar', '16000', '-ac', '1', '-f', 'wav', 
                    output_path, '-y'
                ]
                result = subprocess.run(cmd, capture_output=True, timeout=30)
                return result.returncode == 0
            except Exception as ffmpeg_error:
                print(f"FFmpeg conversion also failed: {ffmpeg_error}")
                return False
    
    def transcribe_audio(self, audio_file_path: str) -> Dict[str, Any]:
        """
        Transcribe audio file using Vosk
        
        Args:
            audio_file_path: Path to audio file
            
        Returns:
            Dictionary with transcription result
        """
        if not self.is_available():
            return {
                'error': 'Voice transcription is not available in this deployment mode. Please type your message instead.',
                'transcript': ''
            }
        
        try:
            # Convert audio to WAV format
            with tempfile.NamedTemporaryFile(suffix='.wav', delete=False) as wav_file:
                wav_path = wav_file.name
            
            if not self.convert_audio_format(audio_file_path, wav_path):
                return {
                    'error': 'Failed to convert audio format',
                    'transcript': ''
                }
            
            # Open WAV file
            with wave.open(wav_path, 'rb') as wf:
                # Check audio format
                if wf.getnchannels() != 1 or wf.getsampwidth() != 2 or wf.getframerate() != 16000:
                    return {
                        'error': 'Audio format not supported. Please use mono 16kHz WAV.',
                        'transcript': ''
                    }
                
                # Create recognizer
                rec = vosk.KaldiRecognizer(self.model, wf.getframerate())
                rec.SetWords(True)  # Enable word-level timestamps if needed
                
                results = []
                
                # Process audio in chunks
                while True:
                    data = wf.readframes(4000)
                    if len(data) == 0:
                        break
                    
                    if rec.AcceptWaveform(data):
                        result = json.loads(rec.Result())
                        if result.get('text'):
                            results.append(result['text'])
                
                # Get final result
                final_result = json.loads(rec.FinalResult())
                if final_result.get('text'):
                    results.append(final_result['text'])
                
                # Clean up temp file
                try:
                    os.unlink(wav_path)
                except:
                    pass
                
                # Combine all results
                full_transcript = ' '.join(results).strip()
                
                if not full_transcript or len(full_transcript) < 2:
                    return {
                        'transcript': '',
                        'error': 'No speech detected. Please speak clearly and hold the button longer.'
                    }
                
                print(f"Vosk transcription result: '{full_transcript}'")
                return {'transcript': full_transcript}
                
        except Exception as e:
            print(f"Vosk transcription error: {e}")
            return {
                'error': f'Transcription failed: {str(e)}',
                'transcript': ''
            }

# Global instance
opensource_stt = OpenSourceSTT()

def transcribe_with_vosk(audio_file_path: str) -> Dict[str, Any]:
    """
    Convenience function for transcribing audio with Vosk
    """
    return opensource_stt.transcribe_audio(audio_file_path)

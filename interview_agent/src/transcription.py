"""
Interview Agent - Transcription Module
Handles audio file upload and transcription using OpenAI's Whisper API
"""

import os
import tempfile
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
import time

import openai
from pydub import AudioSegment
from tqdm import tqdm

class TranscriptionService:
    """Service for handling audio transcription using OpenAI's Whisper API"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize the transcription service
        
        Args:
            api_key: OpenAI API key (optional, will use environment variable if not provided)
        """
        if api_key:
            openai.api_key = api_key
        elif os.environ.get("OPENAI_API_KEY"):
            openai.api_key = os.environ.get("OPENAI_API_KEY")
        else:
            raise ValueError("OpenAI API key must be provided or set as OPENAI_API_KEY environment variable")
        
        self.client = openai.OpenAI()
        self.supported_formats = [".mp3", ".mp4", ".mpeg", ".mpga", ".m4a", ".wav", ".webm"]
    
    def validate_audio_file(self, file_path: str) -> Tuple[bool, str]:
        """
        Validate if the audio file is in a supported format and exists
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Tuple of (is_valid, message)
        """
        path = Path(file_path)
        
        if not path.exists():
            return False, f"File does not exist: {file_path}"
        
        if path.suffix.lower() not in self.supported_formats:
            return False, f"Unsupported file format: {path.suffix}. Supported formats: {', '.join(self.supported_formats)}"
        
        return True, "File is valid"
    
    def preprocess_audio(self, file_path: str) -> str:
        """
        Preprocess audio file if needed (format conversion, etc.)
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Path to the processed audio file
        """
        path = Path(file_path)
        
        # If already in supported format, return as is
        if path.suffix.lower() in [".mp3", ".m4a", ".wav"]:
            return file_path
        
        # Convert to mp3 for better compatibility
        try:
            audio = AudioSegment.from_file(file_path)
            
            # Create temp file for the converted audio
            temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
            temp_path = temp_file.name
            temp_file.close()
            
            # Export as mp3
            audio.export(temp_path, format="mp3")
            return temp_path
            
        except Exception as e:
            raise ValueError(f"Error preprocessing audio file: {str(e)}")
    
    def transcribe(self, file_path: str, progress_callback=None) -> Dict[str, Any]:
        """
        Transcribe audio file using OpenAI's GPT-4o transcription API, handling large files by chunking.
        Args:
            file_path: Path to the audio file
            progress_callback: Optional callback function to report progress
        Returns:
            Dictionary containing transcription results
        """
        # Validate file
        is_valid, message = self.validate_audio_file(file_path)
        if not is_valid:
            raise ValueError(message)

        # Preprocess audio if needed
        processed_file = self.preprocess_audio(file_path)

        # OpenAI's max file size is 25MB (26214400 bytes)
        # OpenAI's max duration is 1500 seconds (25 minutes)
        MAX_CHUNK_SIZE = 25 * 1024 * 1024  # 25MB
        MAX_CHUNK_DURATION = 1500  # seconds
        audio_size = os.path.getsize(processed_file)

        from openai import OpenAI
        client = OpenAI()

        def transcribe_chunk(chunk_path):
            with open(chunk_path, "rb") as audio_file:
                response = client.audio.transcriptions.create(
                    model="gpt-4o-transcribe",
                    file=audio_file
                )
            return response.text

        try:
            # Always use pydub to check duration and split if needed
            audio = AudioSegment.from_file(processed_file)
            duration_ms = len(audio)
            bytes_per_ms = audio_size / duration_ms
            max_chunk_duration_ms = min(
                int(MAX_CHUNK_SIZE / bytes_per_ms),
                MAX_CHUNK_DURATION * 1000
            )
            if duration_ms <= max_chunk_duration_ms and audio_size <= MAX_CHUNK_SIZE:
                # File is small enough, transcribe directly
                if progress_callback:
                    progress_callback(10)
                text = transcribe_chunk(processed_file)
                if progress_callback:
                    progress_callback(100)
                return {"text": text}
            else:
                # File is too large or too long, split into chunks
                chunks = []
                for i in range(0, duration_ms, max_chunk_duration_ms):
                    chunk = audio[i:i+max_chunk_duration_ms]
                    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=".mp3")
                    chunk.export(temp_file.name, format="mp3")
                    chunks.append(temp_file.name)
                    temp_file.close()
                # Transcribe each chunk
                texts = []
                total_chunks = len(chunks)
                for idx, chunk_path in enumerate(chunks):
                    if progress_callback:
                        progress_callback(int(100 * idx / total_chunks))
                    texts.append(transcribe_chunk(chunk_path))
                    os.unlink(chunk_path)
                if progress_callback:
                    progress_callback(100)
                return {"text": "\n".join(texts)}
        except Exception as e:
            if processed_file != file_path and os.path.exists(processed_file):
                os.unlink(processed_file)
            raise ValueError(f"Error transcribing audio: {str(e)}")
    
    def transcribe_with_progress(self, file_path: str) -> Dict[str, Any]:
        """
        Transcribe audio file with progress tracking using tqdm
        
        Args:
            file_path: Path to the audio file
            
        Returns:
            Dictionary containing transcription results
        """
        progress_bar = tqdm(total=100, desc="Transcribing audio")
        
        def update_progress(value):
            progress_bar.update(value - progress_bar.n)
        
        try:
            result = self.transcribe(file_path, update_progress)
            progress_bar.close()
            return result
        except Exception as e:
            progress_bar.close()
            raise e

# Example usage
if __name__ == "__main__":
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: python transcription.py <audio_file_path>")
        sys.exit(1)
    
    audio_path = sys.argv[1]
    
    # Initialize service
    service = TranscriptionService()
    
    try:
        # Transcribe with progress bar
        result = service.transcribe_with_progress(audio_path)
        
        # Print results
        print("\nTranscription complete!")
        print(f"Language detected: {result.get('language', 'unknown')}")
        print("\nTranscript:")
        print(result["text"])
        
    except ValueError as e:
        print(f"Error: {str(e)}")
        sys.exit(1)

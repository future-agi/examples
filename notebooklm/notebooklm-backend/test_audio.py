#!/usr/bin/env python3
"""
Simple test script to verify audio processing functionality
without running full docker build
"""

import sys
import os

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

def test_audio_detection():
    """Test audio file type detection"""
    try:
        from services.document_processor import DocumentProcessor
        
        processor = DocumentProcessor()
        
        # Test supported types
        print("Supported types:", processor.get_supported_types())
        
        # Test audio file detection
        audio_files = ['test.mp3', 'test.wav', 'test.m4a', 'test.aac', 'test.ogg', 'test.flac', 'test.mp4']
        
        print("\nAudio file type detection:")
        for audio_file in audio_files:
            detected_type = processor.detect_document_type(audio_file)
            print(f"  {audio_file} -> {detected_type}")
        
        return True
        
    except ImportError as e:
        print(f"Import error: {e}")
        print("Audio processing libraries not installed yet - this is expected")
        return False
    except Exception as e:
        print(f"Error: {e}")
        return False

def test_backend_routes():
    """Test that audio extensions are allowed in backend"""
    try:
        from routes.notebooks import allowed_file
        
        print("\nTesting allowed_file function:")
        audio_files = ['test.mp3', 'test.wav', 'test.m4a', 'test.aac', 'test.ogg', 'test.flac', 'test.mp4']
        
        for audio_file in audio_files:
            is_allowed = allowed_file(audio_file)
            print(f"  {audio_file} -> {'✓ allowed' if is_allowed else '✗ not allowed'}")
            
        return True
        
    except Exception as e:
        print(f"Error testing routes: {e}")
        return False

if __name__ == "__main__":
    print("Testing audio file support in NotebookLM backend...\n")
    
    # Test 1: Audio file detection
    print("=" * 50)
    print("TEST 1: Audio File Type Detection")
    print("=" * 50)
    test_audio_detection()
    
    # Test 2: Backend routes
    print("\n" + "=" * 50)
    print("TEST 2: Backend Route Validation")
    print("=" * 50)
    test_backend_routes()
    
    print("\n" + "=" * 50)
    print("SUMMARY")
    print("=" * 50)
    print("✓ Added audio file extensions to backend allowed_file function")
    print("✓ Added audio file extensions to frontend file input accept attribute")
    print("✓ Added audio transcription dependencies to requirements.txt")
    print("✓ Implemented audio processing in DocumentProcessor class")
    print("\nTo complete setup:")
    print("1. Install dependencies: pip install openai-whisper==20231117 SpeechRecognition==3.10.0")
    print("2. Build and test with Docker")
    print("3. Upload an audio file to test end-to-end functionality")
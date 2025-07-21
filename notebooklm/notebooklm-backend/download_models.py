#!/usr/bin/env python3
"""
Pre-download required models during Docker build to avoid runtime downloads
"""

import os
import sys
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def download_models():
    """Download all required models"""
    
    # Create cache directory
    cache_dir = "/app/model_cache"
    os.makedirs(cache_dir, exist_ok=True)
    
    # Download sentence transformer model
    logger.info("Downloading sentence transformer model...")
    try:
        from sentence_transformers import SentenceTransformer
        model = SentenceTransformer(
            "all-MiniLM-L6-v2",
            cache_folder=cache_dir,
            device='cpu'
        )
        logger.info("✓ Sentence transformer model downloaded successfully")
    except Exception as e:
        logger.error(f"Failed to download sentence transformer model: {e}")
        return False
    
    # Download Whisper models
    logger.info("Downloading Whisper models...")
    try:
        import whisper
        # Download multiple models for different file sizes
        models_to_download = ["tiny", "base", "small"]
        for model_name in models_to_download:
            logger.info(f"Downloading Whisper {model_name} model...")
            model = whisper.load_model(model_name, download_root=cache_dir)
            logger.info(f"✓ Whisper {model_name} model downloaded successfully")
    except Exception as e:
        logger.error(f"Failed to download Whisper models: {e}")
        return False
    
    logger.info("All models downloaded successfully!")
    return True

if __name__ == "__main__":
    success = download_models()
    sys.exit(0 if success else 1)
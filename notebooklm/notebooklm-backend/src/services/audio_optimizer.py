"""
Audio processing optimization for better transcription and Q&A accuracy
"""

import os
import logging
from typing import Dict, List, Tuple
import re
from datetime import datetime

class AudioOptimizer:
    """Optimized audio processing for NotebookLM"""
    
    @staticmethod
    def process_whisper_transcript(result: Dict) -> Tuple[str, List[Dict]]:
        """
        Process Whisper transcript for better vector search and Q&A
        
        Returns:
            Tuple of (clean_text, segments_with_timestamps)
        """
        segments_with_timestamps = []
        clean_text_parts = []
        
        if 'segments' in result:
            for segment in result['segments']:
                # Store segment with timestamp for reference
                segments_with_timestamps.append({
                    'start': segment['start'],
                    'end': segment['end'],
                    'text': segment['text'].strip(),
                    'start_formatted': AudioOptimizer._format_timestamp(segment['start']),
                    'end_formatted': AudioOptimizer._format_timestamp(segment['end'])
                })
                
                # Add clean text without timestamps
                clean_text_parts.append(segment['text'].strip())
        else:
            # Fallback if no segments
            clean_text_parts.append(result.get('text', ''))
        
        # Join with proper spacing
        clean_text = ' '.join(clean_text_parts)
        
        # Clean up common transcription artifacts
        clean_text = AudioOptimizer._clean_transcript_text(clean_text)
        
        return clean_text, segments_with_timestamps
    
    @staticmethod
    def _clean_transcript_text(text: str) -> str:
        """Clean common artifacts from audio transcripts"""
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        
        # Fix common speech artifacts
        text = re.sub(r'\b(um|uh|ah|er)\b', '', text, flags=re.IGNORECASE)
        
        # Remove extra whitespace from removed words
        text = re.sub(r'\s+', ' ', text)
        
        # Ensure proper sentence spacing
        text = re.sub(r'\.(?=[A-Z])', '. ', text)
        
        return text.strip()
    
    @staticmethod
    def create_smart_chunks(text: str, segments: List[Dict], 
                          chunk_size: int = 500, overlap: int = 50) -> List[Dict]:
        """
        Create intelligent chunks that respect natural boundaries
        
        Args:
            text: Clean transcript text
            segments: Original segments with timestamps
            chunk_size: Target words per chunk
            overlap: Word overlap between chunks
            
        Returns:
            List of chunks with metadata
        """
        # Split into sentences
        sentences = AudioOptimizer._split_into_sentences(text)
        
        chunks = []
        current_chunk = []
        current_word_count = 0
        chunk_start_time = 0
        chunk_segments = []
        
        for sentence in sentences:
            sentence_words = sentence.split()
            sentence_word_count = len(sentence_words)
            
            # If adding this sentence exceeds chunk size, create a chunk
            if current_word_count + sentence_word_count > chunk_size and current_chunk:
                chunk_text = ' '.join(current_chunk)
                
                # Find corresponding segments for this chunk
                chunk_segments = AudioOptimizer._find_segments_for_text(
                    chunk_text, segments
                )
                
                chunks.append({
                    'text': chunk_text,
                    'word_count': current_word_count,
                    'segments': chunk_segments,
                    'time_range': AudioOptimizer._get_time_range(chunk_segments),
                    'chunk_type': 'audio_transcript'
                })
                
                # Start new chunk with overlap
                overlap_sentences = AudioOptimizer._get_overlap_sentences(
                    current_chunk, overlap
                )
                current_chunk = overlap_sentences + [sentence]
                current_word_count = sum(len(s.split()) for s in current_chunk)
            else:
                current_chunk.append(sentence)
                current_word_count += sentence_word_count
        
        # Add final chunk
        if current_chunk:
            chunk_text = ' '.join(current_chunk)
            chunk_segments = AudioOptimizer._find_segments_for_text(
                chunk_text, segments
            )
            
            chunks.append({
                'text': chunk_text,
                'word_count': current_word_count,
                'segments': chunk_segments,
                'time_range': AudioOptimizer._get_time_range(chunk_segments),
                'chunk_type': 'audio_transcript'
            })
        
        return chunks
    
    @staticmethod
    def _split_into_sentences(text: str) -> List[str]:
        """Split text into sentences, handling common edge cases"""
        # Simple sentence splitter - can be enhanced with NLTK
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Filter out empty sentences
        sentences = [s.strip() for s in sentences if s.strip()]
        
        return sentences
    
    @staticmethod
    def _find_segments_for_text(text: str, segments: List[Dict]) -> List[Dict]:
        """Find which segments correspond to a chunk of text"""
        matching_segments = []
        
        for segment in segments:
            # Check if segment text appears in chunk
            if segment['text'] in text:
                matching_segments.append(segment)
        
        return matching_segments
    
    @staticmethod
    def _get_time_range(segments: List[Dict]) -> Dict:
        """Get time range for a list of segments"""
        if not segments:
            return {'start': 0, 'end': 0, 'formatted': '00:00 - 00:00'}
        
        start_time = segments[0]['start']
        end_time = segments[-1]['end']
        
        return {
            'start': start_time,
            'end': end_time,
            'formatted': f"{segments[0]['start_formatted']} - {segments[-1]['end_formatted']}"
        }
    
    @staticmethod
    def _get_overlap_sentences(sentences: List[str], overlap_words: int) -> List[str]:
        """Get sentences for overlap, respecting word count"""
        overlap_sentences = []
        word_count = 0
        
        # Start from the end and work backwards
        for sentence in reversed(sentences):
            sentence_words = len(sentence.split())
            if word_count + sentence_words <= overlap_words:
                overlap_sentences.insert(0, sentence)
                word_count += sentence_words
            else:
                break
        
        return overlap_sentences
    
    @staticmethod
    def _format_timestamp(seconds: float) -> str:
        """Format seconds to MM:SS or HH:MM:SS"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        seconds = int(seconds % 60)
        
        if hours > 0:
            return f"{hours:02d}:{minutes:02d}:{seconds:02d}"
        else:
            return f"{minutes:02d}:{seconds:02d}"
    
    @staticmethod
    def create_audio_metadata(file_path: str, result: Dict, 
                            clean_text: str, segments: List[Dict]) -> Dict:
        """Create comprehensive metadata for audio files"""
        return {
            'type': 'audio',
            'format': file_path.split('.')[-1].upper(),
            'duration_seconds': segments[-1]['end'] if segments else 0,
            'duration_formatted': AudioOptimizer._format_timestamp(
                segments[-1]['end'] if segments else 0
            ),
            'language': result.get('language', 'unknown'),
            'segments_count': len(segments),
            'transcript_length': len(clean_text),
            'word_count': len(clean_text.split()),
            'has_timestamps': True,
            'processing_date': datetime.now().isoformat()
        }
    
    @staticmethod
    def optimize_whisper_settings(file_size: int) -> Dict:
        """Get optimal Whisper settings based on file size"""
        # File size in MB
        size_mb = file_size / (1024 * 1024)
        
        if size_mb < 10:
            # Small files - use base model for quality
            return {
                'model': 'base',
                'language': None,  # Auto-detect
                'temperature': 0,  # Deterministic
                'compression_ratio_threshold': 2.4,
                'logprob_threshold': -1.0,
                'no_speech_threshold': 0.6
            }
        elif size_mb < 50:
            # Medium files - use small model for balance
            return {
                'model': 'small',
                'language': None,
                'temperature': 0,
                'compression_ratio_threshold': 2.4,
                'logprob_threshold': -1.0,
                'no_speech_threshold': 0.6
            }
        else:
            # Large files - use tiny model for speed
            return {
                'model': 'tiny',
                'language': None,
                'temperature': 0,
                'compression_ratio_threshold': 2.4,
                'logprob_threshold': -1.0,
                'no_speech_threshold': 0.6,
                'condition_on_previous_text': False  # Speed optimization
            }
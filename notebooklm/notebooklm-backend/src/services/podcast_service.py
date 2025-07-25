import os
import logging
from typing import Dict, List, Optional, Tuple
import json
from datetime import datetime
import uuid
import tempfile
import subprocess

from src.services.ai_service import AIService
from fi_instrumentation import register, FITracer
from opentelemetry import trace
from fi_instrumentation.fi_types import SpanAttributes, FiSpanKindValues

tracer = trace.get_tracer(__name__)

class PodcastService:
    """
    Service for generating audio podcasts from document content
    """
    
    def __init__(self):
        self.ai_service = AIService()
        self.temp_dir = tempfile.gettempdir()
        
        # TTS configuration
        self.tts_config = {
            'default_voice_male': 'male_voice',
            'default_voice_female': 'female_voice',
            'sample_rate': 22050,
            'audio_format': 'wav'
        }
        
        # Podcast generation templates
        self.script_templates = {
            'conversational': self._get_conversational_template(),
            'interview': self._get_interview_template(),
            'narrative': self._get_narrative_template(),
            'educational': self._get_educational_template()
        }
    
    def _get_conversational_template(self) -> str:
        """Template for conversational podcast style"""
        return """Create a natural, engaging conversation between two hosts discussing the provided content. 

Guidelines:
- Host A should be curious and ask insightful questions
- Host B should be knowledgeable and provide detailed explanations
- Include natural conversation elements like "That's interesting", "I see", "What about..."
- Break down complex topics into digestible segments
- Use examples and analogies to make concepts accessible
- Include smooth transitions between topics
- End with key takeaways and implications

Format the output as a script with:
[HOST A]: dialogue
[HOST B]: dialogue

Make it sound natural and conversational, not scripted. The conversation should flow naturally and be engaging for listeners."""
    
    def _get_interview_template(self) -> str:
        """Template for interview podcast style"""
        return """Create an interview-style podcast where an interviewer questions an expert about the provided content.

Guidelines:
- Interviewer should ask probing, thoughtful questions
- Expert should provide comprehensive, authoritative answers
- Include follow-up questions that dig deeper
- Cover different aspects and perspectives of the topic
- Include practical implications and real-world applications
- End with advice or recommendations for listeners

Format the output as:
[INTERVIEWER]: question or comment
[EXPERT]: detailed response

Make it feel like a professional interview with good pacing and natural flow."""
    
    def _get_narrative_template(self) -> str:
        """Template for narrative podcast style"""
        return """Create a narrative-style podcast that tells the story of the content in an engaging way.

Guidelines:
- Use storytelling techniques to make the content compelling
- Include context, background, and progression
- Use descriptive language to paint a picture
- Include key characters, events, or concepts as story elements
- Build tension and resolution where appropriate
- Make complex information accessible through narrative

Format the output as:
[NARRATOR]: narrative content

Create an engaging story that educates while entertaining."""
    
    def _get_educational_template(self) -> str:
        """Template for educational podcast style"""
        return """Create an educational podcast that teaches the content in a structured, clear manner.

Guidelines:
- Start with learning objectives or key questions
- Break content into logical segments or lessons
- Use clear explanations with examples
- Include summaries and key points
- Add practical applications and exercises
- End with a comprehensive review

Format the output as:
[INSTRUCTOR]: educational content

Make it informative, well-structured, and easy to follow."""
    
    def generate_podcast_script(self, sources: List[Dict], style: str = 'conversational',
                              title: str = None, duration_target: str = 'medium',
                              custom_instructions: str = None) -> Dict:
        with tracer.start_as_current_span("generate_podcast_script") as span:
            span.set_attribute(SpanAttributes.FI_SPAN_KIND, FiSpanKindValues.TOOL.value)
            span.set_attribute("input.value", json.dumps({"sources": sources, "style": style, "title": title, "duration_target": duration_target, "custom_instructions": custom_instructions}))
            """
            Generate a podcast script from document sources
            
            Args:
                sources: List of document chunks to use as source material
                style: Podcast style (conversational, interview, narrative, educational)
                title: Optional title for the podcast
                duration_target: Target duration (short: 5-10min, medium: 15-20min, long: 25-30min)
                custom_instructions: Custom instructions for script generation
                
            Returns:
                Dict with generated script and metadata
            """
            try:
                if style not in self.script_templates:
                    raise ValueError(f"Unsupported podcast style: {style}")
                
                # Prepare content from sources
                content_text = self._prepare_source_content(sources)
                
                if not content_text:
                    raise ValueError("No content available for podcast generation")
                
                # Build the prompt
                template = self.script_templates[style]
                
                # Add duration guidance
                duration_guidance = {
                    'short': "Create a concise 5-10 minute podcast (approximately 750-1500 words).",
                    'medium': "Create a 15-20 minute podcast (approximately 2250-3000 words).",
                    'long': "Create a comprehensive 25-30 minute podcast (approximately 3750-4500 words)."
                }
                
                duration_instruction = duration_guidance.get(duration_target, duration_guidance['medium'])
                
                # Combine instructions
                full_prompt = f"""
    {duration_instruction}

    {template}

    {custom_instructions or ''}

    Source Content:
    {content_text}

    Generate an engaging podcast script based on this content."""
                
                # Generate script using AI service
                messages = [{"role": "user", "content": full_prompt}]
                
                response = self.ai_service.chat_completion(
                    messages=messages,
                    context_sources=[],  # Context already included in prompt
                    model='gpt-4' if style in ['interview', 'narrative'] else 'gpt-3.5-turbo'  # Use better model for complex styles
                )
                
                if response.get('error'):
                    raise Exception(f"Script generation failed: {response.get('error')}")
                
                script_content = response.get('content', '')
                
                # Parse script into segments
                segments = self._parse_script_segments(script_content, style)

                span.set_attribute("output.value", json.dumps({
                    'script': script_content,
                    'segments': segments,
                    'style': style,
                    'title': title or f"Generated {style.title()} Podcast",
                    'duration_target': duration_target,
                    'estimated_duration': self._estimate_duration(script_content),
                    'word_count': len(script_content.split()),
                    'sources_used': len(sources),
                    'generation_metadata': {
                        'model': response.get('model'),
                        'provider': response.get('provider'),
                        'usage': response.get('usage'),
                        'timestamp': response.get('timestamp')
                    }
                }))
                
                return {
                    'script': script_content,
                    'segments': segments,
                    'style': style,
                    'title': title or f"Generated {style.title()} Podcast",
                    'duration_target': duration_target,
                    'estimated_duration': self._estimate_duration(script_content),
                    'word_count': len(script_content.split()),
                    'sources_used': len(sources),
                    'generation_metadata': {
                        'model': response.get('model'),
                        'provider': response.get('provider'),
                        'usage': response.get('usage'),
                        'timestamp': response.get('timestamp')
                    }
                }
                
            except Exception as e:
                logging.error(f"Podcast script generation error: {e}")
                return {
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
    
    def _prepare_source_content(self, sources: List[Dict]) -> str:
        """Prepare and format source content for script generation"""
        content_parts = []
        
        for i, source in enumerate(sources):
            text = source.get('text', '')
            metadata = source.get('metadata', {})
            source_id = metadata.get('source_id', f'source_{i+1}')
            
            # Limit text length to avoid token limits
            if len(text) > 2000:
                text = text[:2000] + "..."
            
            content_parts.append(f"[Source {i+1} - {source_id}]\\n{text}\\n")
        
        return "\\n".join(content_parts)
    
    def _parse_script_segments(self, script: str, style: str) -> List[Dict]:
        with tracer.start_as_current_span("parse_script_segments") as span:
            span.set_attribute(SpanAttributes.FI_SPAN_KIND, FiSpanKindValues.TOOL.value)
            span.set_attribute("input.value", json.dumps({"script": script, "style": style}))
            """Parse script into segments for audio generation"""
            segments = []
            
            # Define speaker patterns based on style
            patterns = {
                'conversational': ['[HOST A]:', '[HOST B]:'],
                'interview': ['[INTERVIEWER]:', '[EXPERT]:'],
                'narrative': ['[NARRATOR]:'],
                'educational': ['[INSTRUCTOR]:']
            }
            
            style_patterns = patterns.get(style, ['[SPEAKER]:'])
            
            # Split script by speaker patterns
            lines = script.split('\\n')
            current_speaker = None
            current_content = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                # Check if line starts with a speaker pattern
                speaker_found = None
                for pattern in style_patterns:
                    if line.startswith(pattern):
                        speaker_found = pattern.replace('[', '').replace(']:', '').lower()
                        break
                
                if speaker_found:
                    # Save previous segment
                    if current_speaker and current_content:
                        segments.append({
                            'speaker': current_speaker,
                            'content': ' '.join(current_content).strip(),
                            'voice_type': self._get_voice_for_speaker(current_speaker),
                            'duration_estimate': self._estimate_segment_duration(' '.join(current_content))
                        })
                    
                    # Start new segment
                    current_speaker = speaker_found
                    current_content = [line.replace(f'[{speaker_found.upper()}]:', '').strip()]
                else:
                    # Continue current segment
                    if current_content:
                        current_content.append(line)
            
            # Add final segment
            if current_speaker and current_content:
                segments.append({
                    'speaker': current_speaker,
                    'content': ' '.join(current_content).strip(),
                    'voice_type': self._get_voice_for_speaker(current_speaker),
                    'duration_estimate': self._estimate_segment_duration(' '.join(current_content))
                })
            
            span.set_attribute("output.value", json.dumps(segments))
            return segments
    
    def _get_voice_for_speaker(self, speaker: str) -> str:
        with tracer.start_as_current_span("get_voice_for_speaker") as span:
            span.set_attribute(SpanAttributes.FI_SPAN_KIND, FiSpanKindValues.TOOL.value)
            span.set_attribute("input.value", json.dumps({"speaker": speaker}))
            """Assign voice type to speaker"""
            # Simple voice assignment logic
            voice_mapping = {
                'host a': 'female_voice',
                'host b': 'male_voice',
                'interviewer': 'female_voice',
                'expert': 'male_voice',
                'narrator': 'male_voice',
                'instructor': 'female_voice'
            }
            span.set_attribute("output.value", json.dumps(voice_mapping.get(speaker.lower(), 'male_voice')))
            return voice_mapping.get(speaker.lower(), 'male_voice')
    
    def _estimate_duration(self, text: str) -> float:
        """Estimate audio duration in minutes based on text length"""
        # Average speaking rate: ~150 words per minute
        word_count = len(text.split())
        return round(word_count / 150, 1)
    
    def _estimate_segment_duration(self, text: str) -> float:
        """Estimate duration for a single segment"""
        word_count = len(text.split())
        return round(word_count / 150 * 60, 1)  # Return in seconds
    
    def generate_audio_from_script(self, script_data: Dict, output_path: str = None) -> Dict:
        with tracer.start_as_current_span("generate_audio_from_script") as span:
            span.set_attribute(SpanAttributes.FI_SPAN_KIND, FiSpanKindValues.TOOL.value)
            span.set_attribute("input.value", json.dumps({"script_data": script_data, "output_path": output_path}))
            """
            Generate audio from podcast script using text-to-speech
            
            Args:
                script_data: Script data with segments
                output_path: Optional output path for audio file
                
            Returns:
                Dict with audio file information and metadata
            """
            try:
                segments = script_data.get('segments', [])
                if not segments:
                    raise ValueError("No script segments available for audio generation")
                
                # Generate output path if not provided
                if not output_path:
                    podcast_id = str(uuid.uuid4())
                    output_path = os.path.join(self.temp_dir, f"podcast_{podcast_id}.wav")
                
                # Generate audio for each segment
                segment_files = []
                total_duration = 0
                
                for i, segment in enumerate(segments):
                    segment_file = os.path.join(self.temp_dir, f"segment_{i}_{uuid.uuid4().hex[:8]}.wav")
                    
                    # Generate TTS for segment
                    success = self._generate_tts_segment(
                        text=segment['content'],
                        voice_type=segment['voice_type'],
                        output_file=segment_file
                    )
                    
                    if success:
                        segment_files.append(segment_file)
                        total_duration += segment.get('duration_estimate', 0)
                    else:
                        logging.warning(f"Failed to generate audio for segment {i}")
                
                if not segment_files:
                    raise Exception("No audio segments were generated successfully")
                
                # Combine segments into final audio file
                success = self._combine_audio_segments(segment_files, output_path)
                
                # Clean up temporary segment files
                for file_path in segment_files:
                    try:
                        os.remove(file_path)
                    except:
                        pass
                
                if not success:
                    raise Exception("Failed to combine audio segments")
                
                # Get file information
                file_size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
                span.set_attribute("output.value", json.dumps({
                    'audio_file': {
                        'path': output_path,
                        'size': file_size,
                        'format': 'wav',
                        'sample_rate': self.tts_config['sample_rate']
                    },
                    'duration': total_duration,
                    'segments_count': len(segments),
                    'generation_metadata': {
                        'timestamp': datetime.now().isoformat(),
                        'segments_generated': len(segment_files),
                        'total_segments': len(segments)
                    }
                }))
                
                return {
                    'audio_file': {
                        'path': output_path,
                        'size': file_size,
                        'format': 'wav',
                        'sample_rate': self.tts_config['sample_rate']
                    },
                    'duration': total_duration,
                    'segments_count': len(segments),
                    'generation_metadata': {
                        'timestamp': datetime.now().isoformat(),
                        'segments_generated': len(segment_files),
                        'total_segments': len(segments)
                    }
                }
                
            except Exception as e:
                logging.error(f"Audio generation error: {e}")
                return {
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                }
    
    def _generate_tts_segment(self, text: str, voice_type: str, output_file: str) -> bool:
        """
        Generate TTS audio for a single segment
        This is a placeholder - in production, you would integrate with actual TTS services
        """
        try:
            # For demo purposes, create a simple placeholder
            # In production, integrate with services like:
            # - OpenAI TTS API
            # - Google Cloud Text-to-Speech
            # - Amazon Polly
            # - Azure Cognitive Services Speech
            # - Local TTS engines like espeak, festival, or piper
            
            # Placeholder implementation using system TTS (if available)
            if self._is_system_tts_available():
                return self._generate_system_tts(text, voice_type, output_file)
            else:
                # Create a silent audio file as placeholder
                return self._create_placeholder_audio(text, output_file)
                
        except Exception as e:
            logging.error(f"TTS generation error: {e}")
            return False
    
    def _is_system_tts_available(self) -> bool:
        """Check if system TTS is available"""
        try:
            # Check for common TTS commands
            result = subprocess.run(['which', 'espeak'], capture_output=True, text=True)
            return result.returncode == 0
        except:
            return False
    
    def _generate_system_tts(self, text: str, voice_type: str, output_file: str) -> bool:
        """Generate TTS using system espeak (if available)"""
        try:
            # Use espeak for basic TTS
            voice_param = '+f3' if voice_type == 'female_voice' else '+m3'
            
            cmd = [
                'espeak',
                '-v', f'en{voice_param}',
                '-s', '150',  # Speed
                '-w', output_file,  # Write to file
                text
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0 and os.path.exists(output_file)
            
        except Exception as e:
            logging.error(f"System TTS error: {e}")
            return False
    
    def _create_placeholder_audio(self, text: str, output_file: str) -> bool:
        """Create placeholder audio file"""
        try:
            # Calculate duration based on text length
            duration = max(len(text.split()) / 150 * 60, 1)  # At least 1 second
            
            # Create silent audio using sox (if available) or ffmpeg
            if self._is_command_available('sox'):
                cmd = ['sox', '-n', '-r', '22050', '-c', '1', output_file, 'trim', '0.0', str(duration)]
                result = subprocess.run(cmd, capture_output=True)
                return result.returncode == 0
            elif self._is_command_available('ffmpeg'):
                cmd = ['ffmpeg', '-f', 'lavfi', '-i', f'anullsrc=r=22050:cl=mono', '-t', str(duration), '-y', output_file]
                result = subprocess.run(cmd, capture_output=True)
                return result.returncode == 0
            else:
                # Create a minimal WAV file header for placeholder
                return self._create_minimal_wav(output_file, duration)
                
        except Exception as e:
            logging.error(f"Placeholder audio creation error: {e}")
            return False
    
    def _is_command_available(self, command: str) -> bool:
        """Check if a command is available in the system"""
        try:
            result = subprocess.run(['which', command], capture_output=True)
            return result.returncode == 0
        except:
            return False
    
    def _create_minimal_wav(self, output_file: str, duration: float) -> bool:
        """Create a minimal WAV file with silence"""
        try:
            import wave
            import struct
            
            sample_rate = 22050
            samples = int(sample_rate * duration)
            
            with wave.open(output_file, 'w') as wav_file:
                wav_file.setnchannels(1)  # Mono
                wav_file.setsampwidth(2)  # 16-bit
                wav_file.setframerate(sample_rate)
                
                # Write silence
                for _ in range(samples):
                    wav_file.writeframes(struct.pack('<h', 0))
            
            return os.path.exists(output_file)
            
        except Exception as e:
            logging.error(f"Minimal WAV creation error: {e}")
            return False
    
    def _combine_audio_segments(self, segment_files: List[str], output_file: str) -> bool:
        """Combine multiple audio segments into one file"""
        try:
            if len(segment_files) == 1:
                # Just copy the single file
                import shutil
                shutil.copy2(segment_files[0], output_file)
                return True
            
            # Try to use sox for concatenation
            if self._is_command_available('sox'):
                cmd = ['sox'] + segment_files + [output_file]
                result = subprocess.run(cmd, capture_output=True)
                return result.returncode == 0
            
            # Try to use ffmpeg for concatenation
            elif self._is_command_available('ffmpeg'):
                # Create concat file
                concat_file = os.path.join(self.temp_dir, f'concat_{uuid.uuid4().hex[:8]}.txt')
                with open(concat_file, 'w') as f:
                    for segment_file in segment_files:
                        f.write(f"file '{segment_file}'\\n")
                
                cmd = ['ffmpeg', '-f', 'concat', '-safe', '0', '-i', concat_file, '-c', 'copy', '-y', output_file]
                result = subprocess.run(cmd, capture_output=True)
                
                # Clean up concat file
                try:
                    os.remove(concat_file)
                except:
                    pass
                
                return result.returncode == 0
            
            else:
                # Simple binary concatenation for WAV files (basic approach)
                return self._simple_wav_concat(segment_files, output_file)
                
        except Exception as e:
            logging.error(f"Audio combination error: {e}")
            return False
    
    def _simple_wav_concat(self, segment_files: List[str], output_file: str) -> bool:
        """Simple WAV file concatenation"""
        try:
            import wave
            
            # Open first file to get parameters
            with wave.open(segment_files[0], 'rb') as first_wav:
                params = first_wav.getparams()
                
                with wave.open(output_file, 'wb') as output_wav:
                    output_wav.setparams(params)
                    
                    # Copy data from all files
                    for segment_file in segment_files:
                        with wave.open(segment_file, 'rb') as segment_wav:
                            output_wav.writeframes(segment_wav.readframes(segment_wav.getnframes()))
            
            return os.path.exists(output_file)
            
        except Exception as e:
            logging.error(f"Simple WAV concatenation error: {e}")
            return False
    
    def get_available_styles(self) -> Dict:
        """Get available podcast styles and their descriptions"""
        return {
            'conversational': {
                'name': 'Conversational',
                'description': 'Natural conversation between two hosts discussing the content',
                'voices': ['Host A (Female)', 'Host B (Male)'],
                'best_for': 'General topics, making complex subjects accessible'
            },
            'interview': {
                'name': 'Interview',
                'description': 'Professional interview format with expert insights',
                'voices': ['Interviewer (Female)', 'Expert (Male)'],
                'best_for': 'Technical topics, expert knowledge, deep dives'
            },
            'narrative': {
                'name': 'Narrative',
                'description': 'Storytelling approach that makes content engaging',
                'voices': ['Narrator (Male)'],
                'best_for': 'Historical content, case studies, stories'
            },
            'educational': {
                'name': 'Educational',
                'description': 'Structured teaching format with clear explanations',
                'voices': ['Instructor (Female)'],
                'best_for': 'Learning materials, tutorials, academic content'
            }
        }
    
    def get_health_status(self) -> Dict:
        """Get health status of podcast service"""
        try:
            status = {
                'tts_available': self._is_system_tts_available(),
                'audio_tools': {
                    'sox': self._is_command_available('sox'),
                    'ffmpeg': self._is_command_available('ffmpeg'),
                    'espeak': self._is_command_available('espeak')
                },
                'temp_directory': self.temp_dir,
                'temp_dir_writable': os.access(self.temp_dir, os.W_OK),
                'available_styles': list(self.script_templates.keys()),
                'timestamp': datetime.now().isoformat()
            }
            
            return status
            
        except Exception as e:
            return {
                'status': 'error',
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }


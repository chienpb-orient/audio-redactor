"""
Audio processing module for redacting sensitive content with beep sounds
"""

import ffmpeg
import os
import tempfile
import numpy as np
from pathlib import Path

def generate_beep_audio(duration, sample_rate=44100, frequency=1000):
    """
    Generate a beep sound of specified duration
    
    Args:
        duration (float): Duration in seconds
        sample_rate (int): Sample rate in Hz
        frequency (int): Beep frequency in Hz
        
    Returns:
        numpy array: Audio samples
    """
    t = np.linspace(0, duration, int(sample_rate * duration), False)
    # Generate sine wave for beep
    beep = np.sin(2 * np.pi * frequency * t)
    # Apply fade in/out to avoid clicks
    fade_samples = int(0.01 * sample_rate)  # 10ms fade
    if len(beep) > fade_samples * 2:
        beep[:fade_samples] *= np.linspace(0, 1, fade_samples)
        beep[-fade_samples:] *= np.linspace(1, 0, fade_samples)
    
    return beep

def create_temp_beep_file(duration, temp_dir=None):
    """
    Create a temporary beep audio file
    
    Args:
        duration (float): Duration in seconds
        temp_dir (str): Temporary directory path
        
    Returns:
        str: Path to temporary beep file
    """
    print(f"DEBUG: create_temp_beep_file called with duration={duration}, temp_dir={temp_dir}")
    
    if temp_dir is None:
        temp_dir = tempfile.gettempdir()
        print(f"DEBUG: Using default temp_dir: {temp_dir}")
    
    beep_path = os.path.join(temp_dir, f"beep_{duration:.2f}s.wav")
    print(f"DEBUG: Beep file path: {beep_path}")
    
    # Generate beep using ffmpeg
    print("DEBUG: Calling ffmpeg to generate beep...")
    try:
        (
            ffmpeg
            .input(f'sine=frequency=1000:duration={duration}', f='lavfi')
            .output(beep_path, acodec='pcm_s16le')
            .overwrite_output()
            .run(quiet=True)
        )
        print(f"DEBUG: Beep file created successfully: {beep_path}")
        print(f"DEBUG: Beep file exists: {os.path.exists(beep_path)}")
    except ffmpeg.Error as e:
        print("DEBUG: STDERR:", e.stderr.decode() if hasattr(e.stderr, "decode") else e.stderr)
        raise
    
    return beep_path

def redact_audio_segments(input_file, timestamp_ranges, output_file, temp_dir=None):
    """
    Redact audio segments by replacing them with beep sounds
    
    Args:
        input_file (str): Path to input audio file
        timestamp_ranges (list): List of [start, end] timestamp pairs in seconds
        output_file (str): Path to output audio file
        temp_dir (str): Temporary directory for intermediate files
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        print(f"DEBUG: redact_audio_segments called with:")
        print(f"DEBUG:   input_file: {input_file}")
        print(f"DEBUG:   output_file: {output_file}")
        print(f"DEBUG:   timestamp_ranges: {timestamp_ranges}")
        print(f"DEBUG:   temp_dir: {temp_dir}")
        
        if not timestamp_ranges:
            print("DEBUG: No timestamp ranges, copying file directly")
            # No redaction needed, just copy the file
            (
                ffmpeg
                .input(input_file)
                .output(output_file)
                .overwrite_output()
                .run(quiet=True)
            )
            return True
        
        if temp_dir is None:
            temp_dir = tempfile.mkdtemp()
        print(f"DEBUG: Using temp_dir: {temp_dir}")
        
        # Get audio info
        print("DEBUG: Probing input file with ffmpeg...")
        probe = ffmpeg.probe(input_file)
        print("DEBUG: ffmpeg.probe() completed successfully")
        audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
        if not audio_stream:
            raise Exception("No audio stream found in input file")
        
        duration = float(audio_stream['duration'])
        print(f"DEBUG: Audio duration: {duration}s")
        
        # Sort timestamp ranges by start time
        sorted_ranges = sorted(timestamp_ranges, key=lambda x: x[0])
        print(f"DEBUG: Sorted ranges: {sorted_ranges}")
        
        # Create list of segments (either original audio or beep)
        segments = []
        current_time = 0.0
        
        for i, (start, end) in enumerate(sorted_ranges):
            print(f"DEBUG: Processing range {i+1}/{len(sorted_ranges)}: [{start}, {end}]")
            
            # Ensure valid range
            start = max(0, min(start, duration))
            end = max(start, min(end, duration))
            print(f"DEBUG: Adjusted range: [{start}, {end}]")
            
            # Add original audio before redaction
            if current_time < start:
                original_segment = os.path.join(temp_dir, f"original_{current_time:.2f}_{start:.2f}.wav")
                print(f"DEBUG: Creating original segment: {original_segment}")
                print(f"DEBUG: Extracting from {current_time}s to {start}s (duration: {start-current_time}s)")
                (
                    ffmpeg
                    .input(input_file, ss=current_time, t=start-current_time)
                    .output(original_segment, acodec='pcm_s16le')
                    .overwrite_output()
                    .run(quiet=True)
                )
                print(f"DEBUG: Original segment created successfully")
                segments.append(original_segment)
            
            # Add beep for redacted section
            if end > start:
                beep_duration = end - start
                print(f"DEBUG: Creating beep file for duration: {beep_duration}s")
                beep_file = create_temp_beep_file(beep_duration, temp_dir)
                print(f"DEBUG: Beep file created: {beep_file}")
                segments.append(beep_file)
            
            current_time = end
        
        # Add remaining original audio after last redaction
        if current_time < duration:
            final_segment = os.path.join(temp_dir, f"final_{current_time:.2f}_{duration:.2f}.wav")
            (
                ffmpeg
                .input(input_file, ss=current_time)
                .output(final_segment, acodec='pcm_s16le')
                .overwrite_output()
                .run(quiet=True)
            )
            segments.append(final_segment)
        
        # Concatenate all segments
        if len(segments) == 1:
            # Only one segment, just copy it
            (
                ffmpeg
                .input(segments[0])
                .output(output_file)
                .overwrite_output()
                .run(quiet=True)
            )
        else:
            # Concatenate using ffmpeg concat filter (safe for mixed WAV segments)
            input_streams = [ffmpeg.input(s) for s in segments]

            try:
                (
                    ffmpeg
                    .concat(*input_streams, v=0, a=1)
                    .output(output_file, acodec='libmp3lame', format='mp3')
                    .overwrite_output()
                    .run(quiet=True)
                )
            except ffmpeg.Error as e:
                print("DEBUG: STDERR:", e.stderr.decode() if hasattr(e.stderr, "decode") else e.stderr)
                raise

        
        # Clean up temporary files
        try:
            for segment in segments:
                if os.path.exists(segment):
                    os.remove(segment)
        except Exception as e:
            print(f"DEBUG: Cleanup warning: {e}")
            pass  # Still ignore cleanup errors

        return True

        
    except Exception as e:
        print(f"DEBUG: Exception in redact_audio_segments: {e}")
        print(f"DEBUG: Exception type: {type(e)}")
        import traceback
        print(f"DEBUG: Traceback: {traceback.format_exc()}")
        print(f"Error redacting audio: {e}")
        return False

def get_audio_info(audio_file):
    """
    Get basic information about an audio file
    
    Args:
        audio_file (str): Path to audio file
        
    Returns:
        dict: Audio information (duration, sample_rate, format, etc.)
    """
    try:
        probe = ffmpeg.probe(audio_file)
        audio_stream = next((stream for stream in probe['streams'] if stream['codec_type'] == 'audio'), None)
        
        if not audio_stream:
            return None
            
        return {
            'duration': float(audio_stream.get('duration', 0)),
            'sample_rate': int(audio_stream.get('sample_rate', 0)),
            'channels': int(audio_stream.get('channels', 0)),
            'format': audio_stream.get('codec_name', 'unknown'),
            'bit_rate': int(audio_stream.get('bit_rate', 0)) if audio_stream.get('bit_rate') else None
        }
        
    except Exception as e:
        print(f"Error getting audio info: {e}")
        return None

def convert_audio_format(input_file, output_file, target_format='wav'):
    """
    Convert audio file to a different format
    
    Args:
        input_file (str): Path to input file
        output_file (str): Path to output file
        target_format (str): Target format (wav, mp3, etc.)
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        (
            ffmpeg
            .input(input_file)
            .output(output_file, format=target_format)
            .overwrite_output()
            .run(quiet=True)
        )
        return True
        
    except Exception as e:
        print(f"Error converting audio format: {e}")
        return False
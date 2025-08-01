#!/usr/bin/env python3
"""
Command-line version of Audio Transcriber - Faster Whisper
Works great in Docker containers without GUI dependencies
"""

import argparse
import os
import sys
from datetime import datetime
from pathlib import Path

# Import configuration
try:
    from config import (
        AVAILABLE_MODELS, DEFAULT_MODEL, COMPUTE_TYPE, DEVICE,
        DEFAULT_BEAM_SIZE, ENABLE_WORD_TIMESTAMPS
    )
except ImportError:
    # Fallback configuration
    AVAILABLE_MODELS = ["tiny", "tiny.en", "base", "base.en", "small", "small.en"]
    DEFAULT_MODEL = "base"
    COMPUTE_TYPE = "int8"
    DEVICE = "cpu"
    DEFAULT_BEAM_SIZE = 5
    ENABLE_WORD_TIMESTAMPS = True

def load_model(model_size):
    """Load the Whisper model"""
    try:
        from faster_whisper import WhisperModel
        print(f"Loading model: {model_size}...")
        model = WhisperModel(
            model_size, 
            device=DEVICE, 
            compute_type=COMPUTE_TYPE
        )
        print(f"✅ Model {model_size} loaded successfully")
        return model
    except Exception as e:
        print(f"❌ Error loading model: {e}")
        return None

def transcribe_audio(model, audio_file, beam_size=None, word_timestamps=None):
    """Transcribe audio file"""
    try:
        print(f"Transcribing: {audio_file}")
        
        # Use configured defaults if not specified
        if beam_size is None:
            beam_size = DEFAULT_BEAM_SIZE
        if word_timestamps is None:
            word_timestamps = ENABLE_WORD_TIMESTAMPS
            
        segments, info = model.transcribe(
            audio_file, 
            word_timestamps=word_timestamps,
            beam_size=beam_size
        )
        
        return segments, info
    except Exception as e:
        print(f"❌ Error during transcription: {e}")
        return None, None

def format_output(segments, info, audio_file, model_size):
    """Format transcription output"""
    output_lines = []
    output_lines.append(f"Transcription of: {os.path.basename(audio_file)}")
    output_lines.append(f"Model: {model_size}")
    output_lines.append(f"Language: {info.language} (confidence: {info.language_probability:.2f})")
    output_lines.append(f"Duration: {info.duration:.2f}s")
    output_lines.append("-" * 80)
    output_lines.append("")
    
    # Process segments and words
    for segment in segments:
        output_lines.append(f"Segment [{segment.start:.2f}s -> {segment.end:.2f}s]: {segment.text}")
        
        if hasattr(segment, 'words') and segment.words:
            output_lines.append("Word-level timestamps:")
            for word in segment.words:
                output_lines.append(f"  [{word.start:.2f}s -> {word.end:.2f}s] {word.word}")
        output_lines.append("")
    
    return "\n".join(output_lines)

def save_output(content, output_file):
    """Save transcription to file"""
    try:
        # Create output directory if it doesn't exist
        os.makedirs(os.path.dirname(output_file), exist_ok=True)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"✅ Transcription saved to: {output_file}")
        return True
    except Exception as e:
        print(f"❌ Error saving file: {e}")
        return False

def generate_output_filename(audio_file, output_dir="output"):
    """Generate output filename"""
    base_name = os.path.splitext(os.path.basename(audio_file))[0]
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    filename = f"{base_name}_transcription_{timestamp}.txt"
    return os.path.join(output_dir, filename)

def main():
    parser = argparse.ArgumentParser(
        description="Audio Transcriber CLI - Faster Whisper",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
Examples:
  {sys.argv[0]} audio.mp3
  {sys.argv[0]} audio.wav --model small --output my_transcription.txt
  {sys.argv[0]} audio.flac --beam-size 10 --no-word-timestamps
  
Available models: {', '.join(AVAILABLE_MODELS)}
        """
    )
    
    parser.add_argument(
        "audio_file", 
        help="Path to audio file to transcribe"
    )
    
    parser.add_argument(
        "-m", "--model", 
        choices=AVAILABLE_MODELS,
        default=DEFAULT_MODEL,
        help=f"Whisper model to use (default: {DEFAULT_MODEL})"
    )
    
    parser.add_argument(
        "-o", "--output",
        help="Output file path (default: auto-generated in output/ directory)"
    )
    
    parser.add_argument(
        "-b", "--beam-size",
        type=int,
        default=DEFAULT_BEAM_SIZE,
        help=f"Beam size for decoding (default: {DEFAULT_BEAM_SIZE})"
    )
    
    parser.add_argument(
        "--no-word-timestamps",
        action="store_true",
        help="Disable word-level timestamps"
    )
    
    parser.add_argument(
        "--list-models",
        action="store_true",
        help="List available models and exit"
    )
    
    args = parser.parse_args()
    
    # List models and exit
    if args.list_models:
        print("Available models:")
        for model in AVAILABLE_MODELS:
            print(f"  • {model}")
        return
    
    # Validate input file
    if not os.path.exists(args.audio_file):
        print(f"❌ Error: Audio file not found: {args.audio_file}")
        return 1
    
    # Load model
    model = load_model(args.model)
    if not model:
        return 1
    
    # Transcribe
    word_timestamps = not args.no_word_timestamps
    segments, info = transcribe_audio(
        model, 
        args.audio_file, 
        args.beam_size, 
        word_timestamps
    )
    
    if segments is None:
        return 1
    
    # Format output
    content = format_output(segments, info, args.audio_file, args.model)
    
    # Print to console
    print("\n" + "="*80)
    print("TRANSCRIPTION RESULTS")
    print("="*80)
    print(content)
    
    # Save to file
    if args.output:
        output_file = args.output
    else:
        output_file = generate_output_filename(args.audio_file)
    
    if save_output(content, output_file):
        print(f"\n📄 Full transcription saved to: {output_file}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main()) 
"""
Streamlit Audio Transcription and Redaction App
Transcribes audio, detects sensitive content, and redacts with beep sounds
"""

import streamlit as st
import os
import tempfile
from datetime import datetime
from pathlib import Path
import traceback
from dotenv import load_dotenv

# Core imports
from faster_whisper import WhisperModel


load_dotenv()  

os.environ["PATH"] += os.pathsep + os.getenv("FFMPEG_PATH")


# Local imports
from config import (
    AVAILABLE_MODELS, DEFAULT_MODEL, COMPUTE_TYPE, DEVICE,
    DEFAULT_BEAM_SIZE, ENABLE_WORD_TIMESTAMPS
)
from gemini import detect_sensitive_content
from audio_processor import redact_audio_segments, get_audio_info

# Streamlit page config
st.set_page_config(
    page_title="Audio Transcription & Redaction",
    page_icon="🎵",
    layout="wide",
    initial_sidebar_state="expanded"
)

def init_session_state():
    """Initialize session state variables"""
    if 'model' not in st.session_state:
        st.session_state.model = None
    if 'loaded_model_size' not in st.session_state:
        st.session_state.loaded_model_size = None
    if 'transcript_content' not in st.session_state:
        st.session_state.transcript_content = None
    if 'sensitive_timestamps' not in st.session_state:
        st.session_state.sensitive_timestamps = []
    if 'audio_info' not in st.session_state:
        st.session_state.audio_info = None

@st.cache_resource
def load_whisper_model(model_size):
    """Load and cache Whisper model"""
    try:
        model = WhisperModel(
            model_size, 
            device=DEVICE, 
            compute_type=COMPUTE_TYPE
        )
        return model
    except Exception as e:
        st.error(f"Error loading model: {e}")
        return None

def format_transcript_output(segments, info, audio_filename, model_size):
    """Format transcription output with word-level timestamps"""
    output_lines = []
    output_lines.append(f"Transcription of: {audio_filename}")
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

def transcribe_audio(audio_file, model_size, beam_size, word_timestamps):
    """Transcribe audio file"""
    try:
        # Load model
        model = load_whisper_model(model_size)
        if not model:
            return None, None
        
        # Transcribe
        segments, info = model.transcribe(
            audio_file, 
            word_timestamps=word_timestamps,
            beam_size=beam_size
        )
        
        return segments, info
        
    except Exception as e:
        st.error(f"Error during transcription: {e}")
        return None, None

def save_transcript_to_temp(transcript_content):
    """Save transcript to temporary file and return path"""
    try:
        temp_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt', encoding='utf-8')
        temp_file.write(transcript_content)
        temp_file.close()
        return temp_file.name
    except Exception as e:
        st.error(f"Error saving transcript: {e}")
        return None

def main():
    # Initialize session state
    init_session_state()
    
    # Title and description
    st.title("🎵 Audio Transcription & Redaction")
    st.markdown("Upload an audio file to transcribe it, detect sensitive content, and create a redacted version with beep sounds.")
    
    # Sidebar configuration
    st.sidebar.header("⚙️ Configuration")
    
    # Model selection
    model_size = st.sidebar.selectbox(
        "Select Whisper Model",
        AVAILABLE_MODELS,
        index=AVAILABLE_MODELS.index(DEFAULT_MODEL) if DEFAULT_MODEL in AVAILABLE_MODELS else 0,
        help="Smaller models are faster but less accurate"
    )
    
    # Transcription settings
    st.sidebar.subheader("Transcription Settings")
    beam_size = st.sidebar.slider(
        "Beam Size", 
        min_value=1, 
        max_value=10, 
        value=DEFAULT_BEAM_SIZE,
        help="Higher values may improve accuracy but take longer"
    )
    
    word_timestamps = st.sidebar.checkbox(
        "Enable Word Timestamps", 
        value=ENABLE_WORD_TIMESTAMPS,
        help="Required for sensitive content detection"
    )
    
    # Main content area
    col1, col2 = st.columns([1, 1])
    
    with col1:
        st.header("📁 Upload Audio File")
        
        # Audio file upload
        uploaded_file = st.file_uploader(
            "Choose an audio file",
            type=['wav', 'mp3', 'flac', 'm4a', 'ogg', 'aac'],
            help="Supported formats: WAV, MP3, FLAC, M4A, OGG, AAC"
        )
        
        if uploaded_file is not None:
            # Display audio info
            st.audio(uploaded_file)
            st.write(f"**Filename:** {uploaded_file.name}")
            st.write(f"**Size:** {uploaded_file.size / 1024 / 1024:.2f} MB")
            
            # Save uploaded file temporarily
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_file:
                tmp_file.write(uploaded_file.getvalue())
                temp_audio_path = tmp_file.name
            
            # Get audio info
            audio_info = get_audio_info(temp_audio_path)
            if audio_info:
                st.session_state.audio_info = audio_info
                st.write(f"**Duration:** {audio_info['duration']:.2f} seconds")
                st.write(f"**Sample Rate:** {audio_info['sample_rate']} Hz")
                st.write(f"**Channels:** {audio_info['channels']}")
                st.write(f"**Format:** {audio_info['format']}")
            
            # Transcription button
            if st.button("🎤 Start Transcription", type="primary"):
                if not word_timestamps:
                    st.warning("⚠️ Word timestamps are required for sensitive content detection. Please enable them in the sidebar.")
                
                with st.spinner("Transcribing audio... This may take a while."):
                    # Transcribe
                    segments, info = transcribe_audio(temp_audio_path, model_size, beam_size, word_timestamps)
                    
                    if segments and info:
                        # Format transcript
                        transcript_content = format_transcript_output(
                            segments, info, uploaded_file.name, model_size
                        )
                        st.session_state.transcript_content = transcript_content
                        
                        st.success("✅ Transcription completed!")
                        
                        # Display transcript preview
                        st.subheader("📄 Transcript Preview")
                        st.text_area("Transcript", transcript_content, height=300)
                        
                        # Download transcript
                        st.download_button(
                            label="💾 Download Transcript",
                            data=transcript_content,
                            file_name=f"{Path(uploaded_file.name).stem}_transcript_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt",
                            mime="text/plain"
                        )
                    else:
                        st.error("❌ Transcription failed. Please try again.")
            
            # Clean up temp file
            try:
                os.unlink(temp_audio_path)
            except:
                pass
    
    with col2:
        st.header("🔍 Sensitive Content Detection")
        
        if st.session_state.transcript_content and word_timestamps:
            if st.button("🔎 Detect Sensitive Content", type="secondary"):
                with st.spinner("Analyzing transcript for sensitive content..."):
                    try:
                        # Detect sensitive timestamps
                        sensitive_timestamps = detect_sensitive_content(st.session_state.transcript_content)
                        st.session_state.sensitive_timestamps = sensitive_timestamps
                        
                        if sensitive_timestamps:
                            st.success(f"✅ Found {len(sensitive_timestamps)} sensitive segments")
                            
                            # Display detected segments
                            st.subheader("🚨 Detected Sensitive Segments")
                            for i, (start, end) in enumerate(sensitive_timestamps):
                                st.write(f"**Segment {i+1}:** {start:.2f}s - {end:.2f}s ({end-start:.2f}s duration)")
                        else:
                            st.info("ℹ️ No sensitive content detected")
                            
                    except Exception as e:
                        st.error(f"❌ Error detecting sensitive content: {e}")
                        st.error(traceback.format_exc())
        
        elif st.session_state.transcript_content and not word_timestamps:
            st.warning("⚠️ Word timestamps are required for sensitive content detection. Please re-transcribe with word timestamps enabled.")
        
        elif not st.session_state.transcript_content:
            st.info("ℹ️ Please transcribe an audio file first")
    
    # Audio redaction section
    if st.session_state.sensitive_timestamps and uploaded_file is not None:
        st.header("🔇 Audio Redaction")
        
        col3, col4 = st.columns([2, 1])
        
        with col3:
            st.write(f"**Segments to redact:** {len(st.session_state.sensitive_timestamps)}")
            
            # Show redaction preview
            total_redacted_time = sum(end - start for start, end in st.session_state.sensitive_timestamps)
            original_duration = st.session_state.audio_info['duration'] if st.session_state.audio_info else 0
            redaction_percentage = (total_redacted_time / original_duration * 100) if original_duration > 0 else 0
            
            st.write(f"**Total redacted time:** {total_redacted_time:.2f} seconds")
            st.write(f"**Redaction percentage:** {redaction_percentage:.1f}%")
        
        with col4:
            if st.button("🔇 Create Redacted Audio", type="primary"):
                with st.spinner("Creating redacted audio... This may take a while."):
                    try:
                        print("=== DEBUG: Starting audio redaction process ===")
                        print(f"DEBUG: Uploaded file name: {uploaded_file.name}")
                        print(f"DEBUG: Uploaded file size: {uploaded_file.size}")
                        
                        # Save uploaded file temporarily
                        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(uploaded_file.name).suffix) as tmp_input:
                            tmp_input.write(uploaded_file.getvalue())
                            temp_input_path = tmp_input.name
                        
                        print(f"DEBUG: Created temp input file: {temp_input_path}")
                        print(f"DEBUG: Temp input file exists: {os.path.exists(temp_input_path)}")
                        
                        # Create output file
                        output_filename = f"{Path(uploaded_file.name).stem}_redacted_{datetime.now().strftime('%Y%m%d_%H%M%S')}.mp3"
                        temp_output_path = tempfile.NamedTemporaryFile(delete=False, suffix='.mp3').name
                        
                        print(f"DEBUG: Output filename: {output_filename}")
                        print(f"DEBUG: Temp output path: {temp_output_path}")
                        print(f"DEBUG: Number of sensitive timestamps: {len(st.session_state.sensitive_timestamps)}")
                        print(f"DEBUG: Sensitive timestamps: {st.session_state.sensitive_timestamps}")
                        
                        # Redact audio
                        print("DEBUG: Calling redact_audio_segments...")
                        success = redact_audio_segments(
                            temp_input_path, 
                            st.session_state.sensitive_timestamps, 
                            temp_output_path
                        )
                        print(f"DEBUG: Redaction success: {success}")
                        
                        if success:
                            print(f"DEBUG: Output file exists after redaction: {os.path.exists(temp_output_path)}")
                            print(f"DEBUG: Output file size: {os.path.getsize(temp_output_path) if os.path.exists(temp_output_path) else 'File not found'}")
                            
                            # Read redacted audio for download
                            print("DEBUG: Reading redacted audio file...")
                            with open(temp_output_path, 'rb') as f:
                                redacted_audio_bytes = f.read()
                            print(f"DEBUG: Read {len(redacted_audio_bytes)} bytes from output file")
                            
                            st.success("✅ Redacted audio created successfully!")
                            
                            # Play redacted audio
                            st.audio(redacted_audio_bytes)
                            
                            # Download button
                            st.download_button(
                                label="💾 Download Redacted Audio",
                                data=redacted_audio_bytes,
                                file_name=output_filename,
                                mime="audio/mpeg"
                            )
                        else:
                            print("DEBUG: Redaction failed!")
                            st.error("❌ Failed to create redacted audio")
                        
                        # Clean up temp files
                        print("DEBUG: Cleaning up temp files...")
                        try:
                            print(f"DEBUG: Deleting input file: {temp_input_path}")
                            os.unlink(temp_input_path)
                            print("DEBUG: Input file deleted successfully")
                        except Exception as e:
                            print(f"DEBUG: Error deleting input file: {e}")
                        
                        try:
                            print(f"DEBUG: Deleting output file: {temp_output_path}")
                            os.unlink(temp_output_path)
                            print("DEBUG: Output file deleted successfully")
                        except Exception as e:
                            print(f"DEBUG: Error deleting output file: {e}")
                            
                    except Exception as e:
                        print(f"DEBUG: Exception occurred during redaction: {e}")
                        print(f"DEBUG: Exception traceback: {traceback.format_exc()}")
                        st.error(f"❌ Error creating redacted audio: {e}")
                        st.error(traceback.format_exc())
    
    # Footer
    st.markdown("---")
    st.markdown("Built with ❤️ using Streamlit, Faster-Whisper, Google Gemini AI, and FFmpeg")

if __name__ == "__main__":
    main()
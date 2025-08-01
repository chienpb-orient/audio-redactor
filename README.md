# Audio Transcriber - Faster Whisper with AI Redaction

A comprehensive audio transcription solution with AI-powered sensitive content detection and redaction. Features a modern Streamlit web interface, traditional GUI, and command-line options.

## 🆕 New Streamlit Web App with AI Redaction

**The newest addition!** A modern web interface that not only transcribes audio but also:
- 🔍 **Detects sensitive content** using Google Gemini AI
- 🔇 **Automatically redacts** sensitive parts with beep sounds
- 🎵 **Audio processing** with FFmpeg integration
- 🌐 **Web-based interface** accessible from any browser

## Features

- 🎤 **Easy Audio File Selection** - Support for various audio formats (WAV, MP3, FLAC, M4A, OGG, AAC)
- 🤖 **Multiple Model Options** - Choose from tiny to large-v3 models, including distil variants
- ⏱️ **Word-Level Timestamps** - Precise timing information for each word
- 🔍 **AI Content Detection** - Automatically find sensitive information using Google Gemini
- 🔇 **Audio Redaction** - Replace sensitive content with beep sounds
- 💾 **Export Options** - Save transcriptions and redacted audio files
- 🌐 **Streamlit Web UI** - Modern, intuitive web interface
- 🖥️ **Traditional GUI** - Desktop tkinter interface (legacy)
- 🐳 **Docker Ready** - Containerized for easy deployment
- ⚡ **CPU Optimized** - Efficient INT8 quantization for faster processing

## Quick Start

### 🚀 Streamlit Web App (Recommended)

The modern web interface with AI-powered redaction:

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up environment:**
   ```bash
   # Create .env file with your Google AI API key
   echo "GOOGLE_GENERATIVE_AI_API_KEY=your_api_key_here" > .env
   ```

3. **Run the Streamlit app:**
   ```bash
   # Option 1: Direct streamlit command
   streamlit run streamlit_app.py
   
   # Option 2: Using the run script
   python run_streamlit.py
   ```

4. **Open your browser** to `http://localhost:8501` and start transcribing!

**Features available in Streamlit app:**
- 📁 Upload audio files directly in the browser
- 🎤 Transcribe with word-level timestamps
- 🔍 Detect sensitive content (names, emails, passwords, etc.)
- 🔇 Generate redacted audio with beep sounds
- 💾 Download both transcript and redacted audio files


## Usage Guide

### Step-by-Step Instructions

1. **Launch the Application**
   - The GUI will open with the main transcriber interface

2. **Select a Model**
   - Choose from the dropdown menu (default: "base")
   - Smaller models are faster but less accurate
   - Larger models provide better accuracy but take more time

3. **Choose Audio File**
   - Click "Browse" to select your audio file
   - Supported formats: WAV, MP3, FLAC, M4A, OGG, AAC

4. **Start Transcription**
   - Click "Start Transcription"
   - Progress will be shown in the progress bar
   - Status updates will appear below

5. **Review Results**
   - Transcription appears in the text area
   - Includes segment-level and word-level timestamps

6. **Save Output**
   - Click "Save to File" to export as a text file
   - Default filename includes timestamp and original file name



### Model Selection Guide

| Model | Size | Speed | Accuracy | Use Case |
|-------|------|-------|----------|----------|
| `tiny` | ~39 MB | Fastest | Basic | Quick drafts, simple audio |
| `base` | ~74 MB | Fast | Good | General purpose, balanced |
| `small` | ~244 MB | Medium | Better | Clear speech, presentations |
| `medium` | ~769 MB | Slower | High | Professional transcription |
| `large-v3` | ~1550 MB | Slowest | Highest | Best quality, complex audio |
| `distil-large-v3` | ~756 MB | Fast | High | Good balance of speed/quality |

### Customizing Available Models

**By default, only lightweight models (tiny, base, small) are enabled to save disk space and download time.**

To customize which models are available:

1. **Edit `config.py`** - Uncomment the models you want to use:
   ```python
   AVAILABLE_MODELS = [
       "tiny", "base", "small",        # Currently enabled
       # "medium", "large-v3",         # Uncomment to enable
       # "distil-large-v3",            # Uncomment to enable
   ]
   ```
   ```

**💡 Disk Space Savings:**
- **Default config (tiny, base, small)**: ~357 MB total
- **All models enabled**: ~6+ GB total  
- Models are downloaded only when first used

### Resource Limits

Default limits in docker-compose.yml:
- Memory: 8GB limit, 2GB reservation
- CPU: 4 cores limit, 1 core reservation

Adjust based on your system and chosen models.

### Model Download Issues

- Models are downloaded automatically on first use
- Check internet connection
- Verify the model-cache volume is properly mounted

### Performance Issues

- Use smaller models for faster processing
- Increase Docker memory limits if needed
- Consider using distil models for better speed/accuracy balance

### Audio Format Issues

- Try converting to WAV format if other formats fail
- Ensure audio file is not corrupted
- Check file permissions

## 🔧 Setup for AI Redaction Features

To use the sensitive content detection and redaction features:

### 1. Get Google AI API Key
1. Go to [Google AI Studio](https://aistudio.google.com/)
2. Create an API key for Gemini
3. Copy your API key

### 2. Set Environment Variable
```bash
# Create .env file
echo "GOOGLE_GENERATIVE_AI_API_KEY=your_actual_api_key_here" > .env
echo "FFMPEG_PATH=path_to_your_ffmpeg_if_not_registered_globally" > .env

# Or set environment variable directly
export GOOGLE_GENERATIVE_AI_API_KEY="your_actual_api_key_here"
export FFMPEG_PATH="path_to_your_ffmpeg_if_not_registered_globally"
```

### 3. Install FFmpeg
The audio redaction requires FFmpeg:

**Windows:**
- Download from [FFmpeg.org](https://ffmpeg.org/download.html)
- Add to PATH

**macOS:**
```bash
brew install ffmpeg
```

**Linux:**
```bash
sudo apt update && sudo apt install ffmpeg
```
# Audio Transcriber Configuration
# Customize which models are available in the GUI dropdown

# Available model configurations
AVAILABLE_MODELS = [
    # Lightweight models (recommended for most users)
    "tiny",     # ~39 MB  - Fastest, basic accuracy
    "tiny.en",  # ~39 MB  - English-only version
    "base",     # ~74 MB  - Good balance of speed/accuracy  
    "base.en",  # ~74 MB  - English-only version
    "small",    # ~244 MB - Better accuracy
    "small.en", # ~244 MB - English-only version
    
    # Medium models (uncomment if needed)
    # "medium",    # ~769 MB - High accuracy, slower
    # "medium.en", # ~769 MB - English-only version
    
    # Large models (uncomment if needed - requires more RAM)
    # "large-v1",  # ~1550 MB - Highest accuracy, slowest
    # "large-v2",  # ~1550 MB - Improved version
    # "large-v3",  # ~1550 MB - Latest version
    
    # Distilled models (good speed/accuracy balance)
    # "distil-large-v2",  # ~756 MB - Faster large model
    # "distil-large-v3",  # ~756 MB - Latest distilled version
]

# Default model to select when app starts
DEFAULT_MODEL = "base"

# Model download settings
COMPUTE_TYPE = "int8"  # Options: "int8", "int16", "float16", "float32"
DEVICE = "cpu"         # Force CPU-only (no GPU dependencies)

# GUI settings
WINDOW_TITLE = "Audio Transcriber - Faster Whisper"
WINDOW_SIZE = "800x600"

# File settings
SUPPORTED_AUDIO_FORMATS = [
    ("Audio files", "*.wav *.mp3 *.flac *.m4a *.ogg *.aac"),
    ("All files", "*.*")
]

# Transcription settings
DEFAULT_BEAM_SIZE = 5
ENABLE_WORD_TIMESTAMPS = True

# Performance settings (for Docker)
DOCKER_MEMORY_LIMIT = "8G"
DOCKER_CPU_LIMIT = "4.0" 
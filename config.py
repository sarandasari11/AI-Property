"""
Configuration settings for AI Property Video Generator
"""
import os
from pathlib import Path

# Paths
BASE_DIR = Path(__file__).resolve().parent
ASSETS_DIR = BASE_DIR / "assets"
SAMPLE_DATA_DIR = ASSETS_DIR / "sample_data"
AUDIO_DIR = ASSETS_DIR / "audio"
OUTPUT_DIR = BASE_DIR / "output"
TEMP_DIR = BASE_DIR / "temp"

# Ensure output & temp directories exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
TEMP_DIR.mkdir(parents=True, exist_ok=True)
SAMPLE_DATA_DIR.mkdir(parents=True, exist_ok=True)
AUDIO_DIR.mkdir(parents=True, exist_ok=True)

# Video Rendering Specifications
DEFAULT_FPS = 24
DEFAULT_WIDTH = 1920
DEFAULT_HEIGHT = 1080
ASPECT_RATIO_16_9 = (1920, 1080)
ASPECT_RATIO_9_16 = (1080, 1920)

# Slide / Scene Timings (in seconds)
INTRO_DURATION = 5.0
FEATURE_SCENE_DURATION = 5.5
OUTRO_DURATION = 5.0
TRANSITION_DURATION = 0.8

# Audio Configuration
DEFAULT_TTS_VOICE = "en-US-ChristopherNeural"  # Professional, confident tone
FALLBACK_TTS_VOICE = "en-US-JennyNeural"
DEFAULT_SPEECH_RATE = "+0%"
BG_MUSIC_VOLUME = 0.12  # Ducked volume when voiceover plays
BG_MUSIC_FULL_VOLUME = 0.40

# Branding & Colors (Modern Real Estate Aesthetic)
COLOR_PRIMARY = (18, 24, 38)        # Deep Navy / Slate
COLOR_ACCENT = (212, 160, 23)       # Warm Gold / Champagne
COLOR_TEXT_LIGHT = (255, 255, 255)  # Pure White
COLOR_TEXT_MUTED = (200, 210, 220)  # Soft Silver
COLOR_CARD_BG = (15, 23, 42, 210)   # Semi-transparent dark card (RGBA)

# Constraints from Assignment Brief
MIN_PROPERTY_IMAGES = 4
MAX_PROPERTY_IMAGES = 8

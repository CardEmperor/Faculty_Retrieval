import os

# Application Settings
APP_NAME = "Faculty Retrieval System"
APP_VERSION = "1.0.0"
DEBUG = True

# Streamlit Configuration
STREAMLIT_CONFIG = {
    'page_title': 'AI & Future of Work — Professor Directory',
    'page_icon': '🤖',
    'layout': 'wide',
    'initial_sidebar_state': 'expanded'
}

# Data File
DATA_FILE = os.path.join(os.path.dirname(__file__), "professors_data.json")

# API Configuration
API_HOST = '127.0.0.1'
API_PORT = 5000
API_DEBUG = DEBUG

# Display Settings
DEFAULT_RESULTS_PER_PAGE = 20
MAX_RESULTS = 500

# Filter Defaults
DEFAULT_IMPACT_RANGE = (0, 100)
DEFAULT_SOCIAL_RANGE = (0, 100)

# Sorting Options
SORT_OPTIONS = [
    "Impact Score ↓",
    "Social Score ↓",
    "h-index ↓",
    "Citations ↓",
    "Name A-Z"
]

# Research Focus
RESEARCH_FOCUS = "AI, Automation, Finance, Future of Work, Economics"

# UI Colors (Dark Theme)
COLORS = {
    'primary': '#E94560',
    'secondary': '#FF7675',
    'background': '#0E1117',
    'surface': 'rgba(255,255,255,0.03)',
    'border': 'rgba(255,255,255,0.06)',
    'text': '#FFFFFF'
}

# Export Formats
EXPORT_FORMATS = ['CSV', 'JSON']

# Analytics Settings
ANALYTICS_ENABLED = True
TOP_N_DISPLAY = 15

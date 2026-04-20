# Faculty Retrieval System

A comprehensive directory of 80+ leading academics in AI, Automation, Economics, FinTech, and the Future of Work. Features interactive profiles, advanced search & filtering, analytics, and a REST API.

## 📋 Features

### Streamlit Web App (`app.py`)
- **Professor Profiles**: Browse detailed faculty information with contact links
- **Advanced Filtering**: Filter by name, university, country, research areas, impact score, social presence
- **Analytics Dashboard**: Visualizations of impact scores, social presence, research areas
- **Top Cited Works**: Search and explore most influential publications
- **Data Export**: Download full database as CSV or JSON

### REST API (`api.py`)
- Search professors with query parameters
- Get individual professor profiles
- Retrieve aggregated statistics
- List all research areas and countries

### Utilities Module (`utils.py`)
- Programmatic access to professor data
- Search functions for various criteria
- Statistical analysis tools
- Data filtering utilities

## 🚀 Quick Start

### Installation

1. Clone the repository
```bash
git clone <your-repo-url>
cd Faculty_Retrieval
```

2. Install dependencies
```bash
pip install -r requirements.txt
```

### Running the Streamlit App

```bash
streamlit run app.py
```

The app will open at `http://localhost:8501`

### Running the API Server

```bash
python api.py
```

The API will run at `http://localhost:5000`

## 📚 API Endpoints

### GET /api/professors
Returns filtered list of professors

**Query Parameters:**
- `search`: Search by name, university, or area
- `areas`: Filter by research area (repeatable)
- `country`: Filter by country
- `min_impact`: Minimum impact score
- `ra_hiring`: Filter for RA/PhD hiring professors (true/false)

**Example:**
```
GET /api/professors?search=AI&country=USA&ra_hiring=true
```

### GET /api/professors/<name>
Get detailed profile for a specific professor

**Example:**
```
GET /api/professors/Daron%20Acemoglu
```

### GET /api/stats
Get aggregate statistics about all professors

### GET /api/areas
Get list of all research areas

### GET /api/countries
Get list of all countries represented

## 🔧 Configuration

Edit `config.py` to customize:
- App display settings
- API configuration
- Default filters
- Color scheme
- Export options

## 📊 Data Structure

Each professor profile includes:
- Name, University, Department, Title, Country
- h-index, Citation Count, Impact Score, Social Score
- Research Areas
- Top Cited Works
- Contact Information (Email, Website, Scholar, Twitter, LinkedIn)
- RA/PhD Hiring Status
- Research Interests ("Seeks")
- Awards & Recognition

## 🛠️ Usage Examples

### Using the Python API

```python
from utils import *

# Search professors
researchers = search_by_area("AI & Automation")

# Get hiring professors
hiring = get_hiring_professors()

# Get top researchers
top10 = get_top_by_impact(limit=10)

# Get statistics
stats = get_stats()
print(f"Total professors: {stats['total']}")
print(f"Average impact: {stats['avg_impact']}")
```

### Using the REST API

```bash
# Search for AI researchers in the USA
curl "http://localhost:5000/api/professors?search=AI&country=USA"

# Get stats
curl "http://localhost:5000/api/stats"

# Get all research areas
curl "http://localhost:5000/api/areas"
```

## 📁 Files

- `app.py` - Main Streamlit application
- `api.py` - Flask REST API server
- `utils.py` - Data access and utility functions
- `config.py` - Configuration settings
- `professors_data.json` - Faculty database
- `requirements.txt` - Python dependencies
- `README.md` - This file

## 📦 Dependencies

- **streamlit** - Web app framework
- **pandas** - Data manipulation
- **plotly** - Interactive visualizations
- **flask** - REST API server

See `requirements.txt` for specific versions.

## 🚢 Deployment

### Deploy Streamlit App
```bash
# Push to GitHub
git push origin main

# Deploy via Streamlit Cloud
# 1. Go to https://share.streamlit.io
# 2. Connect your GitHub repository
# 3. Select this repo and main branch
# 4. App deploys automatically
```

### Deploy API Server
```bash
# Deploy to Heroku, AWS, or your preferred platform
# Ensure Python and requirements are installed
python api.py
```

## 📝 License

This project compiles public research data about academic professionals.

## 🤝 Contributing

To add new professors or update information:

1. Edit `professors_data.json`
2. Follow the existing data structure
3. Submit a pull request

## ❓ FAQ

**Q: How is the data curated?**
A: This is a curated list of leading researchers in AI, economics, and related fields based on publication impact, social influence, and research focus.

**Q: How often is the data updated?**
A: Manually updated. Please submit updates via pull requests.

**Q: Can I use this data for my own project?**
A: Yes! Use the API or data export features.

## 📧 Contact

For questions or suggestions about individual researchers, please open an issue.

---

**Last Updated**: April 2026

import json
import os
from typing import List, Dict

def load_professors() -> List[Dict]:
    data_file = os.path.join(os.path.dirname(__file__), "professors_data.json")
    with open(data_file) as f:
        return json.load(f)

def search_by_name(name: str) -> Dict:
    profs = load_professors()
    return next((p for p in profs if name.lower() in p['name'].lower()), None)

def search_by_area(area: str) -> List[Dict]:
    profs = load_professors()
    return [p for p in profs if any(area.lower() in a.lower() for a in p['areas'])]

def search_by_university(university: str) -> List[Dict]:
    profs = load_professors()
    return [p for p in profs if university.lower() in p['university'].lower()]

def search_by_country(country: str) -> List[Dict]:
    profs = load_professors()
    return [p for p in profs if p['country'].lower() == country.lower()]

def get_hiring_professors() -> List[Dict]:
    profs = load_professors()
    return [p for p in profs if p['ra_hiring']]

def get_top_by_impact(limit: int = 10) -> List[Dict]:
    profs = load_professors()
    return sorted(profs, key=lambda p: p['impact_score'], reverse=True)[:limit]

def get_top_by_social(limit: int = 10) -> List[Dict]:
    profs = load_professors()
    return sorted(profs, key=lambda p: p['social_score'], reverse=True)[:limit]

def get_stats() -> Dict:
    profs = load_professors()
    return {
        'total': len(profs),
        'avg_impact': round(sum(p['impact_score'] for p in profs) / len(profs), 2),
        'avg_social': round(sum(p['social_score'] for p in profs) / len(profs), 2),
        'avg_hindex': round(sum(p['h_index'] for p in profs) / len(profs), 2),
        'avg_citations': round(sum(p['citations'] for p in profs) / len(profs), 0),
        'hiring': sum(1 for p in profs if p['ra_hiring']),
        'countries': len(set(p['country'] for p in profs)),
        'universities': len(set(p['university'] for p in profs)),
    }

def get_all_research_areas() -> List[str]:
    profs = load_professors()
    return sorted(set(a for p in profs for a in p['areas']))

def get_all_countries() -> List[str]:
    profs = load_professors()
    return sorted(set(p['country'] for p in profs))

def get_all_universities() -> List[str]:
    profs = load_professors()
    return sorted(set(p['university'] for p in profs))

def filter_professors(search: str = '', areas: List[str] = None,
                     country: str = '', min_impact: int = 0,
                     ra_hiring_only: bool = False) -> List[Dict]:
    profs = load_professors()

    if search:
        s = search.lower()
        profs = [p for p in profs if s in p['name'].lower() or
                s in p['university'].lower() or
                any(s in a.lower() for a in p['areas']) or
                s in p.get('seeks', '').lower()]

    if areas:
        profs = [p for p in profs if any(a in p['areas'] for a in areas)]

    if country:
        profs = [p for p in profs if p['country'] == country]

    profs = [p for p in profs if p['impact_score'] >= min_impact]

    if ra_hiring_only:
        profs = [p for p in profs if p['ra_hiring']]

    return profs

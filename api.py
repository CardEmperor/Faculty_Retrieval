from flask import Flask, request, jsonify
import json
import os

app = Flask(__name__)

def load_professors():
    data_file = os.path.join(os.path.dirname(__file__), "professors_data.json")
    with open(data_file) as f:
        return json.load(f)

@app.route('/api/professors', methods=['GET'])
def get_professors():
    profs = load_professors()

    # Filtering
    search = request.args.get('search', '').lower()
    areas = request.args.getlist('areas')
    country = request.args.get('country', '')
    min_impact = int(request.args.get('min_impact', 0))
    ra_hiring = request.args.get('ra_hiring', '').lower() == 'true'

    filtered = profs

    if search:
        filtered = [p for p in filtered if search in p['name'].lower() or
                   search in p['university'].lower() or
                   any(search in a.lower() for a in p['areas'])]

    if areas:
        filtered = [p for p in filtered if any(a in p['areas'] for a in areas)]

    if country:
        filtered = [p for p in filtered if p['country'] == country]

    filtered = [p for p in filtered if p['impact_score'] >= min_impact]

    if ra_hiring:
        filtered = [p for p in filtered if p['ra_hiring']]

    return jsonify(filtered)

@app.route('/api/professors/<name>', methods=['GET'])
def get_professor(name):
    profs = load_professors()
    prof = next((p for p in profs if p['name'].lower() == name.lower()), None)

    if prof:
        return jsonify(prof)
    return jsonify({'error': 'Professor not found'}), 404

@app.route('/api/stats', methods=['GET'])
def get_stats():
    profs = load_professors()

    stats = {
        'total_professors': len(profs),
        'avg_impact_score': sum(p['impact_score'] for p in profs) / len(profs),
        'avg_social_score': sum(p['social_score'] for p in profs) / len(profs),
        'hiring_count': sum(1 for p in profs if p['ra_hiring']),
        'countries': len(set(p['country'] for p in profs)),
        'universities': len(set(p['university'] for p in profs)),
        'top_researcher': max(profs, key=lambda p: p['impact_score'])['name']
    }

    return jsonify(stats)

@app.route('/api/areas', methods=['GET'])
def get_areas():
    profs = load_professors()
    areas = sorted(set(a for p in profs for a in p['areas']))
    return jsonify({'areas': areas})

@app.route('/api/countries', methods=['GET'])
def get_countries():
    profs = load_professors()
    countries = sorted(set(p['country'] for p in profs))
    return jsonify({'countries': countries})

if __name__ == '__main__':
    app.run(debug=True, port=5000)

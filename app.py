from flask import Flask, render_template, request
import sqlite3

app = Flask(__name__)

# Function to get locations from the database
def get_locations():
    conn = sqlite3.connect('musician_database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, city FROM locations")
    locations = cursor.fetchall()
    conn.close()
    return locations

# Function to get musicians based on selected location, instruments, and skill levels
def get_musicians_by_location_and_instruments(location_id, instrument_ids, skill_levels):
    conn = sqlite3.connect('musician_database.db')
    cursor = conn.cursor()

    # # Create placeholders for the number of instruments selected
    # placeholders = ', '.join('?' for _ in instrument_ids) - latest chatgpt didn't include this - modified the AND mi.instrument_id IN ({this-had-a-placeholder-here})

    query = f"""
        SELECT m.id, m.name
        FROM musicians m
        JOIN musician_locations ml ON m.id = ml.musician_id
        JOIN musician_instruments mi ON m.id = mi.musician_id
        WHERE ml.location_id = ?
        AND mi.instrument_id IN ({', '.join('?' for _ in instrument_ids)})
        GROUP BY m.id
        HAVING COUNT(DISTINCT mi.instrument_id) >= ?
    """

 # Debugging: Print the query and parameters
    print("SQL Query:", query)  # Debug statement
    print("Parameters:", [location_id] + instrument_ids + [len(instrument_ids)])  # Debug statement


        # Add skill level filter for each instrument (if specified)
    skill_conditions = []
    skill_params = []
    for i in range(len(instrument_ids)):
        if i < len(skill_levels) and skill_levels[i]:  # Ensure we don't go out of range
            skill_conditions.append("mi.instrument_id = ? AND mi.skill_level >= ?")
            skill_params.extend([instrument_ids[i], skill_levels[i]])
        # Ian added the above to make multiple searches work (before it was throwing an index error)
        # Ian: Something in either these sections (above or below) or the query is making it so 
        # we are able to select multiple instruments (piano, flute for alice) and show alice correctly
        # but we can only select a single skill_level, if we select more than 1 skill level it shows nobody
        # Why does the skill conditions join happen outside of the query?

    if skill_conditions:
        skill_query = " AND " + " AND ".join(skill_conditions)
        query += skill_query


    # Execute the query with location_id, instrument_ids, and skill levels
    params = [location_id] + instrument_ids + [len(instrument_ids)] + skill_params
    cursor.execute(query, params)
    musicians = cursor.fetchall()
    conn.close()

    print("fetched musicians:", musicians)

    return musicians

@app.route('/')
def index():
    locations = get_locations()
    print("Locations fetched from database:", locations)  # Debug statement
    return render_template('index.html', locations=locations)

@app.route('/search', methods=['GET'])
def search():
    location_id = request.args.get('location')
    instruments = request.args.getlist('instruments')
    skill_levels = request.args.getlist('skill_levels')
    print("Submitted skill levels:", skill_levels) # debug statement 

    # Convert instrument IDs to integers
    instrument_ids = list(map(int, instruments)) if instruments else []
    # Convert skill levels to integers, ignoring empty strings
    skill_levels = [int(level) for level in skill_levels if level.isdigit()] #check this
    locations = get_locations()
    musicians = []

    if location_id and instrument_ids:
        musicians = get_musicians_by_location_and_instruments(location_id, instrument_ids, skill_levels)

    return render_template('index.html', locations=locations, musicians=musicians, selected_location=location_id, selected_instruments=instrument_ids, selected_skills=skill_levels)

if __name__ == '__main__':
    app.run(debug=True)

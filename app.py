from flask import Flask, render_template, request, jsonify
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
    
    # Base query
    query = """
        SELECT m.id, m.name
        FROM musicians m
        INNER JOIN musician_locations ml ON m.id = ml.musician_id
        INNER JOIN musician_instruments mi ON m.id = mi.musician_id
        WHERE ml.location_id = ?
    """
    params = [location_id]

    # Instrument conditions
    if instrument_ids:
        query += " AND mi.instrument_id IN ({})".format(', '.join('?' for _ in instrument_ids))
        params.extend(instrument_ids)

    # Add skill level conditions for each instrument
    for i, instrument_id in enumerate(instrument_ids):
        if i < len(skill_levels) and skill_levels[i]:  # Only add the condition if skill level is specified
            query += f" AND EXISTS (SELECT 1 FROM musician_instruments mi_skill{i} WHERE m.id = mi_skill{i}.musician_id AND mi_skill{i}.instrument_id = ? AND mi_skill{i}.skill_level >= ?)"
            params.extend([instrument_id, skill_levels[i]])
        else:
            # If no skill level is specified, just ensure this instrument is included in the results
            query += f" AND mi.instrument_id = ?"
            params.append(instrument_id)

    # GROUP BY clause to ensure unique musicians are returned
    query += " GROUP BY m.id HAVING COUNT(DISTINCT mi.instrument_id) = ?"    
    params.append(len(instrument_ids))  # Ensure all instruments are matched


    # commenting this out for now but this is what we were working with before
    # for i, instrument_id in enumerate(instrument_ids):
    #     query = f"""
    #         SELECT m.id, m.name
    #         FROM musicians m
    #         INNER JOIN musician_locations ml ON m.id = ml.musician_id
    #         INNER JOIN musician_instruments mi{i} ON m.id = mi{i}.musician_id
    #         WHERE ml.location_id = ?
    #         AND mi.instrument_id IN ({', '.join('?' for _ in instrument_ids)})
    #         GROUP BY m.id
    #         HAVING COUNT(DISTINCT mi.instrument_id) >= ?
    #         AND (mi{i}.instrument_id = ? AND mi{i}.skill_level >= ?)
    #     """
# see in the query above, i tried to start the whole thing with the "for i" statement and put all the {i}s in where applicable (i.e. if there's more than one instrument)
# so i added the last line of the query which wasn't there before, it was in a separate statement under the "for i" thing that i've now moved to line 22 but used to exist as an append-ment after the initial query
# and i added the {i}s on line 27 as well. but if you take those things out it'll be the original query. 
# for what it's worth, the query works if you put it directly into the database (without the {i}'s. as follows - this correctly returns alice:)
# SELECT m.id, m.name
# FROM musicians m
#INNER JOIN musician_locations ml ON m.id = ml.musician_id
#INNER JOIN musician_instruments mi ON m.id = mi.musician_id
#WHERE ml.location_id = 1  -- New York location ID
#AND mi.instrument_id IN (1, 2)  -- Piano and Flute instrument IDs
#GROUP BY m.id
#HAVING COUNT(DISTINCT mi.instrument_id) >= 2  -- Searching for musicians who play both instruments
#AND (mi.instrument_id = 1 AND mi.skill_level >= 1)  -- Piano skill level 1
#AND (mi.instrument_id = 2 AND mi.skill_level >= 1); -- Flute skill level 1

    # params = [location_id, instrument_id, skill_levels[i]] - commenting out for now

    # # Group by musician to ensure unique musicians are returned
    # query += """
    #     GROUP BY m.id
    # """

        # Add skill level filter for each instrument (if specified)
    # skill_conditions = []
    # skill_params = []
    # for i in range(len(instrument_ids)):
    #     if i < len(skill_levels) and skill_levels[i]:  # Ensure we don't go out of range
    #         skill_conditions.append("mi.instrument_id = ? AND mi.skill_level >= ?")
    #         skill_params.extend([instrument_ids[i], skill_levels[i]])
    #     # Ian added the above to make multiple searches work (before it was throwing an index error)
    #     # Ian: Something in either these sections (above or below) or the query is making it so 
    #     # we are able to select multiple instruments (piano, flute for alice) and show alice correctly
    #     # but we can only select a single skill_level, if we select more than 1 skill level it shows nobody
    #     # Why does the skill conditions join happen outside of the query?

    # if skill_conditions:
    #     skill_query = " AND " + " AND ".join(skill_conditions)
    #     query += skill_query

    # # Compile parameters: start with location_id and instrument_ids
    # params = [location_id] + instrument_ids + [len(instrument_ids)] + skill_params

    # Debugging: Check final parameters and query
    print("SQL Query:", query)
    print("Parameters:", params)


    # Execute the query with location_id, instrument_ids, and skill levels
    cursor.execute(query, params)
    musicians = cursor.fetchall()
    conn.close()

    print("fetched musicians:", musicians)

    return musicians

@app.route('/')
def index():
    locations = get_locations()
    musicians = get_all_musicians()  # Fetch all musicians for initial load
    print("Locations fetched from database:", locations)  # Debug statement
    return render_template('index.html', locations=locations, musicians=musicians)

def get_all_musicians():
    conn = sqlite3.connect('musician_database.db')
    cursor = conn.cursor()
    cursor.execute("SELECT m.name FROM musicians m")
    musicians = cursor.fetchall()
    conn.close()
    return musicians

@app.route('/filter_musicians', methods=['GET'])
def filter_musicians():
    location_id = request.args.get('location')
    instruments = request.args.getlist('instruments')
    skill_levels = request.args.getlist('skill_levels')

    # Convert instrument IDs and skill levels to integers
    instrument_ids = list(map(int, instruments)) if instruments else []
    skill_levels = [int(level) for level in skill_levels if level.isdigit()]

    musicians = []

    if location_id and instrument_ids:
        musicians = get_musicians_by_location_and_instruments(location_id, instrument_ids, skill_levels)

    return jsonify(musicians)

# @app.route('/search', methods=['GET'])
# def search():
#     location_id = request.args.get('location')
#     instruments = request.args.getlist('instruments')
#     skill_levels = request.args.getlist('skill_levels')
#     print(f"Instruments selected: {instruments}")
#     print("Submitted skill levels:", skill_levels) # debug statement 

#     # Convert instrument IDs to integers
#     instrument_ids = list(map(int, instruments)) if instruments else []
#     # Convert skill levels to integers, ignoring empty strings
#     skill_levels = [int(level) for level in skill_levels if level.isdigit()] #check this
#     locations = get_locations()
#     musicians = []

#     if location_id and instrument_ids:
#         musicians = get_musicians_by_location_and_instruments(location_id, instrument_ids, skill_levels)

#     return render_template('index.html', locations=locations, musicians=musicians, selected_location=location_id, selected_instruments=instrument_ids, selected_skills=skill_levels)

if __name__ == '__main__':
    app.run(debug=True)

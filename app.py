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

# Function to get musicians based on selected location
def get_musicians_by_location(location_id):
    conn = sqlite3.connect('musician_database.db')
    cursor = conn.cursor()
    cursor.execute("""
        SELECT m.id, m.name
        FROM musicians m
        JOIN musician_locations ml ON m.id = ml.musician_id
        WHERE ml.location_id = ?
    """, (location_id,))
    musicians = cursor.fetchall()
    conn.close()
    return musicians

@app.route('/')
def index():
    locations = get_locations()
    print("Locations fetched from database:", locations)  # Debug statement
    return render_template('index.html', locations=locations)

@app.route('/search')
def search():
    location_id = request.args.get('location')
    locations = get_locations()
    musicians = get_musicians_by_location(location_id) if location_id else []
    print("Musicians fetched for location_id {}: {}".format(location_id, musicians))  # Debug output
    return render_template('index.html', locations=locations, musicians=musicians)

if __name__ == '__main__':
    app.run(debug=True)

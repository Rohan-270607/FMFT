import sqlite3
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def home():

    
    if request.method == "POST":

        event_name = request.form["event_name"]
        day = request.form["day"]
        start_time = request.form["start_time"]
        end_time = request.form["end_time"]

        conn = sqlite3.connect("events.db")
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO events (event_name, day, start_time, end_time)
            VALUES (?, ?, ?, ?)
        """, (event_name, day, start_time, end_time))

        conn.commit()
        conn.close()

        
        return redirect(url_for("home"))

    
    conn = sqlite3.connect("events.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM events
        ORDER BY day, start_time
    """)

    events = cursor.fetchall()

    conn.close()

    return render_template("index.html", events=events)


if __name__ == "__main__":
    app.run(debug=True)
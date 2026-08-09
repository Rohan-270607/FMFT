import sqlite3
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)


# -----------------------------------
# TIME CONVERSION
# -----------------------------------

def time_to_minutes(time):
    hours, minutes = map(int, time.split(":"))
    return hours * 60 + minutes


def minutes_to_time(minutes):
    hours = minutes // 60
    minutes = minutes % 60
    return f"{hours:02d}:{minutes:02d}"


# -----------------------------------
# GET ALL EVENTS
# -----------------------------------

def get_events():

    conn = sqlite3.connect("events.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM events
        ORDER BY
            CASE day
                WHEN 'Sunday' THEN 1
                WHEN 'Monday' THEN 2
                WHEN 'Tuesday' THEN 3
                WHEN 'Wednesday' THEN 4
                WHEN 'Thursday' THEN 5
                WHEN 'Friday' THEN 6
                WHEN 'Saturday' THEN 7
            END,
            start_time
    """)

    events = cursor.fetchall()

    conn.close()

    return events


# -----------------------------------
# GROUP EVENTS BY DAY
# -----------------------------------

def get_events_by_day(events):

    days = [
        "Sunday",
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday"
    ]

    events_by_day = {}

    for day in days:
        events_by_day[day] = []

    for event in events:
        events_by_day[event[2]].append(event)

    return events_by_day


# -----------------------------------
# FIND FREE TIME FOR ONE DAY
# -----------------------------------

def find_free_slots(events):

    free_slots = []

    day_start = time_to_minutes("08:00")
    day_end = time_to_minutes("22:00")

    current_time = day_start

    for event in events:

        start_time = time_to_minutes(event[3])
        end_time = time_to_minutes(event[4])

        # There is a free period before this event
        if start_time > current_time:

            free_slots.append(
                (
                    minutes_to_time(current_time),
                    minutes_to_time(start_time)
                )
            )

        # Move current time to the end of this event
        if end_time > current_time:
            current_time = end_time

    # Free time after the final event
    if current_time < day_end:

        free_slots.append(
            (
                minutes_to_time(current_time),
                minutes_to_time(day_end)
            )
        )

    return free_slots


# -----------------------------------
# FIND FREE TIME FOR ALL DAYS
# -----------------------------------

def get_free_slots(events):

    events_by_day = get_events_by_day(events)

    free_slots = {}

    for day, day_events in events_by_day.items():

        free_slots[day] = find_free_slots(day_events)

    return free_slots


# -----------------------------------
# HOME / ADD EVENT
# -----------------------------------

@app.route("/", methods=["GET", "POST"])
def home():

    if request.method == "POST":

        event_name = request.form["event_name"]
        day = request.form["day"]
        start_time = request.form["start_time"]
        end_time = request.form["end_time"]

        # Check time validity
        if start_time >= end_time:

            return render_template(
                "index.html",
                events=get_events(),
                free_slots=get_free_slots(get_events()),
                error="End time must be after start time."
            )

        conn = sqlite3.connect("events.db")
        cursor = conn.cursor()

        # Check for conflicting events
        cursor.execute("""
            SELECT event_name, start_time, end_time
            FROM events
            WHERE day = ?
            AND start_time < ?
            AND end_time > ?
        """, (
            day,
            end_time,
            start_time
        ))

        conflict = cursor.fetchone()

        conn.close()

        # Conflict found
        if conflict:

            conflict_name = conflict[0]
            conflict_start = conflict[1]
            conflict_end = conflict[2]

            error_message = (
                f'Conflict with "{conflict_name}" '
                f'({conflict_start} - {conflict_end}).'
            )

            events = get_events()

            return render_template(
                "index.html",
                events=events,
                free_slots=get_free_slots(events),
                error=error_message
            )

        # No conflict → save event
        conn = sqlite3.connect("events.db")
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO events
            (event_name, day, start_time, end_time)
            VALUES (?, ?, ?, ?)
        """, (
            event_name,
            day,
            start_time,
            end_time
        ))

        conn.commit()
        conn.close()

        return redirect(url_for("home"))

    # GET request

    events = get_events()

    free_slots = get_free_slots(events)

    return render_template(
        "index.html",
        events=events,
        free_slots=free_slots
    )


# -----------------------------------
# DELETE EVENT
# -----------------------------------

@app.route("/delete/<int:event_id>", methods=["POST"])
def delete_event(event_id):

    conn = sqlite3.connect("events.db")
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM events WHERE id = ?",
        (event_id,)
    )

    conn.commit()
    conn.close()

    return redirect(url_for("home"))


# -----------------------------------
# EDIT EVENT
# -----------------------------------

@app.route("/edit/<int:event_id>", methods=["GET", "POST"])
def edit_event(event_id):

    conn = sqlite3.connect("events.db")
    cursor = conn.cursor()

    # -------------------------------
    # SAVE EDITED EVENT
    # -------------------------------

    if request.method == "POST":

        event_name = request.form["event_name"]
        day = request.form["day"]
        start_time = request.form["start_time"]
        end_time = request.form["end_time"]

        # Check time validity
        if start_time >= end_time:

            event = (
                event_id,
                event_name,
                day,
                start_time,
                end_time
            )

            conn.close()

            return render_template(
                "edit.html",
                event=event,
                error="End time must be after start time."
            )

        # Check for conflicts
        # id != event_id prevents the event
        # from conflicting with itself

        cursor.execute("""
            SELECT event_name, start_time, end_time
            FROM events
            WHERE day = ?
            AND id != ?
            AND start_time < ?
            AND end_time > ?
        """, (
            day,
            event_id,
            end_time,
            start_time
        ))

        conflict = cursor.fetchone()

        # Conflict found
        if conflict:

            conflict_name = conflict[0]
            conflict_start = conflict[1]
            conflict_end = conflict[2]

            conn.close()

            event = (
                event_id,
                event_name,
                day,
                start_time,
                end_time
            )

            error_message = (
                f'Conflict with "{conflict_name}" '
                f'({conflict_start} - {conflict_end}).'
            )

            return render_template(
                "edit.html",
                event=event,
                error=error_message
            )

        # No conflict → update event

        cursor.execute("""
            UPDATE events
            SET event_name = ?,
                day = ?,
                start_time = ?,
                end_time = ?
            WHERE id = ?
        """, (
            event_name,
            day,
            start_time,
            end_time,
            event_id
        ))

        conn.commit()
        conn.close()

        return redirect(url_for("home"))

    # -------------------------------
    # LOAD EVENT
    # -------------------------------

    cursor.execute(
        "SELECT * FROM events WHERE id = ?",
        (event_id,)
    )

    event = cursor.fetchone()

    conn.close()

    if event is None:
        return "Event not found", 404

    return render_template(
        "edit.html",
        event=event
    )


# -----------------------------------
# RUN FLASK
# -----------------------------------

if __name__ == "__main__":
    app.run(debug=True)
    
from flask import Flask,render_template,request

app=Flask(__name__)

@app.route("/", methods=["GET","POST"])
def home():
    if request.method=="POST":
        event_name=request.form["event_name"]
        day=request.form["day"]
        start_time=request.form["start_time"]
        end_time=request.form["end_time"]

        print("Event:", event_name)
        print("Day:", day)
        print("Start:", start_time)
        print("End:", end_time)

    return render_template("index.html")

if __name__ =="__main__":
    app.run(debug=True)
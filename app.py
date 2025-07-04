from flask import Flask, render_template, request
from scraper import scrape_google_maps
import os  # Added for Render compatibility

app = Flask(__name__)

@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        city = request.form["city"]
        category = request.form["category"]
        results = scrape_google_maps(city, category)
        results = sorted(results, key=lambda x: x.get("rating", 0), reverse=True)
        return render_template("results.html", results=results, city=city, category=category)
    return render_template("index.html")

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))  # Updated for Render
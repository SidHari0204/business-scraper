from flask import Flask, render_template, request
from scraper import scrape_google_maps
import os  # Added for Render compatibility
from scraper import setup_driver

app = Flask(__name__)

@app.route("/debug")
def debug():
    try:
        driver = setup_driver()
        driver.get("https://www.google.com/maps")
        return {"status": "success", "title": driver.title}
    except Exception as e:
        return {"status": "error", "message": str(e)}

@app.route('/health')
def health():
    return {'status': 'healthy'}, 200

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
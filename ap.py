from flask import Flask, request, jsonify
from bs4 import BeautifulSoup
import requests
from datetime import datetime, timedelta

app = Flask(__name__)

@app.route("/visibility", methods=["GET"])
def get_visibility():
    try:
        start_str = request.args.get("start")
        end_str = request.args.get("end")
        if not start_str or not end_str:
            return jsonify({"error": "Missing start or end date"}), 400

        start = datetime.fromisoformat(start_str)
        end = datetime.fromisoformat(end_str)

        url = "https://tides4fishing.com/uk/wales/swansea/forecast/visibility"
        response = requests.get(url, timeout=10)
        soup = BeautifulSoup(response.text, "html.parser")

        table = soup.select_one("#weather-forecast-table")
        if not table:
            return jsonify({"error": "Visibility table not found"}), 500

        visibility_blocks = []
        rows = table.select("tr")

        current_date = None
        for row in rows:
            if "weather-day" in row.get("class", []):
                current_date = datetime.strptime(row.text.strip(), "%A %d %B %Y")
            elif "weather-hour" in row.get("class", []):
                tds = row.select("td")
                if len(tds) >= 10:
                    time_str = tds[0].text.strip()
                    try:
                        dt = datetime.strptime(time_str, "%H:%M")
                        full_time = current_date.replace(hour=dt.hour, minute=dt.minute)
                    except Exception:
                        continue

                    if full_time < start or full_time > end:
                        continue

                    vis_text = tds[9].text.strip().lower().replace("less than", "<").replace("more than", ">")
                    if "<" in vis_text:
                        meters = 1000
                    elif ">" in vis_text:
                        meters = 10000
                    else:
                        try:
                            meters = int(vis_text.split()[0]) * 1000
                        except Exception:
                            meters = None

                    if meters:
                        visibility_blocks.append(meters)

        if visibility_blocks:
            return jsonify({"min_visibility": min(visibility_blocks)})
        else:
            return jsonify({"error": "No visibility data found"}), 404

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run()

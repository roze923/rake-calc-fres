from flask import Flask, request, render_template_string, send_file
import os
import csv
from io import StringIO
from datetime import datetime

app = Flask(__name__)
history = []

HTML = """<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>還元率計算ツール</title>
    <style>
      body { font-family: Arial, sans-serif; max-width: 800px; margin: 40px auto; padding: 20px; background-color: #f9f9f9; }
      input, button, select { padding: 8px; margin-top: 8px; width: 100%; font-size: 16px; }
      h2 { text-align: center; }
      .result, .history { background-color: #fff; padding: 15px; border-radius: 5px; margin-top: 20px; }
    </style>
  </head>
  <body>
    <h2>還元率自動計算</h2>
    <form method="POST">
      <h3>基本設定</h3>
      エントリー費（円）:<br><input name="entry_fee" type="number" required><br>
      エントリー数:<br><input name="entry_count" type="number" required><br>
      賞金総額（円・任意）:<br><input name="total_prize" type="number"><br>
      チケット枚数（任意）:<br><input name="ticket_count" type="number"><br>
      1チケットの価値（円）:<br><input name="ticket_value" type="number" value="20000"><br>
      レイク（%）:<br><input name="rake_percent" type="number" value="0"><br>
      税（%）:<br><input name="tax_percent" type="number" value="0"><br>
      <h3>チケット比較（任意）</h3>
      チケット取得単価（円）:<br><input name="ticket_cost" type="number"><br>
      チケット使用枚数:<br><input name="ticket_use" type="number"><br>
      チケット使用時の現金追加額:<br><input name="ticket_cash" type="number"><br>
      <br><button type="submit">計算</button>
    </form>
    {% if result %}
    <div class="result">
      <p><strong>総参加費:</strong> {{ result.total_cost }} 円</p>
      <p><strong>賞金総額:</strong> {{ result.prize_total }} 円</p>
      <p><strong>控除後（レイク+税）:</strong> {{ result.adjusted_prize }} 円</p>
      <p><strong>現金エントリー還元率:</strong> {{ result.cash_rakeback }} %</p>
      {% if result.ticket_rakeback is not none %}
      <p><strong>チケットエントリー還元率:</strong> {{ result.ticket_rakeback }} %</p>
      {% endif %}
      <form method="GET" action="/download">
        <button type="submit">📥 CSVで履歴をダウンロード</button>
      </form>
    </div>
    {% endif %}
    {% if history %}
    <div class="history">
      <h3>履歴（最新5件）</h3>
      <ul>
        {% for h in history %}
        <li>{{ h.timestamp }} - 還元率: {{ h.cash_rakeback }}% / 賞金: {{ h.prize_total }}円 / 参加費: {{ h.total_cost }}円</li>
        {% endfor %}
      </ul>
    </div>
    {% endif %}
  </body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    global history
    result = None
    if request.method == "POST":
        try:
            entry_fee = int(request.form["entry_fee"])
            entry_count = int(request.form["entry_count"])
            total_cost = entry_fee * entry_count

            prize_total = 0
            prize_total_input = request.form.get("total_prize", "").strip()
            if prize_total_input not in ["", "0", "0.0"]:
                prize_total += int(prize_total_input)

            ticket_count = int(request.form.get("ticket_count", 0))
            ticket_value = int(request.form.get("ticket_value", 20000))
            if ticket_count > 0:
                prize_total += ticket_count * ticket_value

            rake_percent = float(request.form.get("rake_percent", 0))
            tax_percent = float(request.form.get("tax_percent", 0))
            deductions = prize_total * (rake_percent + tax_percent) / 100
            adjusted_prize = prize_total - deductions

            cash_rakeback = round((adjusted_prize / total_cost) * 100, 2) if total_cost > 0 else 0.0

            # チケット比較用
            ticket_rakeback = None
            try:
                ticket_cost = float(request.form.get("ticket_cost", 0))
                ticket_use = int(request.form.get("ticket_use", 0))
                ticket_cash = float(request.form.get("ticket_cash", 0))
                ticket_total_spent = ticket_use * ticket_cost + ticket_cash
                if ticket_total_spent > 0:
                    ticket_rakeback = round((adjusted_prize / ticket_total_spent) * 100, 2)
            except:
                ticket_rakeback = None

            result = {
                "total_cost": total_cost,
                "prize_total": prize_total,
                "adjusted_prize": round(adjusted_prize),
                "cash_rakeback": cash_rakeback,
                "ticket_rakeback": ticket_rakeback
            }

            history.insert(0, {
                "timestamp": datetime.now().strftime("%m/%d %H:%M"),
                "total_cost": total_cost,
                "prize_total": prize_total,
                "adjusted_prize": adjusted_prize,
                "cash_rakeback": cash_rakeback
            })
            history = history[:5]

        except Exception as e:
            result = {"error": str(e)}

    return render_template_string(HTML, result=result, history=history)

@app.route("/download")
def download():
    si = StringIO()
    cw = csv.writer(si)
    cw.writerow(["日時", "総参加費", "賞金総額", "控除後", "現金還元率"])
    for h in history:
        cw.writerow([h["timestamp"], h["total_cost"], h["prize_total"], round(h["adjusted_prize"]), h["cash_rakeback"]])
    si.seek(0)
    return send_file(StringIO(si.read()), mimetype="text/csv", as_attachment=True, download_name="rake_history.csv")

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)

from flask import Flask, request, render_template_string
import os

app = Flask(__name__)

HTML = """<!doctype html>
<html>
  <head>
    <meta charset="utf-8">
    <title>還元率計算ツール</title>
    <style>
      body { font-family: Arial, sans-serif; max-width: 600px; margin: 40px auto; padding: 20px; background-color: #f9f9f9; }
      input, button { padding: 8px; margin-top: 8px; width: 100%; font-size: 16px; }
      h2 { text-align: center; }
      .result { background-color: #fff; padding: 15px; border-radius: 5px; margin-top: 20px; }
    </style>
  </head>
  <body>
    <h2>還元率自動計算</h2>
    <form method="POST">
      エントリー費（円）:<br><input name="entry_fee" type="number" required><br>
      エントリー数:<br><input name="entry_count" type="number" required><br>
      賞金総額（円・任意）:<br><input name="total_prize" type="number"><br>
      チケット枚数（任意）:<br><input name="ticket_count" type="number"><br>
      1チケットの価値（円）:<br><input name="ticket_value" type="number" value="20000"><br>
      <br><button type="submit">計算</button>
    </form>
    {% if result %}
    <div class="result">
      <p><strong>総参加費:</strong> {{ result.total_cost }} 円</p>
      <p><strong>賞金総額（円）:</strong> {{ result.prize_total }} 円</p>
      <p><strong>還元率:</strong> {{ result.rakeback }} %</p>
    </div>
    {% endif %}
  </body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    if request.method == "POST":
        try:
            entry_fee = int(request.form["entry_fee"])
            entry_count = int(request.form["entry_count"])
            total_cost = entry_fee * entry_count

            # 優先：賞金総額入力 → なければチケットで計算
            prize_total_input = request.form.get("total_prize", "").strip()
            if prize_total_input != "":
                prize_total = int(prize_total_input)
            else:
                ticket_count = int(request.form.get("ticket_count", 0))
                ticket_value = int(request.form.get("ticket_value", 20000))
                prize_total = ticket_count * ticket_value

            rakeback = round((prize_total / total_cost) * 100, 2) if total_cost > 0 else 0.0

            result = {
                "total_cost": total_cost,
                "prize_total": prize_total,
                "rakeback": rakeback
            }
        except Exception as e:
            result = {"error": str(e)}

    return render_template_string(HTML, result=result)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)


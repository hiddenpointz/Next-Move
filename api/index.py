from flask import Flask, request, render_template_string, session
import math, re, requests, os, time
from dataclasses import dataclass, asdict
import openai

app = Flask(__name__)
app.secret_key = "family-risk-radar-safe-key"  # required for sessions

# ---------------- INDICATOR STACK ----------------
@dataclass
class UEDPIndicatorStack:
    turn: int
    omega_dyn: float
    i_seq: float
    at_ratio: float
    tau_rsl: float
    agency_sign: str
    strategic_verdict: str

    k_entropy: float = 0.0
    c_load: float = 0.0
    p_reserve: float = 0.0
    market_q: float = 0.0
    science_q: float = 0.0
    llm_q: float = 0.0
    prescriptions: list = None


# ---------------- ENGINE ----------------
class UnifiedUEDPEngine:
    def __init__(self, omega_ref=0.85):
        self.omega_ref = omega_ref
        self.omega_crit = 0.368
        self.openai_key = os.getenv("OPENAI_API_KEY")
        if self.openai_key:
            openai.api_key = self.openai_key

    # ---------- SAFE MARKET ----------
    def fetch_market_score(self):
        key = os.getenv("ALPHA_VANTAGE_KEY")
        if not key:
            return 5.0  # neutral fallback

        try:
            r = requests.get(
                "https://www.alphavantage.co/query",
                params={
                    "function": "GLOBAL_QUOTE",
                    "symbol": "SPY",
                    "apikey": key
                },
                timeout=4
            ).json()

            price = float(r["Global Quote"]["05. price"])
            change = abs(float(r["Global Quote"]["10. change percent"].replace("%", "")))
            return min(10.0, (price / 100) * (1 - change / 100))
        except:
            return 5.0

    # ---------- SAFE PUBMED ----------
    def fetch_pubmed_score(self, text):
        try:
            r = requests.get(
                "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
                params={
                    "db": "pubmed",
                    "term": text,
                    "retmode": "json"
                },
                timeout=4
            ).json()
            count = int(r["esearchresult"]["count"])
            return min(10.0, math.log1p(count))
        except:
            return 3.0

    # ---------- TRIANGULATION ----------
    def triangulate(self, text):
        user_q = min(10, 5 + len(re.findall(r'must|guarantee|definitely', text, re.I)))
        science_q = self.fetch_pubmed_score(text)
        ai_q = max(1, 8 - len(re.findall(r'but|risk|maybe|however', text, re.I)))
        return user_q, science_q, ai_q

    # ---------- PRESCRIPTION ----------
    def get_prescription(self, stack):
        if not self.openai_key or stack.omega_dyn >= 0.7:
            return ["System stable. No corrective intervention required."]

        try:
            prompt = (
                f"Omega={stack.omega_dyn:.3f}, "
                f"Load={stack.c_load:.1f}, "
                f"Reserves={stack.p_reserve:.1f}. "
                "Provide exactly 3 concrete risk-shielding actions."
            )

            r = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=200
            )
            return [l for l in r.choices[0].message.content.split("\n") if l.strip()]
        except:
            return ["LLM unavailable — manual stabilization advised."]

    # ---------- CORE PROCESS ----------
    def process(self, text, turn):
        uq, sq, aiq = self.triangulate(text)
        market_q = self.fetch_market_score()

        magnitude = uq*0.25 + sq*0.25 + aiq*0.15 + market_q*0.15 + 1.2
        variance = max(0.01, (10 - magnitude)/2)

        omega = math.exp(-0.4 * variance)

        stack = UEDPIndicatorStack(
            turn=turn,
            omega_dyn=omega,
            i_seq=math.sqrt(variance),
            at_ratio=(omega/self.omega_ref)*1.5,
            tau_rsl=self.omega_ref - omega,
            agency_sign="ANADOS" if omega >= self.omega_crit else "THANATOS",
            strategic_verdict="STABLE" if omega >= self.omega_crit else "CAUTION",
            k_entropy=variance,
            c_load=(10-aiq),
            p_reserve=sq*0.6,
            market_q=market_q,
            science_q=sq,
            llm_q=5.0
        )

        stack.prescriptions = self.get_prescription(stack)
        return stack


engine = UnifiedUEDPEngine()

# ---------------- UI ----------------
TEMPLATE = """
<!doctype html>
<html>
<head>
<title>Family Risk Radar</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<style>
body { font-family: Arial; background:#f3f4f6; padding:20px; }
.card { background:white; padding:20px; margin-bottom:20px; border-radius:8px; }
</style>
</head>
<body>

<div class="card">
<h2>🛡️ Family Risk Radar</h2>
<form method="POST">
<textarea name="text" rows="4" style="width:100%"></textarea><br><br>
<button type="submit">Analyze</button>
</form>
</div>

{% if result %}
<div class="card">
<b>Verdict:</b> {{ result.strategic_verdict }}<br>
<b>Omega:</b> {{ result.omega_dyn }}
</div>

<div class="card">
<h3>Prescriptions</h3>
<ul>{% for p in result.prescriptions %}<li>{{ p }}</li>{% endfor %}</ul>
</div>

<div class="card">
<canvas id="chart"></canvas>
</div>
{% endif %}

<script>
{% if history %}
new Chart(document.getElementById('chart'), {
    type: 'line',
    data: {
        labels: {{ labels|tojson }},
        datasets: [{
            label: 'Ω Coherence',
            data: {{ history|tojson }},
            tension: 0.3
        }]
    }
});
{% endif %}
</script>

</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    if "history" not in session:
        session["history"] = []

    result = None
    if request.method == "POST":
        text = request.form.get("text", "")
        turn = len(session["history"]) + 1
        result = engine.process(text, turn)
        session["history"].append(result.omega_dyn)

    return render_template_string(
        TEMPLATE,
        result=result,
        history=session["history"],
        labels=[f"T{i+1}" for i in range(len(session["history"]))],
    )


if __name__ == "__main__":
    app.run(debug=True)

from flask import Flask, request, render_template_string
import math, re, requests, os
from dataclasses import dataclass, asdict
import openai

app = Flask(__name__)

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
    s_latency: float = 0.0
    p_reserve: float = 0.0
    prescriptions: list = None

    user_q: float = 0.0
    science_q: float = 0.0
    ai_mental_q: float = 0.0
    market_q: float = 0.0
    llm_q: float = 0.0


# ---------------- ENGINE ----------------
class UnifiedUEDPEngine:
    def __init__(self, omega_ref=0.85):
        self.omega_ref = omega_ref
        self.omega_crit = 0.368
        self.turn = 0

        self.openai_key = os.getenv("OPENAI_API_KEY")
        if self.openai_key:
            openai.api_key = self.openai_key

    # ---------- HIGH QUALITY PRESCRIPTION ----------
    def get_high_quality_prescription(self, stack):
        if not self.openai_key:
            return ["LLM prescription unavailable (no API key)."]

        if stack.omega_dyn >= 0.70:
            return ["System already stable (ANADOS). No corrective action required."]

        prompt = (
            "You are an expert systems strategist.\n\n"
            f"Omega: {stack.omega_dyn:.3f}\n"
            f"Cognitive Load: {stack.c_load:.1f}\n"
            f"Strategic Reserves: {stack.p_reserve:.1f}\n\n"
            "Provide exactly 3 concrete, testable actions "
            "to shift this system from instability to stability.\n\n"
            "Format:\n"
            "1. Action\n2. Action\n3. Action"
        )

        try:
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=250
            )
            text = response.choices[0].message.content.strip()
            return [l.strip() for l in text.split("\n") if l.strip()]
        except Exception as e:
            return [f"Prescription generation failed safely: {e}"]

    # ---------- TRIANGULATION ----------
    def get_triangulation(self, text):
        uq = min(10.0, 5.0 + len(re.findall(r'must|guarantee|definitely', text, re.I)))
        sq = min(10.0, 4.0 + len(re.findall(r'research|data|study|science', text, re.I)))
        aiq = max(1.0, 8.0 - len(re.findall(r'but|risk|maybe|however', text, re.I)))
        return uq, sq, aiq

    # ---------- CORE PROCESS ----------
    def process(self, text_input):
        self.turn += 1
        uq, sq, aiq = self.get_triangulation(text_input)

        magnitude = uq*0.3 + sq*0.3 + aiq*0.2 + 1.5
        variance = max(0.01, (10 - magnitude)/2)

        omega_dyn = math.exp(-0.4 * variance)
        i_seq = math.sqrt(variance)

        p_reserve = sq * 0.6
        c_load = (10 - aiq)

        stack = UEDPIndicatorStack(
            turn=self.turn,
            omega_dyn=omega_dyn,
            i_seq=i_seq,
            at_ratio=(omega_dyn/self.omega_ref)*1.5,
            tau_rsl=self.omega_ref - omega_dyn,
            agency_sign="ANADOS" if omega_dyn >= self.omega_crit else "THANATOS",
            strategic_verdict="STABLE" if omega_dyn >= self.omega_crit else "CAUTION",
            p_reserve=p_reserve,
            c_load=c_load,
            user_q=uq,
            science_q=sq,
            ai_mental_q=aiq,
            llm_q=5.0
        )

        stack.prescriptions = self.get_high_quality_prescription(stack)
        return stack


# ---------------- FLASK ----------------
engine = UnifiedUEDPEngine()
history = []

TEMPLATE = """
<!doctype html>
<html>
<head>
<title>Family Risk Radar</title>
<style>
body { font-family: Arial; background:#f4f4f4; padding:20px; }
.card { background:white; padding:20px; margin-bottom:20px; border-radius:8px; }
</style>
</head>
<body>

<div class="card">
<h2>🛡️ Family Risk Radar</h2>
<form method="POST">
<textarea name="text_input" rows="5" style="width:100%"></textarea><br><br>
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
<ul>
{% for p in result.prescriptions %}
<li>{{ p }}</li>
{% endfor %}
</ul>
</div>
{% endif %}

</body>
</html>
"""

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    if request.method == "POST":
        text = request.form.get("text_input", "")
        if text:
            result = engine.process(text)
            history.append(result.omega_dyn)
    return render_template_string(TEMPLATE, result=result)


if __name__ == "__main__":
    app.run(debug=True)

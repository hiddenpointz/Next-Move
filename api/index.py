from flask import Flask, request, render_template_string
import math
from dataclasses import dataclass

app = Flask(__name__)

# --- ENGINE ---
@dataclass
class UEDPIndicatorStack:
    turn: int
    omega_dyn: float
    i_seq: float
    at_ratio: float
    tau_rsl: float
    agency_sign: str

class UnifiedUEDPEngine:
    def __init__(self, omega_ref=0.85):
        self.omega_ref = omega_ref
        self.omega_crit = 0.368
        self.x_history = []
        self.turn_count = 0

    def process_turn(self, user_text):
        self.turn_count += 1
        x_j = (0.4 * (len(user_text) % 10)) + 1.5
        self.x_history.append(x_j)

        mean_x = sum(self.x_history) / len(self.x_history)
        variance = (
            sum((x - mean_x) ** 2 for x in self.x_history) / len(self.x_history)
            if len(self.x_history) > 1 else 0
        )

        i_seq = math.sqrt(variance)
        omega_dyn = math.exp(-1.0 * (0.4 * variance + 0.3))
        tau_rsl = self.omega_ref - omega_dyn
        agency = "ANADOS (Growth)" if omega_dyn >= self.omega_crit else "THANATOS (Braking)"
        at_ratio = (omega_dyn / self.omega_ref) * 1.2

        return UEDPIndicatorStack(
            self.turn_count, omega_dyn, i_seq, at_ratio, tau_rsl, agency
        )

engine = UnifiedUEDPEngine()
history_omega = []

HTML = """
<h2>🛡️ Family Risk Radar</h2>
<form method="POST">
<textarea name="text" rows="3"></textarea><br>
<button type="submit">Analyze</button>
</form>

{% if result %}
<p><b>{{ result.agency_sign }}</b></p>
<p>Ω {{ "%.4f"|format(result.omega_dyn) }}</p>
{% endif %}
"""

@app.route("/", methods=["GET", "POST"])
def index():
    result = None
    if request.method == "POST":
        text = request.form.get("text", "")
        if text:
            result = engine.process_turn(text)
            history_omega.append(result.omega_dyn)

    return render_template_string(HTML, result=result)

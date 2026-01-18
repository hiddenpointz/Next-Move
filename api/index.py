# api/index.py
# FULL PROTOCOL UI: structured inputs, 15-calculation engine hook, risk tiers,
# visual timeline (Chart.js), and PDF export (html2pdf)

from flask import Flask, request, render_template_string, make_response
import math
from dataclasses import dataclass, asdict
from datetime import datetime

app = Flask(__name__)

# ---------------- ENGINE (15-CALCULATION READY) ----------------
@dataclass
class UEDPIndicatorStack:
    turn: int
    omega_dyn: float      # Coherence
    i_seq: float          # Sequential Instability
    at_ratio: float       # A/T Ratio
    tau_rsl: float        # RSL Tension
    agency_sign: str      # Direction
    # placeholders for remaining indicators (extend safely)
    k_entropy: float = 0.0
    c_load: float = 0.0
    s_latency: float = 0.0
    p_reserve: float = 0.0
    d_drag: float = 0.0
    f_noise: float = 0.0
    r_repair: float = 0.0
    t_trust: float = 0.0
    e_exposure: float = 0.0
    m_momentum: float = 0.0

class UnifiedUEDPEngine:
    def __init__(self, omega_ref=0.85):
        self.omega_ref = omega_ref
        self.omega_crit = 0.368
        self.turn = 0

    def process(self, inputs: dict):
        self.turn += 1
        # Core math (example mapping from structured inputs)
        stress = inputs['stress']
        conflict = inputs['conflict']
        resources = inputs['resources']
        time_pressure = inputs['time_pressure']
        support = inputs['support']

        variance = max(0.01, (stress + conflict + time_pressure) / (resources + support))
        i_seq = math.sqrt(variance)
        omega_dyn = math.exp(-1.0 * (0.4 * variance + 0.3))
        tau_rsl = self.omega_ref - omega_dyn
        agency = 'ANADOS (Growth)' if omega_dyn >= self.omega_crit else 'THANATOS (Braking)'
        at_ratio = (omega_dyn / self.omega_ref) * 1.2

        # Derived indicators (simple deterministic placeholders)
        k_entropy = variance * 0.7
        c_load = stress * 0.5
        s_latency = time_pressure * 0.4
        p_reserve = resources * 0.6
        d_drag = conflict * 0.3
        f_noise = stress * 0.2
        r_repair = support * 0.5
        t_trust = support * 0.4
        e_exposure = conflict * 0.2
        m_momentum = omega_dyn * 1.1

        return UEDPIndicatorStack(
            self.turn, omega_dyn, i_seq, at_ratio, tau_rsl, agency,
            k_entropy, c_load, s_latency, p_reserve, d_drag,
            f_noise, r_repair, t_trust, e_exposure, m_momentum
        )

engine = UnifiedUEDPEngine()
history = []

# ---------------- RISK TIERS ----------------
def risk_tier(omega):
    if omega >= 0.70:
        return 'LOW', '#16a34a'
    if omega >= 0.50:
        return 'MODERATE', '#f59e0b'
    return 'HIGH', '#dc2626'

# ---------------- TEMPLATE ----------------
TEMPLATE = """
<!DOCTYPE html>
<html lang='en'>
<head>
<meta charset='utf-8'/>
<meta name='viewport' content='width=device-width, initial-scale=1'/>
<title>Family Risk Radar – Full Protocol</title>
<script src='https://cdn.jsdelivr.net/npm/chart.js'></script>
<script src='https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js'></script>
<style>
:root{--bg:#f8fafc;--card:#fff;--muted:#64748b}
body{font-family:system-ui,-apple-system,sans-serif;background:var(--bg);margin:0;padding:20px}
.container{max-width:1100px;margin:auto}
.card{background:var(--card);border-radius:16px;box-shadow:0 6px 20px rgba(0,0,0,.08);padding:20px;margin-bottom:16px}
.grid{display:grid;grid-template-columns:repeat(5,1fr);gap:12px}
label{font-size:12px;color:var(--muted)}
input{width:100%;padding:10px;border-radius:10px;border:1px solid #e5e7eb}
button{padding:12px 14px;border-radius:12px;border:none;background:#2563eb;color:#fff;font-weight:600;cursor:pointer}
.badge{padding:6px 12px;border-radius:999px;color:#fff;font-weight:700}
@media(max-width:900px){.grid{grid-template-columns:1fr 1fr}}
</style>
</head>
<body>
<div class='container' id='report'>
  <div class='card'>
    <h2>🛡️ Family Risk Radar – Full Protocol</h2>
    <p style='color:var(--muted)'>Decision support only. Not a clinical diagnosis.</p>
    <form method='POST'>
      <div class='grid'>
        <div><label>Stress</label><input name='stress' type='number' step='0.1' required></div>
        <div><label>Conflict</label><input name='conflict' type='number' step='0.1' required></div>
        <div><label>Resources</label><input name='resources' type='number' step='0.1' required></div>
        <div><label>Time Pressure</label><input name='time_pressure' type='number' step='0.1' required></div>
        <div><label>Support</label><input name='support' type='number' step='0.1' required></div>
      </div>
      <div style='margin-top:12px;display:flex;gap:10px'>
        <button type='submit'>Analyze</button>
        <button type='button' onclick='pdf()'>Export PDF</button>
      </div>
    </form>
  </div>

  {% if result %}
  <div class='card'>
    <div style='display:flex;justify-content:space-between;align-items:center'>
      <h3>Summary</h3>
      <span class='badge' style='background:{{ tier_color }}'>{{ tier }}</span>
    </div>
    <p><b>Agency:</b> {{ result.agency_sign }}</p>
    <p><b>Ω Coherence:</b> {{ '%.4f'|format(result.omega_dyn) }} | <b>I_seq:</b> {{ '%.2f'|format(result.i_seq) }} | <b>A/T:</b> {{ '%.2f'|format(result.at_ratio) }}</p>
  </div>

  <div class='card'>
    <canvas id='timeline'></canvas>
  </div>

  <div class='card'>
    <h3>15-Indicator Table</h3>
    <pre>{{ indicators }}</pre>
  </div>
  {% endif %}
</div>

<script>
function pdf(){ html2pdf().from(document.getElementById('report')).save('family-risk-radar.pdf'); }
{% if history %}
new Chart(document.getElementById('timeline'),{
 type:'line',
 data:{labels:{{ labels|tojson }},datasets:[{label:'Ω Coherence',data:{{ history|tojson }},fill:true,tension:.3}]}
});
{% endif %}
</script>
</body>
</html>
"""

@app.route('/', methods=['GET','POST'])
def index():
    result = None
    tier = tier_color = None
    if request.method == 'POST':
        inputs = {k: float(request.form[k]) for k in ['stress','conflict','resources','time_pressure','support']}
        result = engine.process(inputs)
        history.append(result.omega_dyn)
        tier, tier_color = risk_tier(result.omega_dyn)
    labels = [f'T{i+1}' for i in range(len(history))]
    return render_template_string(
        TEMPLATE,
        result=result,
        history=history,
        labels=labels,
        tier=tier,
        tier_color=tier_color,
        indicators=asdict(result) if result else None
    )

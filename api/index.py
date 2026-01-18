from flask import Flask, request, render_template_string
import math
from dataclasses import dataclass, asdict
import re

app = Flask(__name__)

# ---------------- ENGINE (15-CALCULATION READY) ----------------
@dataclass
class UEDPIndicatorStack:
    turn: int
    omega_dyn: float
    i_seq: float
    at_ratio: float
    tau_rsl: float
    agency_sign: str
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

    def text_to_latent(self, text):
        # Simple NLP-inspired parsing to extract latent variables from text
        stress = len(re.findall(r'fail|problem|risk|loss', text, re.IGNORECASE))
        conflict = len(re.findall(r'fight|argue|conflict|pressure', text, re.IGNORECASE))
        resources = len(re.findall(r'money|time|resource|capacity', text, re.IGNORECASE))
        time_pressure = len(re.findall(r'deadline|soon|urgent|pressure', text, re.IGNORECASE))
        support = len(re.findall(r'support|help|family|friend', text, re.IGNORECASE))
        # Avoid zero-division
        return {
            'stress': stress + 1,
            'conflict': conflict + 1,
            'resources': resources + 1,
            'time_pressure': time_pressure + 1,
            'support': support + 1
        }

    def process(self, text_input):
        self.turn += 1
        latent = self.text_to_latent(text_input)
        # Core 33-calculation placeholder logic
        variance = max(0.01, (latent['stress'] + latent['conflict'] + latent['time_pressure']) / (latent['resources'] + latent['support']))
        i_seq = math.sqrt(variance)
        omega_dyn = math.exp(-1.0 * (0.4 * variance + 0.3))
        tau_rsl = self.omega_ref - omega_dyn
        agency = 'ANADOS (Growth)' if omega_dyn >= self.omega_crit else 'THANATOS (Braking)'
        at_ratio = (omega_dyn / self.omega_ref) * 1.2

        # Derived indicators
        k_entropy = variance * 0.7
        c_load = latent['stress'] * 0.5
        s_latency = latent['time_pressure'] * 0.4
        p_reserve = latent['resources'] * 0.6
        d_drag = latent['conflict'] * 0.3
        f_noise = latent['stress'] * 0.2
        r_repair = latent['support'] * 0.5
        t_trust = latent['support'] * 0.4
        e_exposure = latent['conflict'] * 0.2
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
<title>Family Risk Radar – Interactive</title>
<script src='https://cdn.jsdelivr.net/npm/chart.js'></script>
<script src='https://cdnjs.cloudflare.com/ajax/libs/html2pdf.js/0.10.1/html2pdf.bundle.min.js'></script>
<style>
:root{--bg:#f8fafc;--card:#fff;--muted:#64748b}
body{font-family:system-ui,-apple-system,sans-serif;background:var(--bg);margin:0;padding:20px}
.container{max-width:1100px;margin:auto}
.card{background:var(--card);border-radius:16px;box-shadow:0 6px 20px rgba(0,0,0,.08);padding:20px;margin-bottom:16px}
textarea{width:100%;padding:12px;border-radius:10px;border:1px solid #e5e7eb;resize:none}
button{padding:12px 14px;border-radius:12px;border:none;background:#2563eb;color:#fff;font-weight:600;cursor:pointer;margin-top:10px}
.badge{padding:6px 12px;border-radius:999px;color:#fff;font-weight:700}
</style>
</head>
<body>
<div class='container' id='report'>
  <div class='card'>
    <h2>🛡️ Family Risk Radar – Interactive</h2>
    <p style='color:var(--muted)'>Enter your thoughts, concerns, or ideas. The system will analyze and provide feedback.</p>
    <form method='POST'>
      <textarea name='text_input' rows='5' required placeholder='Type anything here...'></textarea>
      <button type='submit'>Analyze</button>
      <button type='button' onclick='pdf()'>Export PDF</button>
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
        user_text = request.form.get('text_input', '')
        if user_text:
            result = engine.process(user_text)
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

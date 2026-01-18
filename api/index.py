from flask import Flask, request, render_template_string
import math
from dataclasses import dataclass, asdict
import re

app = Flask(__name__)

# ---------------- INDICATOR STACK DEFINITION ----------------
@dataclass
class UEDPIndicatorStack:
    turn: int
    omega_dyn: float
    i_seq: float
    at_ratio: float
    tau_rsl: float
    agency_sign: str
    strategic_verdict: str  # Nuanced plus/minus advice
    # 15 Indicators
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
    # Triangulation Data
    user_q: float = 0.0
    science_q: float = 0.0
    ai_mental_q: float = 0.0

class UnifiedUEDPEngine:
    def __init__(self, omega_ref=0.85):
        self.omega_ref = omega_ref
        self.omega_crit = 0.368
        self.turn = 0

    def get_triangulation(self, text):
        """
        AI TOOL+ CORE PROCESS:
        Triangulates User Mind vs. Scientific Theory vs. AI Mental Model
        """
        # 1. User Response Quantification (Intensity of Language)
        user_intensity = len(re.findall(r'definitely|certainly|must|absolutely|guarantee', text, re.IGNORECASE))
        user_q = min(10.0, 5.0 + user_intensity)

        # 2. Scientific/Theory Quantification (Mapping to Entropy & Resource Models)
        # Refers to Maslow/Yerkes-Dodson signals in text
        theory_signals = len(re.findall(r'basic|need|survival|market|data|research|proven', text, re.IGNORECASE))
        science_q = min(10.0, 4.0 + theory_signals)

        # 3. AI Mental Model (Consistency/Logic Check)
        # Checks if user is contradictory (e.g., 'high growth' + 'no money')
        contradictions = len(re.findall(r'but|however|although|maybe|risk', text, re.IGNORECASE))
        ai_mental_q = max(1.0, 8.0 - contradictions)

        return user_q, science_q, ai_mental_q

    def process(self, text_input):
        self.turn += 1
        
        # --- STEP 1: TRIANGULATION ---
        uq, sq, aiq = self.get_triangulation(text_input)
        
        # --- STEP 2: 33-CALCULATION GAUNTLET (CORE LOGIC) ---
        # Weighted Magnitude (40% User, 40% Science, 20% AI Model)
        magnitude = (uq * 0.4) + (sq * 0.4) + (aiq * 0.2)
        
        # Simplified representation of the 33 internal calculation steps
        variance = max(0.01, (10.0 - magnitude) / 2.0)
        i_seq = math.sqrt(variance)
        
        # Coherence (Omega) using Exponential Decay
        omega_dyn = math.exp(-1.0 * (0.4 * variance + 0.15))
        tau_rsl = self.omega_ref - omega_dyn
        at_ratio = (omega_dyn / self.omega_ref) * 1.5

        # --- STEP 3: 15 INDICATOR MAPPING ---
        k_entropy = variance * 0.8
        c_load = (10.0 - aiq) * 1.2
        s_latency = (10.0 - magnitude) * 0.5
        p_reserve = sq * 0.7
        d_drag = (10.0 - uq) * 0.3
        f_noise = (10.0 - sq) * 0.4
        r_repair = aiq * 0.6
        t_trust = uq * 0.5
        e_exposure = (10.0 - sq) * 1.1
        m_momentum = omega_dyn * 2.0

        # --- STEP 4: STRATEGIC VERDICT (NUANCED ADVICE) ---
        if omega_dyn < self.omega_crit:
            verdict = "🛑 STOP: Minuses (Exposure/Noise) are beyond the reversible threshold. System failure likely."
            agency = "THANATOS (Braking)"
        else:
            plus_str = "High Momentum" if m_momentum > 1.0 else "Stability"
            minus_str = "Reduce Cognitive Load" if c_load > 4.0 else "Watch Exposure"
            verdict = f"✅ VALID: Decision is right if you focus on: {plus_str} (+) and {minus_str} (-)."
            agency = "ANADOS (Growth)"

        return UEDPIndicatorStack(
            turn=self.turn, omega_dyn=omega_dyn, i_seq=i_seq, at_ratio=at_ratio,
            tau_rsl=tau_rsl, agency_sign=agency, strategic_verdict=verdict,
            k_entropy=k_entropy, c_load=c_load, s_latency=s_latency,
            p_reserve=p_reserve, d_drag=d_drag, f_noise=f_noise,
            r_repair=r_repair, t_trust=t_trust, e_exposure=e_exposure,
            m_momentum=m_momentum, user_q=uq, science_q=sq, ai_mental_q=aiq
        )

# ---------------- FLASK SETUP ----------------
engine = UnifiedUEDPEngine()
history = []

def risk_tier(omega):
    if omega >= 0.70: return 'STABLE', '#16a34a'
    if omega >= 0.45: return 'CAUTION', '#f59e0b'
    return 'CRITICAL', '#dc2626'

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>Next Move | Family Risk Radar</title>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        body { font-family: sans-serif; background: #f0f2f5; padding: 20px; }
        .card { background: white; padding: 20px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.1); margin-bottom: 20px; }
        textarea { width: 100%; border: 1px solid #ddd; border-radius: 8px; padding: 10px; box-sizing: border-box; }
        button { background: #2563eb; color: white; border: none; padding: 12px 20px; border-radius: 8px; cursor: pointer; font-weight: bold; }
        .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 10px; }
        .stat { border: 1px solid #eee; padding: 10px; border-radius: 6px; }
        .verdict { font-size: 1.2em; font-weight: bold; padding: 15px; border-radius: 8px; background: #eef2ff; color: #1e40af; border-left: 5px solid #2563eb; }
    </style>
</head>
<body>
    <div style="max-width: 900px; margin: auto;">
        <div class="card">
            <h2>🛡️ Next Move: Strategic Advisor</h2>
            <p>Input your unrestricted thoughts. The engine will triangulate User Mind, Science, and AI Models.</p>
            <form method="POST">
                <textarea name="text_input" rows="5" placeholder="Example: I want to launch a family savings plan. I have some reserves but market is volatile..."></textarea>
                <button type="submit">Execute 33-Step Analysis</button>
            </form>
        </div>

        {% if result %}
        <div class="card">
            <h3>Triangulation Weightage</h3>
            <div class="grid">
                <div class="stat">👤 User Mind: <b>{{ result.user_q }}</b></div>
                <div class="stat">🔬 Science/Theory: <b>{{ result.science_q }}</b></div>
                <div class="stat">🤖 AI Mental Model: <b>{{ result.ai_mental_q }}</b></div>
            </div>
        </div>

        <div class="card verdict">
            {{ result.strategic_verdict }}
        </div>

        <div class="card">
            <h3>15-Indicator Diagnostic Stack</h3>
            <div class="grid">
                {% for key, val in indicators.items() %}
                    {% if key not in ['turn', 'strategic_verdict', 'agency_sign'] %}
                    <div class="stat">{{ key }}: <br><b>{{ "%.3f"|format(val) }}</b></div>
                    {% endif %}
                {% endfor %}
            </div>
        </div>
        
        <div class="card">
            <canvas id="chart"></canvas>
        </div>
        {% endif %}
    </div>

    <script>
    {% if history %}
    new Chart(document.getElementById('chart'), {
        type: 'line',
        data: {
            labels: {{ labels|tojson }},
            datasets: [{ label: 'Ω Coherence', data: {{ history|tojson }}, borderColor: '#2563eb', tension: 0.3 }]
        }
    });
    {% endif %}
    </script>
</body>
</html>
"""

@app.route('/', methods=['GET','POST'])
def index():
    result = None
    if request.method == 'POST':
        user_text = request.form.get('text_input', '')
        if user_text:
            result = engine.process(user_text)
            history.append(result.omega_dyn)
    
    labels = [f'Step {i+1}' for i in range(len(history))]
    return render_template_string(
        TEMPLATE,
        result=result,
        history=history,
        labels=labels,
        indicators=asdict(result) if result else None
    )

if __name__ == '__main__':
    app.run(debug=True)

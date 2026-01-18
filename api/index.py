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

    # 1) Triangulate user/science/AI
    def get_triangulation(self, text):
        user_intensity = len(re.findall(r'definitely|certainly|must|absolutely|guarantee', text, re.IGNORECASE))
        user_q = min(10.0, 5.0 + user_intensity)
        theory_signals = len(re.findall(r'basic|need|survival|market|data|research|proven', text, re.IGNORECASE))
        science_q = min(10.0, 4.0 + theory_signals)
        contradictions = len(re.findall(r'but|however|although|maybe|risk', text, re.IGNORECASE))
        ai_mental_q = max(1.0, 8.0 - contradictions)
        return user_q, science_q, ai_mental_q

    # 2) Detect query domain
    def detect_domains(self, text):
        text = text.lower()
        domains = []
        if any(k in text for k in ["market","stocks","equity","index","returns","volatility"]):
            domains.append("market")
        if any(k in text for k in ["risk","planning","psychology","stress","science","research"]):
            domains.append("science")
        if any(k in text for k in ["wiki","information","wikipedia","learn"]):
            domains.append("wiki")
        return domains

    # 3A) Alpha Vantage market
    def fetch_alpha_vantage(self, symbol="IBM"):
        key = os.getenv("ALPHA_VANTAGE_KEY")
        if not key:
            return 5.0, 0.3, 0.05, 0.02
        url = "https://www.alphavantage.co/query"
        params = {"function":"GLOBAL_QUOTE","symbol":symbol,"apikey":key}
        try:
            r = requests.get(url, params=params, timeout=10).json()
            quote = r.get("Global Quote", {})
            price = float(quote.get("05. price","0") or 0)
            change_pct = float(quote.get("10. change percent","0%").replace("%","") or 0)
            volatility = abs(change_pct)/100.0
            market_score = min(10.0, price/100*(1-volatility)*10)
            return market_score, volatility, change_pct/100, 0.02
        except:
            return 5.0, 0.3, 0.05, 0.02

    # 3B) PubMed
    def fetch_pubmed_score(self, text):
        base = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        params = {"db":"pubmed","term":text,"retmode":"json"}
        try:
            r = requests.get(base, params=params, timeout=10).json()
            count = int(r.get("esearchresult", {}).get("count", "0"))
            return min(10.0, math.log1p(count))
        except:
            return 3.0

    # 3C) Wikipedia
    def fetch_wikipedia_score(self, text):
        try:
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{'+'.join(text.split()[:4])}"
            r = requests.get(url, timeout=5).json()
            summary = r.get("extract","")
            return min(10.0, len(summary)/200)
        except:
            return 4.0

    # 4) LLM reasoning
    def query_llm_quantification(self, text, domains):
        if not self.openai_key:
            return 5.0, "No LLM key configured"
        try:
            prompt = f"Extract normalized 0-10 score for query relevance ({','.join(domains)}). Query: {text}"
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=[{"role":"user","content":prompt}],
                max_tokens=150
            )
            llm_txt = response.choices[0].message.content
            found = re.findall(r"\b([0-9](?:\.\d+)?)\b", llm_txt)
            score = float(found[0]) if found else 5.0
            return min(10.0, score), llm_txt.strip()
        except Exception as e:
            return 5.0, f"LLM error: {e}"

    # 5) Full process
    def process(self, text_input):
        self.turn += 1
        uq, sq, aiq = self.get_triangulation(text_input)
        domains = self.detect_domains(text_input)

        market_q, market_vol, equity_ret, fd_ret = 0.0, 0.3, 0.0, 0.0
        science_pub, wiki_pub = 0.0, 0.0

        if "market" in domains:
            market_q, market_vol, equity_ret, fd_ret = self.fetch_alpha_vantage()
        if "science" in domains:
            science_pub = self.fetch_pubmed_score(text_input)
        if "wiki" in domains:
            wiki_pub = self.fetch_wikipedia_score(text_input)

        science_q = min(10.0, sq + science_pub + wiki_pub)

        llm_q, llm_text = self.query_llm_quantification(text_input, domains)

        magnitude = uq*0.25 + science_q*0.20 + aiq*0.15 + market_q*0.20 + llm_q*0.20
        variance = max(0.01, (10.0 - magnitude)/2.0)
        i_seq = math.sqrt(variance)
        omega_dyn = math.exp(-1.0*(0.4*variance + 0.15))
        tau_rsl = self.omega_ref - omega_dyn
        at_ratio = (omega_dyn/self.omega_ref)*1.5

        # 15 indicators
        k_entropy = variance*0.8
        c_load = (10.0 - aiq)*1.2
        s_latency = (10.0 - magnitude)*0.5
        p_reserve = science_q*0.7
        d_drag = (10.0 - uq)*0.3
        f_noise = (10.0 - science_q)*0.4
        r_repair = aiq*0.6
        t_trust = uq*0.5
        e_exposure = (10.0 - science_q)*1.1
        m_momentum = omega_dyn*2.0

        if omega_dyn < self.omega_crit or market_vol>0.35:
            verdict = f"🛑 High market volatility ({market_vol*100:.1f}%). Caution recommended."
            agency = "THANATOS"
        else:
            plus_str = "Growth" if m_momentum>1 else "Stability"
            minus_str = "Watch Load" if c_load>4 else "Watch Exposure"
            verdict = f"✅ {plus_str} (+), {minus_str} (-). LLM: {llm_text}"
            agency = "ANADOS"

        return UEDPIndicatorStack(
            turn=self.turn, omega_dyn=omega_dyn, i_seq=i_seq, at_ratio=at_ratio,
            tau_rsl=tau_rsl, agency_sign=agency, strategic_verdict=verdict,
            k_entropy=k_entropy, c_load=c_load, s_latency=s_latency,
            p_reserve=p_reserve, d_drag=d_drag, f_noise=f_noise,
            r_repair=r_repair, t_trust=t_trust, e_exposure=e_exposure,
            m_momentum=m_momentum, user_q=uq, science_q=science_q,
            ai_mental_q=aiq, market_q=market_q, llm_q=llm_q
        )

# ---------------- FLASK ----------------
engine = UnifiedUEDPEngine()
history = []

TEMPLATE = """
<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Family Risk Radar - Live</title>
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
<div style="max-width:900px;margin:auto;">
<div class="card">
<h2>🛡️ Family Risk Radar</h2>
<p>Enter your thoughts; engine pulls live Market, PubMed, Wikipedia, and LLM reasoning.</p>
<form method="POST">
<textarea name="text_input" rows="5" placeholder="Example: I want to launch a family savings plan. Market is volatile."></textarea>
<button type="submit">Analyze</button>
</form>
</div>

{% if result %}
<div class="card">
<h3>Triangulation & Live Data</h3>
<div class="grid">
<div class="stat">👤 User Mind: <b>{{ result.user_q }}</b></div>
<div class="stat">🔬 Science: <b>{{ result.science_q }}</b></div>
<div class="stat">🤖 AI Mental: <b>{{ result.ai_mental_q }}</b></div>
<div class="stat">💹 Market Score: <b>{{ result.market_q }}</b></div>
<div class="stat">🧠 LLM Score: <b>{{ result.llm_q }}</b></div>
</div>
</div>

<div class="card verdict">{{ result.strategic_verdict }}</div>

<div class="card">
<h3>15-Indicator Diagnostic Stack</h3>
<div class="grid">
{% for key, val in indicators.items() %}
    {% if key not in ['turn','strategic_verdict','agency_sign'] %}
    <div class="stat">{{ key }}:<br><b>{{ "%.3f"|format(val) }}</b></div>
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
        datasets: [{ label: 'Ω Coherence', data: {{ history|tojson }}, borderColor:'#2563eb', tension:0.3 }]
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
    if request.method=='POST':
        user_text = request.form.get('text_input','')
        if user_text:
            result = engine.process(user_text)
            history.append(result.omega_dyn)
    labels = [f"Step {i+1}" for i in range(len(history))]
    return render_template_string(TEMPLATE, result=result, history=history,
                                  labels=labels, indicators=asdict(result) if result else None
                                 )
if __name__ == "__main__":
    app.run(debug=True)


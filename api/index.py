from flask import Flask, request, render_template_string
import math, re, os, asyncio, aiohttp
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
    # 15+ indicators
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
    extra1: float = 0.0
    extra2: float = 0.0
    # Triangulation
    user_q: float = 0.0
    science_q: float = 0.0
    ai_mental_q: float = 0.0
    market_q: float = 0.0
    llm_q: float = 0.0
    prescriptions: list = None

# ---------------- ENGINE ----------------
class UnifiedUEDPEngine:
    def __init__(self, omega_ref=0.85):
        self.omega_ref = omega_ref
        self.omega_crit = 0.368
        self.turn = 0
        # Let OpenAI SDK handle key itself
        self.openai_key = os.getenv("OPENAI_API_KEY")
        if self.openai_key:
            openai.api_key = self.openai_key

    # Triangulate user/science/AI
    def get_triangulation(self, text):
        user_intensity = len(re.findall(r'definitely|certainly|must|absolutely|guarantee', text, re.IGNORECASE))
        user_q = min(10.0, 5.0 + user_intensity)
        theory_signals = len(re.findall(r'basic|need|survival|market|data|research|proven', text, re.IGNORECASE))
        science_q = min(10.0, 4.0 + theory_signals)
        contradictions = len(re.findall(r'but|however|although|maybe|risk', text, re.IGNORECASE))
        ai_mental_q = max(1.0, 8.0 - contradictions)
        return user_q, science_q, ai_mental_q

    # Detect query domains
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

    # ---------------- ASYNC FETCHES ----------------
    async def fetch_alpha_vantage(self, session, symbol="IBM"):
        key = os.getenv("ALPHA_VANTAGE_KEY")
        if not key:
            return 5.0, 0.3
        try:
            url = "https://www.alphavantage.co/query"
            params = {"function":"GLOBAL_QUOTE","symbol":symbol,"apikey":key}
            async with session.get(url, params=params, timeout=5) as r:
                data = await r.json()
            price = float(data.get("Global Quote", {}).get("05. price", 100))
            change_pct = float(data.get("Global Quote", {}).get("10. change percent","0%").replace("%",""))
            volatility = abs(change_pct)/100.0
            market_score = min(10.0, price/100*(1-volatility)*10)
            return market_score, volatility
        except:
            return 5.0, 0.3

    async def fetch_pubmed_score(self, session, text):
        try:
            url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
            params = {"db":"pubmed","term":text,"retmode":"json"}
            async with session.get(url, params=params, timeout=5) as r:
                data = await r.json()
            count = int(data.get("esearchresult", {}).get("count","0"))
            return min(10.0, math.log1p(count))
        except:
            return 3.0

    async def fetch_wikipedia_score(self, session, text):
        try:
            url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{'+'.join(text.split()[:4])}"
            async with session.get(url, timeout=5) as r:
                data = await r.json()
            summary = data.get("extract","")
            return min(10.0, len(summary)/200)
        except:
            return 4.0

    async def get_high_quality_prescription(self, stack):
        if not self.openai_key:
            return ["LLM API key not set."]
        if stack.omega_dyn >= 0.7:
            return ["System stable. No corrective intervention required."]
        prompt = (
            f"UEDP State:\nOmega={stack.omega_dyn:.3f}, Load={stack.c_load:.1f}, "
            f"Reserves={stack.p_reserve:.1f}, Market={stack.market_q:.1f}\n"
            "Provide exactly 3 high-resolution strategic actions to flip from THANATOS to ANADOS."
        )
        try:
            response = await openai.ChatCompletion.acreate(
                model="gpt-3.5-turbo",
                messages=[{"role":"user","content":prompt}],
                temperature=0.3,
                max_tokens=300
            )
            text = response.choices[0].message.content.strip()
            return [line.strip() for line in text.split("\n") if line.strip()]
        except:
            return ["LLM prescription generation failed."]

    # ---------------- FULL PROCESS ----------------
    async def process(self, text_input):
        self.turn += 1
        uq, sq, aiq = self.get_triangulation(text_input)
        domains = self.detect_domains(text_input)

        market_q, market_vol = 0.0, 0.3
        science_pub, wiki_pub = 0.0, 0.0

        async with aiohttp.ClientSession() as session:
            tasks = []
            if "market" in domains:
                tasks.append(self.fetch_alpha_vantage(session))
            else:
                tasks.append(asyncio.sleep(0, result=(5.0,0.3)))
            if "science" in domains:
                tasks.append(self.fetch_pubmed_score(session, text_input))
            else:
                tasks.append(asyncio.sleep(0, result=0.0))
            if "wiki" in domains:
                tasks.append(self.fetch_wikipedia_score(session, text_input))
            else:
                tasks.append(asyncio.sleep(0, result=0.0))
            results = await asyncio.gather(*tasks)
            market_q, market_vol = results[0]
            science_pub = results[1]
            wiki_pub = results[2]

            # Generate LLM prescriptions asynchronously
            stack_for_llm = UEDPIndicatorStack(
                turn=self.turn, omega_dyn=0.0, i_seq=0.0, at_ratio=0.0, tau_rsl=0.0,
                agency_sign="", strategic_verdict="", k_entropy=0, c_load=0, s_latency=0,
                p_reserve=0, d_drag=0, f_noise=0, r_repair=0, t_trust=0,
                e_exposure=0, m_momentum=0, extra1=0, extra2=0,
                user_q=uq, science_q=sq, ai_mental_q=aiq,
                market_q=market_q, llm_q=5.0
            )
            prescriptions_task = asyncio.create_task(self.get_high_quality_prescription(stack_for_llm))

        science_q = min(10.0, sq + science_pub + wiki_pub)
        llm_q = 5.0  # fallback

        magnitude = uq*0.25 + science_q*0.20 + aiq*0.15 + market_q*0.20 + llm_q*0.20
        variance = max(0.01, (10.0 - magnitude)/2.0)
        i_seq = math.sqrt(variance)
        omega_dyn = math.exp(-1.0*(0.4*variance + 0.15))
        tau_rsl = self.omega_ref - omega_dyn
        at_ratio = (omega_dyn/self.omega_ref)*1.5

        # 15+ indicators
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
        extra1 = market_q*0.5
        extra2 = variance*0.6

        agency = "ANADOS" if omega_dyn >= self.omega_crit else "THANATOS"
        verdict = f"✅ System Stable" if agency=="ANADOS" else f"🛑 CAUTION"

        prescriptions = await prescriptions_task

        return UEDPIndicatorStack(
            turn=self.turn, omega_dyn=omega_dyn, i_seq=i_seq, at_ratio=at_ratio,
            tau_rsl=tau_rsl, agency_sign=agency, strategic_verdict=verdict,
            k_entropy=k_entropy, c_load=c_load, s_latency=s_latency,
            p_reserve=p_reserve, d_drag=d_drag, f_noise=f_noise,
            r_repair=r_repair, t_trust=t_trust, e_exposure=e_exposure,
            m_momentum=m_momentum, extra1=extra1, extra2=extra2,
            user_q=uq, science_q=science_q, ai_mental_q=aiq,
            market_q=market_q, llm_q=llm_q,
            prescriptions=prescriptions
        )

# ---------------- FLASK ----------------
engine = UnifiedUEDPEngine()
history = []

TEMPLATE = """<!DOCTYPE html>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Family Risk Radar</title>
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
<textarea name="text_input" rows="5" placeholder="Example: Family savings plan. Market is volatile."></textarea>
<button type="submit">Analyze</button>
</form>
</div>

{% if result %}
<div class="card">
<h3>Indicators & Triangulation</h3>
<div class="grid">
{% for key, val in indicators.items() %}
    {% if key not in ['turn','strategic_verdict','agency_sign','prescriptions'] %}
    <div class="stat">{{ key }}:<br><b>{{ "%.3f"|format(val) }}</b></div>
    {% endif %}
{% endfor %}
</div>
</div>

<div class="card verdict">
{{ result.strategic_verdict }}<br>
Prescriptions:
<ul>
{% for p in result.prescriptions %}
<li>{{ p }}</li>
{% endfor %}
</ul>
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
        datasets: [{ label: 'Ω Coherence', data: {{ history|tojson }}, borderColor:'#2563eb', tension:0.3, fill:false }]
    },
    options: { responsive:true, maintainAspectRatio:false }
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
            result = asyncio.run(engine.process(user_text))
            history.append(result.omega_dyn)
    labels = [f"Step {i+1}" for i in range(len(history))]
    return render_template_string(TEMPLATE, result=result, history=history,
                                  labels=labels, indicators=asdict(result) if result else None)

if __name__=="__main__":
    app.run(debug=True)

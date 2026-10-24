"""
A complete, realistic sample for the idea in intake_data/sample_intake.json (CropLink).

It is written in the SAME shape the AI returns, then passed through the SAME
normalisers the agents use. It powers:
  * the "Sample report" page (so visitors can see a finished report instantly),
  * the offline test (a fake AI returns these payloads).

It is illustrative content, clearly labelled as a sample on the site.
"""
import json
import os

from framework import RESEARCH_SPLITS, MARKETS
from scoring import normalize_evaluation, assemble_research

HERE = os.path.dirname(__file__)

# ------------------------------- evaluation -------------------------------
_PK = [
    (8, "Farmers losing a large share of crop value to commission agents is a recurring, well-known pain. The founder has seen real sale slips, and grocers also feel price and freshness problems."),
    (7, "Punjab has a huge smallholder base and a large urban grocery market. Only connected farmers near Lahore and Multan are reachable at first, which still gives a workable pilot."),
    (5, "Farmers switch only if net income beats the arthi after fees and payment delays. Grocers may move for a 10% saving but are used to wholesaler credit."),
    (5, "A small take-rate on thin-margin produce can be wiped out by delivery and spoilage costs. Unit economics are untested and no logistics partner is signed."),
    (6, "The mandi and arthi system is entrenched and offers credit and guaranteed buying. Named rivals exist, but a WhatsApp-only, two-district focus is a credible wedge."),
    (6, "WhatsApp and mobile wallets are widely used, but cold-chain, reliable delivery and rural connectivity are uneven, and no payment or logistics stack is planned yet."),
    (7, "A produce marketplace faces few licences, but market-committee rules, food safety and sales-tax registration need checking. Arthis may resist being bypassed."),
    (4, "Perishables need aggregation, grading, transport and returns handling. A solo non-technical founder with no logistics partner is the weakest link in the plan."),
    (5, "Farmers' arthi relationships include credit and trust, so a young newcomer must prove on-time payment. Village agents can help, but trust builds slowly."),
    (5, "Repeating district by district is feasible, but inflation, fuel costs and crop seasonality strain thin margins, and local execution capacity is the limit."),
]
_GL = [
    (6, "Digital agri supply chains and B2B produce marketplaces are a large, growing category worldwide, but a single-country WhatsApp model addresses only a slice of it."),
    (6, "Intermediary losses for smallholders appear in many emerging markets, so the problem travels. Logistics and credit needs differ a lot by country."),
    (4, "A WhatsApp-first, hyper-local approach is easy to copy, and funded agri-tech firms already operate in several emerging markets. There is no data or network moat yet."),
    (5, "Take-rate marketplaces can work at scale, but logistics-heavy models often struggle with profit abroad. Produce is close to a commodity, which limits pricing power."),
    (5, "The playbook of aggregating, grading and delivering can be repeated, but each country needs local agents and logistics, so scaling is operations-heavy."),
    (6, "Food safety, trade and data rules vary by country, but few block a marketplace outright. Payments and licensing need country-level checks."),
    (5, "Language, crops, payment habits and WhatsApp reliance differ by region, so each new market needs local partnerships and product changes."),
    (4, "Reaching farmers abroad depends on field agents or cooperatives, which are costly and slow to build. No channel plan beyond Pakistan exists yet."),
    (4, "Logistics-heavy marketplaces need real working capital, and investors want proven unit economics that a pilot-stage solo founder cannot yet show."),
    (4, "New countries add currency, regulatory and supplier risk. Resilience depends on proving the model in Pakistan before any expansion."),
]


def raw_eval():
    def block(rows, summary):
        return {
            "summary": summary,
            "criteria": [{"id": i + 1, "score": s, "rationale": r} for i, (s, r) in enumerate(rows)],
        }
    return {
        "idea_summary": "A WhatsApp-based marketplace that lets small Punjab farmers sell directly to urban grocers, cutting out commission agents.",
        "pakistan": block(_PK, "The problem is real and a focused pilot near Lahore and Multan is realistic. Logistics, trust and thin margins, not demand, decide whether it works."),
        "global": block(_GL, "The problem exists in many markets, but a WhatsApp-first marketplace has little defensibility alone. Global potential depends on a repeatable, profitable playbook proven in Pakistan first."),
        "biggest_strength": "A clearly felt problem with first-hand evidence and a narrow, testable starting market.",
        "biggest_risk": "Delivery, spoilage and trust costs could erase a thin margin before the model proves itself.",
        "recommendation": "Validate further before building",
        "recommendation_reasoning": "Demand looks real, but logistics, unit economics and farmer trust are unproven. A small manual pilot will answer these cheaply before any build.",
        "priority_actions": [
            "Run a four-week manual pilot with 10 farmers and 5 grocers in one district and measure net price gain, spoilage and delivery cost per kilo.",
            "Sign a logistics or cold-chain partner and price the delivery leg per order before writing any software.",
            "Use no-code WhatsApp tools or find a technical co-founder so the ordering flow can ship in weeks.",
            "Interview 15 arthis and 15 farmers to learn what credit and guaranteed buying they offer and how to match it.",
        ],
    }


# -------------------------------- research --------------------------------
def _s(i, findings, analysis, data, validate, conf):
    return {"id": i, "findings": findings, "analysis": analysis,
            "data_points": data, "validate_next": validate, "confidence": conf}


_PK_RESEARCH = [
    _s(1, ["Farmers often accept mandi prices set through commission agents, so the gap between farm-gate and retail price is a daily complaint.",
           "Grocers report quality and freshness variation when buying through wholesalers.",
           "The founder's own sale slips are useful evidence but still anecdotal."],
       "The problem looks real and repeated, but severity differs by crop and season. The pilot should start with two crops where the price gap is widest.",
       ["Commission and handling deductions of roughly 5-10% of sale value are often reported (estimate; verify with real slips)."],
       ["Collect 30 real sale slips across two seasons.", "Interview 10 grocers about rejected stock and price swings."], "Medium"),
    _s(2, ["Start with vegetable farmers on 2-10 acres near Lahore and Multan who already use WhatsApp.",
           "Buyers split into neighbourhood grocers, small supermarkets and restaurants.",
           "Farmers who trust a relative or cooperative leader are the likeliest early adopters."],
       "Choosing one crop, one district and one buyer type keeps the pilot small and makes delivery routes predictable.",
       [], ["Map 50 farmers and 30 buyers within a 60 km radius.", "Rank segments by crop value and delivery distance."], "Medium"),
    _s(3, ["Farmers switch only if net income clearly beats the arthi after transport and payment delays.",
           "Grocers compare price per kilo and reliability first, and many rely on wholesaler credit.",
           "A small delivery fee may be accepted if produce arrives fresher."],
       "Price sensitivity is high on both sides, so the take-rate must stay small and be shown openly.",
       ["A 3-5% take-rate plus a delivery fee is a starting hypothesis (estimate)."],
       ["Run a price test with two take-rate levels.", "Ask grocers what discount justifies giving up credit."], "Low"),
    _s(4, ["Punjab is Pakistan's main vegetable-growing province with a very large smallholder base.",
           "Urban grocery demand around Lahore is large and grows with the population.",
           "Only the connected, nearby share of farmers is reachable in year one."],
       "Total demand is large. The reachable pilot market is a few thousand farmers and hundreds of grocers, which is enough to test the model.",
       ["A year-one target of 100-300 farmers and 50-150 buyers is a planning assumption (estimate)."],
       ["Count grocers and restaurants within delivery range using map data.", "Check district agriculture office crop statistics."], "Medium"),
    _s(5, ["The mandi and arthi chain is the main alternative and provides credit, guaranteed buying and local trust.",
           "The founder names Tazah and Farmdar as similar services working at larger scale.",
           "Wholesalers and informal WhatsApp groups also link farmers and buyers directly."],
       "Informal alternatives are the real competitor. The edge is convenience and price transparency, not technology.",
       [], ["Interview 10 arthis about which services farmers value most.", "Study the named competitors' pricing, coverage and complaints."], "Medium"),
    _s(6, ["Thin produce margins mean delivery and spoilage costs decide profitability.",
           "Small grocers order modest quantities, so delivery cost per order is high unless routes are batched.",
           "Payment delays and cash handling add working-capital pressure."],
       "A positive margin per order is possible only with batched routes and low spoilage. Model it before scaling.",
       ["A contribution of a few percent of order value after delivery is the target (estimate)."],
       ["Build a per-order cost model from real transport quotes.", "Track spoilage on 20 pilot deliveries."], "Low"),
    _s(7, ["WhatsApp groups and local field agents are the most direct channels to farmers.",
           "Grocers can be reached through market visits and referrals.",
           "Word of mouth from the first satisfied farmers will matter more than ads."],
       "Acquisition is relationship-driven and local, so budget should go to field agents and trust-building rather than digital ads.",
       [], ["Recruit two village agents on commission and track sign-ups per week.", "Test a referral reward for farmers."], "Medium"),
    _s(8, ["Agricultural marketing may involve market committee rules, food-safety standards and provincial regulations.",
           "Business registration and sales-tax duties apply once revenue grows.",
           "Handling money brings payment compliance rules."],
       "No single licence appears to block a pilot, but requirements vary by district and must be confirmed locally.",
       [], ["Ask a local lawyer or the market committee which permits apply.", "Check whether holding customer funds needs a licensed payment partner."], "Low"),
    _s(9, ["WhatsApp and mobile wallets are widely used, but rural connectivity and smartphone use vary.",
           "Cold-chain and reliable transport are limited, adding cost and spoilage risk.",
           "Last-mile delivery to many small grocers is hard to batch."],
       "Logistics is the make-or-break area. A reliable transport partner matters more than any software feature.",
       [], ["Get quotes from three transport operators for fixed routes.", "Test a voice-note ordering flow for farmers with low literacy."], "Medium"),
    _s(10, ["Farmers trust long-standing arthi relationships that include credit and social obligations.",
            "A young newcomer needs visible proof of fair weighing and on-time payment.",
            "Respected local figures such as cooperative leaders can speed up trust."],
       "Trust, not technology, is the main adoption barrier. Expanding district by district is realistic once a trust playbook is proven.",
       [], ["Pilot a pay-on-delivery guarantee and measure repeat sales.", "Ask 10 farmers what would make them try a new buyer."], "Medium"),
]

_GL_RESEARCH = [
    _s(1, ["Digital agricultural supply chains and B2B produce marketplaces are a large, growing category across emerging markets.",
           "Growth is driven by smartphone adoption and pressure to cut intermediary costs.",
           "A WhatsApp-first model sits at the small, informal end of the category."],
       "The category is big, but a district-level pilot addresses a very small slice. The opportunity depends on repeating the playbook.",
       ["No reliable global figure is claimed here. Size the category from independent industry reports before pitching (estimate needed)."],
       ["Gather two or three independent reports on agri B2B marketplaces.", "List five countries with similar smallholder and mandi structures."], "Low"),
    _s(2, ["Many countries in South Asia, Africa and Latin America share long, intermediary-heavy produce chains.",
           "The pain is similar, but the shape of the middleman differs by country.",
           "Ordering habits, including WhatsApp use, differ by region."],
       "The core problem travels well, but the solution needs local adaptation. Start with countries that share Pakistan's market structure.",
       [], ["Interview two farmers or founders in a neighbouring market.", "Compare mandi-style systems in India and Bangladesh."], "Medium"),
    _s(3, ["A WhatsApp-first design is easy for others to copy.",
           "Funded agri-tech companies already run marketplaces in several emerging markets.",
           "Possible moats are trusted local networks, farmer data and reliable logistics partnerships."],
       "There is no strong moat yet. Defensibility would come from local network density and data on farmers and buyers, not from technology.",
       [], ["Map five funded competitors and note what they do not cover.", "Decide which proprietary data you can collect from day one."], "Medium"),
    _s(4, ["Farmers want higher net income and quicker payment.",
           "Buyers want fresher produce at a fair price with reliable delivery.",
           "Product-market fit is unproven because no transactions have happened yet."],
       "The promise is clear, but fit can only be shown with repeat orders. Measure repeat purchase and net price gain in the pilot.",
       [], ["Define a fit signal such as 60% of pilot farmers selling again.", "Track grocer reorder rate over six weeks."], "Low"),
    _s(5, ["A take-rate on each transaction is the simplest model, with delivery fees and premium grading as options.",
           "Produce is close to a commodity, which limits pricing power.",
           "Software-like margins are hard once logistics is included."],
       "Revenue is likely a small percentage of order value, so volume and low cost per order matter most.",
       ["Take-rates of a few percent are a starting assumption (estimate)."],
       ["Model margin at 3%, 5% and 8% take-rates with real delivery costs.", "Test a paid quality-grading add-on."], "Low"),
    _s(6, ["Field agents and cooperatives are the likeliest way to reach farmers abroad, at a real cost per farmer.",
           "Retention depends on timely payment and steady demand.",
           "Grocer lifetime value grows with repeat weekly orders."],
       "Lifetime value can be attractive if buyers order weekly, but acquiring people-by-people is slow and costly.",
       [], ["Track cost per active farmer and per active grocer in the pilot.", "Measure twelve-week retention on both sides."], "Low"),
    _s(7, ["A WhatsApp ordering flow is technically simple with existing chat and payment tools.",
           "The harder parts are matching supply to demand, grading and routing deliveries.",
           "Scaling needs a proper order and logistics system, not only chat."],
       "Technology is not the barrier. A basic version can be built quickly with no-code tools, while scale needs better routing and data.",
       [], ["Prototype the ordering flow with an existing WhatsApp business tool.", "List the manual steps that must be automated first."], "High"),
    _s(8, ["Food safety, trade and licensing rules differ by country.",
           "Data protection rules apply once personal data is collected.",
           "Brand and name protection are low-cost early steps."],
       "Rules rarely block a marketplace outright, but each country needs checking. Handle personal data carefully from the start.",
       [], ["Check requirements in the first one or two target countries.", "Register the brand name in Pakistan before expanding."], "Low"),
    _s(9, ["Language, local crops and payment habits change by region.",
           "Partnering with cooperatives or local logistics firms speeds entry.",
           "A sensible order is Pakistan first, then a similar neighbouring market."],
       "Expand by copying a proven playbook into markets with a similar structure rather than entering many at once.",
       [], ["Choose a pilot partner in a second country only after Pakistan metrics are strong.", "Document the playbook step by step."], "Medium"),
    _s(10, ["Working capital for payments and logistics is the main cost, not software.",
            "Investors usually want proven unit economics before funding expansion.",
            "Currency, regulation and supplier risk grow abroad."],
       "Capital needs rise quickly with each new market. Prove profitability in one district before raising money.",
       ["Early funding is likely to be small and angel-sized (estimate)."],
       ["Build a 12-month cash plan with working-capital needs.", "Talk to two agri-tech investors about the traction they expect."], "Low"),
]

_EXTRAS = {
    "pakistan": {
        "snapshot": "Pakistan offers a real, repeated problem and a workable pilot market near Lahore and Multan. The hard parts are logistics, trust and thin margins, not demand. A small, tightly measured pilot should come before any build.",
        "key_risks": [
            {"risk": "Spoilage and delivery costs erase the thin margin.", "mitigation": "Batch routes, start with two durable crops and model cost per order before scaling."},
            {"risk": "Farmers stay loyal to arthis who provide credit.", "mitigation": "Offer payment guarantees and recruit trusted local agents."},
            {"risk": "A solo non-technical founder cannot ship the ordering flow.", "mitigation": "Use no-code WhatsApp tools or find a technical co-founder."},
        ],
        "validation_plan": [
            {"when": "Days 1-30", "action": "Interview 15 farmers, 15 grocers and 10 arthis, and collect real sale slips."},
            {"when": "Days 31-60", "action": "Run a manual pilot over WhatsApp with 10 farmers and 5 grocers."},
            {"when": "Days 61-90", "action": "Measure net price gain, spoilage and delivery cost, then decide whether to build."},
        ],
    },
    "global": {
        "snapshot": "The problem exists in many markets, but a WhatsApp-first marketplace has little defensibility on its own. Global potential depends on proving a repeatable, profitable playbook in Pakistan first.",
        "key_risks": [
            {"risk": "Funded competitors can copy the model easily.", "mitigation": "Build local network density and proprietary farmer and price data."},
            {"risk": "A logistics-heavy model needs more capital than expected.", "mitigation": "Prove unit economics in one district before expanding."},
            {"risk": "Each country needs different partners and rules.", "mitigation": "Pick one similar market and enter through a local partner."},
        ],
        "validation_plan": [
            {"when": "Days 1-30", "action": "Shortlist two similar countries and review their produce supply chains."},
            {"when": "Days 31-60", "action": "Interview five farmers or buyers in the best-fit country."},
            {"when": "Days 61-90", "action": "Write the repeatable playbook from the Pakistan pilot and test it on paper for a second market."},
        ],
    },
}

_RESEARCH = {"pakistan": _PK_RESEARCH, "global": _GL_RESEARCH}


def raw_research(market: str, part: str):
    """What the fake AI returns for one research call (market + part A/B)."""
    lo, hi = next((lo, hi) for p, lo, hi in RESEARCH_SPLITS if p == part)
    out = {"sections": _RESEARCH[market][lo:hi]}
    if part == "A":
        out["snapshot"] = _EXTRAS[market]["snapshot"]
    else:
        out["key_risks"] = _EXTRAS[market]["key_risks"]
        out["validation_plan"] = _EXTRAS[market]["validation_plan"]
    return out


def sample_intake():
    with open(os.path.join(HERE, "intake_data", "sample_intake.json"), "r", encoding="utf-8") as f:
        data = json.load(f)
    for key in ("progress_so_far", "needs_most"):
        if isinstance(data.get(key), list):
            data[key] = ", ".join(data[key])
    return data


def build_demo_result():
    """The full normalised result for the sample idea."""
    parts = [(m, p, lo, hi, raw_research(m, p)) for m in MARKETS for (p, lo, hi) in RESEARCH_SPLITS]
    return {
        "intake": sample_intake(),
        "evaluation": normalize_evaluation(raw_eval()),
        "research": assemble_research(parts),
        "meta": {"id": "sample", "generated_at": "", "is_sample": True},
    }

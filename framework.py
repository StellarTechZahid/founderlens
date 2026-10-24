"""
The FoundersLens frameworks, copied from the two PDFs you supplied:

  * FoundersLens_Startup_Evaluation_Parameters.pdf  -> EVALUATION (scored 1-10)
  * Startup_Business_Research_Parameters_Pakistan_Global.pdf -> RESEARCH (written up)

Each market has exactly 10 parameters, so 20 evaluation criteria and 20 research
areas in total. The prompts, the score maths, the PDFs and the website all read
from this file, so changing a name or description here changes it everywhere.

`asks` is a one-line plain-English description of what each parameter looks at.
It is used on the Framework page and given to the AI as guidance.
"""


def _p(items):
    return [{"id": i + 1, "name": n, "asks": a} for i, (n, a) in enumerate(items)]


# ---------------------------------------------------------------------------
# EVALUATION (scored 1-10)  - FoundersLens_Startup_Evaluation_Parameters.pdf
# ---------------------------------------------------------------------------
EVAL_PAKISTAN = _p([
    ("Market Demand & Problem Severity",
     "How painful and frequent is the problem for Pakistani customers, and is demand already visible?"),
    ("Total Addressable Market & Reachable Demand",
     "How many customers exist in Pakistan, and how many can realistically be reached?"),
    ("Purchasing Power & Willingness to Pay",
     "Can the target customers afford it, and will they pay the price the business needs?"),
    ("Revenue Model & Local Unit Economics",
     "Do margins, acquisition cost and customer lifetime value work in rupees?"),
    ("Competition & Existing Alternatives",
     "Who solves this today, including informal, manual and offline alternatives?"),
    ("Digital & Physical Infrastructure Readiness",
     "Do connectivity, devices, payments and logistics support the product?"),
    ("Regulatory, Legal & Tax Feasibility",
     "Which licences, regulators and taxes apply, and how hard are they to meet?"),
    ("Supply Chain & Operational Feasibility",
     "Can the idea be delivered reliably with local suppliers, people and processes?"),
    ("Trust, Adoption & Customer Behavior",
     "Will customers trust and adopt it given local habits and cultural norms?"),
    ("Scalability, Resilience & Local Execution",
     "Can it grow across cities and survive inflation, currency and policy shocks?"),
])

EVAL_GLOBAL = _p([
    ("Global Market Size & Growth Potential",
     "How large and fast-growing is the international market for this?"),
    ("Global Problem-Solution Fit",
     "Is the problem real outside Pakistan, and does the solution fit it?"),
    ("Competitive Advantage & Defensibility",
     "What makes the idea hard to copy for well-funded global players?"),
    ("Global Business Model & Profitability",
     "Does the model reach healthy margins at international prices?"),
    ("Scalability & Replicability",
     "Can it be repeated in new countries without rebuilding the business?"),
    ("International Regulatory & Legal Compatibility",
     "Do privacy, licensing, IP and trade rules allow it abroad?"),
    ("Localization & Cross-Cultural Fit",
     "How much must language, product and messaging change from market to market?"),
    ("Customer Acquisition & Distribution Potential",
     "Can it reach customers abroad affordably through repeatable channels?"),
    ("Capital Requirements & Funding Attractiveness",
     "How much capital is needed, and would investors want to fund it?"),
    ("Market Entry Risk & Long-Term Resilience",
     "What are the biggest risks of entering new markets, and can the business endure them?"),
])

# ---------------------------------------------------------------------------
# RESEARCH (written up) - Startup_Business_Research_Parameters_Pakistan_Global.pdf
# ---------------------------------------------------------------------------
RESEARCH_PAKISTAN = _p([
    ("Problem Severity & Local Demand",
     "Evidence that Pakistani customers feel the problem strongly and already act on it."),
    ("Target Customer and Market Segmentation",
     "Who the first customers are, how they split into segments, and which segment to start with."),
    ("Willingness to Pay & Price Sensitivity",
     "What people pay today for alternatives and how price changes affect their choice."),
    ("Market Size, Reachable Demand & Growth",
     "Size of the market, the part that can be reached, and how fast it is growing."),
    ("Competitive Landscape and Informal Alternatives",
     "Direct competitors, substitutes and the informal ways people solve this today."),
    ("Local Purchasing Power & Unit Economics",
     "Income levels, cost to serve, margin per customer and break-even logic in rupees."),
    ("Distribution, Sales Channels & Customer Acquisition",
     "Which channels reach customers, what they cost, and how the first 100 customers are won."),
    ("Regulatory, Tax, Licensing & Compliance Requirements",
     "Registrations, licences, taxes and compliance duties that apply in Pakistan."),
    ("Infrastructure, Payments, Logistics & Operational Fit",
     "Connectivity, payment rails, delivery and day-to-day operations in local conditions."),
    ("Cultural Fit, Trust, Adoption Barriers & Scalability",
     "What slows adoption, how trust is built, and whether the model scales across regions."),
])

RESEARCH_GLOBAL = _p([
    ("Global Market Size, Growth & Addressable Opportunity",
     "Global market size, growth rate and the share a new entrant could realistically address."),
    ("Cross-Market Problem Validation & Customer Demand",
     "Whether the same problem and demand exist in other countries, and where it is strongest."),
    ("Differentiation, Competitive Moat & Substitutes",
     "Who competes globally, what the moat is, and which substitutes could replace the product."),
    ("Value Proposition & Product–Market Fit",
     "The promise to customers, and signs that the product fits what the market wants."),
    ("Revenue Model, Pricing Power & Unit Economics",
     "How the business earns, how much pricing power it has, and what each customer is worth."),
    ("Customer Acquisition, Retention & Lifetime Value",
     "How customers are found and kept abroad, and what they are worth over time."),
    ("Technical Feasibility, Innovation & Scalability",
     "Whether it can be built, how novel it is, and whether the technology scales."),
    ("Country-by-Country Regulation, Privacy & IP Protection",
     "Rules, data protection and intellectual-property issues in the likeliest target countries."),
    ("Localization, Partnerships & Go-to-Market Strategy",
     "Language, partners and the sequence of markets to enter."),
    ("Capital Requirements, Risk Exposure & Long-Term Resilience",
     "Money needed to expand, the main risks, and how well the business withstands them."),
])

MARKETS = ("pakistan", "global")
MARKET_LABEL = {"pakistan": "Pakistan", "global": "Global"}

EVAL_PARAMS = {"pakistan": EVAL_PAKISTAN, "global": EVAL_GLOBAL}
RESEARCH_PARAMS = {"pakistan": RESEARCH_PAKISTAN, "global": RESEARCH_GLOBAL}

# The research calls are split in two halves per market so each AI reply stays
# short enough to finish cleanly (long JSON replies are what get cut off).
RESEARCH_SPLITS = (("A", 0, 5), ("B", 5, 10))

# Recommendation values the evaluator may return (anything else is mapped).
RECOMMENDATIONS = (
    "Proceed to build",
    "Validate further before building",
    "Pivot needed",
    "Do not proceed as-is",
)

assert all(len(v) == 10 for v in EVAL_PARAMS.values())
assert all(len(v) == 10 for v in RESEARCH_PARAMS.values())

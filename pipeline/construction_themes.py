"""Construction-sector sub-themes + polarity signs.

The macro themes in config.py answer "how is the economy doing". These answer
"how is the construction sector doing" — the corpus on EILA is sector-specific,
so the six macro buckets collapse into one and tell us nothing.

Signs work exactly like THEME_SIGN in config.py: finBERT reads "cement prices
soar" as POSITIVE (soar is bullish), but rising input costs are bad for the
sector. health = sign * tone.
"""
from __future__ import annotations
import re

# Each theme: word-boundary regex alternatives. An article can carry several.
THEMES = {
    "demand_orders": r"order book|new orders?|order inflow|bags? (?:the )?order|"
        r"wins? (?:a |the )?contract|contract wins?|awarded|awarding|bid|tender|"
        r"L1 |letter of award|project pipeline|capex plan|new launches?",
    "input_costs": r"cement price|steel price|input cost|raw material|"
        r"commodity price|price hike|cost inflation|freight cost|"
        r"aggregate price|sand price|bitumen|clinker price",
    "labour": r"labour|labor|workers?|workforce|migrant|wages?|hiring|layoffs?|"
        r"job cuts?|skilled manpower|construction worker|site staff",
    "housing_realty": r"housing|home sales|residential|apartment|flats?|"
        r"property price|realty|real estate|homebuyers?|inventory overhang|"
        r"absorption|RERA|affordable housing|luxury housing",
    "infra_capex": r"highway|expressway|NHAI|metro rail|railway|port|airport|"
        r"infrastructure|infra project|Gati Shakti|Bharatmala|Sagarmala|"
        r"capital expenditure|capex|smart city|irrigation project",
    "finance_credit": r"funding|fund raise|debt|NBFC|loan|lender|credit|"
        r"interest rate|refinanc|IPO|QIP|bond issue|cash flow|working capital|"
        r"insolvency|IBC|NCLT|default",
    "execution_risk": r"delay(?:ed|s)?|stalled|halted|suspend|cost overrun|"
        r"time overrun|collapse|accident|mishap|dispute|arbitration|penalt|"
        r"terminat|cancel(?:led|s)?|litigation|stop-work",
    "policy_reg": r"approval|clearance|environment(?:al)? clearance|GST|policy|"
        r"regulation|regulator|notification|guidelines?|amendment|subsidy|"
        r"incentive scheme|PLI",
}

# +1 = upbeat coverage means a healthier sector; -1 = upbeat coverage is bad news.
THEME_SIGN = {
    "overall": 1,
    "demand_orders": 1,
    "input_costs": -1,     # "cement prices soar" reads positive to finBERT
    "labour": 1,
    "housing_realty": 1,
    "infra_capex": 1,
    "finance_credit": 1,
    "execution_risk": -1,  # "record number of stalled projects" ditto
    "policy_reg": 1,
}

_COMPILED = {t: re.compile(p, re.I) for t, p in THEMES.items()}

# Distress vocabulary — the sector analogue of the R-word index (ECB WP 3122).
_DISTRESS = re.compile(
    r"\bslowdown|slump|downturn|stalled|insolven|bankrupt|default|"
    r"NPA|distress|crisis|recession|halted|shut down\b", re.I)


def tag(text: str) -> list[str]:
    """Return every sub-theme the text mentions. Always includes 'overall'."""
    t = text or ""
    hits = [name for name, rx in _COMPILED.items() if rx.search(t)]
    return ["overall"] + hits


def is_distress(text: str) -> bool:
    return bool(_DISTRESS.search(text or ""))

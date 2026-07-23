#!/usr/bin/env python3
"""Aangan financial model — feeds business-plan Sections 15 (financial plan)
and 16 (funding), per docs/BUSINESS_PLAN_ALIGNMENT.md Part D3.

What it does
    1. Pulls REAL observed unit costs from the local DB (llm_calls token
       averages per agent, asks per member, voice seconds per entry, members
       per circle). Sparse tables degrade to clearly-labeled defaults.
    2. Converts them to a cost per active family (circle) per month.
    3. Simulates revenue under pessimistic/base/optimistic scenarios:
       monthly Year-1 table, 3-year annual P&L, break-even circles,
       max cumulative cash shortfall -> funding need with contingency.

Usage, from backend/:
    .venv/bin/python scripts/financial_model.py
    .venv/bin/python scripts/financial_model.py --price-inr 499 --tok-in 0.15 --tok-out 0.60

Every unit price below is an ASSUMPTION constant with source + date; every
usage number is observed from the DB when there is enough data, otherwise a
labeled default. Re-run after the pilot: the observed numbers replace the
defaults automatically as the tables fill up.
"""
import argparse
import math
import sys
from typing import NamedTuple

from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# ---------------------------------------------------------------------------
# ASSUMPTION CONSTANTS — unit prices (all overridable via CLI flags)
# ---------------------------------------------------------------------------
# LLM token prices, USD per 1M tokens. Default = OpenAI gpt-5-mini
# (openai.com/api/pricing, checked Aug 2025: $0.25 in / $2.00 out) — the
# mini-tier matching OPENAI_CANDIDATES in agents/llm.py. Alternatives:
#   gpt-4o-mini  $0.15 / $0.60      gpt-5-nano  $0.05 / $0.40
TOKEN_USD_PER_MTOK_IN = 0.25
TOKEN_USD_PER_MTOK_OUT = 2.00

# Deepgram speech-to-text, USD per audio minute. Default = Nova-2 streaming
# pay-as-you-go (deepgram.com/pricing, checked 2025) — Nova-2 covers Hindi,
# which the Hindi-first elder persona needs. Nova-3 multilingual is ~$0.0092.
STT_USD_PER_MIN = 0.0059

# Hosting: one small VPS (2 vCPU / 4 GB, e.g. Hetzner CX22 / DO basic droplet,
# checked 2025) runs the whole single-container deploy (docker compose).
HOSTING_USD_PER_HOST_PM = 12.0
CIRCLES_PER_HOST = 500          # capacity assumption per VPS slice

FX_INR_PER_USD = 86.0           # assumption, ~mid-2026 spot; --fx to override

# Indian SaaS pricing realities (assumptions, checked 2025):
GST_RATE = 0.18                 # GST on digital subscriptions; price is GST-inclusive
GATEWAY_FEE_RATE = 0.02         # Razorpay-style standard card/UPI fee on gross

FIXED_OPEX_INR_PM = 2000.0      # domain, email, error tracking, misc tools (assumption)
PLUS_USAGE_MULT = 1.5           # paying (uncapped) circles use ~1.5x a free circle (assumption)

PRICE_CANDIDATES_INR = (199.0, 349.0, 499.0)   # from D1 willingness-to-pay research
DEFAULT_PRICE_INR = 349.0
CONTINGENCY = 0.25              # funding-need buffer on top of max cash shortfall

# ---------------------------------------------------------------------------
# USAGE DEFAULTS — used only while the DB is too sparse to trust (thresholds
# below). All are per-month, per-active-family assumptions to validate in pilot.
# ---------------------------------------------------------------------------
DEFAULT_MEMBERS_PER_CIRCLE = 4.0     # persona: 2 parents + 2 adult children
DEFAULT_ENTRIES_PER_MEMBER_PM = 12.0  # ~3 journal entries/week feels "active"
DEFAULT_ASKS_PER_MEMBER_PM = 15.0     # 60/circle at 4 members — under free cap of 100
DEFAULT_VOICE_SEC_PER_ENTRY = 90.0    # short spoken check-in
DEFAULT_VOICE_SHARE = 0.70            # 70% of entries voice, 30% typed
DEFAULT_AGENT_TOKENS = {              # (prompt, completion) per call — near observed
    "Summarizer": (200.0, 60.0),
    "Extractor": (420.0, 110.0),
    "Alerter": (140.0, 40.0),
    "Companion": (450.0, 60.0),
}
PER_ENTRY_AGENTS = ("Summarizer", "Extractor", "Alerter")  # capture pipeline
ASK_AGENT = "Companion"                                    # one call per ask

# Observation thresholds: below these, defaults are used and labeled as such.
MIN_CALLS_OBSERVED = 2
MIN_ASKS_OBSERVED = 20
MIN_ENTRIES_OBSERVED = 30

# ---------------------------------------------------------------------------
# GROWTH & SCENARIOS (assumptions — state them in the plan, then re-fit)
# ---------------------------------------------------------------------------
M1_NEW_CIRCLES = 5.0            # month-1 signups = pilot families
GROWTH_BY_YEAR = (0.25, 0.10, 0.05)  # m/m signup growth in Y1, Y2, Y3

SCENARIOS = {
    # monthly free->paid conversion of the free base; paid churn; free churn
    "pessimistic": {"conv": 0.005, "paid_churn": 0.08, "free_churn": 0.12},
    "base":        {"conv": 0.015, "paid_churn": 0.05, "free_churn": 0.10},
    "optimistic":  {"conv": 0.030, "paid_churn": 0.03, "free_churn": 0.08},
}


class Obs(NamedTuple):
    value: float
    source: str  # "observed (…)" or "default (…)"


# ---------------------------------------------------------------------------
# 1. Observed unit inputs from the local DB
# ---------------------------------------------------------------------------
def observe_db() -> dict[str, Obs]:
    """Read real usage from aangan.db; label everything observed vs default."""
    out: dict[str, Obs] = {}
    try:
        from db import SessionLocal
        from sqlalchemy import func
        from models import AskRecord, FamilyCircle, JournalEntry, LlmCall, User
    except Exception as exc:  # pragma: no cover — env problem, not data
        return _all_defaults(f"default (DB unavailable: {exc})")

    db = SessionLocal()
    try:
        # -- token averages per agent (only rows that actually hit a provider)
        rows = (
            db.query(
                LlmCall.agent,
                func.count(LlmCall.id),
                func.avg(LlmCall.prompt_tokens),
                func.avg(LlmCall.completion_tokens),
            )
            .filter(LlmCall.provider != "fallback")
            .group_by(LlmCall.agent)
            .all()
        )
        by_agent = {r[0]: r for r in rows}
        for agent, (d_in, d_out) in DEFAULT_AGENT_TOKENS.items():
            row = by_agent.get(agent)
            if row and row[1] >= MIN_CALLS_OBSERVED:
                out[f"tok_in_{agent}"] = Obs(float(row[2]), f"observed (n={row[1]})")
                out[f"tok_out_{agent}"] = Obs(float(row[3]), f"observed (n={row[1]})")
            else:
                n = row[1] if row else 0
                out[f"tok_in_{agent}"] = Obs(d_in, f"default (only {n} metered call(s))")
                out[f"tok_out_{agent}"] = Obs(d_out, f"default (only {n} metered call(s))")

        # -- share of LLM calls actually served by a paid provider
        total_calls = db.query(LlmCall).count()
        served = db.query(LlmCall).filter(LlmCall.provider != "fallback").count()
        if total_calls:
            out["llm_served_rate"] = Obs(
                served / total_calls, f"observed ({served}/{total_calls} calls)"
            )
        else:
            out["llm_served_rate"] = Obs(1.0, "default (no calls; cost-conservative)")

        # -- members per circle
        users = db.query(User).count()
        circles = db.query(FamilyCircle).count()
        if circles >= 1 and users >= 2:
            out["members_per_circle"] = Obs(
                users / circles, f"observed ({users} users / {circles} circle(s))"
            )
        else:
            out["members_per_circle"] = Obs(DEFAULT_MEMBERS_PER_CIRCLE, "default")

        # -- asks per member per month (needs a real usage window)
        asks = db.query(AskRecord).count()
        ask_span = db.query(
            func.min(AskRecord.created_at), func.max(AskRecord.created_at)
        ).one()
        if asks >= MIN_ASKS_OBSERVED and ask_span[0] and ask_span[1]:
            months = max((ask_span[1] - ask_span[0]).days / 30.44, 1.0)
            rate = asks / max(users, 1) / months
            out["asks_per_member_pm"] = Obs(rate, f"observed ({asks} asks / {months:.1f} mo)")
        else:
            out["asks_per_member_pm"] = Obs(
                DEFAULT_ASKS_PER_MEMBER_PM, f"default (only {asks} ask(s) so far)"
            )

        # -- entries per member per month
        entries = db.query(JournalEntry).count()
        entry_span = db.query(
            func.min(JournalEntry.created_at), func.max(JournalEntry.created_at)
        ).one()
        if entries >= MIN_ENTRIES_OBSERVED and entry_span[0] and entry_span[1]:
            months = max((entry_span[1] - entry_span[0]).days / 30.44, 1.0)
            out["entries_per_member_pm"] = Obs(
                entries / max(users, 1) / months, f"observed ({entries} entries)"
            )
        else:
            out["entries_per_member_pm"] = Obs(
                DEFAULT_ENTRIES_PER_MEMBER_PM, f"default (only {entries} entries)"
            )

        # -- voice seconds per voice entry, and voice share of entries
        voiced = db.query(JournalEntry).filter(JournalEntry.duration_sec > 0).count()
        avg_sec = (
            db.query(func.avg(JournalEntry.duration_sec))
            .filter(JournalEntry.duration_sec > 0)
            .scalar()
        )
        if voiced >= 10 and avg_sec:
            out["voice_sec_per_entry"] = Obs(float(avg_sec), f"observed (n={voiced})")
            out["voice_share"] = Obs(voiced / max(entries, 1), f"observed ({voiced}/{entries})")
        else:
            out["voice_sec_per_entry"] = Obs(
                DEFAULT_VOICE_SEC_PER_ENTRY, f"default (only {voiced} voice entries)"
            )
            out["voice_share"] = Obs(DEFAULT_VOICE_SHARE, "default")
    finally:
        db.close()
    return out


def _all_defaults(reason: str) -> dict[str, Obs]:
    out = {}
    for agent, (d_in, d_out) in DEFAULT_AGENT_TOKENS.items():
        out[f"tok_in_{agent}"] = Obs(d_in, reason)
        out[f"tok_out_{agent}"] = Obs(d_out, reason)
    out["llm_served_rate"] = Obs(1.0, reason)
    out["members_per_circle"] = Obs(DEFAULT_MEMBERS_PER_CIRCLE, reason)
    out["asks_per_member_pm"] = Obs(DEFAULT_ASKS_PER_MEMBER_PM, reason)
    out["entries_per_member_pm"] = Obs(DEFAULT_ENTRIES_PER_MEMBER_PM, reason)
    out["voice_sec_per_entry"] = Obs(DEFAULT_VOICE_SEC_PER_ENTRY, reason)
    out["voice_share"] = Obs(DEFAULT_VOICE_SHARE, reason)
    return out


# ---------------------------------------------------------------------------
# 2. Cost per active family per month
# ---------------------------------------------------------------------------
def family_month_cost(obs: dict[str, Obs], a: argparse.Namespace, plan: str) -> dict:
    """Variable cost (INR + USD) for one active circle for one month."""
    from entitlements import CAPS  # the app's real caps bound free-plan usage

    members = obs["members_per_circle"].value
    entries = members * obs["entries_per_member_pm"].value
    asks = members * obs["asks_per_member_pm"].value
    voice_min = entries * obs["voice_share"].value * obs["voice_sec_per_entry"].value / 60.0

    mult = 1.0
    if plan == "free":
        caps = CAPS["free"]
        asks = min(asks, caps["asks_per_month"])
        voice_min = min(voice_min, caps["voice_minutes_per_month"])
    else:
        mult = a.plus_mult  # uncapped + heavier usage

    per_entry_in = sum(obs[f"tok_in_{ag}"].value for ag in PER_ENTRY_AGENTS)
    per_entry_out = sum(obs[f"tok_out_{ag}"].value for ag in PER_ENTRY_AGENTS)
    ask_in = obs[f"tok_in_{ASK_AGENT}"].value
    ask_out = obs[f"tok_out_{ASK_AGENT}"].value

    served = obs["llm_served_rate"].value
    token_usd = served * mult * (
        entries * (per_entry_in * a.tok_in + per_entry_out * a.tok_out)
        + asks * (ask_in * a.tok_in + ask_out * a.tok_out)
    ) / 1e6
    stt_usd = mult * voice_min * a.stt_per_min
    total_usd = token_usd + stt_usd
    return {
        "entries_pm": entries * mult,
        "asks_pm": asks * mult,
        "voice_min_pm": voice_min * mult,
        "token_usd": token_usd,
        "stt_usd": stt_usd,
        "total_usd": total_usd,
        "total_inr": total_usd * a.fx,
    }


def net_revenue_per_paid_inr(price_inr: float) -> float:
    """Gross price -> net of GST (price is GST-inclusive) and gateway fees."""
    return price_inr / (1 + GST_RATE) - price_inr * GATEWAY_FEE_RATE


# ---------------------------------------------------------------------------
# 3. Growth simulation
# ---------------------------------------------------------------------------
def simulate(scn: dict, cost_free: float, cost_paid: float,
             a: argparse.Namespace) -> list[dict]:
    net_rev = net_revenue_per_paid_inr(a.price_inr)
    free = paid = cum = 0.0
    new = a.m1_signups
    rows = []
    for m in range(1, a.months + 1):
        year = min((m - 1) // 12, len(GROWTH_BY_YEAR) - 1)
        if m > 1:
            new *= 1 + GROWTH_BY_YEAR[year]
        free += new
        converts = free * scn["conv"]
        free -= converts
        paid += converts
        paid *= 1 - scn["paid_churn"]
        free *= 1 - scn["free_churn"]

        circles = free + paid
        revenue = paid * net_rev
        variable = free * cost_free + paid * cost_paid
        hosts = math.ceil(max(circles, 1) / a.circles_per_host)
        fixed = hosts * a.hosting_usd * a.fx + a.fixed_opex
        net = revenue - variable - fixed
        cum += net
        rows.append({
            "month": m, "new": new, "free": free, "paid": paid,
            "revenue": revenue, "variable": variable, "fixed": fixed,
            "net": net, "cum": cum,
        })
    return rows


# ---------------------------------------------------------------------------
# Output helpers (stdlib only)
# ---------------------------------------------------------------------------
def print_table(title: str, headers: list[str], rows: list[list[str]]) -> None:
    widths = [
        max(len(h), *(len(r[i]) for r in rows)) if rows else len(h)
        for i, h in enumerate(headers)
    ]
    print(f"\n{title}")
    line = "  " + "  ".join(h.ljust(w) if i == 0 else h.rjust(w)
                            for i, (h, w) in enumerate(zip(headers, widths)))
    print(line)
    print("  " + "-" * (len(line) - 2))
    for r in rows:
        print("  " + "  ".join(c.ljust(w) if i == 0 else c.rjust(w)
                               for i, (c, w) in enumerate(zip(r, widths))))


def inr(x: float) -> str:
    return f"{x:,.0f}"


# ---------------------------------------------------------------------------
def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Aangan financial model (Sections 15-16)")
    p.add_argument("--tok-in", type=float, default=TOKEN_USD_PER_MTOK_IN,
                   help="USD per 1M prompt tokens")
    p.add_argument("--tok-out", type=float, default=TOKEN_USD_PER_MTOK_OUT,
                   help="USD per 1M completion tokens")
    p.add_argument("--stt-per-min", type=float, default=STT_USD_PER_MIN,
                   help="Deepgram USD per audio minute")
    p.add_argument("--hosting-usd", type=float, default=HOSTING_USD_PER_HOST_PM,
                   help="USD/month per hosting slice")
    p.add_argument("--circles-per-host", type=int, default=CIRCLES_PER_HOST)
    p.add_argument("--fx", type=float, default=FX_INR_PER_USD, help="INR per USD")
    p.add_argument("--price-inr", type=float, default=DEFAULT_PRICE_INR,
                   help="Aangan Plus price per circle per month (INR, GST-incl.)")
    p.add_argument("--prices", type=str,
                   default=",".join(str(int(x)) for x in PRICE_CANDIDATES_INR),
                   help="comma-separated price candidates for sensitivity table")
    p.add_argument("--fixed-opex", type=float, default=FIXED_OPEX_INR_PM,
                   help="fixed non-hosting opex INR/month")
    p.add_argument("--plus-mult", type=float, default=PLUS_USAGE_MULT,
                   help="usage multiplier for paying circles")
    p.add_argument("--m1-signups", type=float, default=M1_NEW_CIRCLES,
                   help="new circles in month 1")
    p.add_argument("--months", type=int, default=36)
    p.add_argument("--contingency", type=float, default=CONTINGENCY,
                   help="buffer on funding need, e.g. 0.25")
    return p.parse_args()


def main() -> None:
    a = parse_args()
    obs = observe_db()

    # -- 1. observed unit inputs --------------------------------------------
    unit_rows = []
    for agent in DEFAULT_AGENT_TOKENS:
        o_in, o_out = obs[f"tok_in_{agent}"], obs[f"tok_out_{agent}"]
        unit_rows.append([f"{agent} tokens/call",
                          f"{o_in.value:.0f} in / {o_out.value:.0f} out", o_in.source])
    for key, label in [
        ("llm_served_rate", "LLM served rate (non-fallback)"),
        ("members_per_circle", "Members per circle"),
        ("entries_per_member_pm", "Entries / member / month"),
        ("asks_per_member_pm", "Asks / member / month"),
        ("voice_sec_per_entry", "Voice seconds / voice entry"),
        ("voice_share", "Voice share of entries"),
    ]:
        o = obs[key]
        unit_rows.append([label, f"{o.value:.2f}", o.source])
    print("=== Aangan financial model (business plan Sections 15-16) ===")
    print_table("1. Unit inputs (observed from aangan.db where possible)",
                ["Input", "Value", "Source"], unit_rows)

    # -- 2. cost per active family per month ---------------------------------
    free_cost = family_month_cost(obs, a, "free")
    paid_cost = family_month_cost(obs, a, "plus")
    cost_rows = []
    for name, c in [("Free circle", free_cost), ("Plus circle", paid_cost)]:
        cost_rows.append([
            name,
            f"{c['entries_pm']:.0f}", f"{c['asks_pm']:.0f}", f"{c['voice_min_pm']:.0f}",
            f"${c['token_usd']:.3f}", f"${c['stt_usd']:.3f}",
            f"${c['total_usd']:.3f}", f"Rs {c['total_inr']:.1f}",
        ])
    print_table(
        "2. Variable cost per ACTIVE family (circle) per month "
        f"(fx {a.fx:.0f} INR/USD; free caps from entitlements.py applied)",
        ["Plan", "Entries", "Asks", "VoiceMin", "LLM $", "STT $", "Total $", "Total INR"],
        cost_rows,
    )
    print(f"\n  >> Cost per active family at observed unit costs: "
          f"Rs {free_cost['total_inr']:.1f}/month (free plan, ${free_cost['total_usd']:.3f});"
          f" Rs {paid_cost['total_inr']:.1f}/month (Plus, x{a.plus_mult} usage).")

    # -- 3. price sensitivity / simple break-even ----------------------------
    prices = [float(x) for x in a.prices.split(",")]
    fixed_pm = a.hosting_usd * a.fx + a.fixed_opex  # pilot-scale: 1 host
    price_rows = []
    for price in prices:
        net = net_revenue_per_paid_inr(price)
        contribution = net - paid_cost["total_inr"]
        be = math.ceil(fixed_pm / contribution) if contribution > 0 else float("inf")
        price_rows.append([
            f"Rs {price:.0f}", f"Rs {net:.0f}", f"Rs {paid_cost['total_inr']:.0f}",
            f"Rs {contribution:.0f}", f"{be}",
        ])
    print_table(
        "3. Price candidates -> contribution & simple break-even "
        f"(GST {GST_RATE:.0%} + gateway {GATEWAY_FEE_RATE:.0%}; "
        f"fixed Rs {inr(fixed_pm)}/mo at pilot scale; ignores free-rider cost)",
        ["Price/mo", "Net rev", "Var cost", "Contribution", "Break-even paying circles"],
        price_rows,
    )

    # -- 4. scenario simulations ---------------------------------------------
    results = {}
    for name, scn in SCENARIOS.items():
        results[name] = simulate(scn, free_cost["total_inr"], paid_cost["total_inr"], a)

    for name, rows in results.items():
        scn = SCENARIOS[name]
        y1 = [[f"M{r['month']}", f"{r['new']:.0f}", f"{r['free']:.0f}", f"{r['paid']:.1f}",
               inr(r["revenue"]), inr(r["variable"]), inr(r["fixed"]),
               inr(r["net"]), inr(r["cum"])] for r in rows[:12]]
        print_table(
            f"4. Year-1 monthly — {name.upper()} "
            f"(conv {scn['conv']:.1%}/mo, paid churn {scn['paid_churn']:.0%}, "
            f"free churn {scn['free_churn']:.0%}, price Rs {a.price_inr:.0f}) — all INR",
            ["Month", "New", "Free", "Paid", "Revenue", "Variable", "Fixed", "Net", "Cum cash"],
            y1,
        )

    # -- 5. 3-year annual P&L -------------------------------------------------
    pl_rows = []
    for name, rows in results.items():
        for y in range(min(3, math.ceil(a.months / 12))):
            yr = rows[y * 12:(y + 1) * 12]
            rev = sum(r["revenue"] for r in yr)
            var = sum(r["variable"] for r in yr)
            fix = sum(r["fixed"] for r in yr)
            gross = rev - var
            gm = f"{gross / rev:.0%}" if rev else "-"
            pl_rows.append([
                f"{name} Y{y + 1}", f"{yr[-1]['paid']:.0f}", inr(rev), inr(var),
                inr(gross), gm, inr(fix), inr(rev - var - fix), inr(yr[-1]["cum"]),
            ])
    print_table(
        "5. Three-year annual P&L per scenario (INR; team salaries excluded — "
        "layer them into Section 15 from the Team section)",
        ["Scenario", "Paid EOY", "Revenue", "Variable", "Gross", "GM%", "Fixed",
         "Net", "Cum cash EOY"],
        pl_rows,
    )

    # -- 6. funding need --------------------------------------------------------
    fund_rows = []
    for name, rows in results.items():
        trough = min(r["cum"] for r in rows)
        shortfall = max(0.0, -trough)
        need = shortfall * (1 + a.contingency)
        be_month = next((r["month"] for r in rows if r["net"] > 0), None)
        cum_pos = next((r["month"] for r in rows if r["cum"] > 0), None)
        fund_rows.append([
            name, inr(shortfall), f"{a.contingency:.0%}", inr(need),
            f"M{be_month}" if be_month else f">{a.months}",
            f"M{cum_pos}" if cum_pos else f">{a.months}",
        ])
    print_table(
        "6. Funding need = max cumulative cash shortfall + contingency (INR)",
        ["Scenario", "Max shortfall", "Contingency", "Funding need",
         "Monthly break-even", "Cash-positive"],
        fund_rows,
    )
    print("\nAssumption provenance and business-plan mapping: docs/FINANCIAL_MODEL.md")
    print("Re-run after the pilot; observed values replace defaults automatically.\n")


if __name__ == "__main__":
    main()

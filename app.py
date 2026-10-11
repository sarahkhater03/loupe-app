"""Loupe: where a diamond's story gets lost.

An interactive Streamlit page built on official Kimberley Process statistics (2019-2025)
and The Knot's engagement-ring surveys.
"""

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="Loupe · Where a Diamond's Story Gets Lost", page_icon="💎", layout="wide")

# ------------------------------------------------------------------ colours (validated palette)
MINED = "#2a78d6"      # blue   – carats mined / natural
IMPORTED = "#1baf7a"   # aqua   – carats imported
EXPORTED = "#eb6834"   # orange – carats exported / lab-grown
MUTED = "#c9c7c1"      # grey   – context bars
INK = "#0b0b0b"
INK_2 = "#52514e"

# A country is treated as a "producer" if what it mines is at least a quarter of what it exports.
# Everything else that trades diamonds is a "trading / cutting hub".
PRODUCER_THRESHOLD = 0.25


@st.cache_data
def load_kp() -> tuple[pd.DataFrame, pd.DataFrame]:
    df =    pd.read_csv("kp_raw.csv")
    totals = df[df["country"] == "TOTAL"].drop(columns="country").set_index("year").sort_index()
    df = df[df["country"] != "TOTAL"].copy()
    df = df[(df[["prod_cts", "imp_cts", "exp_cts"]].sum(axis=1)) > 0]
    df["role"] = df.apply(
        lambda r: "Producer" if r.prod_cts > 0 and r.prod_cts >= PRODUCER_THRESHOLD * r.exp_cts
        else "Trading / cutting hub",
        axis=1,
    )
    df["trade_cts"] = df["imp_cts"] + df["exp_cts"]
    return df, totals


@st.cache_data
def load_lab() -> pd.DataFrame:
    return    pd.read_csv("lab_grown.csv")


def per_carat(usd, cts):
    return usd / cts if cts else None


def base_layout(fig, height=420, **kw):
    fig.update_layout(
        template="plotly_white",
        height=height,
        margin=dict(l=10, r=20, t=30, b=40),
        font=dict(color=INK_2, size=13),
        legend=dict(orientation="h", y=1.08, x=0, title=None),
        hoverlabel=dict(bgcolor="white", font_color=INK),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        **kw,
    )
    fig.update_xaxes(gridcolor="#ecebe7", zeroline=False)
    fig.update_yaxes(gridcolor="#ecebe7", zeroline=False)
    return fig


kp, totals = load_kp()
lab = load_lab()
YEARS = sorted(kp["year"].unique())

# ================================================================== header
st.markdown("<p style='letter-spacing:.2em;color:#52514e;margin-bottom:0'>LOUPE · DIAMOND PROVENANCE</p>",
            unsafe_allow_html=True)
st.title("Where a diamond's story gets lost")
st.markdown(
    """
Every rough diamond traded legally crosses borders with a **Kimberley Process (KP) certificate**. But that
certificate describes a *shipment between two countries*, not an individual stone. Once parcels reach a trading
hub they are sorted, mixed and re-exported, and the link to the mine fades.

This page uses the KP's official statistics for **2019–2025** (production, imports and exports for every member
country) to show where that happens, and why buyers are turning to stones whose origin is never in doubt.
"""
)

# ================================================================== controls (linked)
st.markdown("### Choose what to explore")
c1, c2, c3 = st.columns([1.2, 1.3, 3])
with c1:
    year = st.select_slider("Year", options=YEARS, value=YEARS[-1])
with c2:
    role = st.radio(
        "Type of country",
        ["Trading / cutting hub", "Producer"],
        help="Producers mine diamonds. Hubs import, sort, cut and re-export them.",
    )

# The country list depends on BOTH the year and the type chosen: this is the drill-down link.
pool = kp[(kp["year"] == year) & (kp["role"] == role)].sort_values("trade_cts" if role != "Producer" else "prod_cts",
                                                                    ascending=False)
options = pool["country"].tolist()
with c3:
    countries = st.multiselect(
        f"{role}s active in {year} (largest first)",
        options,
        default=options[:6],
        key=f"countries_{role}_{year}",
        help="Only countries of the chosen type that traded or mined diamonds in the chosen year are listed.",
    )

if not countries:
    st.warning("Pick at least one country to draw the charts.")
    st.stop()

sel = pool[pool["country"].isin(countries)].copy()
t = totals.loc[year]

# ================================================================== headline numbers
st.markdown(f"### {year} at a glance")
k1, k2, k3, k4 = st.columns(4)
k1.metric("Carats mined worldwide", f"{t.prod_cts / 1e6:,.0f} M")
k2.metric("Carats exported (all borders)", f"{t.exp_cts / 1e6:,.0f} M")
k3.metric("Border crossings per mined carat", f"{t.exp_cts / t.prod_cts:.1f}×",
          help="Total carats exported by all countries ÷ carats mined that year.")
gap = t.imp_usd - t.exp_usd
k4.metric("Imports vs exports mismatch", f"${abs(gap) / 1e9:.2f} B",
          help="Globally, every export should be someone's import. The difference is value nobody can account for.")

# ================================================================== 1. the journey
st.markdown("---")
st.markdown("## 1 · The journey: mined in one place, traded in another")
st.markdown(
    "Compare how many carats each country **mined**, **imported** and **exported**. Hubs mine nothing yet "
    "handle the largest volumes. Every bar on the right of a hub is a parcel whose origin is now one step further away."
)

order = sel.sort_values("trade_cts" if role != "Producer" else "prod_cts")["country"].tolist()
fig1 = go.Figure()
for col, name, colour in [("prod_cts", "Mined", MINED), ("imp_cts", "Imported", IMPORTED),
                          ("exp_cts", "Exported", EXPORTED)]:
    s = sel.set_index("country").loc[order, col] / 1e6
    fig1.add_bar(y=order, x=s, name=name, orientation="h", marker_color=colour,
                 hovertemplate="%{y}<br>" + name + ": %{x:.2f} M carats<extra></extra>")
base_layout(fig1, height=max(320, 70 * len(order) + 80), barmode="group", bargap=0.25, bargroupgap=0.08)
fig1.update_layout(legend_traceorder="reversed")
fig1.update_xaxes(title="Million carats")
st.plotly_chart(fig1, width="stretch")

hub_year = kp[kp["year"] == year]
hub_share = hub_year.loc[hub_year["role"] != "Producer", "exp_cts"].sum() / hub_year["exp_cts"].sum()
st.info(
    f"**Insight:** in {year}, **{hub_share:.0%} of all carats exported** left from a country that mines little or "
    f"nothing. On average each mined carat crossed a border **{t.exp_cts / t.prod_cts:.1f} times**. "
    "The KP records each crossing, but never which mine an individual stone came from."
)

# ================================================================== 2. the gap
st.markdown("---")
st.markdown("## 2 · The gap: value changes at every border")
left, right = st.columns([3, 2])

with left:
    st.markdown("**Declared value per carat: coming in vs going out**")
    st.caption("For hubs, 'in' is the import price. For producers, it is the value at the mine.")
    rows = []
    for _, r in sel.iterrows():
        in_ppc = per_carat(r.imp_usd, r.imp_cts) if role != "Producer" else per_carat(r.prod_usd, r.prod_cts)
        out_ppc = per_carat(r.exp_usd, r.exp_cts)
        if in_ppc and out_ppc:
            rows.append((r.country, in_ppc, out_ppc))
    dumb = pd.DataFrame(rows, columns=["country", "in", "out"]).sort_values("out")
    fig2 = go.Figure()
    for _, r in dumb.iterrows():
        fig2.add_shape(type="line", x0=r["in"], x1=r["out"], y0=r.country, y1=r.country,
                       line=dict(color=MUTED, width=2))
    fig2.add_scatter(x=dumb["in"], y=dumb["country"], mode="markers", name="Value coming in",
                     marker=dict(size=12, color=IMPORTED if role != "Producer" else MINED,
                                 line=dict(color="white", width=2)),
                     hovertemplate="%{y}<br>In: $%{x:,.0f}/ct<extra></extra>")
    fig2.add_scatter(x=dumb["out"], y=dumb["country"], mode="markers", name="Value going out",
                     marker=dict(size=12, color=EXPORTED, line=dict(color="white", width=2)),
                     hovertemplate="%{y}<br>Out: $%{x:,.0f}/ct<extra></extra>")
    base_layout(fig2, height=max(300, 55 * len(dumb) + 90))
    ticks = [10, 25, 50, 100, 200, 400, 800]
    fig2.update_xaxes(title="US$ per carat (log scale)", type="log", tickvals=ticks,
                      ticktext=[f"${v}" for v in ticks])
    st.plotly_chart(fig2, width="stretch")
    if len(dumb):
        dumb["change"] = dumb["out"] / dumb["in"] - 1
        big = dumb.loc[dumb["change"].abs().idxmax()]
        st.caption(
            f"Biggest change in your selection: **{big.country}**, from **\\${big['in']:,.0f}** to "
            f"**\\${big['out']:,.0f}** per carat (**{big.change:+.0%}**). Log scale, so equal distances mean equal % changes."
        )

with right:
    st.markdown("**Records that don't add up**")
    st.caption("Globally, imports should equal exports. Bars show the difference (imports − exports).")
    mism = (totals["imp_usd"] - totals["exp_usd"]) / 1e9
    fig3 = go.Figure(go.Bar(
        x=[str(y) for y in mism.index], y=mism.values,
        marker_color=[MINED if y == year else MUTED for y in mism.index],
        hovertemplate="%{x}: $%{y:+.2f} B<extra></extra>",
    ))
    base_layout(fig3, height=360, showlegend=False)
    fig3.update_yaxes(title="Imports − exports", tickprefix="$", ticksuffix="B", zeroline=True, zerolinecolor="#9a9893")
    st.plotly_chart(fig3, width="stretch")

st.info(
    "**Insight:** the same parcel can be declared at very different values from one border to the next. Hubs like the "
    "UAE routinely export at a higher price per carat than they import, and countries' records never fully match: "
    f"in {year} global imports and exports differed by **\\${abs(gap) / 1e9:.2f} billion**. These are exactly the "
    "'claims nobody can verify' that stone-level provenance would close."
)

# ================================================================== 3. the pressure
st.markdown("---")
st.markdown("## 3 · The pressure: lab-grown is winning on trust")
p1, p2 = st.columns(2)

with p1:
    st.markdown("**Value of natural diamonds mined worldwide**")
    fig4 = go.Figure(go.Bar(
        x=[str(y) for y in totals.index], y=totals["prod_usd"] / 1e9,
        marker_color=[MINED if y == year else MUTED for y in totals.index],
        text=[f"${v:.1f}B" for v in totals["prod_usd"] / 1e9], textposition="outside",
        hovertemplate="%{x}: $%{y:.2f} B<extra></extra>",
    ))
    base_layout(fig4, height=360, showlegend=False)
    fig4.update_yaxes(title="US$ billion", range=[0, totals["prod_usd"].max() / 1e9 * 1.18])
    st.plotly_chart(fig4, width="stretch")

with p2:
    st.markdown("**Share of US engagement rings with a lab-grown centre stone**")
    fig5 = go.Figure(go.Scatter(
        x=lab["year"], y=lab["lab_share_pct"], mode="lines+markers+text",
        line=dict(color=EXPORTED, width=2, dash="dot"), marker=dict(size=10, color=EXPORTED),
        text=[f"{v}%" for v in lab["lab_share_pct"]], textposition="top center",
        hovertemplate="%{x}: %{y}% lab-grown<extra></extra>",
    ))
    base_layout(fig5, height=360, showlegend=False)
    fig5.update_yaxes(title="% of engagement rings", range=[0, 75])
    fig5.update_xaxes(dtick=1, range=[2018.5, 2025.5])
    st.plotly_chart(fig5, width="stretch")
    st.caption("Source: The Knot Real Weddings Study. No published figures for 2020–2022, so the dotted line only connects surveyed years.")

peak = totals["prod_usd"].idxmax()
drop = 1 - totals.loc[YEARS[-1], "prod_usd"] / totals.loc[peak, "prod_usd"]
st.info(
    f"**Insight:** the value of natural diamonds mined fell **{drop:.0%}** from its {peak} peak to {YEARS[-1]}, while "
    "lab-grown stones went from **12%** of US engagement rings (2019) to **61%** (2025). A lab-grown stone's origin is "
    "never in question. Natural producers need verifiable provenance to compete on trust."
)

# ================================================================== 4. close-up
st.markdown("---")
st.markdown("## 4 · Close-up: one country over time")
focus = st.selectbox("Country (from your selection above)", countries)
hist = kp[kp["country"] == focus].sort_values("year")
fig6 = go.Figure()
for col, name, colour in [("prod_cts", "Mined", MINED), ("imp_cts", "Imported", IMPORTED),
                          ("exp_cts", "Exported", EXPORTED)]:
    if hist[col].sum() > 0:
        fig6.add_scatter(x=hist["year"], y=hist[col] / 1e6, name=name, mode="lines+markers",
                         line=dict(color=colour, width=2), marker=dict(size=8),
                         hovertemplate=name + " %{x}: %{y:.2f} M ct<extra></extra>")
fig6.add_vline(x=year, line_color="#9a9893", line_dash="dash")
base_layout(fig6, height=380, hovermode="x unified")
fig6.update_yaxes(title="Million carats", rangemode="tozero")
fig6.update_xaxes(dtick=1)
st.plotly_chart(fig6, width="stretch")

# ================================================================== design + limits
st.markdown("---")
with st.expander("💡 Why these controls? (design justification)"):
    st.markdown(
        """
**Type of country (radio buttons) → Countries (multiselect).**
*User question:* "Where do diamonds lose their origin: at the mines, or at the hubs that trade them?"
*Why these widgets:* there are only two types, so radio buttons show both choices at once with no extra click.
A dropdown would hide them. The multiselect's list is rebuilt from that choice and the year: you only see hubs, or
only producers, that were active that year, largest first. This links the two controls so the reader drills down
(type → specific countries) instead of filtering two things independently. I considered checkboxes for countries,
but with up to 30 active countries they would take over the page.
*Course concept:* **reducing clutter / focusing attention**. Mixing Russia (mines 30–60M ct) with Switzerland
(trades under 2M ct) on one axis would flatten most bars. Separating roles keeps comparisons fair and readable.

**Year (select slider).**
*User question:* "Is this a one-off, or a pattern?"
*Why this widget:* years are ordered, and a slider makes stepping through them natural. A dropdown would hide that order.
*Course concept:* **providing context**. The selected year is highlighted in the trend charts rather than replacing
them, so a single year is always read against the full 2019–2025 history.
"""
    )

with st.expander("⚠️ What this data cannot show (and why that's the point)"):
    st.markdown(
        """
- KP statistics are **country totals**, not stone-level records. There is no public dataset that follows a single
  diamond from mine to jeweller, and that missing record is the problem Loupe addresses.
- The **European Union** reports as one KP participant, so Belgium (Antwerp) is included under "European Union".
- Values are **declared** by each country and are not independently audited, which is why they can disagree.
- "Producer" vs "hub" is my classification: a country is a producer if it mines at least 25% of what it exports.
- Lab-grown share is for **US** engagement rings only, from survey data.
"""
    )

st.markdown(
    """
<small>
<b>Sources.</b> Kimberley Process Certification Scheme, <i>Annual Global Summary</i> 2019–2025
(kimberleyprocessstatistics.org). The Knot, <i>Real Weddings Study</i> (via IDEX Online and JCK, 2024–2026).
</small>
""",
    unsafe_allow_html=True,
)

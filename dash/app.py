# app.py — Superstore Sales Dashboard (dark teal version)
from pathlib import Path
import pandas as pd
import numpy as np
from dash import Dash, dcc, html, Input, Output
import plotly.express as px

# -------------------- Paths --------------------
BASE_DIR = Path(__file__).resolve().parent.parent
P_PARQUET = BASE_DIR / "data" / "processed" / "superstore_clean.parquet"
P_CSV     = BASE_DIR / "data" / "processed" / "superstore_clean.csv"
RAW1      = BASE_DIR / "data" / "Sample - Superstore.csv"
RAW2      = BASE_DIR / "data" / "Sample-Superstore.csv"

# -------------------- Load Data --------------------
if P_PARQUET.exists():
    df = pd.read_parquet(P_PARQUET)
elif P_CSV.exists():
    df = pd.read_csv(P_CSV, parse_dates=["order_date", "order_month"])
elif RAW1.exists() or RAW2.exists():
    p = RAW1 if RAW1.exists() else RAW2
    for enc in ("utf-8", "cp1252", "latin-1"):
        try:
            df = pd.read_csv(p, encoding=enc); break
        except UnicodeDecodeError:
            continue
    else:
        df = pd.read_csv(p, encoding="latin-1", errors="replace")

    if "Order Date" in df.columns:
        df["order_date"] = pd.to_datetime(df["Order Date"], errors="coerce")
    if "Sales" in df.columns:    df["sales"]    = pd.to_numeric(df["Sales"], errors="coerce")
    if "Profit" in df.columns:   df["profit"]   = pd.to_numeric(df["Profit"], errors="coerce")
    if "Discount" in df.columns: df["discount"] = pd.to_numeric(df["Discount"], errors="coerce")
    if "Region" in df.columns:   df["region"]   = df["Region"].astype("string")
    if "Category" in df.columns: df["category"] = df["Category"].astype("string")
    df["order_month"] = pd.to_datetime(df["order_date"]).dt.to_period("M").dt.to_timestamp()
else:
    raise FileNotFoundError("Missing dataset in data/processed or data/ folder")

df["order_date"]  = pd.to_datetime(df["order_date"], errors="coerce")
df["order_month"] = pd.to_datetime(df["order_month"], errors="coerce")
required = ["order_month", "sales", "profit", "discount", "region", "category"]
missing = [c for c in required if c not in df.columns]
if missing:
    raise ValueError(f"Missing columns: {missing}")

# -------------------- Slider months --------------------
m_start = df["order_month"].min()
m_end   = df["order_month"].max()
months = pd.date_range(m_start, m_end, freq="MS")
month_marks = {i: m.strftime("%Y-%m") for i, m in enumerate(months) if i % 4 == 0}
month_marks[len(months) - 1] = months[-1].strftime("%Y-%m")

# -------------------- Palettes --------------------
# Teal palette (good contrast on dark)
UNIFORM_PALETTE = [
    "#14B8A6",  # teal-500
    "#10A3A3",  # teal-ish
    "#2DD4BF",  # cyan-teal
    "#5EEAD4",  # light aqua
    "#99F6E4",  # pale aqua
]

CAT_ORDER = sorted(df["category"].dropna().unique().tolist())
REG_ORDER = sorted(df["region"].dropna().unique().tolist())
CAT_MAP = {c: UNIFORM_PALETTE[i % len(UNIFORM_PALETTE)] for i, c in enumerate(CAT_ORDER)}
REG_MAP = {r: UNIFORM_PALETTE[i % len(UNIFORM_PALETTE)] for i, r in enumerate(REG_ORDER)}

# -------------------- App Layout --------------------
app = Dash(__name__, title="Superstore Sales Dashboard (Dark)")
server = app.server

# Dark theme tokens
BG = "#0F1117"          # page background
PANEL = "#111827"       # card background
BORDER = "#1F2937"
TEXT = "#E5E7EB"
MUTED = "#9CA3AF"

CARD = {
    "background": PANEL,
    "border": f"1px solid {BORDER}",
    "borderRadius": "14px",
    "padding": "16px 18px",
    "boxShadow": "0 1px 3px rgba(0,0,0,0.4)",
}
app = Dash(__name__, title="Superstore Sales Dashboard (Dark)")

# --- Dark Dropdown Style ---
app.css.append_css({
    "external_url": (
        "https://cdnjs.cloudflare.com/ajax/libs/normalize/8.0.1/normalize.min.css"
    )
})

app.index_string = """
<!DOCTYPE html>
<html>
    <head>
        {%metas%}
        <title>{%title%}</title>
        {%favicon%}
        {%css%}
        <style>
            /* DARK DROPDOWNS */
            .Select-control, .Select-menu-outer, .Select-menu {
                background-color: #111827 !important;
                color: #E5E7EB !important;
                border: 1px solid #1F2937 !important;
            }
            .Select-placeholder {
                color: #9CA3AF !important;
            }
            .Select-value-label {
                color: #E5E7EB !important;
            }
            .Select--multi .Select-value {
                background-color: #0D9488 !important;
                border: none !important;
                color: #E5E7EB !important;
            }
            .Select--multi .Select-value-icon {
                color: #E5E7EB !important;
            }
            .Select--multi .Select-value-icon:hover {
                background-color: #134E4A !important;
                color: white !important;
            }
        </style>
    </head>
    <body>
        {%app_entry%}
        <footer>
            {%config%}
            {%scripts%}
            {%renderer%}
        </footer>
    </body>
</html>
"""

app.layout = html.Div(
    style={
        "fontFamily": "Inter, system-ui, sans-serif",
        "padding": "24px 36px",
        "backgroundColor": BG,
        "color": TEXT,
    },
    children=[
        html.H1(
            "Superstore Sales Dashboard",
            style={
                "textAlign": "center",
                "fontSize": "38px",
                "fontWeight": "800",
                "color": "#34D399",  # emerald accent
                "marginBottom": "24px",
                "letterSpacing": "-0.4px",
            },
        ),
        # ---------- KPI ROW ----------
        html.Div(
            style={
                "display": "grid",
                "gridTemplateColumns": "repeat(5, 1fr)",
                "gap": "14px",
                "marginBottom": "20px",
            },
            children=[
                html.Div([
                    html.Div("Total Sales", style={"fontSize": "13px", "color": MUTED}),
                    html.Div(id="kpi-sales", style={"fontSize": "24px", "fontWeight": 700, "color": "#5EEAD4"})
                ], style=CARD),
                html.Div([
                    html.Div("Total Profit", style={"fontSize": "13px", "color": MUTED}),
                    html.Div(id="kpi-profit", style={"fontSize": "24px", "fontWeight": 700, "color": "#34D399"})
                ], style=CARD),
                html.Div([
                    html.Div("Profit Margin", style={"fontSize": "13px", "color": MUTED}),
                    html.Div(id="kpi-margin", style={"fontSize": "24px", "fontWeight": 700, "color": "#2DD4BF"})
                ], style=CARD),
                html.Div([
                    html.Div("Orders", style={"fontSize": "13px", "color": MUTED}),
                    html.Div(id="kpi-orders", style={"fontSize": "24px", "fontWeight": 700, "color": "#A7F3D0"})
                ], style=CARD),
                html.Div([
                    html.Div("Avg. Discount", style={"fontSize": "13px", "color": MUTED}),
                    html.Div(id="kpi-discount", style={"fontSize": "24px", "fontWeight": 700, "color": "#99F6E4"})
                ], style=CARD),
            ]
        ),
        # ---------- FILTERS ----------
        html.Div(
            style={
                "display": "grid",
                "gridTemplateColumns": "1fr 1fr 1fr",
                "gap": "16px",
                "marginBottom": "20px",
            },
            children=[
                html.Div([
                    html.Label("Category", style={"fontWeight": "600", "color": TEXT}),
                    dcc.Dropdown(
                        options=[{"label": c, "value": c} for c in CAT_ORDER],
                        value=CAT_ORDER, multi=True, id="f-category",
                        style={"color": "#0F1117"},    # text color in input
                        className="dropdown-dark"
                    )
                ], style=CARD),
                html.Div([
                    html.Label("Region", style={"fontWeight": "600", "color": TEXT}),
                    dcc.Dropdown(
                        options=[{"label": r, "value": r} for r in REG_ORDER],
                        value=REG_ORDER, multi=True, id="f-region",
                        style={"color": "#0F1117"},
                        className="dropdown-dark"
                    )
                ], style=CARD),
                html.Div([
                    html.Label("Month range", style={"fontWeight": "600", "color": TEXT}),
                    dcc.RangeSlider(
                        min=0, max=len(months) - 1, step=1, value=[0, len(months) - 1],
                        marks=month_marks, id="f-month",
                        tooltip={"placement": "bottom", "always_visible": False}
                    )
                ], style=CARD),
            ]
        ),
        # ---------- CHARTS ----------
        html.Div(
            style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "16px"},
            children=[dcc.Graph(id="g-sales-category"), dcc.Graph(id="g-sales-region")]
        ),
        html.Div(
            style={"display": "grid", "gridTemplateColumns": "1fr 1fr", "gap": "16px", "marginTop": "20px"},
            children=[dcc.Graph(id="g-monthly"), dcc.Graph(id="g-discount-profit")]
        ),
    ]
)

# -------------------- Callbacks --------------------
@app.callback(
    [
        Output("kpi-sales", "children"),
        Output("kpi-profit", "children"),
        Output("kpi-margin", "children"),
        Output("kpi-orders", "children"),
        Output("kpi-discount", "children"),
        Output("g-sales-category", "figure"),
        Output("g-sales-region", "figure"),
        Output("g-monthly", "figure"),
        Output("g-discount-profit", "figure"),
    ],
    [
        Input("f-category", "value"),
        Input("f-region", "value"),
        Input("f-month", "value"),
    ],
)
def update_figs(sel_categories, sel_regions, sel_month_idx):
    if not sel_categories: sel_categories = CAT_ORDER
    if not sel_regions: sel_regions = REG_ORDER
    if not isinstance(sel_categories, list): sel_categories = [sel_categories]
    if not isinstance(sel_regions, list): sel_regions = [sel_regions]

    m0, m1 = sel_month_idx
    d0, d1 = months[m0], months[m1]
    dff = df[
        df["category"].isin(sel_categories)
        & df["region"].isin(sel_regions)
        & (df["order_month"] >= d0)
        & (df["order_month"] <= d1)
    ].copy()

    if dff.empty:
        blank = px.scatter(title="No data for current filters", template="plotly_dark")
        blank.update_layout(paper_bgcolor=BG, plot_bgcolor=BG)
        return "$0", "$0", "0%", "0", "0%", blank, blank, blank, blank

    total_sales = dff["sales"].sum()
    total_profit = dff["profit"].sum()
    margin_pct = (total_profit / total_sales) if total_sales else 0
    orders = dff["order_id"].nunique() if "order_id" in dff.columns else len(dff)
    avg_discount = dff["discount"].mean()

    k_sales  = f"${total_sales:,.0f}"
    k_profit = f"${total_profit:,.0f}"
    k_margin = f"{margin_pct:.1%}"
    k_orders = f"{orders:,}"
    k_disc   = f"{avg_discount:.1%}"

    # --- Sales by Category ---
    cat = dff.groupby("category", as_index=False).agg(sales=("sales", "sum"), profit=("profit", "sum"))
    cat["margin_pct"] = (cat["profit"] / cat["sales"]) * 100
    f1 = px.bar(cat, x="category", y="sales",
                color="category", color_discrete_map=CAT_MAP,
                text=cat["margin_pct"].round(1).astype(str) + "%",
                title="Sales by Category", template="plotly_dark")
    f1.update_traces(textposition="outside")
    f1.update_layout(yaxis_title="Sales ($)", xaxis_title="Category", yaxis_tickformat="$,.0f",
                     title_x=0.5, paper_bgcolor=BG, plot_bgcolor=BG)

    # --- Sales by Region ---
    reg = dff.groupby("region", as_index=False).agg(sales=("sales", "sum"), profit=("profit", "sum"))
    reg["margin_pct"] = (reg["profit"] / reg["sales"]) * 100
    f2 = px.bar(reg, x="region", y="sales",
                color="region", color_discrete_map=REG_MAP,
                text=reg["margin_pct"].round(1).astype(str) + "%",
                title="Sales by Region", template="plotly_dark")
    f2.update_traces(textposition="outside")
    f2.update_layout(yaxis_title="Sales ($)", xaxis_title="Region", yaxis_tickformat="$,.0f",
                     title_x=0.5, paper_bgcolor=BG, plot_bgcolor=BG)

    # --- Monthly Sales Trend ---
    monthly = dff.set_index("order_month")[["sales", "profit"]].resample("MS").sum().reset_index()
    f3 = px.line(monthly, x="order_month", y="sales",
                 markers=True, title="Monthly Sales Trend",
                 color_discrete_sequence=["#2DD4BF"], template="plotly_dark")
    f3.update_layout(xaxis_title="Month", yaxis_title="Sales ($)",
                     yaxis_tickformat="$,.0f", title_x=0.5, hovermode="x unified",
                     paper_bgcolor=BG, plot_bgcolor=BG)

    # --- Profit vs Discount ---
    f4 = px.scatter(dff, x="discount", y="profit",
                    color="category", color_discrete_map=CAT_MAP,
                    title="Profit vs Discount by Category", template="plotly_dark")
    f4.update_traces(opacity=0.8, marker=dict(size=7, line=dict(width=0)))
    f4.update_layout(yaxis_title="Profit ($)", xaxis_title="Discount",
                     yaxis_tickformat="$,.0f", title_x=0.5,
                     paper_bgcolor=BG, plot_bgcolor=BG)

    return k_sales, k_profit, k_margin, k_orders, k_disc, f1, f2, f3, f4

# -------------------- Run --------------------
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8050, debug=False)



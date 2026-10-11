# Loupe · Where a Diamond's Story Gets Lost

An interactive Streamlit page showing where rough diamonds lose their link to the mine, using the official
**Kimberley Process** statistics (2019–2025) and The Knot's engagement-ring surveys.

**Live app:** https://loupe-diamonds.streamlit.app/

## What's on the page
1. **The journey:** carats mined vs. imported vs. exported per country (producers vs. trading/cutting hubs).
2. **The gap:** declared value per carat coming in vs. going out, and how global import/export records disagree.
3. **The pressure:** falling value of natural production vs. the rise of lab-grown engagement rings.
4. **Close-up:** one country's diamond flows over 2019–2025.

Linked controls: **Year** + **Type of country** → the **country list** only shows countries of that type active that year.

## Run locally
```bash
pip install -r requirements.txt
streamlit run app.py
```

## Data
- `data/kp_raw.csv`: Kimberley Process *Annual Global Summary* 2019–2025 (kimberleyprocessstatistics.org).
  Each year's rows sum to the published totals.
- `data/lab_grown.csv`: The Knot *Real Weddings Study* (US engagement rings with lab-grown centre stones).

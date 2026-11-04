#!/usr/bin/env python3
"""Print the NPS respondent emails (last 8 weeks) in batches of 45 as Shopify customer-search strings.
Usage: python3 -I nps_emails.py <run_dir> <week_start>   -> one line per batch: email:a OR email:b ...
"""
import sys
from datetime import timedelta
import pandas as pd
RUN, WS = sys.argv[1], sys.argv[2]
WK0 = pd.Timestamp(WS)
r = pd.read_csv(f"{RUN}/inputs/retently.csv", low_memory=False)
r["dt"] = pd.to_datetime(r["Response date (ISO)"]).dt.tz_convert("America/Los_Angeles").dt.tz_localize(None)
n = r[(r.Metric == "NPS") & (r.dt >= WK0 - timedelta(days=49)) & (r.dt < WK0 + timedelta(days=7))]
em = sorted(set(n.Email.dropna().str.lower().str.strip()))
for i in range(0, len(em), 45): print(" OR ".join("email:" + e for e in em[i:i + 45]))

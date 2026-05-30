"""
IPL Data Analysis (2008-2023)
Computes 10 custom metrics from CLAUDE.md + 6 additional insights.
Outputs: individual charts to output/ + multi-tab Plotly HTML dashboard.
"""

import os
import re
import warnings
import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyArrowPatch
import seaborn as sns
import squarify
from wordcloud import WordCloud
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots

warnings.filterwarnings("ignore")

# ── Paths ──────────────────────────────────────────────────────────────────────
BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_PATH = os.path.join(BASE, "Dataset", "IPL_Dataset(2008 - 2023).csv")
OUT = os.path.join(BASE, "output")
os.makedirs(OUT, exist_ok=True)

# ── Style ──────────────────────────────────────────────────────────────────────
plt.rcParams.update({
    "figure.dpi": 150,
    "figure.facecolor": "#0f1117",
    "axes.facecolor": "#1a1d27",
    "axes.edgecolor": "#3a3d4d",
    "axes.labelcolor": "#e0e0e0",
    "xtick.color": "#a0a0a0",
    "ytick.color": "#a0a0a0",
    "text.color": "#e0e0e0",
    "grid.color": "#2a2d3d",
    "grid.linestyle": "--",
    "grid.alpha": 0.5,
    "font.family": "DejaVu Sans",
    "axes.titlesize": 13,
    "axes.labelsize": 10,
})

TEAM_COLORS = {
    "Mumbai Indians": "#004BA0",
    "Chennai Super Kings": "#F9CD05",
    "Royal Challengers Bangalore": "#EC1C24",
    "Royal Challengers Bengaluru": "#EC1C24",
    "Kolkata Knight Riders": "#3A225D",
    "Delhi Capitals": "#17479E",
    "Delhi Daredevils": "#17479E",
    "Rajasthan Royals": "#E91D8E",
    "Sunrisers Hyderabad": "#F7A721",
    "Punjab Kings": "#AAAF26",
    "Kings XI Punjab": "#AAAF26",
    "Deccan Chargers": "#FF8C00",
    "Rising Pune Supergiant": "#6D2077",
    "Rising Pune Supergiants": "#6D2077",
    "Gujarat Lions": "#E8461E",
    "Gujarat Titans": "#1D3461",
    "Lucknow Super Giants": "#A0E6FF",
    "Kochi Tuskers Kerala": "#F26522",
    "Pune Warriors": "#9B59B6",
}
DEFAULT_COLOR = "#7f8c8d"


def team_color(name):
    return TEAM_COLORS.get(name, DEFAULT_COLOR)


def savefig(name, tight=True):
    path = os.path.join(OUT, name)
    if tight:
        plt.tight_layout()
    plt.savefig(path, facecolor=plt.gcf().get_facecolor(), bbox_inches="tight")
    plt.close()
    print(f"  Saved: {name}")


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 0 — Load & Clean Data
# ══════════════════════════════════════════════════════════════════════════════

def load_data():
    df = pd.read_csv(DATA_PATH)

    # Clean Player_of_Match: remove [''] wrapper
    df["Player_of_Match"] = (
        df["Player_of_Match"]
        .astype(str)
        .str.replace(r"^\[\'|'\]$", "", regex=True)
        .str.strip()
    )

    # Parse dates
    df["Date"] = pd.to_datetime(df["Date"], dayfirst=False, errors="coerce")

    # Normalise Season to integer year (e.g. "2007/08" → 2008)
    def parse_season(s):
        s = str(s).strip()
        if "/" in s:
            return int(s.split("/")[0]) + 1
        return int(s)

    df["Year"] = df["Season"].apply(parse_season)

    # MatchType: League vs Playoff
    playoff_labels = {
        "Semi Final", "Final", "Qualifier 1", "Qualifier 2",
        "Elimination Final", "3rd Place Play-Off"
    }
    df["MatchType"] = df["MatchNumber"].apply(
        lambda x: "Playoff" if str(x).strip() in playoff_labels else "League"
    )

    # Did toss winner win?
    df["TossWon"] = df["TossWinner"] == df["WinningTeam"]

    # Normalize margin within WonBy groups
    for wby in ["runs", "wickets"]:
        mask = df["WonBy"] == wby
        col = df.loc[mask, "Margin"]
        mn, mx = col.min(), col.max()
        df.loc[mask, "MarginNorm"] = (col - mn) / (mx - mn) if mx > mn else 0.5

    print(f"Loaded {len(df)} matches | Years: {df['Year'].min()}–{df['Year'].max()}")
    print(f"Teams: {sorted(df['WinningTeam'].dropna().unique())}\n")
    return df


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 1 — Required Metrics
# ══════════════════════════════════════════════════════════════════════════════

# ── 1. Toss Decision Yield (TDY) ───────────────────────────────────────────────
def plot_tdy(df):
    print("1. Toss Decision Yield (TDY)...")
    toss_wins = df[df["TossWinner"] == df["WinningTeam"]].copy()
    # For each team that won the toss, what was their decision and win rate
    tdy = (
        df.assign(TossTeamWon=df["TossWinner"] == df["WinningTeam"])
        .groupby(["TossWinner", "TossDecision"])
        .agg(matches=("TossTeamWon", "count"), wins=("TossTeamWon", "sum"))
        .reset_index()
    )
    tdy["WinRate"] = tdy["wins"] / tdy["matches"]
    tdy = tdy[tdy["matches"] >= 5]  # min sample
    tdy = tdy.rename(columns={"TossWinner": "Team"})

    teams = sorted(tdy["Team"].unique())
    x = np.arange(len(teams))
    width = 0.35

    fig, ax = plt.subplots(figsize=(16, 7))
    for i, decision in enumerate(["bat", "field"]):
        subset = tdy[tdy["TossDecision"] == decision].set_index("Team")
        vals = [subset.loc[t, "WinRate"] if t in subset.index else 0 for t in teams]
        offset = (i - 0.5) * width
        bars = ax.bar(x + offset, vals, width, label=decision.capitalize(),
                      color=["#3498DB" if decision == "bat" else "#E74C3C"] * len(teams),
                      alpha=0.85, edgecolor="#0f1117", linewidth=0.5)
        for bar, val in zip(bars, vals):
            if val > 0:
                ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.01,
                        f"{val:.0%}", ha="center", va="bottom", fontsize=7, color="#a0a0a0")

    ax.axhline(0.5, color="#F39C12", linestyle="--", linewidth=1, label="50% baseline")
    ax.set_xticks(x)
    ax.set_xticklabels([t.replace(" ", "\n") for t in teams], fontsize=8)
    ax.set_ylabel("Win Rate after winning toss")
    ax.set_title("Toss Decision Yield (TDY) — Win rate by toss decision per team")
    ax.legend(loc="upper right")
    ax.set_ylim(0, 0.9)
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0%}"))
    ax.grid(axis="y", alpha=0.4)
    savefig("tdy_grouped_bar.png")


# ── 2. Toss Advantage Coefficient (TAC) ────────────────────────────────────────
def plot_tac(df):
    print("2. Toss Advantage Coefficient (TAC)...")
    all_teams = sorted(set(df["Team1"].unique()) | set(df["Team2"].unique()))
    records = []
    for team in all_teams:
        team_matches = df[(df["Team1"] == team) | (df["Team2"] == team)].copy()
        if len(team_matches) < 10:
            continue
        team_matches["Won"] = team_matches["WinningTeam"] == team
        team_matches["WonToss"] = team_matches["TossWinner"] == team
        toss_won = team_matches[team_matches["WonToss"]]
        toss_lost = team_matches[~team_matches["WonToss"]]
        wr_won = toss_won["Won"].mean() if len(toss_won) > 5 else np.nan
        wr_lost = toss_lost["Won"].mean() if len(toss_lost) > 5 else np.nan
        if pd.notna(wr_won) and pd.notna(wr_lost) and wr_lost > 0:
            tac = wr_won / wr_lost
        else:
            tac = np.nan
        records.append({"Team": team, "WinRateTossWon": wr_won, "WinRateTossLost": wr_lost, "TAC": tac})

    tac_df = pd.DataFrame(records).dropna()

    fig, ax = plt.subplots(figsize=(12, 9))
    for _, row in tac_df.iterrows():
        color = team_color(row["Team"])
        ax.scatter(row["WinRateTossWon"], row["WinRateTossLost"], s=150,
                   color=color, zorder=5, edgecolors="white", linewidth=0.7)
        ax.annotate(row["Team"].replace(" ", "\n"), (row["WinRateTossWon"], row["WinRateTossLost"]),
                    textcoords="offset points", xytext=(6, 4), fontsize=7.5, color="#e0e0e0")
        if row["TAC"] > 1.5:
            ax.scatter(row["WinRateTossWon"], row["WinRateTossLost"], s=350,
                       facecolors="none", edgecolors="#E74C3C", linewidth=2, zorder=4)

    lims = [0.2, 0.75]
    ax.plot(lims, lims, "w--", linewidth=1, alpha=0.5, label="No toss advantage")
    ax.set_xlim(*lims)
    ax.set_ylim(*lims)
    ax.set_xlabel("Win Rate when TOSS WON")
    ax.set_ylabel("Win Rate when TOSS LOST")
    ax.set_title("Toss Advantage Coefficient (TAC)\nRed ring = TAC > 1.5 (extreme toss dependency)")
    ax.xaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0%}"))
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0%}"))
    ax.legend()
    ax.grid(alpha=0.3)
    savefig("tac_scatter.png")


# ── 3. Margin-Weighted Dominance Index (MWDI) ──────────────────────────────────
def plot_mwdi(df):
    print("3. Margin-Weighted Dominance Index (MWDI)...")
    wins = df[df["WinningTeam"].notna() & df["MarginNorm"].notna()].copy()

    fig, ax = plt.subplots(figsize=(16, 7))
    teams = sorted(wins["WinningTeam"].unique())
    data_by_team = [wins[wins["WinningTeam"] == t]["MarginNorm"].values for t in teams]
    colors = [team_color(t) for t in teams]

    bp = ax.boxplot(data_by_team, patch_artist=True, notch=False,
                    medianprops=dict(color="white", linewidth=2),
                    whiskerprops=dict(color="#a0a0a0"),
                    capprops=dict(color="#a0a0a0"),
                    flierprops=dict(marker="o", markersize=3, color="#a0a0a0", alpha=0.4))
    for patch, color in zip(bp["boxes"], colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.75)

    ax.set_xticklabels([t.replace(" ", "\n") for t in teams], fontsize=8)
    ax.set_ylabel("Normalized Win Margin [0=narrow, 1=dominant]")
    ax.set_title("Margin-Weighted Dominance Index (MWDI)\nDistribution of normalized win margins per team")
    ax.grid(axis="y", alpha=0.4)
    savefig("mwdi_box.png")


# ── 4. Close-Match Resilience Index (CMRI) ─────────────────────────────────────
def plot_cmri(df):
    print("4. Close-Match Resilience Index (CMRI)...")
    close_mask = (
        ((df["WonBy"] == "runs") & (df["Margin"] <= 10)) |
        ((df["WonBy"] == "wickets") & (df["Margin"] <= 3)) |
        (df["WonBy"] == "tie")
    )
    close = df[close_mask].copy()

    records = []
    for team in sorted(df["WinningTeam"].dropna().unique()):
        team_close = close[(close["Team1"] == team) | (close["Team2"] == team)]
        close_wins = close[close["WinningTeam"] == team]
        cmri = len(close_wins) / len(team_close) if len(team_close) > 0 else 0
        records.append({"Team": team, "CloseGames": len(team_close), "CloseWins": len(close_wins), "CMRI": cmri})

    cmri_df = pd.DataFrame(records)
    cmri_df = cmri_df[cmri_df["CloseGames"] >= 5].sort_values("CMRI")
    baseline = cmri_df["CMRI"].mean()
    cmri_df["RelCMRI"] = cmri_df["CMRI"] - baseline

    colors = ["#2ECC71" if v >= 0 else "#E74C3C" for v in cmri_df["RelCMRI"]]

    fig, ax = plt.subplots(figsize=(12, 8))
    bars = ax.barh(cmri_df["Team"], cmri_df["RelCMRI"], color=colors, edgecolor="#0f1117",
                   linewidth=0.5, height=0.65)
    ax.axvline(0, color="white", linewidth=1.2, linestyle="--")
    for bar, val, cmri_val in zip(bars, cmri_df["RelCMRI"], cmri_df["CMRI"]):
        xpos = val + (0.005 if val >= 0 else -0.005)
        ha = "left" if val >= 0 else "right"
        ax.text(xpos, bar.get_y() + bar.get_height() / 2,
                f"{cmri_val:.0%}", va="center", ha=ha, fontsize=9, color="#e0e0e0")
    ax.set_xlabel("CMRI relative to league average")
    ax.set_title(f"Close-Match Resilience Index (CMRI)\nLeague average CMRI = {baseline:.1%}")
    ax.grid(axis="x", alpha=0.3)
    savefig("cmri_diverging.png")


# ── 5. Venue Bias Score (VBS) ──────────────────────────────────────────────────
def plot_vbs(df):
    print("5. Venue Bias Score (VBS)...")
    # Chase = TossDecision is "field" AND TossWinner wins
    venue_data = df.groupby("Venue").apply(
        lambda g: pd.Series({
            "TotalMatches": len(g),
            "ChasesWon": ((g["TossDecision"] == "field") & (g["TossWinner"] == g["WinningTeam"])).sum()
        })
    ).reset_index()
    venue_data = venue_data[venue_data["TotalMatches"] >= 8]
    venue_data["VBS"] = venue_data["ChasesWon"] / venue_data["TotalMatches"]
    venue_data = venue_data.sort_values("VBS")

    def vbs_color(v):
        if v > 0.55:
            return "#2ECC71"  # chasing bias
        elif v < 0.45:
            return "#E74C3C"  # defending bias
        return "#F39C12"      # neutral

    colors = [vbs_color(v) for v in venue_data["VBS"]]

    fig, ax = plt.subplots(figsize=(14, max(6, len(venue_data) * 0.35)))
    bars = ax.barh(venue_data["Venue"], venue_data["VBS"], color=colors,
                   edgecolor="#0f1117", linewidth=0.4, height=0.7)
    ax.axvline(0.55, color="#2ECC71", linestyle=":", linewidth=1.2, label="Chase bias (>55%)")
    ax.axvline(0.45, color="#E74C3C", linestyle=":", linewidth=1.2, label="Defend bias (<45%)")
    ax.axvline(0.5, color="white", linestyle="--", linewidth=0.8, label="Neutral")
    for bar, val in zip(bars, venue_data["VBS"]):
        ax.text(val + 0.005, bar.get_y() + bar.get_height() / 2,
                f"{val:.0%}", va="center", fontsize=7, color="#e0e0e0")
    ax.set_xlabel("Venue Bias Score (chase wins / total matches)")
    ax.set_title("Venue Bias Score (VBS) — Chasing vs Defending advantage by ground")
    ax.legend(loc="lower right", fontsize=8)
    ax.set_xlim(0, 0.85)
    ax.grid(axis="x", alpha=0.3)
    savefig("vbs_horizontal_bar.png")


# ── 6. Fortress Dominance Ratio (FDR) ─────────────────────────────────────────
def plot_fdr(df):
    print("6. Fortress Dominance Ratio (FDR)...")
    league = df[df["MatchType"] == "League"].copy()
    # Home = team is Team1 (first listed team at their home venue)
    records = []
    all_teams = sorted(set(league["Team1"].unique()) | set(league["Team2"].unique()))
    for team in all_teams:
        home = league[league["Team1"] == team]
        away = league[league["Team2"] == team]
        home_wr = (home["WinningTeam"] == team).mean() if len(home) >= 5 else np.nan
        away_wr = (away["WinningTeam"] == team).mean() if len(away) >= 5 else np.nan
        if pd.notna(home_wr) and pd.notna(away_wr) and away_wr > 0:
            fdr = home_wr / away_wr
        else:
            fdr = np.nan
        records.append({"Team": team, "HomeWR": home_wr, "AwayWR": away_wr, "FDR": fdr})

    fdr_df = pd.DataFrame(records).dropna().sort_values("FDR", ascending=False).head(8)

    # Radar chart
    categories = list(fdr_df["Team"])
    home_vals = list(fdr_df["HomeWR"])
    away_vals = list(fdr_df["AwayWR"])
    fdr_vals = list(fdr_df["FDR"])
    N = len(categories)
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]

    fig, ax = plt.subplots(figsize=(10, 10), subplot_kw=dict(polar=True))
    ax.set_facecolor("#1a1d27")
    fig.patch.set_facecolor("#0f1117")

    def plot_radar(values, color, label, alpha=0.25):
        v = values + values[:1]
        ax.plot(angles, v, "o-", linewidth=2, color=color, label=label)
        ax.fill(angles, v, alpha=alpha, color=color)

    plot_radar(home_vals, "#3498DB", "Home Win Rate")
    plot_radar(away_vals, "#E74C3C", "Away Win Rate")

    ax.set_xticks(angles[:-1])
    ax.set_xticklabels([c.replace(" ", "\n") for c in categories], size=8, color="#e0e0e0")
    ax.set_yticks([0.3, 0.4, 0.5, 0.6, 0.7])
    ax.set_yticklabels(["30%", "40%", "50%", "60%", "70%"], size=7, color="#a0a0a0")
    ax.set_ylim(0, 0.85)
    ax.grid(color="#3a3d4d", linewidth=0.5)
    ax.spines["polar"].set_color("#3a3d4d")
    ax.set_title("Fortress Dominance Ratio (FDR)\nHome vs Away Win Rate — Top 8 Franchises",
                 pad=20, color="#e0e0e0", size=12)
    ax.legend(loc="lower right", bbox_to_anchor=(1.25, 0.1), fontsize=9)

    # Annotate FDR values
    for angle, team, fdr_v in zip(angles[:-1], categories, fdr_vals):
        ax.text(angle, 0.88, f"FDR={fdr_v:.2f}", ha="center", va="center",
                fontsize=7, color="#F39C12")

    savefig("fdr_radar.png", tight=False)


# ── 7. POM Concentration Index ─────────────────────────────────────────────────
def plot_pom_concentration(df):
    print("7. POM Concentration Index (Treemap)...")
    # Assign POM to winning team
    pom = df[df["Player_of_Match"].notna() & df["WinningTeam"].notna()].copy()
    # HHI-style: for each team, distribution of POM awards among its players
    records = []
    for team in sorted(pom["WinningTeam"].unique()):
        team_pom = pom[pom["WinningTeam"] == team]["Player_of_Match"]
        total = len(team_pom)
        if total < 5:
            continue
        counts = team_pom.value_counts()
        hhi = sum((c / total) ** 2 for c in counts)
        concentration = 1 - hhi  # high = diverse/collective
        records.append({"Team": team, "TotalPOM": total, "Concentration": concentration})

    pom_df = pd.DataFrame(records).sort_values("TotalPOM", ascending=False)

    fig, ax = plt.subplots(figsize=(14, 9))
    fig.patch.set_facecolor("#0f1117")
    ax.set_facecolor("#0f1117")

    sizes = pom_df["TotalPOM"].values
    concs = pom_df["Concentration"].values
    norm = plt.Normalize(concs.min(), concs.max())
    cmap = plt.cm.RdYlGn
    colors = [cmap(norm(c)) for c in concs]
    labels = [f"{row['Team']}\n{row['TotalPOM']} POMs\nConc={row['Concentration']:.2f}"
              for _, row in pom_df.iterrows()]

    squarify.plot(sizes=sizes, label=labels, color=colors, alpha=0.85,
                  text_kwargs={"color": "black", "fontsize": 8, "wrap": True}, ax=ax)
    ax.set_title("POM Concentration Index (Treemap)\nTile size = total POM wins | Color: Green=collective, Red=star-dependent",
                 color="#e0e0e0")
    ax.axis("off")
    sm = plt.cm.ScalarMappable(cmap=cmap, norm=norm)
    sm.set_array([])
    cbar = plt.colorbar(sm, ax=ax, fraction=0.025, pad=0.02)
    cbar.set_label("Concentration (1=collective)", color="#e0e0e0")
    cbar.ax.yaxis.set_tick_params(color="#a0a0a0")
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color="#a0a0a0")
    savefig("pom_treemap.png")


# ── 8. Big-Match Performance Index (BMPI) ──────────────────────────────────────
def plot_bmpi(df):
    print("8. Big-Match Performance Index (BMPI)...")
    pom = df[df["Player_of_Match"].notna()].copy()
    pom_league = pom[pom["MatchType"] == "League"]
    pom_playoff = pom[pom["MatchType"] == "Playoff"]

    total_pom = pom["Player_of_Match"].value_counts().reset_index()
    total_pom.columns = ["Player", "TotalPOM"]
    playoff_pom = pom_playoff["Player_of_Match"].value_counts().reset_index()
    playoff_pom.columns = ["Player", "PlayoffPOM"]

    top20 = total_pom.head(20).merge(playoff_pom, on="Player", how="left").fillna(0)
    top20["BMPI"] = top20["PlayoffPOM"] / top20["TotalPOM"]

    fig, ax = plt.subplots(figsize=(12, 8))
    sc = ax.scatter(top20["TotalPOM"], top20["PlayoffPOM"],
                    s=top20["BMPI"] * 1500 + 80, c=top20["BMPI"],
                    cmap="RdYlGn", alpha=0.85, edgecolors="white", linewidth=0.7,
                    vmin=0, vmax=top20["BMPI"].max())
    for _, row in top20.iterrows():
        ax.annotate(row["Player"], (row["TotalPOM"], row["PlayoffPOM"]),
                    xytext=(5, 4), textcoords="offset points", fontsize=8, color="#e0e0e0")
    cbar = plt.colorbar(sc)
    cbar.set_label("BMPI (Playoff POMs / Total POMs)", color="#e0e0e0")
    cbar.ax.yaxis.set_tick_params(color="#a0a0a0")
    plt.setp(cbar.ax.yaxis.get_ticklabels(), color="#a0a0a0")
    ax.set_xlabel("Total Player of Match Awards")
    ax.set_ylabel("Playoff Player of Match Awards")
    ax.set_title("Big-Match Performance Index (BMPI)\nDot size & color = big-game performer ratio | Top 20 players")
    ax.grid(alpha=0.3)
    savefig("bmpi_dot.png")


# ── 9. Dynamic Momentum Coefficient (DMC) ──────────────────────────────────────
def plot_dmc(df):
    print("9. Dynamic Momentum Coefficient (DMC)...")
    league = df[df["MatchType"] == "League"].copy()
    league["MatchSeq"] = league.groupby(["Year", "Team1"]).cumcount() + 1

    # Build per-team per-season win sequence
    all_teams = sorted(set(league["Team1"].unique()) | set(league["Team2"].unique()))
    # Use top 8 by total matches
    team_counts = pd.Series(
        [t for row in league[["Team1", "Team2"]].values for t in row]
    ).value_counts().head(8).index.tolist()

    records = []
    for team in team_counts:
        team_df = league[(league["Team1"] == team) | (league["Team2"] == team)].copy()
        team_df = team_df.sort_values(["Year", "Date"])
        team_df["Won"] = (team_df["WinningTeam"] == team).astype(int)
        team_df["GameNum"] = team_df.groupby("Year").cumcount() + 1
        team_df["RollingWin"] = team_df.groupby("Year")["Won"].transform(
            lambda x: x.rolling(3, min_periods=1).mean()
        )
        team_df["Team"] = team
        records.append(team_df[["Year", "GameNum", "RollingWin", "Team"]])

    dmc_df = pd.concat(records)

    g = sns.FacetGrid(dmc_df, col="Team", col_wrap=4, height=3, aspect=1.4,
                      sharey=True, hue="Year", palette="tab10")
    g.map(sns.lineplot, "GameNum", "RollingWin", alpha=0.75, linewidth=1.2)
    g.add_legend(title="Season", bbox_to_anchor=(1.01, 0.5))
    g.set_titles(col_template="{col_name}", size=9, color="#e0e0e0")
    g.set_axis_labels("Match # in Season", "Rolling 3-game Win Rate")
    g.figure.suptitle("Dynamic Momentum Coefficient (DMC)\nRolling 3-game win rate per team per season",
                       y=1.02, color="#e0e0e0")
    for ax in g.axes.flat:
        ax.axhline(0.5, color="white", linestyle="--", linewidth=0.8, alpha=0.5)
        ax.set_facecolor("#1a1d27")
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0%}"))
    g.figure.patch.set_facecolor("#0f1117")
    g.figure.savefig(os.path.join(OUT, "dmc_facetgrid.png"), bbox_inches="tight",
                     facecolor="#0f1117", dpi=150)
    plt.close()
    print("  Saved: dmc_facetgrid.png")


# ── 10. Title Conversion Efficiency (TCE) ──────────────────────────────────────
def plot_tce(df):
    print("10. Title Conversion Efficiency (TCE)...")
    finals = df[df["MatchNumber"].astype(str).str.strip() == "Final"].copy()
    if len(finals) == 0:
        print("  No 'Final' rows found — skipping TCE")
        return

    # Teams that appeared in finals
    finalists = pd.concat([finals["Team1"], finals["Team2"]]).value_counts().reset_index()
    finalists.columns = ["Team", "FinalsReached"]
    winners = finals["WinningTeam"].value_counts().reset_index()
    winners.columns = ["Team", "FinalsWon"]
    tce_df = finalists.merge(winners, on="Team", how="left").fillna(0)
    tce_df["TCE"] = tce_df["FinalsWon"] / tce_df["FinalsReached"]
    tce_df = tce_df.sort_values("FinalsReached", ascending=False)

    fig, ax = plt.subplots(figsize=(10, 10))
    fig.patch.set_facecolor("#0f1117")
    ax.set_facecolor("#0f1117")
    ax.set_aspect("equal")

    n = len(tce_df)
    outer_r = 1.0
    inner_r = 0.55
    ring_w = (outer_r - inner_r) / 2
    colors_outer = [team_color(t) for t in tce_df["Team"]]
    colors_inner = [team_color(t) for t in tce_df["Team"]]

    # Outer ring: Finals reached
    outer_sizes = tce_df["FinalsReached"].values
    inner_sizes = tce_df["FinalsWon"].values

    def _donut_ring(ax, sizes, radius, width, colors, labels=None, fontsize=8):
        total = sum(sizes)
        start = 0
        for i, (size, color) in enumerate(zip(sizes, colors)):
            angle = size / total * 360
            wedge = mpatches.Wedge(center=(0, 0), r=radius, theta1=start, theta2=start + angle,
                                   width=width, facecolor=color, edgecolor="#0f1117",
                                   linewidth=1.5, alpha=0.85)
            ax.add_patch(wedge)
            if labels and angle > 10:
                mid_angle = np.radians(start + angle / 2)
                lx = (radius - width / 2) * np.cos(mid_angle)
                ly = (radius - width / 2) * np.sin(mid_angle)
                ax.text(lx, ly, labels[i], ha="center", va="center",
                        fontsize=fontsize, color="white", fontweight="bold")
            start += angle

    _donut_ring(ax, outer_sizes, outer_r, ring_w, colors_outer,
                labels=[f"{r['Team'].split()[-1]}\n{int(r['FinalsReached'])}" for _, r in tce_df.iterrows()])
    _donut_ring(ax, inner_sizes + 0.001, inner_r, ring_w, colors_inner,
                labels=[f"{int(r['FinalsWon'])}\n({r['TCE']:.0%})" for _, r in tce_df.iterrows()])

    ax.text(0, outer_r + 0.12, "Outer ring: Finals Reached", ha="center", fontsize=9, color="#3498DB")
    ax.text(0, -(outer_r + 0.12), "Inner ring: Finals Won (TCE%)", ha="center", fontsize=9, color="#E74C3C")
    ax.set_xlim(-1.3, 1.3)
    ax.set_ylim(-1.3, 1.3)
    ax.axis("off")
    ax.set_title("Title Conversion Efficiency (TCE)\nFinals Reached vs Finals Won per Team",
                 color="#e0e0e0", fontsize=12, pad=15)
    savefig("tce_donut.png", tight=False)


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 2 — Additional Insights
# ══════════════════════════════════════════════════════════════════════════════

# ── A. Head-to-Head Heatmap ────────────────────────────────────────────────────
def plot_h2h(df):
    print("A. Head-to-Head Matrix (Heatmap)...")
    teams = sorted(df["WinningTeam"].dropna().unique())
    matrix = pd.DataFrame(0, index=teams, columns=teams)
    for _, row in df.dropna(subset=["WinningTeam"]).iterrows():
        loser = row["Team2"] if row["WinningTeam"] == row["Team1"] else row["Team1"]
        if row["WinningTeam"] in teams and loser in teams:
            matrix.loc[row["WinningTeam"], loser] += 1

    fig, ax = plt.subplots(figsize=(14, 12))
    mask = matrix == 0
    sns.heatmap(matrix, annot=True, fmt="d", cmap="YlOrRd", linewidths=0.5,
                linecolor="#0f1117", ax=ax, mask=mask,
                annot_kws={"size": 8},
                cbar_kws={"label": "Win Count", "shrink": 0.7})
    ax.set_xticklabels([t.replace(" ", "\n") for t in matrix.columns], rotation=45, ha="right", fontsize=8)
    ax.set_yticklabels([t.replace(" ", "\n") for t in matrix.index], rotation=0, fontsize=8)
    ax.set_title("Head-to-Head Win Matrix (Row team beat Column team)", color="#e0e0e0", pad=12)
    ax.set_xlabel("Defeated Team")
    ax.set_ylabel("Winning Team")
    savefig("h2h_heatmap.png")


# ── B. Era Analysis — Chasing vs Defending ────────────────────────────────────
def plot_era_analysis(df):
    print("B. Era Analysis — Chasing vs Defending...")
    def assign_era(year):
        if year <= 2013:
            return "Era 1 (2008–13)"
        elif year <= 2018:
            return "Era 2 (2014–18)"
        return "Era 3 (2019–23)"

    df2 = df.copy()
    df2["Era"] = df2["Year"].apply(assign_era)
    df2["BatFirst"] = df2["TossDecision"].apply(lambda x: "Bat First" if x == "bat" else "Chase")
    df2["TossWinnerWon"] = df2["TossWinner"] == df2["WinningTeam"]
    df2["BattingFirstWon"] = (
        ((df2["TossDecision"] == "bat") & df2["TossWinnerWon"]) |
        ((df2["TossDecision"] == "field") & ~df2["TossWinnerWon"])
    )

    era_summary = df2.groupby("Era").agg(
        Matches=("BattingFirstWon", "count"),
        BatFirstWins=("BattingFirstWon", "sum")
    ).reset_index()
    era_summary["ChaseWins"] = era_summary["Matches"] - era_summary["BatFirstWins"]
    era_summary["BatFirstRate"] = era_summary["BatFirstWins"] / era_summary["Matches"]
    era_summary["ChaseRate"] = era_summary["ChaseWins"] / era_summary["Matches"]

    x = np.arange(len(era_summary))
    width = 0.35
    fig, ax = plt.subplots(figsize=(10, 6))
    bars1 = ax.bar(x - width / 2, era_summary["BatFirstRate"], width,
                   label="Bat First Wins", color="#3498DB", alpha=0.85)
    bars2 = ax.bar(x + width / 2, era_summary["ChaseRate"], width,
                   label="Chase Wins", color="#E74C3C", alpha=0.85)
    for bars in [bars1, bars2]:
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.005,
                    f"{bar.get_height():.0%}", ha="center", va="bottom", fontsize=9, color="#e0e0e0")
    ax.set_xticks(x)
    ax.set_xticklabels(era_summary["Era"], fontsize=10)
    ax.set_ylabel("Win Rate")
    ax.set_title("Batting First vs Chasing Win Rate Across IPL Eras")
    ax.legend()
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0%}"))
    ax.set_ylim(0, 0.75)
    ax.grid(axis="y", alpha=0.4)
    savefig("era_chase_bat_bar.png")


# ── C. Season Win Rate Trends ──────────────────────────────────────────────────
def plot_season_trends(df):
    print("C. Season-by-Season Win Rate Trends...")
    # Map old team names to current
    name_map = {
        "Delhi Daredevils": "Delhi Capitals",
        "Kings XI Punjab": "Punjab Kings",
        "Rising Pune Supergiant": "Rising Pune Supergiants",
        "Royal Challengers Bangalore": "Royal Challengers Bengaluru",
    }
    df2 = df.copy()
    for col in ["Team1", "Team2", "WinningTeam"]:
        df2[col] = df2[col].replace(name_map)

    top_teams = (
        pd.concat([df2["Team1"], df2["Team2"]])
        .value_counts()
        .head(8)
        .index.tolist()
    )

    records = []
    for team in top_teams:
        for year in sorted(df2["Year"].unique()):
            yr = df2[df2["Year"] == year]
            team_matches = yr[(yr["Team1"] == team) | (yr["Team2"] == team)]
            if len(team_matches) < 5:
                continue
            wr = (team_matches["WinningTeam"] == team).mean()
            records.append({"Team": team, "Year": year, "WinRate": wr})

    trend_df = pd.DataFrame(records)

    fig, ax = plt.subplots(figsize=(16, 7))
    for team in top_teams:
        t_data = trend_df[trend_df["Team"] == team].sort_values("Year")
        color = team_color(team)
        ax.plot(t_data["Year"], t_data["WinRate"], "o-", color=color,
                linewidth=2, markersize=5, label=team, alpha=0.85)

    ax.axhline(0.5, color="white", linestyle="--", linewidth=0.8, alpha=0.5)
    ax.set_xlabel("Season")
    ax.set_ylabel("Win Rate")
    ax.set_title("Season-by-Season Team Win Rate Trends (Top 8 Franchises)")
    ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda y, _: f"{y:.0%}"))
    ax.legend(loc="upper left", fontsize=8, bbox_to_anchor=(1.01, 1))
    ax.grid(alpha=0.3)
    savefig("season_win_trend.png")


# ── D. Venue-Toss Decision Interaction Heatmap ────────────────────────────────
def plot_venue_toss_heatmap(df):
    print("D. Venue-Toss Decision Interaction Heatmap...")
    df2 = df.copy()
    df2["TossWinnerWon"] = df2["TossWinner"] == df2["WinningTeam"]
    counts = df2.groupby("Venue").size()
    valid_venues = counts[counts >= 10].index
    df2 = df2[df2["Venue"].isin(valid_venues)]
    pivot = df2.pivot_table(index="Venue", columns="TossDecision",
                            values="TossWinnerWon", aggfunc="mean")
    pivot = pivot.T  # TossDecision as rows, Venue as columns

    fig, ax = plt.subplots(figsize=(18, 5))
    sns.heatmap(pivot, annot=True, fmt=".0%", cmap="RdYlGn", linewidths=0.3,
                linecolor="#0f1117", ax=ax, vmin=0.3, vmax=0.7,
                annot_kws={"size": 7},
                cbar_kws={"label": "Win Rate (toss winner)", "shrink": 0.6})
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha="right", fontsize=7)
    ax.set_title("Venue × Toss Decision Interaction\nWin rate of toss winner when choosing to bat/field",
                 color="#e0e0e0", pad=10)
    ax.set_ylabel("Toss Decision")
    ax.set_xlabel("")
    savefig("venue_toss_heatmap.png")


# ── E. Super Over Analysis ─────────────────────────────────────────────────────
def plot_super_over(df):
    print("E. Super Over Analysis...")
    ties = df[df["WonBy"] == "tie"].copy()
    if len(ties) == 0:
        # Some datasets use "Superover" or just have margin=0
        ties = df[(df["Margin"] == 0) | (df["WonBy"].str.lower().str.contains("super", na=False))].copy()

    if len(ties) == 0:
        print("  No Super Over data found — skipping")
        return

    # Count appearances and wins
    appeared = pd.concat([ties["Team1"], ties["Team2"]]).value_counts().reset_index()
    appeared.columns = ["Team", "Appearances"]
    won = ties["WinningTeam"].value_counts().reset_index()
    won.columns = ["Team", "Wins"]
    so_df = appeared.merge(won, on="Team", how="left").fillna(0)
    so_df["Losses"] = so_df["Appearances"] - so_df["Wins"]
    so_df = so_df.sort_values("Appearances", ascending=False)

    fig, ax = plt.subplots(figsize=(12, 6))
    x = np.arange(len(so_df))
    ax.bar(x, so_df["Wins"], label="Won Super Over", color="#2ECC71", alpha=0.85)
    ax.bar(x, so_df["Losses"], bottom=so_df["Wins"], label="Lost Super Over",
           color="#E74C3C", alpha=0.85)
    ax.set_xticks(x)
    ax.set_xticklabels([t.replace(" ", "\n") for t in so_df["Team"]], fontsize=8)
    ax.set_ylabel("Number of Super Overs")
    ax.set_title(f"Super Over Analysis — {len(ties)} matches decided by Super Over")
    ax.legend()
    ax.grid(axis="y", alpha=0.4)
    savefig("super_over_bar.png")


# ── F. POM Word Cloud ──────────────────────────────────────────────────────────
def plot_pom_wordcloud(df):
    print("F. POM Word Cloud...")
    pom_counts = df["Player_of_Match"].dropna().value_counts().to_dict()
    wc = WordCloud(width=1400, height=700, background_color="#0f1117",
                   colormap="RdYlGn", max_words=80,
                   prefer_horizontal=0.8).generate_from_frequencies(pom_counts)
    fig, ax = plt.subplots(figsize=(14, 7))
    fig.patch.set_facecolor("#0f1117")
    ax.set_facecolor("#0f1117")
    ax.imshow(wc, interpolation="bilinear")
    ax.axis("off")
    ax.set_title("Player of Match — Frequency Word Cloud (2008–2023)",
                 color="#e0e0e0", pad=12)
    savefig("pom_wordcloud.png", tight=False)


# ══════════════════════════════════════════════════════════════════════════════
# PHASE 3 — Plotly Dashboard
# ══════════════════════════════════════════════════════════════════════════════

def build_plotly_dashboard(df):
    print("\nBuilding Plotly HTML dashboard...")

    # ── Tab 1: Toss Strategy ──────────────────────────────────────────────────
    tdy_data = (
        df.assign(TossTeamWon=df["TossWinner"] == df["WinningTeam"])
        .groupby(["TossWinner", "TossDecision"])
        .agg(matches=("TossTeamWon", "count"), wins=("TossTeamWon", "sum"))
        .reset_index()
    )
    tdy_data["WinRate"] = tdy_data["wins"] / tdy_data["matches"]
    tdy_data = tdy_data[tdy_data["matches"] >= 5]

    fig_tdy = px.bar(tdy_data, x="TossWinner", y="WinRate", color="TossDecision",
                     barmode="group", title="Toss Decision Yield (TDY)",
                     color_discrete_map={"bat": "#3498DB", "field": "#E74C3C"},
                     labels={"TossWinner": "Team", "WinRate": "Win Rate", "TossDecision": "Decision"},
                     template="plotly_dark")
    fig_tdy.update_layout(yaxis_tickformat=".0%")

    # Chase vs Defend overall
    chase_overall = df.assign(
        TossWon=df["TossWinner"] == df["WinningTeam"]
    ).groupby("TossDecision")["TossWon"].agg(["mean", "count"]).reset_index()
    chase_overall.columns = ["Decision", "WinRate", "Matches"]
    fig_chase = px.bar(chase_overall, x="Decision", y="WinRate",
                       title="Overall Chase vs Defend Win Rate",
                       color="Decision",
                       color_discrete_map={"bat": "#3498DB", "field": "#E74C3C"},
                       template="plotly_dark",
                       text_auto=".0%")
    fig_chase.update_layout(yaxis_tickformat=".0%")

    # ── Tab 2: Clutch Analytics ───────────────────────────────────────────────
    close_mask = (
        ((df["WonBy"] == "runs") & (df["Margin"] <= 10)) |
        ((df["WonBy"] == "wickets") & (df["Margin"] <= 3)) |
        (df["WonBy"] == "tie")
    )
    close = df[close_mask].copy()
    records = []
    for team in sorted(df["WinningTeam"].dropna().unique()):
        team_close = close[(close["Team1"] == team) | (close["Team2"] == team)]
        close_wins = close[close["WinningTeam"] == team]
        cmri = len(close_wins) / len(team_close) if len(team_close) > 0 else 0
        records.append({"Team": team, "CloseGames": len(team_close), "CMRI": cmri})
    cmri_df = pd.DataFrame(records)
    cmri_df = cmri_df[cmri_df["CloseGames"] >= 5].sort_values("CMRI")
    baseline = cmri_df["CMRI"].mean()
    cmri_df["RelCMRI"] = cmri_df["CMRI"] - baseline
    cmri_df["Color"] = cmri_df["RelCMRI"].apply(lambda x: "#2ECC71" if x >= 0 else "#E74C3C")

    fig_cmri = go.Figure(go.Bar(
        x=cmri_df["RelCMRI"], y=cmri_df["Team"],
        orientation="h",
        marker_color=cmri_df["Color"],
        text=cmri_df["CMRI"].apply(lambda x: f"{x:.0%}"),
        textposition="outside"
    ))
    fig_cmri.update_layout(title=f"Close-Match Resilience Index (CMRI) | Avg={baseline:.1%}",
                           template="plotly_dark", xaxis_tickformat=".0%")

    # Win margin distribution
    wins_data = df[df["WinningTeam"].notna() & df["MarginNorm"].notna()].copy()
    fig_mwdi = px.box(wins_data, x="WinningTeam", y="MarginNorm",
                      title="Margin-Weighted Dominance Index (MWDI)",
                      template="plotly_dark",
                      labels={"WinningTeam": "Team", "MarginNorm": "Normalized Win Margin"})
    fig_mwdi.update_xaxes(tickangle=45)

    # ── Tab 3: Venue Insights ─────────────────────────────────────────────────
    venue_data = df.groupby("Venue").apply(
        lambda g: pd.Series({
            "TotalMatches": len(g),
            "ChasesWon": ((g["TossDecision"] == "field") & (g["TossWinner"] == g["WinningTeam"])).sum()
        })
    ).reset_index()
    venue_data = venue_data[venue_data["TotalMatches"] >= 8]
    venue_data["VBS"] = venue_data["ChasesWon"] / venue_data["TotalMatches"]
    venue_data["Bias"] = venue_data["VBS"].apply(
        lambda v: "Chase Bias" if v > 0.55 else ("Defend Bias" if v < 0.45 else "Neutral")
    )
    venue_data = venue_data.sort_values("VBS")

    fig_vbs = px.bar(venue_data, x="VBS", y="Venue", orientation="h",
                     color="Bias",
                     color_discrete_map={"Chase Bias": "#2ECC71", "Defend Bias": "#E74C3C", "Neutral": "#F39C12"},
                     title="Venue Bias Score (VBS)",
                     template="plotly_dark",
                     labels={"VBS": "Chase Win Rate", "Venue": "Ground"})
    fig_vbs.update_layout(xaxis_tickformat=".0%")
    fig_vbs.add_vline(x=0.5, line_dash="dash", line_color="white", opacity=0.5)

    # H2H heatmap
    name_map = {
        "Delhi Daredevils": "Delhi Capitals",
        "Kings XI Punjab": "Punjab Kings",
        "Rising Pune Supergiant": "Rising Pune Supergiants",
        "Royal Challengers Bangalore": "Royal Challengers Bengaluru",
    }
    df_h2h = df.copy()
    for col in ["Team1", "Team2", "WinningTeam"]:
        df_h2h[col] = df_h2h[col].replace(name_map)
    top8 = (pd.concat([df_h2h["Team1"], df_h2h["Team2"]]).value_counts().head(8).index.tolist())
    df_h2h_top = df_h2h[(df_h2h["Team1"].isin(top8)) & (df_h2h["Team2"].isin(top8))]
    matrix = pd.DataFrame(0, index=top8, columns=top8)
    for _, row in df_h2h_top.dropna(subset=["WinningTeam"]).iterrows():
        loser = row["Team2"] if row["WinningTeam"] == row["Team1"] else row["Team1"]
        if row["WinningTeam"] in top8 and loser in top8:
            matrix.loc[row["WinningTeam"], loser] += 1
    fig_h2h = px.imshow(matrix, text_auto=True, color_continuous_scale="YlOrRd",
                        title="Head-to-Head Win Matrix (Top 8 teams)",
                        template="plotly_dark",
                        labels=dict(x="Defeated", y="Winner", color="Wins"))

    # ── Tab 4: Player Impact ──────────────────────────────────────────────────
    pom = df[df["Player_of_Match"].notna()].copy()
    pom_playoff = pom[pom["MatchType"] == "Playoff"]
    total_pom = pom["Player_of_Match"].value_counts().reset_index()
    total_pom.columns = ["Player", "TotalPOM"]
    playoff_pom = pom_playoff["Player_of_Match"].value_counts().reset_index()
    playoff_pom.columns = ["Player", "PlayoffPOM"]
    top20 = total_pom.head(20).merge(playoff_pom, on="Player", how="left").fillna(0)
    top20["BMPI"] = top20["PlayoffPOM"] / top20["TotalPOM"]

    fig_bmpi = px.scatter(top20, x="TotalPOM", y="PlayoffPOM", text="Player",
                          size="BMPI", color="BMPI",
                          color_continuous_scale="RdYlGn",
                          title="Big-Match Performance Index (BMPI) — Top 20 Players",
                          template="plotly_dark",
                          labels={"TotalPOM": "Total POMs", "PlayoffPOM": "Playoff POMs", "BMPI": "Big-Match Index"})
    fig_bmpi.update_traces(textposition="top center")

    # POM frequency bar
    top_pom = total_pom.head(15)
    fig_pom_bar = px.bar(top_pom.sort_values("TotalPOM"), x="TotalPOM", y="Player",
                         orientation="h", title="Top 15 Player of Match Winners",
                         template="plotly_dark",
                         color="TotalPOM", color_continuous_scale="YlOrRd",
                         labels={"TotalPOM": "POM Awards", "Player": ""})

    # ── Season Win Rate ────────────────────────────────────────────────────────
    df_s = df.copy()
    for col in ["Team1", "Team2", "WinningTeam"]:
        df_s[col] = df_s[col].replace(name_map)
    top8_cur = (pd.concat([df_s["Team1"], df_s["Team2"]]).value_counts().head(8).index.tolist())
    season_records = []
    for team in top8_cur:
        for year in sorted(df_s["Year"].unique()):
            yr = df_s[df_s["Year"] == year]
            team_matches = yr[(yr["Team1"] == team) | (yr["Team2"] == team)]
            if len(team_matches) < 5:
                continue
            wr = (team_matches["WinningTeam"] == team).mean()
            season_records.append({"Team": team, "Year": year, "WinRate": wr})
    trend_df = pd.DataFrame(season_records)
    fig_trend = px.line(trend_df, x="Year", y="WinRate", color="Team",
                        title="Season Win Rate Trends (Top 8 Franchises)",
                        template="plotly_dark",
                        labels={"WinRate": "Win Rate", "Year": "Season"})
    fig_trend.update_layout(yaxis_tickformat=".0%")
    fig_trend.add_hline(y=0.5, line_dash="dash", line_color="white", opacity=0.4)

    # ── Assemble Dashboard ────────────────────────────────────────────────────
    html_parts = []
    html_parts.append("""<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<title>IPL Analysis Dashboard 2008-2023</title>
<!-- Plotly must load BEFORE any chart init scripts that call Plotly.newPlot -->
<script src="https://cdn.plot.ly/plotly-2.35.2.min.js"></script>
<style>
  body { background: #0f1117; color: #e0e0e0; font-family: 'Segoe UI', Arial, sans-serif; margin: 0; }
  .header { background: linear-gradient(135deg, #1a1d27, #0f1117);
            padding: 28px 40px; border-bottom: 2px solid #3a3d4d; }
  .header h1 { margin: 0; font-size: 28px; color: #F39C12; letter-spacing: 1px; }
  .header p  { margin: 6px 0 0; color: #a0a0a0; font-size: 14px; }
  .tabs { display: flex; background: #1a1d27; border-bottom: 2px solid #3a3d4d; overflow-x: auto; }
  .tab  { padding: 14px 24px; cursor: pointer; font-size: 14px; color: #a0a0a0;
          border-bottom: 3px solid transparent; white-space: nowrap; transition: all 0.2s; }
  .tab:hover  { color: #F39C12; }
  .tab.active { color: #F39C12; border-bottom-color: #F39C12; background: #0f1117; }
  .content    { display: none; padding: 24px; }
  .content.active { display: block; }
  .grid-2 { display: grid; grid-template-columns: 1fr 1fr; gap: 20px; }
  .grid-1 { display: grid; grid-template-columns: 1fr; gap: 20px; }
  .card { background: #1a1d27; border-radius: 10px; border: 1px solid #2a2d3d; overflow: hidden; }
  .section-title { font-size: 11px; color: #a0a0a0; padding: 8px 14px 0;
                   text-transform: uppercase; letter-spacing: 1px; }
</style>
</head>
<body>
<div class="header">
  <h1>IPL Data Analysis Dashboard</h1>
  <p>Indian Premier League · 2008–2023 · 1,024 matches</p>
</div>
<div class="tabs">
  <div class="tab active" onclick="showTab(0)">Toss Strategy</div>
  <div class="tab" onclick="showTab(1)">Clutch Analytics</div>
  <div class="tab" onclick="showTab(2)">Venue Insights</div>
  <div class="tab" onclick="showTab(3)">Player Impact</div>
  <div class="tab" onclick="showTab(4)">Season Trends</div>
</div>
""")

    def fig_to_div(fig, height=500):
        fig.update_layout(height=height, margin=dict(l=20, r=20, t=50, b=20))
        return fig.to_html(full_html=False, include_plotlyjs=False, config={"responsive": True})

    tabs_content = [
        # Tab 0: Toss Strategy
        f"""<div class="content active" id="tab0">
  <div class="grid-2">
    <div class="card"><p class="section-title">Toss Decision Yield</p>{fig_to_div(fig_tdy)}</div>
    <div class="card"><p class="section-title">Overall Chase vs Defend</p>{fig_to_div(fig_chase, 500)}</div>
  </div>
</div>""",
        # Tab 1: Clutch Analytics
        f"""<div class="content" id="tab1">
  <div class="grid-2">
    <div class="card"><p class="section-title">Close-Match Resilience (CMRI)</p>{fig_to_div(fig_cmri)}</div>
    <div class="card"><p class="section-title">Win Margin Distribution (MWDI)</p>{fig_to_div(fig_mwdi)}</div>
  </div>
</div>""",
        # Tab 2: Venue Insights
        f"""<div class="content" id="tab2">
  <div class="grid-1">
    <div class="card"><p class="section-title">Venue Bias Score (VBS)</p>{fig_to_div(fig_vbs, 700)}</div>
    <div class="card"><p class="section-title">Head-to-Head Matrix</p>{fig_to_div(fig_h2h, 600)}</div>
  </div>
</div>""",
        # Tab 3: Player Impact
        f"""<div class="content" id="tab3">
  <div class="grid-2">
    <div class="card"><p class="section-title">Big-Match Performance Index (BMPI)</p>{fig_to_div(fig_bmpi)}</div>
    <div class="card"><p class="section-title">Top 15 POM Winners</p>{fig_to_div(fig_pom_bar)}</div>
  </div>
</div>""",
        # Tab 4: Season Trends
        f"""<div class="content" id="tab4">
  <div class="grid-1">
    <div class="card"><p class="section-title">Season Win Rate Trends</p>{fig_to_div(fig_trend, 600)}</div>
  </div>
</div>""",
    ]

    for content in tabs_content:
        html_parts.append(content)

    html_parts.append("""
<script>
function showTab(n) {
  document.querySelectorAll('.tab').forEach((t, i) => {
    t.classList.toggle('active', i === n);
  });
  document.querySelectorAll('.content').forEach((c, i) => {
    c.classList.toggle('active', i === n);
  });
  // Resize all Plotly charts in the newly visible tab so they fill their containers
  var activeTab = document.getElementById('tab' + n);
  if (activeTab) {
    activeTab.querySelectorAll('.plotly-graph-div').forEach(function(div) {
      Plotly.Plots.resize(div);
    });
  }
}
</script>
</body>
</html>""")

    dash_path = os.path.join(OUT, "ipl_dashboard.html")
    with open(dash_path, "w", encoding="utf-8") as f:
        f.write("\n".join(html_parts))
    print(f"  Dashboard saved: ipl_dashboard.html")


# ══════════════════════════════════════════════════════════════════════════════
# MAIN
# ══════════════════════════════════════════════════════════════════════════════

def main():
    print("=" * 60)
    print("IPL Data Analysis 2008–2023")
    print("=" * 60)
    df = load_data()

    print("\n-- Phase 1: CLAUDE.md Required Metrics --")
    plot_tdy(df)
    plot_tac(df)
    plot_mwdi(df)
    plot_cmri(df)
    plot_vbs(df)
    plot_fdr(df)
    plot_pom_concentration(df)
    plot_bmpi(df)
    plot_dmc(df)
    plot_tce(df)

    print("\n-- Phase 2: Additional Insights --")
    plot_h2h(df)
    plot_era_analysis(df)
    plot_season_trends(df)
    plot_venue_toss_heatmap(df)
    plot_super_over(df)
    plot_pom_wordcloud(df)

    print("\n-- Phase 3: Dashboard --")
    build_plotly_dashboard(df)

    print("\n" + "=" * 60)
    print(f"All outputs saved to: {OUT}")
    print("=" * 60)


if __name__ == "__main__":
    main()

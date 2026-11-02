
import nflreadpy as nfl
import polars as pl
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

pbp = nfl.load_pbp(2025)

play_data = pbp.select([
    "posteam",
    "down",
    "ydstogo",
    "play_type",
    "game_id",
    "yardline_100",
    "play_id",
    "fourth_down_converted"
])

fourth_down_data = play_data.filter(
    pl.col("down") == 4
)

fourth_down_attempts = fourth_down_data.filter(
    pl.col("play_type").is_in(["run", "pass"])
)

fourth_down_opportunities = fourth_down_data.filter(
    pl.col("play_type").is_in([
        "run", "pass", "punt", "field_goal"
    ])
)

team_attempts = (
    fourth_down_attempts
    .group_by("posteam")
    .len()
    .rename({
        "posteam": "team",
        "len": "attempts"
    })
)

team_opportunities = (
    fourth_down_opportunities
    .group_by("posteam")
    .len()
    .rename({
        "posteam": "team",
        "len": "opportunities"
    })
)

team_fourth_down_stats = team_attempts.join(
    team_opportunities,
    on="team",
    how="inner"
)

team_fourth_down_stats = team_fourth_down_stats.with_columns(
    (
        pl.col("attempts") /
        pl.col("opportunities") * 100
    ).alias("attempt_rate")
)

team_fourth_down_stats = team_fourth_down_stats.sort(
    "attempt_rate",
    descending=True
)

successful_conversions = fourth_down_attempts.filter(
    pl.col("fourth_down_converted") == 1.0
)

team_conversions = (
    successful_conversions
    .group_by("posteam")
    .len()
    .rename({
        "posteam": "team",
        "len": "conversions"
    })
)

team_conversion_stats = team_attempts.join(
    team_conversions,
    on="team",
    how="left"
)

team_conversion_stats = team_conversion_stats.with_columns(
    pl.col("conversions").fill_null(0)
)

team_conversion_stats = team_conversion_stats.with_columns(
    (
        pl.col("conversions") /
        pl.col("attempts") * 100
    ).alias("conversion_rate")
)

team_conversion_stats = team_conversion_stats.sort(
    "conversion_rate",
    descending=True
)

comparison = team_fourth_down_stats.join(
    team_conversion_stats.select([
        "team",
        "conversions",
        "conversion_rate"
    ]),
    on="team",
    how="inner"
)

print("\nFOURTH-DOWN AGGRESSIVENESS RANKINGS")
print(team_fourth_down_stats)

print("\nFOURTH-DOWN CONVERSION RANKINGS")
print(team_conversion_stats)

print("\nCOMPLETE TEAM STATISTICS")
print(comparison)

plt.style.use("dark_background")

legend_items = [
    Patch(color="#22C55E", label="Top 5 Teams"),
    Patch(color="#3B82F6", label="Middle 22 Teams"),
    Patch(color="#EF4444", label="Bottom 5 Teams")
]


def create_bar_chart(data, value_column, title, ylabel, filename):
    teams = data["team"].to_list()
    rates = data[value_column].to_list()

    colors = ["#3B82F6"] * len(teams)
    colors[:5] = ["#22C55E"] * 5
    colors[-5:] = ["#EF4444"] * 5

    fig, ax = plt.subplots(figsize=(18, 9))
    fig.patch.set_facecolor("#0B1120")
    ax.set_facecolor("#111827")

    bars = ax.bar(
        teams,
        rates,
        color=colors,
        width=0.75
    )

    for bar, rate in zip(bars, rates):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            bar.get_height() + 0.5,
            f"{rate:.1f}%",
            ha="center",
            va="bottom",
            fontsize=8,
            color="white"
        )

    ax.set_title(
        title,
        fontsize=22,
        fontweight="bold",
        pad=25
    )

    ax.set_xlabel(
        "NFL Team",
        fontsize=12,
        labelpad=15
    )

    ax.set_ylabel(
        ylabel,
        fontsize=12
    )

    ax.tick_params(
        axis="x",
        labelrotation=90,
        labelsize=10
    )

    ax.set_ylim(0, max(rates) + 10)
    ax.grid(axis="y", linestyle="--", alpha=0.2)
    ax.set_axisbelow(True)

    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)

    ax.legend(
        handles=legend_items,
        loc="upper right"
    )

    plt.tight_layout()

    plt.savefig(
        filename,
        dpi=300,
        bbox_inches="tight",
        facecolor=fig.get_facecolor()
    )

    plt.close(fig)


create_bar_chart(
    team_fourth_down_stats,
    "attempt_rate",
    "NFL FOURTH-DOWN AGGRESSIVENESS | 2025",
    "Fourth-Down Attempt Rate (%)",
    "fourth_down_aggressiveness_2025.png"
)

create_bar_chart(
    team_conversion_stats,
    "conversion_rate",
    "NFL FOURTH-DOWN CONVERSION RATES | 2025",
    "Fourth-Down Conversion Rate (%)",
    "fourth_down_conversion_rates_2025.png"
)

fig, ax = plt.subplots(figsize=(16, 10))
fig.patch.set_facecolor("#0B1120")
ax.set_facecolor("#111827")

x = comparison["attempt_rate"].to_numpy()
y = comparison["conversion_rate"].to_numpy()
teams = comparison["team"].to_list()

avg_x = np.mean(x)
avg_y = np.mean(y)

colors = []

for a, c in zip(x, y):
    if a >= avg_x and c >= avg_y:
        colors.append("#22C55E")
    elif a < avg_x and c >= avg_y:
        colors.append("#38BDF8")
    elif a >= avg_x and c < avg_y:
        colors.append("#F59E0B")
    else:
        colors.append("#EF4444")

ax.scatter(
    x,
    y,
    s=190,
    c=colors,
    alpha=0.95,
    edgecolors="white",
    linewidths=1.2,
    zorder=3
)

for team, a, c in zip(teams, x, y):
    ax.annotate(
        team,
        (a, c),
        xytext=(7, 7),
        textcoords="offset points",
        fontsize=9,
        fontweight="bold",
        color="#E5E7EB"
    )

ax.axvline(
    avg_x,
    color="#94A3B8",
    linestyle="--",
    linewidth=1.5,
    alpha=0.65
)

ax.axhline(
    avg_y,
    color="#94A3B8",
    linestyle="--",
    linewidth=1.5,
    alpha=0.65
)

ax.set_xlim(min(x) - 3, max(x) + 4)
ax.set_ylim(min(y) - 8, max(y) + 8)

ax.text(
    0.98, 0.97,
    "AGGRESSIVE + EFFICIENT",
    transform=ax.transAxes,
    ha="right",
    va="top",
    color="#22C55E",
    fontsize=12,
    fontweight="bold"
)

ax.text(
    0.02, 0.97,
    "SELECTIVE + EFFICIENT",
    transform=ax.transAxes,
    ha="left",
    va="top",
    color="#38BDF8",
    fontsize=12,
    fontweight="bold"
)

ax.text(
    0.98, 0.04,
    "AGGRESSIVE + LESS EFFICIENT",
    transform=ax.transAxes,
    ha="right",
    va="bottom",
    color="#F59E0B",
    fontsize=12,
    fontweight="bold"
)

ax.text(
    0.02, 0.04,
    "SELECTIVE + LESS EFFICIENT",
    transform=ax.transAxes,
    ha="left",
    va="bottom",
    color="#EF4444",
    fontsize=12,
    fontweight="bold"
)

ax.set_title(
    "NFL FOURTH-DOWN DECISION MAKING | 2025",
    fontsize=23,
    fontweight="bold",
    color="white",
    pad=25
)

ax.set_xlabel(
    "FOURTH-DOWN ATTEMPT RATE (%)",
    fontsize=12,
    fontweight="bold",
    labelpad=15
)

ax.set_ylabel(
    "FOURTH-DOWN CONVERSION RATE (%)",
    fontsize=12,
    fontweight="bold",
    labelpad=15
)

ax.grid(
    color="#334155",
    linestyle="--",
    alpha=0.35
)

ax.set_axisbelow(True)

for spine in ax.spines.values():
    spine.set_visible(False)

ax.tick_params(colors="#CBD5E1", labelsize=10)

plt.tight_layout()

plt.savefig(
    "fourth_down_aggressiveness_vs_success_2025.png",
    dpi=300,
    bbox_inches="tight",
    facecolor=fig.get_facecolor()
)

plt.close(fig)

comparison.write_csv(
    "nfl_fourth_down_team_stats_2025.csv"
)

print("\nAnalysis complete!")
print("All three charts and CSV file saved.")


print("\nDATA VALIDATION")
print("Total fourth-down attempts:", fourth_down_attempts.height)
print("Successful conversions:", successful_conversions.height)
print("Missing conversion values:",
      fourth_down_attempts["fourth_down_converted"].null_count())
print("Total opportunities:", fourth_down_opportunities.height)

print("\nFOURTH-DOWN DISTANCE ANALYSIS")

print(
    fourth_down_opportunities
    .group_by("ydstogo")
    .len()
    .sort("ydstogo")
)

distance_stats = (
    fourth_down_opportunities
    .group_by("ydstogo")
    .agg([
        pl.len().alias("opportunities"),
        pl.col("play_type")
        .is_in(["run", "pass"])
        .sum()
        .alias("attempts")
    ])
    .with_columns(
        (
            pl.col("attempts") /
            pl.col("opportunities") * 100
        ).alias("attempt_rate")
    )
    .sort("ydstogo")
)

print("\nFOURTH-DOWN ATTEMPT RATE BY DISTANCE")
print(distance_stats.head(15))


distance_chart = distance_stats.filter(
    pl.col("ydstogo").is_between(1, 15)
)

distances = distance_chart["ydstogo"].to_list()
attempt_rates = distance_chart["attempt_rate"].to_list()

fig, ax = plt.subplots(figsize=(15, 8))
fig.patch.set_facecolor("#0B1120")
ax.set_facecolor("#111827")

ax.plot(
    distances,
    attempt_rates,
    color="#38BDF8",
    linewidth=3,
    marker="o",
    markersize=9,
    markerfacecolor="#22C55E",
    markeredgecolor="white",
    markeredgewidth=1.5
)

ax.fill_between(
    distances,
    attempt_rates,
    color="#38BDF8",
    alpha=0.12
)

for distance, rate in zip(distances, attempt_rates):
    ax.annotate(
        f"{rate:.1f}%",
        (distance, rate),
        xytext=(0, 12),
        textcoords="offset points",
        ha="center",
        fontsize=9,
        color="white",
        fontweight="bold"
    )

ax.set_title(
    "NFL FOURTH-DOWN AGGRESSIVENESS BY DISTANCE | 2025",
    fontsize=20,
    fontweight="bold",
    color="white",
    pad=25
)

ax.set_xlabel(
    "YARDS NEEDED FOR FIRST DOWN",
    fontsize=12,
    fontweight="bold",
    labelpad=15
)

ax.set_ylabel(
    "FOURTH-DOWN ATTEMPT RATE (%)",
    fontsize=12,
    fontweight="bold",
    labelpad=15
)

ax.set_xticks(range(1, 16))
ax.set_ylim(0, 90)

ax.grid(
    color="#334155",
    linestyle="--",
    alpha=0.3
)

ax.set_axisbelow(True)

for spine in ax.spines.values():
    spine.set_visible(False)

ax.tick_params(colors="#CBD5E1", labelsize=10)

plt.tight_layout()

plt.savefig(
    "fourth_down_attempt_rate_by_distance_2025.png",
    dpi=300,
    bbox_inches="tight",
    facecolor=fig.get_facecolor()
)

plt.close(fig)

print("Fourth-down distance chart saved!")


from pathlib import Path

output_dir = Path("project_outputs")
output_dir.mkdir(exist_ok=True)

print("\nSTARTING ADVANCED FOURTH-DOWN ANALYSIS")

analysis_data = fourth_down_opportunities.filter(
    pl.col("posteam").is_not_null()
    & pl.col("ydstogo").is_not_null()
    & pl.col("yardline_100").is_not_null()
    & pl.col("ydstogo").is_between(1, 99)
    & pl.col("yardline_100").is_between(1, 99)
).with_columns(
    pl.col("play_type")
    .is_in(["run", "pass"])
    .cast(pl.Int64)
    .alias("attempted")
)

analysis_data = analysis_data.with_columns(
    pl.when(pl.col("yardline_100") <= 20)
    .then(pl.lit("Opponent 1-20"))
    .when(pl.col("yardline_100") <= 40)
    .then(pl.lit("Opponent 21-40"))
    .when(pl.col("yardline_100") <= 60)
    .then(pl.lit("Midfield"))
    .when(pl.col("yardline_100") <= 80)
    .then(pl.lit("Own 21-40"))
    .otherwise(pl.lit("Own 1-20"))
    .alias("field_zone")
)

field_order = [
    "Own 1-20",
    "Own 21-40",
    "Midfield",
    "Opponent 21-40",
    "Opponent 1-20"
]

field_position_stats = (
    analysis_data
    .group_by("field_zone")
    .agg([
        pl.len().alias("opportunities"),
        pl.col("attempted").sum().alias("attempts")
    ])
    .with_columns(
        (
            pl.col("attempts") /
            pl.col("opportunities") * 100
        ).alias("attempt_rate")
    )
    .with_columns(
        pl.col("field_zone")
        .replace_strict(
            {zone: i for i, zone in enumerate(field_order)}
        )
        .alias("sort_order")
    )
    .sort("sort_order")
)

print("\nATTEMPT RATE BY FIELD POSITION")
print(field_position_stats)

fig, ax = plt.subplots(figsize=(14, 8))
fig.patch.set_facecolor("#0B1120")
ax.set_facecolor("#111827")

zones = field_position_stats["field_zone"].to_list()
rates = field_position_stats["attempt_rate"].to_list()

field_colors = [
    "#EF4444",
    "#F59E0B",
    "#3B82F6",
    "#38BDF8",
    "#22C55E"
]

bars = ax.bar(
    zones,
    rates,
    color=field_colors,
    width=0.65
)

for bar, rate in zip(bars, rates):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 1,
        f"{rate:.1f}%",
        ha="center",
        color="white",
        fontsize=12,
        fontweight="bold"
    )

ax.set_title(
    "NFL FOURTH-DOWN AGGRESSIVENESS BY FIELD POSITION | 2025",
    fontsize=19,
    fontweight="bold",
    pad=25
)

ax.set_ylabel("Fourth-Down Attempt Rate (%)")
ax.set_ylim(0, max(rates) + 12)
ax.grid(axis="y", alpha=0.2, linestyle="--")
ax.set_axisbelow(True)

for spine in ax.spines.values():
    spine.set_visible(False)

plt.tight_layout()

plt.savefig(
    output_dir / "field_position_analysis.png",
    dpi=300,
    bbox_inches="tight",
    facecolor=fig.get_facecolor()
)

plt.close(fig)

conversion_distance_stats = (
    fourth_down_attempts
    .filter(
        pl.col("ydstogo").is_not_null()
        & pl.col("ydstogo").is_between(1, 15)
    )
    .group_by("ydstogo")
    .agg([
        pl.len().alias("attempts"),
        (
            pl.col("fourth_down_converted") == 1.0
        ).sum().alias("conversions")
    ])
    .with_columns(
        (
            pl.col("conversions") /
            pl.col("attempts") * 100
        ).alias("conversion_rate")
    )
    .sort("ydstogo")
)

print("\nCONVERSION SUCCESS BY DISTANCE")
print(conversion_distance_stats)

fig, ax = plt.subplots(figsize=(15, 8))
fig.patch.set_facecolor("#0B1120")
ax.set_facecolor("#111827")

distances = conversion_distance_stats["ydstogo"].to_list()
rates = conversion_distance_stats["conversion_rate"].to_list()

ax.plot(
    distances,
    rates,
    color="#22C55E",
    linewidth=3,
    marker="o",
    markersize=9,
    markeredgecolor="white",
    markeredgewidth=1.2
)

ax.fill_between(
    distances,
    rates,
    color="#22C55E",
    alpha=0.12
)

for distance, rate in zip(distances, rates):
    ax.annotate(
        f"{rate:.1f}%",
        (distance, rate),
        xytext=(0, 12),
        textcoords="offset points",
        ha="center",
        fontsize=9,
        color="white"
    )

ax.set_title(
    "NFL FOURTH-DOWN CONVERSION SUCCESS BY DISTANCE | 2025",
    fontsize=20,
    fontweight="bold",
    pad=25
)

ax.set_xlabel("Yards Needed for First Down")
ax.set_ylabel("Conversion Rate (%)")
ax.set_xticks(range(1, 16))
ax.set_ylim(0, 105)
ax.grid(alpha=0.25, linestyle="--")
ax.set_axisbelow(True)

for spine in ax.spines.values():
    spine.set_visible(False)

plt.tight_layout()

plt.savefig(
    output_dir / "conversion_success_by_distance.png",
    dpi=300,
    bbox_inches="tight",
    facecolor=fig.get_facecolor()
)

plt.close(fig)

team_short_yardage = (
    analysis_data
    .filter(pl.col("ydstogo").is_between(1, 2))
    .group_by("posteam")
    .agg([
        pl.len().alias("short_opportunities"),
        pl.col("attempted").sum().alias("short_attempts")
    ])
    .with_columns(
        (
            pl.col("short_attempts") /
            pl.col("short_opportunities") * 100
        ).alias("short_attempt_rate")
    )
    .rename({"posteam": "team"})
    .sort("short_attempt_rate", descending=True)
)

print("\nTEAM AGGRESSIVENESS ON FOURTH-AND-1 OR 2")
print(team_short_yardage)

fig, ax = plt.subplots(figsize=(18, 9))
fig.patch.set_facecolor("#0B1120")
ax.set_facecolor("#111827")

teams = team_short_yardage["team"].to_list()
rates = team_short_yardage["short_attempt_rate"].to_list()

colors = ["#3B82F6"] * len(teams)
colors[:5] = ["#22C55E"] * 5
colors[-5:] = ["#EF4444"] * 5

bars = ax.bar(teams, rates, color=colors)

for bar, rate in zip(bars, rates):
    ax.text(
        bar.get_x() + bar.get_width() / 2,
        bar.get_height() + 1,
        f"{rate:.0f}%",
        ha="center",
        fontsize=8,
        color="white"
    )

ax.set_title(
    "NFL FOURTH-DOWN SHORT-YARDAGE AGGRESSIVENESS | 2025",
    fontsize=20,
    fontweight="bold",
    pad=25
)

ax.set_xlabel("NFL Team")
ax.set_ylabel("Attempt Rate on 4th-and-1 or 2 (%)")
ax.tick_params(axis="x", labelrotation=90)
ax.set_ylim(0, 110)
ax.grid(axis="y", alpha=0.2, linestyle="--")
ax.set_axisbelow(True)

for spine in ax.spines.values():
    spine.set_visible(False)

plt.tight_layout()

plt.savefig(
    output_dir / "short_yardage_team_rankings.png",
    dpi=300,
    bbox_inches="tight",
    facecolor=fig.get_facecolor()
)

plt.close(fig)

distance_field_matrix = (
    analysis_data
    .with_columns(
        pl.when(pl.col("ydstogo") <= 2)
        .then(pl.lit("1-2"))
        .when(pl.col("ydstogo") <= 5)
        .then(pl.lit("3-5"))
        .when(pl.col("ydstogo") <= 10)
        .then(pl.lit("6-10"))
        .otherwise(pl.lit("11+"))
        .alias("distance_group")
    )
    .group_by(["distance_group", "field_zone"])
    .agg([
        pl.len().alias("opportunities"),
        pl.col("attempted").sum().alias("attempts")
    ])
    .with_columns(
        (
            pl.col("attempts") /
            pl.col("opportunities") * 100
        ).alias("attempt_rate")
    )
)

distance_groups = ["1-2", "3-5", "6-10", "11+"]
heatmap_values = np.full((4, 5), np.nan)
heatmap_counts = np.zeros((4, 5), dtype=int)

for row in distance_field_matrix.iter_rows(named=True):
    i = distance_groups.index(row["distance_group"])
    j = field_order.index(row["field_zone"])
    heatmap_values[i, j] = row["attempt_rate"]
    heatmap_counts[i, j] = row["opportunities"]

fig, ax = plt.subplots(figsize=(15, 8))
fig.patch.set_facecolor("#0B1120")
ax.set_facecolor("#111827")

cmap = plt.get_cmap("viridis").copy()
cmap.set_bad("#334155")

image = ax.imshow(
    heatmap_values,
    cmap=cmap,
    vmin=0,
    vmax=100,
    aspect="auto"
)

ax.set_xticks(range(5))
ax.set_xticklabels(field_order, rotation=20, ha="right")
ax.set_yticks(range(4))
ax.set_yticklabels(distance_groups)

for i in range(4):
    for j in range(5):
        if not np.isnan(heatmap_values[i, j]):
            ax.text(
                j,
                i,
                f"{heatmap_values[i, j]:.1f}%\n(n={heatmap_counts[i, j]})",
                ha="center",
                va="center",
                fontsize=10,
                fontweight="bold",
                color="white" if heatmap_values[i, j] < 55 else "#0B1120"
            )

ax.set_title(
    "NFL FOURTH-DOWN DECISIONS BY DISTANCE & FIELD POSITION | 2025",
    fontsize=18,
    fontweight="bold",
    pad=25
)

ax.set_xlabel("Field Position")
ax.set_ylabel("Yards to Go")

colorbar = fig.colorbar(image, ax=ax)
colorbar.set_label("Fourth-Down Attempt Rate (%)")

plt.tight_layout()

plt.savefig(
    output_dir / "fourth_down_decision_heatmap.png",
    dpi=300,
    bbox_inches="tight",
    facecolor=fig.get_facecolor()
)

plt.close(fig)

field_position_stats.drop("sort_order").write_csv(
    output_dir / "field_position_stats.csv"
)

conversion_distance_stats.write_csv(
    output_dir / "conversion_by_distance.csv"
)

team_short_yardage.write_csv(
    output_dir / "team_short_yardage_stats.csv"
)

distance_field_matrix.write_csv(
    output_dir / "distance_field_matrix.csv"
)

comparison.write_csv(
    output_dir / "team_fourth_down_stats.csv"
)

distance_stats.write_csv(
    output_dir / "attempt_rate_by_distance.csv"
)

league_attempts = fourth_down_attempts.height
league_conversions = successful_conversions.height
league_opportunities = fourth_down_opportunities.height

league_attempt_rate = (
    league_attempts / league_opportunities * 100
)

league_conversion_rate = (
    league_conversions / league_attempts * 100
)

most_aggressive = team_fourth_down_stats.row(
    0, named=True
)

least_aggressive = team_fourth_down_stats.row(
    -1, named=True
)

most_successful = team_conversion_stats.row(
    0, named=True
)

summary = f"""
2025 NFL FOURTH-DOWN ANALYTICS
========================================

LEAGUE OVERVIEW

Fourth-Down Opportunities: {league_opportunities:,}
Fourth-Down Attempts: {league_attempts:,}
Successful Conversions: {league_conversions:,}

League Attempt Rate: {league_attempt_rate:.2f}%
League Conversion Rate: {league_conversion_rate:.2f}%

TEAM LEADERS

Most Aggressive Team:
{most_aggressive['team']} - {most_aggressive['attempt_rate']:.2f}%

Least Aggressive Team:
{least_aggressive['team']} - {least_aggressive['attempt_rate']:.2f}%

Highest Conversion Rate:
{most_successful['team']} - {most_successful['conversion_rate']:.2f}%

METHODOLOGY

Data Source: nflreadpy / nflverse
Season: 2025

Fourth-down attempts:
Run or pass plays on fourth down.

Fourth-down opportunities:
Run, pass, punt, or field goal plays on fourth down.

Attempt rate:
Attempts divided by opportunities.

Conversion rate:
Successful fourth-down conversions divided by attempts.

ANALYSIS LIMITATIONS

Results are descriptive, not causal.

Game score, clock, opponent strength, and win
probability are not controlled for.

Penalties, no-play records, and unusual fourth-down
situations require additional validation.

Team rankings should not be interpreted as proof
of optimal coaching decisions.
"""

(output_dir / "analysis_summary.txt").write_text(summary)

print(summary)

print("\nPROJECT OUTPUTS CREATED")
for file in sorted(output_dir.iterdir()):
    print(file.name)

print("\nNFL FOURTH-DOWN ANALYTICS PROJECT COMPLETE!")

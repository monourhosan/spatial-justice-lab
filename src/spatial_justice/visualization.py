"""Visualization module for spatial justice research figures and interactive maps.

Generates publication-quality static graphics (PNG/SVG) and interactive maps (HTML):
1. fig01_poverty_rate_choropleth
2. fig02_walking_distance_choropleth
3. fig03_access_score_choropleth
4. fig04_poverty_vs_distance_scatter
5. fig05_quintile_disparity_contrast
6. fig06_weighted_lorenz_curve
7. fig07_spatial_disadvantage_map
8. fig08_facility_simulation_map
9. interactive_chicago_map.html
"""

from __future__ import annotations

import logging
from pathlib import Path

import folium
import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
from folium.plugins import MarkerCluster

from spatial_justice.mathematics import compute_lorenz_curve

logger = logging.getLogger(__name__)

ATTRIBUTION_TEXT = "Sources: U.S. Census Bureau ACS 5-Yr (2019-2023), City of Chicago Data Portal, OpenStreetMap."


def setup_matplotlib_style():
    """Configure publication plot styling."""
    plt.rcParams.update(
        {
            "font.size": 10,
            "axes.labelsize": 11,
            "axes.titlesize": 12,
            "xtick.labelsize": 9,
            "ytick.labelsize": 9,
            "legend.fontsize": 9,
            "figure.titlesize": 14,
            "figure.dpi": 300,
            "savefig.dpi": 300,
            "savefig.bbox": "tight",
        }
    )


def plot_choropleth(
    gdf: gpd.GeoDataFrame,
    column: str,
    title: str,
    output_path: Path | str,
    cmap: str = "viridis",
    legend_label: str = "",
    amenity_gdf: gpd.GeoDataFrame | None = None,
    boundary_gdf: gpd.GeoDataFrame | None = None,
    format_pct: bool = False,
):
    """Plot a single spatial choropleth map."""
    setup_matplotlib_style()
    fig, ax = plt.subplots(figsize=(8, 10))

    if boundary_gdf is not None:
        boundary_gdf.plot(ax=ax, color="none", edgecolor="black", linewidth=1.2, zorder=3)

    # Plot tracts
    gdf.plot(
        column=column,
        ax=ax,
        cmap=cmap,
        legend=True,
        legend_kwds={
            "label": legend_label,
            "orientation": "horizontal",
            "shrink": 0.7,
            "pad": 0.05,
        },
        missing_kwds={"color": "lightgrey", "label": "No Data / Unpopulated"},
        edgecolor="#333333",
        linewidth=0.2,
        zorder=2,
    )

    # Plot facility overlay if supplied
    if amenity_gdf is not None:
        amenity_gdf.plot(
            ax=ax,
            color="#e41a1c",
            markersize=25,
            edgecolor="white",
            linewidth=0.6,
            zorder=4,
            label="Library Branch",
        )
        ax.legend(loc="lower left", framealpha=0.9)

    ax.set_title(title, pad=12, fontweight="bold")
    ax.axis("off")
    fig.text(0.5, 0.02, ATTRIBUTION_TEXT, ha="center", fontsize=8, color="#555555")

    dest = Path(output_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(dest)
    plt.close(fig)
    logger.info(f"Saved choropleth map to {dest}")


def plot_scatter_association(
    x: np.ndarray,
    y: np.ndarray,
    weights: np.ndarray,
    output_path: Path | str,
    title: str,
    xlabel: str,
    ylabel: str,
    rho: float,
    p_val: float,
    ci: tuple[float, float],
):
    """Plot associational scatterplot with OLS fit and uncertainty."""
    setup_matplotlib_style()
    fig, ax = plt.subplots(figsize=(8, 6))

    valid = ~np.isnan(x) & ~np.isnan(y) & ~np.isnan(weights)
    x_val = x[valid]
    y_val = y[valid]
    w_val = weights[valid]

    # Bubble scatter scaled by population
    ax.scatter(
        x_val,
        y_val,
        s=np.clip(w_val / 80.0, 10, 150),
        color="#2b83ba",
        alpha=0.5,
        edgecolors="none",
        label="Census Tracts (size ~ population)",
    )

    # Fit associational line
    m, b = np.polyfit(x_val, y_val, 1)
    x_grid = np.linspace(np.min(x_val), np.max(x_val), 100)
    ax.plot(x_grid, m * x_grid + b, color="#d7191c", linewidth=2.0, label=f"OLS Trend (slope = {m:.2f})")

    # Annotation box with statistical parameters
    stat_text = (
        f"Spearman $\\rho = {rho:.3f}$\n"
        f"95% CI: [{ci[0]:.3f}, {ci[1]:.3f}]\n"
        f"p-value: {p_val:.4e}\n"
        f"Sample n = {len(x_val)}"
    )
    ax.text(
        0.05,
        0.95,
        stat_text,
        transform=ax.transAxes,
        verticalalignment="top",
        bbox={"boxstyle": "round,pad=0.5", "facecolor": "white", "alpha": 0.9, "edgecolor": "#cccccc"},
        fontsize=9,
    )

    ax.set_title(title, pad=10, fontweight="bold")
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(True, linestyle="--", alpha=0.5)
    ax.legend(loc="upper right", framealpha=0.9)
    fig.text(0.5, 0.01, ATTRIBUTION_TEXT, ha="center", fontsize=8, color="#555555")

    dest = Path(output_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(dest)
    plt.close(fig)
    logger.info(f"Saved scatterplot to {dest}")


def plot_quintile_contrast(
    disparity_dict: dict[str, float],
    output_path: Path | str,
    metric_label: str = "Access Score A_i",
):
    """Plot high vs low poverty quintile contrast with population weighting."""
    setup_matplotlib_style()
    fig, ax = plt.subplots(figsize=(6, 5))

    groups = ["Lowest Poverty\n(Quintile 1)", "Highest Poverty\n(Quintile 5)"]
    means = [disparity_dict["mean_low_poverty_q1"], disparity_dict["mean_high_poverty_q5"]]
    colors = ["#2b83ba", "#d7191c"]

    bars = ax.bar(groups, means, color=colors, width=0.5, edgecolor="#333333", linewidth=1)

    for bar, mean_val in zip(bars, means):
        ax.text(
            bar.get_x() + bar.get_width() / 2,
            mean_val + 0.02 * max(means),
            f"{mean_val:.3f}",
            ha="center",
            va="bottom",
            fontweight="bold",
            fontsize=10,
        )

    delta = disparity_dict["disparity_delta"]
    ax.set_ylabel(f"Pop-Weighted Mean {metric_label}")
    ax.set_title(f"Socioeconomic Disparity Contrast\n$\\Delta_A = {delta:.3f}$", pad=12, fontweight="bold")
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.set_ylim(0, max(means) * 1.25)
    fig.text(0.5, 0.01, ATTRIBUTION_TEXT, ha="center", fontsize=8, color="#555555")

    dest = Path(output_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(dest)
    plt.close(fig)
    logger.info(f"Saved quintile contrast plot to {dest}")


def plot_lorenz_curve(
    values: np.ndarray,
    weights: np.ndarray,
    gini: float,
    output_path: Path | str,
):
    """Plot population-weighted Lorenz curve for accessibility distribution."""
    setup_matplotlib_style()
    f_pop, l_acc = compute_lorenz_curve(values, weights)

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.plot(f_pop, l_acc, color="#2b83ba", linewidth=2.5, label=f"Accessibility Lorenz Curve ($G_A = {gini:.3f}$)")
    ax.plot([0, 1], [0, 1], color="#999999", linestyle="--", linewidth=1.5, label="Line of Perfect Equality")
    ax.fill_between(f_pop, f_pop, l_acc, color="#2b83ba", alpha=0.15, label="Distributional Disparity Area")

    ax.set_xlim(0, 1)
    ax.set_ylim(0, 1)
    ax.set_xlabel("Cumulative Share of Chicago Population")
    ax.set_ylabel("Cumulative Share of Modeled Amenity Access")
    ax.set_title("Population-Weighted Lorenz Curve: Library Accessibility", pad=12, fontweight="bold")
    ax.legend(loc="upper left", framealpha=0.9)
    ax.grid(True, linestyle="--", alpha=0.5)
    fig.text(0.5, 0.01, ATTRIBUTION_TEXT, ha="center", fontsize=8, color="#555555")

    dest = Path(output_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(dest)
    plt.close(fig)
    logger.info(f"Saved Lorenz curve to {dest}")


def build_interactive_folium_map(
    tracts_gdf: gpd.GeoDataFrame,
    libraries_gdf: gpd.GeoDataFrame,
    output_html_path: Path | str,
):
    """Build an interactive geographic Leaflet/Folium map with tooltips and branch markers."""
    dest = Path(output_html_path)
    dest.parent.mkdir(parents=True, exist_ok=True)

    # Drop auxiliary non-active geometry columns to ensure valid GeoJSON serialization
    extra_geom_cols = [c for c in ["representative_point", "centroid", "origin_point"] if c in tracts_gdf.columns]
    tracts_clean = tracts_gdf.drop(columns=extra_geom_cols, errors="ignore")

    # Convert to WGS84 for web mapping
    t_wgs = tracts_clean.to_crs("EPSG:4326").copy()
    lib_wgs = libraries_gdf.to_crs("EPSG:4326").copy()

    # Center map on Chicago
    center_lat = 41.85
    center_lon = -87.68
    m = folium.Map(location=[center_lat, center_lon], zoom_start=11, tiles="OpenStreetMap")

    # Choropleth layer: Poverty Rate
    folium.Choropleth(
        geo_data=t_wgs.to_json(),
        name="Tract Poverty Rate (q_i)",
        data=t_wgs,
        columns=["GEOID", "poverty_rate"],
        key_on="feature.properties.GEOID",
        fill_color="YlOrRd",
        fill_opacity=0.6,
        line_opacity=0.2,
        legend_name="Tract Poverty Rate (q_i)",
    ).add_to(m)

    # Library branch markers
    marker_cluster = MarkerCluster(name="Chicago Public Library Branches").add_to(m)
    for _, row in lib_wgs.iterrows():
        branch = row.get("branch_name", "Library Branch")
        addr = row.get("address", "")
        popup_html = f"<b>{branch}</b><br>{addr}"
        folium.Marker(
            location=[row.geometry.y, row.geometry.x],
            popup=popup_html,
            tooltip=branch,
            icon=folium.Icon(color="red", icon="book", prefix="fa"),
        ).add_to(marker_cluster)

    folium.LayerControl().add_to(m)
    m.save(str(dest))
    logger.info(f"Saved interactive web map to {dest}")


def plot_facility_simulation_scenario(
    gdf: gpd.GeoDataFrame,
    existing_facilities: gpd.GeoDataFrame,
    new_facility_coord: tuple[float, float],
    access_gain: np.ndarray,
    output_path: Path | str,
    boundary_gdf: gpd.GeoDataFrame | None = None,
):
    """Plot illustrative facility allocation planning scenario."""
    setup_matplotlib_style()
    fig, ax = plt.subplots(figsize=(8, 10))

    if boundary_gdf is not None:
        boundary_gdf.plot(ax=ax, color="none", edgecolor="black", linewidth=1.2, zorder=3)

    gdf_temp = gdf.copy()
    gdf_temp["access_gain"] = access_gain

    gdf_temp.plot(
        column="access_gain",
        ax=ax,
        cmap="Blues",
        legend=True,
        legend_kwds={
            "label": "Modeled Access Gain $\\Delta A_i$",
            "orientation": "horizontal",
            "shrink": 0.7,
            "pad": 0.05,
        },
        edgecolor="#444444",
        linewidth=0.2,
        zorder=2,
    )

    # Existing facilities
    existing_facilities.plot(
        ax=ax,
        color="#555555",
        markersize=20,
        alpha=0.6,
        zorder=4,
        label="Existing Libraries (n=82)",
    )

    # Simulated candidate
    ax.scatter(
        [new_facility_coord[0]],
        [new_facility_coord[1]],
        color="#d7191c",
        s=120,
        edgecolor="black",
        linewidth=1.5,
        marker="*",
        zorder=5,
        label="Simulated Optimal Site (+1)",
    )

    ax.set_title(
        "Illustrative Planning Scenario: Optimal Single Library Allocation\nEquity-Weighted Objective: $\\max_{c} \\sum_i P_i (1 + w_e q_i) [A_i^{(+c)} - A_i]$",
        pad=12,
        fontweight="bold",
    )
    ax.axis("off")
    ax.legend(loc="lower left", framealpha=0.9)
    fig.text(0.5, 0.02, ATTRIBUTION_TEXT, ha="center", fontsize=8, color="#555555")

    dest = Path(output_path)
    dest.parent.mkdir(parents=True, exist_ok=True)
    plt.savefig(dest)
    plt.close(fig)
    logger.info(f"Saved facility simulation map to {dest}")


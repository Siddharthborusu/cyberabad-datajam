"""Load GTFS/OSM sources and build GeoJSON payloads for the atlas."""

from __future__ import annotations

import json
from typing import Any

import geopandas as gpd
import numpy as np
import osmnx as ox
import pandas as pd

from .config import (
    HMRL_DIR,
    HUB_PATH,
    MAP_CENTER,
    METRO_COLORS,
    METRO_INTEL_PATH,
    METRO_LINE_NAMES,
    MMTS_DIR,
    OSM_PATH,
    TGSRTC_DIR,
)


def haversine(lat1: float, lon1: float, lat2: np.ndarray, lon2: np.ndarray) -> np.ndarray:
    """Great-circle distance in metres between one point and arrays of points."""
    radius = 6_371_000
    lat1_r, lon1_r = np.radians(lat1), np.radians(lon1)
    lat2_r, lon2_r = np.radians(lat2), np.radians(lon2)

    dlat = lat2_r - lat1_r
    dlon = lon2_r - lon1_r

    a = (
        np.sin(dlat / 2) ** 2
        + np.cos(lat1_r) * np.cos(lat2_r) * np.sin(dlon / 2) ** 2
    )
    return 2 * radius * np.arcsin(np.sqrt(a))


def _clean(value: Any, fallback: str = "") -> str:
    if value is None or (isinstance(value, float) and np.isnan(value)):
        return fallback
    if pd.isna(value):
        return fallback
    return str(value)


def _num(value: Any) -> float | None:
    if value is None or pd.isna(value):
        return None
    return float(value)


def _int(value: Any) -> int | None:
    if value is None or pd.isna(value):
        return None
    return int(round(float(value)))


def _geojson_from_gdf(gdf: gpd.GeoDataFrame) -> dict:
    return json.loads(gdf.to_json())


def _point_feature(
    lon: float,
    lat: float,
    properties: dict[str, Any],
) -> dict:
    clean_props = {}
    for key, value in properties.items():
        if isinstance(value, (list, dict, tuple)):
            clean_props[key] = value
        elif isinstance(value, np.generic):
            clean_props[key] = value.item()
        elif isinstance(value, float) and np.isnan(value):
            clean_props[key] = None
        elif value is None or (not isinstance(value, float) and pd.isna(value)):
            clean_props[key] = None
        else:
            clean_props[key] = value

    return {
        "type": "Feature",
        "geometry": {
            "type": "Point",
            "coordinates": [float(lon), float(lat),],
        },
        "properties": clean_props,
    }


def _line_feature(coords: list[list[float]], properties: dict[str, Any]) -> dict:
    return {
        "type": "Feature",
        "geometry": {"type": "LineString", "coordinates": coords},
        "properties": properties,
    }


def _feature_collection(features: list[dict]) -> dict:
    return {"type": "FeatureCollection", "features": features}


def load_roads() -> dict:
    print("Loading OSM road network...")
    graph = ox.load_graphml(OSM_PATH)
    _, edges = ox.graph_to_gdfs(graph)

    major = edges[
        edges["highway"]
        .astype(str)
        .str.contains(
            "motorway|trunk|primary|secondary|tertiary",
            case=False,
            na=False,
        )
    ].copy()

    major = major.to_crs(4326)
    major["road_class"] = major["highway"].astype(str)
    major["name"] = major["name"].fillna("").astype(str)

    return _geojson_from_gdf(major[["road_class", "name", "geometry"]])


def _route_color_lookup(routes: pd.DataFrame) -> dict[str, str]:
    lookup: dict[str, str] = {}
    for _, row in routes.iterrows():
        route_id = str(row["route_id"])
        raw = _clean(row.get("route_color"), "")
        if raw:
            lookup[route_id] = f"#{raw.lstrip('#')}"
        else:
            lookup[route_id] = METRO_COLORS.get(route_id, "#667085")
    return lookup


def _child_to_parent(stops: pd.DataFrame) -> dict[str, str]:
    mapping: dict[str, str] = {}
    for _, row in stops.iterrows():
        stop_id = str(row["stop_id"])
        if row.get("location_type") == 1:
            mapping[stop_id] = stop_id
        elif pd.notna(row.get("parent_station")) and row["parent_station"]:
            mapping[stop_id] = str(row["parent_station"])
        else:
            mapping[stop_id] = stop_id
    return mapping


def _station_route_map(
    stops: pd.DataFrame,
    stop_times: pd.DataFrame,
    trips: pd.DataFrame,
) -> dict[str, list[str]]:
    child_map = _child_to_parent(stops)
    linked = stop_times.merge(
        trips[["trip_id", "route_id"]],
        on="trip_id",
        how="left",
    )
    linked["parent"] = linked["stop_id"].astype(str).map(child_map)
    linked["parent"] = linked["parent"].fillna(linked["stop_id"].astype(str))

    station_routes: dict[str, list[str]] = {}
    for parent_id, group in linked.groupby("parent"):
        station_routes[str(parent_id)] = sorted(group["route_id"].astype(str).unique())
    return station_routes


def load_metro_lines() -> dict:
    print("Loading HMRL route geometry...")
    routes = pd.read_csv(HMRL_DIR / "routes.txt")
    shapes = pd.read_csv(HMRL_DIR / "shapes.txt")
    trips = pd.read_csv(HMRL_DIR / "trips.txt")

    color_lookup = _route_color_lookup(routes)
    shape_to_route = (
        trips[["shape_id", "route_id"]]
        .drop_duplicates()
        .set_index("shape_id")["route_id"]
        .astype(str)
        .to_dict()
    )

    features: list[dict] = []
    for shape_id, group in shapes.groupby("shape_id"):
        group = group.sort_values("shape_pt_sequence")
        coords = [
            [float(row["shape_pt_lon"]), float(row["shape_pt_lat"])]
            for _, row in group.iterrows()
        ]
        route_id = shape_to_route.get(str(shape_id), "")
        features.append(
            _line_feature(
                coords,
                {
                    "shape_id": str(shape_id),
                    "route_id": route_id,
                    "line": METRO_LINE_NAMES.get(route_id, route_id or "Metro"),
                    "color": color_lookup.get(route_id, "#667085"),
                },
            )
        )

    return _feature_collection(features)


def load_metro_stations(intel: pd.DataFrame) -> dict:
    print("Loading HMRL stations...")
    stops = pd.read_csv(HMRL_DIR / "stops.txt")
    stop_times = pd.read_csv(HMRL_DIR / "stop_times.txt")
    trips = pd.read_csv(HMRL_DIR / "trips.txt")
    routes = pd.read_csv(HMRL_DIR / "routes.txt")

    color_lookup = _route_color_lookup(routes)
    station_routes = _station_route_map(stops, stop_times, trips)

    metro = stops[stops["location_type"] == 1][
        ["stop_id", "stop_name", "stop_lat", "stop_lon"]
    ].copy()
    metro = metro.rename(
        columns={
            "stop_id": "metro_id",
            "stop_name": "name",
            "stop_lat": "lat",
            "stop_lon": "lon",
        }
    )

    metro = metro.merge(
        intel.drop(columns=["metro_id", "lat", "lon"], errors="ignore"),
        left_on="name",
        right_on="metro_name",
        how="left",
    )

    features: list[dict] = []
    for _, row in metro.iterrows():
        route_ids = station_routes.get(str(row["metro_id"]), [])
        line_names = [METRO_LINE_NAMES.get(rid, rid) for rid in route_ids]
        colors = [color_lookup.get(rid, "#667085") for rid in route_ids]
        primary_color = colors[0] if len(colors) == 1 else "#FFFFFF"
        interchange = len(route_ids) > 1

        features.append(
            _point_feature(
                row["lon"],
                row["lat"],
                {
                    "kind": "metro",
                    "metro_id": row["metro_id"],
                    "name": row["name"],
                    "route_ids": route_ids,
                    "lines": line_names,
                    "line": ", ".join(line_names) if line_names else "Metro",
                    "color": primary_color,
                    "colors": colors,
                    "interchange": interchange,
                    "bus_stops": _int(row.get("bus_stops")),
                    "bus_routes": _int(row.get("bus_routes")),
                    "catchment_scheduled_trips": _int(
                        row.get("catchment_scheduled_trips")
                    ),
                    "nearest_bus_m": _num(row.get("nearest_bus_distance_m")),
                },
            )
        )

    return _feature_collection(features)


def load_bus_stops() -> dict:
    print("Loading TGSRTC...")
    bus = pd.read_csv(TGSRTC_DIR / "stops.txt")[
        ["stop_id", "stop_name", "stop_lat", "stop_lon"]
    ].copy()
    bus = bus.rename(
        columns={
            "stop_id": "id",
            "stop_name": "name",
            "stop_lat": "lat",
            "stop_lon": "lon",
        }
    )
    bus["name"] = bus["name"].fillna("Unnamed bus stop").astype(str)

    bus_trips = pd.read_csv(TGSRTC_DIR / "trips.txt")
    bus_stop_times = pd.read_csv(TGSRTC_DIR / "stop_times.txt")

    service = (
        bus_stop_times[["trip_id", "stop_id"]]
        .merge(bus_trips[["trip_id", "route_id"]], on="trip_id", how="left")
        .groupby("stop_id")
        .agg(
            routes=("route_id", "nunique"),
            scheduled_trips=("trip_id", "nunique"),
        )
        .reset_index()
    )

    bus = bus.merge(service, left_on="id", right_on="stop_id", how="left")
    bus["routes"] = bus["routes"].fillna(0).astype(int)
    bus["scheduled_trips"] = bus["scheduled_trips"].fillna(0).astype(int)

    features = [
        _point_feature(
            row["lon"],
            row["lat"],
            {
                "kind": "bus",
                "id": row["id"],
                "name": row["name"],
                "routes": int(row["routes"]),
                "scheduled_trips": int(row["scheduled_trips"]),
            },
        )
        for _, row in bus.iterrows()
    ]
    return _feature_collection(features)


def load_mmts_stations() -> pd.DataFrame:
    mmts = pd.read_csv(MMTS_DIR / "stops.txt")[
        ["stop_id", "stop_name", "stop_lat", "stop_lon"]
    ].copy()
    mmts = mmts.rename(
        columns={
            "stop_id": "id",
            "stop_name": "name",
            "stop_lat": "lat",
            "stop_lon": "lon",
        }
    )
    mmts["name"] = mmts["name"].fillna("Unnamed MMTS station").astype(str)
    return mmts


def load_mmts_lines(mmts: pd.DataFrame) -> dict:
    print("Loading MMTS...")
    stop_times = pd.read_csv(MMTS_DIR / "stop_times.txt")
    lookup = mmts.set_index("id")

    canonical: dict[tuple[tuple[float, float], ...], list[list[float]]] = {}

    for _, group in stop_times.groupby("trip_id"):
        group = group.sort_values("stop_sequence")
        coords: list[list[float]] = []
        for stop_id in group["stop_id"]:
            if stop_id not in lookup.index:
                continue
            stop = lookup.loc[stop_id]
            coords.append([float(stop["lon"]), float(stop["lat"])])

        if len(coords) < 2:
            continue

        rounded = tuple(
            (round(c[1], 4), round(c[0], 4)) for c in coords
        )
        key = min(rounded, tuple(reversed(rounded)))
        canonical[key] = coords

    features = [
        _line_feature(
            coords,
            {"kind": "mmts_line"},
        )
        for coords in canonical.values()
    ]
    return _feature_collection(features)


def load_mmts_points(mmts: pd.DataFrame) -> dict:
    features = [
        _point_feature(
            row["lon"],
            row["lat"],
            {
                "kind": "mmts",
                "id": row["id"],
                "name": row["name"],
            },
        )
        for _, row in mmts.iterrows()
    ]
    return _feature_collection(features)


def load_hubs() -> dict:
    print("Loading processed mobility intelligence...")
    hubs = pd.read_csv(HUB_PATH)

    features = [
        _point_feature(
            row["metro_lon"],
            row["metro_lat"],
            {
                "kind": "hub",
                "metro_station": row["metro_station"],
                "mmts_station": row["mmts_station"],
                "mmts_distance_m": _num(row["mmts_distance_m"]),
                "bus_stops_500m": _int(row["bus_stops_500m"]),
                "bus_routes_500m": _int(row["bus_routes_500m"]),
                "bus_trips_500m": _int(row["bus_trips_500m"]),
            },
        )
        for _, row in hubs.iterrows()
    ]
    return _feature_collection(features)


def load_intel() -> pd.DataFrame:
    return pd.read_csv(METRO_INTEL_PATH)


def build_connections(
    metro: dict,
    bus: dict,
    mmts: pd.DataFrame,
) -> tuple[dict, dict, dict]:
    print("Calculating spatial connections...")

    bus_df = pd.DataFrame(
        [
            {
                "name": f["properties"]["name"],
                "lat": f["geometry"]["coordinates"][1],
                "lon": f["geometry"]["coordinates"][0],
                "routes": f["properties"]["routes"],
                "scheduled_trips": f["properties"]["scheduled_trips"],
            }
            for f in bus["features"]
        ]
    )

    bus_features: list[dict] = []
    mmts_features: list[dict] = []

    for feature in metro["features"]:
        props = feature["properties"]
        lon, lat = feature["geometry"]["coordinates"]
        name = props["name"]

        bus_dist = haversine(
            lat,
            lon,
            bus_df["lat"].to_numpy(),
            bus_df["lon"].to_numpy(),
        )
        bus_idx = int(np.argmin(bus_dist))
        nearest_bus = bus_df.iloc[bus_idx]
        bus_distance = float(bus_dist[bus_idx])

        bus_features.append(
            _line_feature(
                [
                    [lon, lat],
                    [float(nearest_bus["lon"]), float(nearest_bus["lat"])],
                ],
                {
                    "kind": "connection",
                    "connection_type": "bus",
                    "metro": name,
                    "target": nearest_bus["name"],
                    "distance_m": round(bus_distance),
                    "routes": int(nearest_bus["routes"]),
                    "scheduled_trips": int(nearest_bus["scheduled_trips"]),
                },
            )
        )

        mmts_dist = haversine(
            lat,
            lon,
            mmts["lat"].to_numpy(),
            mmts["lon"].to_numpy(),
        )
        mmts_idx = int(np.argmin(mmts_dist))
        nearest_mmts = mmts.iloc[mmts_idx]
        mmts_distance = float(mmts_dist[mmts_idx])

        props["nearest_mmts_m"] = _num(mmts_distance)
        props["nearest_mmts_name"] = nearest_mmts["name"]

        mmts_features.append(
            _line_feature(
                [
                    [lon, lat],
                    [float(nearest_mmts["lon"]), float(nearest_mmts["lat"])],
                ],
                {
                    "kind": "connection",
                    "connection_type": "mmts",
                    "metro": name,
                    "target": nearest_mmts["name"],
                    "distance_m": round(mmts_distance),
                },
            )
        )

    return (
        _feature_collection(bus_features),
        _feature_collection(mmts_features),
        metro,
    )


def build_payload() -> dict[str, Any]:
    intel = load_intel()
    mmts = load_mmts_stations()

    roads = load_roads()
    metro_lines = load_metro_lines()
    metro = load_metro_stations(intel)
    bus = load_bus_stops()
    mmts_lines = load_mmts_lines(mmts)
    mmts_points = load_mmts_points(mmts)
    hubs = load_hubs()

    bus_connections, mmts_connections, metro = build_connections(
        metro,
        bus,
        mmts,
    )

    return {
        "meta": {
            "center": list(MAP_CENTER),
            "zoom": 11,
            "counts": {
                "roads": len(roads["features"]),
                "metro_stations": len(metro["features"]),
                "metro_lines": len(metro_lines["features"]),
                "mmts_stations": len(mmts_points["features"]),
                "mmts_lines": len(mmts_lines["features"]),
                "bus_stops": len(bus["features"]),
                "hubs": len(hubs["features"]),
            },
        },
        "roads": roads,
        "metro_lines": metro_lines,
        "metro": metro,
        "bus": bus,
        "mmts_lines": mmts_lines,
        "mmts": mmts_points,
        "hubs": hubs,
        "bus_connections": bus_connections,
        "mmts_connections": mmts_connections,
    }


def summarize(payload: dict[str, Any]) -> None:
    counts = payload["meta"]["counts"]
    print()
    print("==========================================")
    print("HYDERABAD MOBILITY ATLAS")
    print("==========================================")
    print(f"Road segments:   {counts['roads']:,}")
    print(f"Metro stations:  {counts['metro_stations']:,}")
    print(f"Metro lines:     {counts['metro_lines']:,}")
    print(f"MMTS stations:   {counts['mmts_stations']:,}")
    print(f"MMTS segments:   {counts['mmts_lines']:,}")
    print(f"Bus stops:       {counts['bus_stops']:,}")
    print(f"Multimodal hubs: {counts['hubs']:,}")
    print("==========================================")

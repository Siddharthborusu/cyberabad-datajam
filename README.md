# Cyberabad Mobility Data Jam

> Mobility intelligence for Hyderabad / Cyberabad

## Live Dashboard

**[→ Open Interactive Mobility Dashboard](https://siddharthborusu.github.io/cyberabad-datajam/)**

## Objective

Explore Hyderabad/Cyberabad mobility problems using public and event-provided data.

The project focuses on:

**Evidence → Diagnosis → Intervention → Measurement**

## Current Data

- Hyderabad Metro Rail GTFS — September 2026
- TGSRTC GTFS — June 2026

## Current Analysis

- Metro–bus connectivity
- Bus service intensity
- Metro station accessibility
- Nearest bus-stop distance
- 500m bus catchments
- Scheduled service distribution
- Route concentration
- Morning vs evening service

## Status

Pre-event exploration — problem statement pending.

# Cyberabad Mobility Data Jam 2026

## Hyderabad Mobility Intelligence

An evidence-driven mobility analysis of Hyderabad, built for the **Cyberabad Mobility Data Jam 2026**.

The project combines public transport schedules, road-network data, urban geography, and population structure to understand how Hyderabad's mobility system is structured — and to create a reusable analytical foundation for investigating specific mobility problems once the event's private operational dataset becomes available.

> **Observe → Diagnose → Decide → Act → Measure → Learn**

---

## The Idea

Most mobility tools answer:

> **"How do I get from A to B?"**

This project asks a different set of questions:

- Where is mobility failing?
- When is it failing?
- Who is affected?
- What infrastructure and network conditions surround the problem?
- What evidence supports the diagnosis?
- What intervention could address it?
- How would we measure whether it worked?

The goal is not to build another navigation application or generic congestion dashboard.

The goal is to build an **evidence layer for mobility decision-making**.

---

## Current Data Foundation

### Public Transport

#### TGSRTC

Source: Telangana Open Data / TGSRTC GTFS

- **4,709** bus stops
- **1,501** routes
- **31,765** trips
- 809,218 stop-time records

The GTFS data represents **scheduled public transport supply and network structure**, not real-time vehicle positions or actual service reliability.

#### Hyderabad Metro Rail

Source: Telangana Open Data / HMRL GTFS

- **57** parent metro stations
- **3** metro lines
- **2,895** scheduled trips
- 705 total stop records
- 62,759 stop-time records

Metro lines:

- Red Line
- Green Line
- Blue Line

#### MMTS

Source: Telangana Open Data / Hyderabad MMTS

- **54** stations
- **142** route/trip records
- 2,354 stop-time records

The MMTS dataset currently available to the project does not contain a `shapes.txt` file, so spatial route geometry may be derived from ordered stops if required.

---

## Road Network

### OpenStreetMap

The Hyderabad road network has been downloaded and converted into a directed NetworkX graph using OSMnx.

Current network:

- **138,456 nodes**
- **359,549 directed edges**

The road network provides structural information such as:

- road connectivity
- intersections
- road hierarchy
- one-way restrictions
- network topology
- route structure
- network centrality

OSM is treated as **road-network structure**, not live traffic data.

---

## Population Structure

### GHMC Wards + Census 2011

The project uses:

- GHMC 2022 ward polygons
- Hyderabad Census 2011 population data

The ward geography contains:

- **150 unique numbered wards**
- 155 total polygon features, including additional non-numbered geographic features

The Census dataset contains population information for **99 GHMC wards**, all of which successfully match the corresponding ward geometries.

Current population layer:

- **99 wards**
- **3,718,651** people represented
- **299.80 km²** of corresponding ward area
- Median density: **20,566 people/km²**
- Mean density: **22,200 people/km²**
- Maximum observed density: **71,320 people/km²**

Population density is calculated from:

> Census 2011 population ÷ 2022 ward polygon area

### Important limitation

This is a **spatial baseline**, not a 2026 population estimate.

The population data is from the 2011 Census while the ward boundaries are from 2022. Areas with substantial development since 2011 should therefore not be interpreted as having their current population represented by this layer.

---

## Multimodal Connectivity

The project currently identifies potential locations where Metro and MMTS infrastructure are geographically close, while also measuring bus connectivity around Metro stations.

Using a **500 m bus catchment** around each Metro station:

- nearby bus stops are identified
- distinct bus routes are counted
- scheduled bus trips are counted

A separate Metro–MMTS proximity analysis identifies:

- **8** Metro stations within 500 m of an MMTS station
- **17** within 1 km

These are currently treated as **potential multimodal hubs**, not as proof of good interchange quality.

Straight-line distance is used for the initial analysis; it does not represent actual pedestrian travel distance or interchange quality.

---

# Mobility Atlas

The project is building an interactive spatial atlas combining:

- GHMC ward boundaries
- population density
- TGSRTC bus stops
- Hyderabad Metro stations
- MMTS stations
- multimodal proximity hubs
- OpenStreetMap road network

The objective is to make the city's mobility structure explorable at a glance while allowing individual infrastructure elements to be inspected in detail.

### Planned layers

| Layer | Purpose |
|---|---|
| Population density | Where people are concentrated |
| Bus network | Public transport supply |
| Metro | High-capacity transit structure |
| MMTS | Suburban rail structure |
| Road network | Physical mobility structure |
| Ward boundaries | Spatial aggregation |
| Multimodal hubs | Potential interchange locations |

---

# Analytical Framework

The project follows an evidence hierarchy:

### 1. Observe

Identify measurable patterns in the city's mobility system.

### 2. Localize

Determine exactly where the pattern occurs.

### 3. Diagnose

Combine multiple datasets to investigate possible explanations.

### 4. Decide

Identify plausible interventions and the authority or system component capable of acting.

### 5. Measure

Define an observable metric that can determine whether the intervention changed the problem.

### 6. Learn

Use the result to improve subsequent mobility decisions.

---

# Evidence Principles

The project distinguishes between:

### Observation

A directly measured property of the dataset.

Example:

> A Metro station has 8 bus stops within 500 m.

### Derived metric

A quantity calculated from available data.

Example:

> Population density = population / ward area.

### Hypothesis

An explanation that requires further evidence.

Example:

> A location with high demand but low scheduled transit supply may indicate a potential service gap.

### Recommendation

A proposed intervention based on the evidence.

Recommendations should only be made after the relevant problem has been established.

---

# Current Analytical Questions

The current data foundation allows us to investigate questions such as:

### Public Transport

- Where is scheduled bus supply concentrated?
- Which Metro stations have strong or weak bus connectivity?
- How does bus service vary around Metro stations?
- Where are Metro and MMTS geographically close?
- Where might multimodal integration warrant further investigation?

### Urban Structure

- Where are population concentrations located?
- How do population concentrations relate to transit infrastructure?
- Which dense areas have access to high-capacity public transport?
- Where do dense population areas intersect with major road infrastructure?

### Road Network

- Where are important network junctions?
- Which roads and intersections occupy structurally important positions?
- How does the road network interact with public transport infrastructure?

### Safety

Crash and road-safety datasets will be incorporated if they become relevant to the final problem investigation.

---

# Event Strategy

The final problem statement will **not be predetermined**.

The Cyberabad Mobility Data Jam provides a private dataset during the event. That dataset may provide operational evidence that changes which mobility problem can be investigated most rigorously.

Therefore:

> **Build the analytical infrastructure first. Let the data determine the final investigation.**

The final prototype will focus on a single, evidence-backed vertical slice rather than attempting to solve every mobility problem in Hyderabad.

---

# Planned Final Output

The project aims to produce three complementary artifacts:

```text
outputs/
├── mobility_atlas.html
├── mobility_evidence.html
└── mobility_intelligence.md
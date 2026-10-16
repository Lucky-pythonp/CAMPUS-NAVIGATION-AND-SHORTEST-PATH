import heapq
import math

import plotly.graph_objects as go
import streamlit as st

st.set_page_config(page_title="GEU Campus Navigator", page_icon="🧭", layout="wide")

# =====================================================================
# 1. CAMPUS DATA  -> yahan apna data edit kar sakta hai
# =====================================================================
PLACES = {
    "Main Gate":              dict(lat=30.268697, lon=77.994826, cat="Gate",     icon="🚪"),
    "GEU Parking":            dict(lat=30.268896, lon=77.994744, cat="Parking",  icon="🅿️"),
    "CS-IT Block":            dict(lat=30.268755, lon=77.993321, cat="Academic", icon="💻"),
    "Paramedical Block":      dict(lat=30.269449, lon=77.992849, cat="Academic", icon="🏥"),
    "Civil Block":            dict(lat=30.266867, lon=77.995624, cat="Academic", icon="🏗️"),
    "Electronics Dept":       dict(lat=30.267374, lon=77.995242, cat="Academic", icon="📡"),
    "Santosh Anand Library":  dict(lat=30.267410, lon=77.995739, cat="Library",  icon="📚"),
    "Canteen":                dict(lat=30.267162, lon=77.994635, cat="Food",     icon="🍔"),
    "Main Ground":            dict(lat=30.268008, lon=77.994436, cat="Sports",   icon="🏟️"),
    "Badminton Court":        dict(lat=30.266894, lon=77.995022, cat="Sports",   icon="🏸"),
    "Atlantis Boys Hostel":   dict(lat=30.270514, lon=77.997671, cat="Hostel",   icon="🏠"),
}

# Raste (undirected). NOTE: ye connections andaze se bane hain,
# campus me ek baar check karke edit kar lena.
EDGES = [
    ("Main Gate", "GEU Parking"),
    ("Main Gate", "CS-IT Block"),
    ("Main Gate", "Main Ground"),
    ("Main Gate", "Atlantis Boys Hostel"),
    ("GEU Parking", "CS-IT Block"),
    ("CS-IT Block", "Paramedical Block"),
    ("CS-IT Block", "Main Ground"),
    ("Main Ground", "Canteen"),
    ("Main Ground", "Santosh Anand Library"),
    ("Main Ground", "Electronics Dept"),
    ("Canteen", "Electronics Dept"),
    ("Canteen", "Badminton Court"),
    ("Electronics Dept", "Badminton Court"),
    ("Electronics Dept", "Santosh Anand Library"),
    ("Electronics Dept", "Civil Block"),
    ("Badminton Court", "Civil Block"),
    ("Santosh Anand Library", "Civil Block"),
    ("Santosh Anand Library", "Atlantis Boys Hostel"),
]

CAT_COLORS = {
    "Gate": "#10B981", "Parking": "#6B7280", "Academic": "#3B82F6",
    "Library": "#8B5CF6", "Food": "#F59E0B", "Sports": "#EF4444", "Hostel": "#EC4899",
}

for _a, _b in EDGES:
    assert _a in PLACES and _b in PLACES, f"Edge me galat naam: {_a}, {_b}"


# =====================================================================
# 2. GEO HELPERS + GRAPH + ALGORITHMS
# =====================================================================
def haversine(a, b):
    """Do places ke beech real distance (meters)."""
    p1, p2 = PLACES[a], PLACES[b]
    r = 6371000
    f1, f2 = math.radians(p1["lat"]), math.radians(p2["lat"])
    df = f2 - f1
    dl = math.radians(p2["lon"] - p1["lon"])
    h = math.sin(df / 2) ** 2 + math.cos(f1) * math.cos(f2) * math.sin(dl / 2) ** 2
    return 2 * r * math.asin(math.sqrt(h))


def bearing_name(a, b):
    p1, p2 = PLACES[a], PLACES[b]
    f1, f2 = math.radians(p1["lat"]), math.radians(p2["lat"])
    dl = math.radians(p2["lon"] - p1["lon"])
    x = math.sin(dl) * math.cos(f2)
    y = math.cos(f1) * math.sin(f2) - math.sin(f1) * math.cos(f2) * math.cos(dl)
    deg = (math.degrees(math.atan2(x, y)) + 360) % 360
    names = ["north", "north-east", "east", "south-east",
             "south", "south-west", "west", "north-west"]
    return names[round(deg / 45) % 8]


@st.cache_data
def build_graph():
    graph = {n: [] for n in PLACES}
    for a, b in EDGES:
        w = haversine(a, b)
        graph[a].append((b, w))
        graph[b].append((a, w))
    return graph


def shortest_path(graph, src, dst, use_astar=False):
    """Dijkstra (h=0) ya A* (h=straight-line distance)."""
    h = (lambda n: haversine(n, dst)) if use_astar else (lambda n: 0)
    pq = [(h(src), 0, src)]
    best, prev, visited = {src: 0}, {}, set()

    while pq:
        _, g, u = heapq.heappop(pq)
        if u in visited:
            continue
        visited.add(u)
        if u == dst:
            break
        for v, w in graph[u]:
            ng = g + w
            if ng < best.get(v, math.inf):
                best[v] = ng
                prev[v] = u
                heapq.heappush(pq, (ng + h(v), ng, v))

    if dst not in best:
        return None, math.inf, len(visited)

    path = [dst]
    while path[-1] != src:
        path.append(prev[path[-1]])
    return path[::-1], best[dst], len(visited)


# =====================================================================
# 3. MAP (OpenStreetMap tiles)
# =====================================================================
MapTrace = getattr(go, "Scattermap", None) or go.Scattermapbox
MAP_KEY = "map" if hasattr(go, "Scattermap") else "mapbox"


def build_map(path=None, show_labels=True, categories=None, height=560):
    fig = go.Figure()
    names = [n for n, p in PLACES.items() if not categories or p["cat"] in categories]

    # saare raste ek trace me
    lats, lons = [], []
    for a, b in EDGES:
        if a in names and b in names:
            lats += [PLACES[a]["lat"], PLACES[b]["lat"], None]
            lons += [PLACES[a]["lon"], PLACES[b]["lon"], None]
    fig.add_trace(MapTrace(lat=lats, lon=lons, mode="lines",
                           line=dict(width=3, color="#94A3B8"),
                           hoverinfo="skip", name="Roads"))

    # shortest path highlight
    if path:
        fig.add_trace(MapTrace(
            lat=[PLACES[n]["lat"] for n in path],
            lon=[PLACES[n]["lon"] for n in path],
            mode="lines", line=dict(width=7, color="#EF4444"),
            hoverinfo="skip", name="Shortest path"))

    # places
    colors, sizes = [], []
    for n in names:
        if path and n == path[0]:
            colors.append("#16A34A"); sizes.append(22)
        elif path and n == path[-1]:
            colors.append("#DC2626"); sizes.append(22)
        elif path and n in path:
            colors.append("#F59E0B"); sizes.append(16)
        else:
            colors.append(CAT_COLORS[PLACES[n]["cat"]]); sizes.append(14)

    fig.add_trace(MapTrace(
        lat=[PLACES[n]["lat"] for n in names],
        lon=[PLACES[n]["lon"] for n in names],
        mode="markers+text" if show_labels else "markers",
        text=[f"{PLACES[n]['icon']} {n}" for n in names],
        textposition="top center",
        textfont=dict(size=12, color="#111827"),
        marker=dict(size=sizes, color=colors),
        hovertemplate="%{text}<extra></extra>", name="Places"))

    clat = sum(p["lat"] for p in PLACES.values()) / len(PLACES)
    clon = sum(p["lon"] for p in PLACES.values()) / len(PLACES)
    fig.update_layout(
        **{MAP_KEY: dict(style="open-street-map",
                         center=dict(lat=clat, lon=clon), zoom=16.2)},
        height=height, margin=dict(l=0, r=0, t=0, b=0),
        showlegend=False, paper_bgcolor="rgba(0,0,0,0)")
    return fig


# =====================================================================
# 4. STYLE
# =====================================================================
st.markdown(
    """
    <style>
    .block-container {padding-top: 1.5rem;}
    .hero {padding: 1.4rem 1.6rem; border-radius: 18px; margin-bottom: 1.2rem;
           background: linear-gradient(135deg, #1D4ED8 0%, #7C3AED 55%, #DB2777 100%);
           box-shadow: 0 10px 30px rgba(79,70,229,.30);}
    .hero h1 {margin: 0; font-size: 2rem; color: #fff !important;}
    .hero p {margin: .35rem 0 0; color: rgba(255,255,255,.9); font-size: 1rem;}
    .card {padding: 1rem 1.1rem; border-radius: 14px; text-align: center;
           background: rgba(99,102,241,.10); border: 1px solid rgba(99,102,241,.25);}
    .card .v {font-size: 1.7rem; font-weight: 700; line-height: 1.2;}
    .card .l {font-size: .8rem; opacity: .75; text-transform: uppercase; letter-spacing: .05em;}
    .step {display: flex; gap: .8rem; align-items: flex-start; padding: .7rem .9rem;
           margin-bottom: .5rem; border-radius: 12px;
           background: rgba(99,102,241,.08); border-left: 4px solid #6366F1;}
    .step .n {min-width: 1.7rem; height: 1.7rem; border-radius: 50%; background: #6366F1;
              color: #fff; display: flex; align-items: center; justify-content: center;
              font-weight: 700; font-size: .85rem;}
    .step small {opacity: .7;}
    .chip {display:inline-block; padding:.15rem .6rem; border-radius:999px; color:#fff;
           font-size:.75rem; margin-right:.3rem;}
    [data-testid="stSidebar"] {border-right: 1px solid rgba(128,128,128,.2);}
    </style>
    """,
    unsafe_allow_html=True,
)


def hero(title, subtitle):
    st.markdown(f"<div class='hero'><h1>{title}</h1><p>{subtitle}</p></div>",
                unsafe_allow_html=True)


def card(col, value, label):
    col.markdown(f"<div class='card'><div class='v'>{value}</div>"
                 f"<div class='l'>{label}</div></div>", unsafe_allow_html=True)


# =====================================================================
# 5. SIDEBAR MENU
# =====================================================================
with st.sidebar:
    st.markdown("## 🧭 GEU Navigator")
    st.caption("Graphic Era Deemed to be University, Dehradun")
    page = st.radio(
        "Menu",
        ["🧭 Navigate", "🗺️ Campus Map", "📍 All Locations", "ℹ️ About Project"],
        label_visibility="collapsed",
    )
    st.divider()
    st.markdown("**⚙️ Settings**")
    algo = st.radio("Algorithm", ["Dijkstra", "A* (faster)"], horizontal=True)
    speed = st.slider("Walking speed (km/h)", 3.0, 7.0, 5.0, 0.5)

graph = build_graph()
places = list(PLACES.keys())

# =====================================================================
# 6. PAGES
# =====================================================================
if page == "🧭 Navigate":
    hero("🧭 Campus Navigator", "Find the shortest walking route between any two spots on campus.")

    st.session_state.setdefault("src", "Main Gate")
    st.session_state.setdefault("dst", "Atlantis Boys Hostel")

    def swap():
        st.session_state.src, st.session_state.dst = st.session_state.dst, st.session_state.src

    c1, c2, c3 = st.columns([5, 1, 5])
    c1.selectbox("📍 From", places, key="src", format_func=lambda n: f"{PLACES[n]['icon']} {n}")
    c2.markdown("<div style='height:1.9rem'></div>", unsafe_allow_html=True)
    c2.button("⇅", on_click=swap, help="Swap From / To", use_container_width=True)
    c3.selectbox("🏁 To", places, key="dst", format_func=lambda n: f"{PLACES[n]['icon']} {n}")

    src, dst = st.session_state.src, st.session_state.dst
    if src == dst:
        st.warning("Source aur destination alag select karo.")
        st.stop()

    path, cost, explored = shortest_path(graph, src, dst, algo.startswith("A*"))
    if path is None:
        st.error("In dono jagahon ke beech koi route nahi mila.")
        st.stop()

    minutes = cost / (speed * 1000 / 60)
    m1, m2, m3, m4 = st.columns(4)
    card(m1, f"{cost:.0f} m", "Distance")
    card(m2, f"{max(minutes, 0.1):.1f} min", "Walking time")
    card(m3, len(path) - 1, "Segments")
    card(m4, explored, "Nodes explored")
    st.write("")

    left, right = st.columns([3, 2])
    with left:
        st.plotly_chart(build_map(path, height=540), use_container_width=True)

    with right:
        st.markdown("#### 🚶 Directions")
        for i in range(len(path) - 1):
            a, b = path[i], path[i + 1]
            d = haversine(a, b)
            st.markdown(
                f"<div class='step'><div class='n'>{i + 1}</div><div>"
                f"Head <b>{bearing_name(a, b)}</b> to <b>{PLACES[b]['icon']} {b}</b><br>"
                f"<small>from {a} · {d:.0f} m</small></div></div>",
                unsafe_allow_html=True)
        st.success(f"You've arrived at {dst} 🎉")

        s, e = PLACES[src], PLACES[dst]
        url = (f"https://www.google.com/maps/dir/?api=1&origin={s['lat']},{s['lon']}"
               f"&destination={e['lat']},{e['lon']}&travelmode=walking")
        st.link_button("📱 Open in Google Maps", url, use_container_width=True)

    with st.expander("📊 Dijkstra vs A* comparison"):
        _, c_d, e_d = shortest_path(graph, src, dst, False)
        _, c_a, e_a = shortest_path(graph, src, dst, True)
        st.table({
            "Algorithm": ["Dijkstra", "A*"],
            "Distance (m)": [round(c_d), round(c_a)],
            "Nodes explored": [e_d, e_a],
        })
        st.caption("Dono same shortest path dete hain, A* aam taur par kam nodes explore karta hai.")

elif page == "🗺️ Campus Map":
    hero("🗺️ Campus Map", "All buildings and walking paths on a live map.")
    cats = st.multiselect("Filter by category", list(CAT_COLORS.keys()),
                          default=list(CAT_COLORS.keys()))
    labels = st.toggle("Show labels", value=True)
    st.plotly_chart(build_map(None, labels, cats, height=620), use_container_width=True)
    st.markdown(
        " ".join(f"<span class='chip' style='background:{c}'>{k}</span>"
                 for k, c in CAT_COLORS.items()),
        unsafe_allow_html=True)

elif page == "📍 All Locations":
    hero("📍 All Locations", "Every place in the navigation graph, with coordinates.")
    q = st.text_input("🔎 Search", placeholder="e.g. library, hostel...")
    rows = [
        {"Place": f"{p['icon']} {n}", "Category": p["cat"],
         "Latitude": p["lat"], "Longitude": p["lon"],
         "Connected to": len(graph[n])}
        for n, p in PLACES.items() if q.lower() in n.lower() or q.lower() in p["cat"].lower()
    ]
    st.dataframe(rows, use_container_width=True, hide_index=True)

else:
    hero("ℹ️ About Project", "Campus Navigation and Shortest Path Finder")
    st.markdown(
        """
**Problem:** New students and visitors often struggle to find the quickest way between campus buildings.

**Approach**
- Campus is modelled as a **weighted graph**: buildings are nodes, walking paths are edges.
- Edge weight = real distance in meters using the **Haversine formula** on GPS coordinates.
- **Dijkstra's algorithm** finds the guaranteed shortest path.
- **A\\*** uses straight-line distance as a heuristic to explore fewer nodes.

**Tech stack:** Python, Streamlit, Plotly, OpenStreetMap tiles.

**Complexity:** Dijkstra with a min-heap runs in O((V + E) log V).

**Future scope:** live GPS location, indoor navigation, event-based crowd avoidance, voice directions.
        """
    )

import heapq
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

st.set_page_config(
    page_title="Campus Navigator | Shortest Path Finder",
    page_icon="🧭",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------- Styling ----------
st.markdown("""
<style>
    .stApp { background: #f5f7fb; }
    [data-testid="stHeader"] { background: rgba(245,247,251,0.85); }
    .block-container { padding-top: 1.6rem; padding-bottom: 2.5rem; max-width: 1400px; }
    .hero {
        padding: 1.7rem 1.8rem; border-radius: 22px; color: white;
        background: linear-gradient(120deg, #102a43 0%, #155e75 55%, #0f766e 100%);
        margin-bottom: 1.2rem;
    }
    .hero h1 { color: white; font-size: 2.25rem; margin: 0; }
    .hero p { color: #d9f3f0; font-size: 1rem; margin: .5rem 0 0 0; }
    .metric-card {
        background: white; border: 1px solid #e5eaf2; border-radius: 16px;
        padding: 1rem 1.1rem; min-height: 112px;
    }
    .metric-label { color: #64748b; font-size: .88rem; }
    .metric-value { color: #102a43; font-size: 1.7rem; font-weight: 750; margin-top: .25rem; }
    .route-step {
        background: white; border: 1px solid #e5eaf2; border-radius: 12px;
        padding: .8rem 1rem; margin: .35rem 0;
    }
    .small-note { color: #64748b; font-size: .86rem; }
    div[data-testid="stSidebar"] { background: #edf3f8; }
    .stButton > button[kind="primary"] {
        border-radius: 10px; min-height: 3rem; font-weight: 650;
    }
</style>
""", unsafe_allow_html=True)

# ---------- Demo campus data ----------
DEFAULT_ROUTES = [
    ("Main Gate", "Reception", 100),
    ("Main Gate", "Parking", 150),
    ("Reception", "Library", 120),
    ("Reception", "Canteen", 180),
    ("Parking", "Canteen", 200),
    ("Library", "Academic Block", 100),
    ("Canteen", "Academic Block", 130),
    ("Academic Block", "Computer Lab", 80),
    ("Library", "Auditorium", 160),
    ("Auditorium", "Computer Lab", 140),
    ("Canteen", "Hostel", 250),
    ("Hostel", "Sports Ground", 180),
    ("Computer Lab", "Sports Ground", 300),
]

def make_default_df():
    return pd.DataFrame(
        DEFAULT_ROUTES,
        columns=["Start", "End", "Distance (meters)"]
    )

def build_graph(route_df):
    """Build an undirected weighted graph using only Python dictionaries."""
    graph = {}
    for _, row in route_df.iterrows():
        start = str(row["Start"]).strip()
        end = str(row["End"]).strip()
        distance = float(row["Distance (meters)"])
        if not start or not end or start == end or distance <= 0:
            continue
        graph.setdefault(start, {})
        graph.setdefault(end, {})
        # Keep the shorter distance if a connection was entered more than once.
        if end not in graph[start] or distance < graph[start][end]:
            graph[start][end] = distance
            graph[end][start] = distance
    return graph

def dijkstra(graph, source, destination):
    """Return (path, distance) using Dijkstra's algorithm and heapq."""
    distances = {node: float("inf") for node in graph}
    previous = {}
    distances[source] = 0
    priority_queue = [(0, source)]
    visited = set()

    while priority_queue:
        current_distance, current_node = heapq.heappop(priority_queue)
        if current_node in visited:
            continue
        visited.add(current_node)

        if current_node == destination:
            break

        for neighbour, weight in graph[current_node].items():
            new_distance = current_distance + weight
            if new_distance < distances[neighbour]:
                distances[neighbour] = new_distance
                previous[neighbour] = current_node
                heapq.heappush(priority_queue, (new_distance, neighbour))

    if distances[destination] == float("inf"):
        return None, None

    path = []
    node = destination
    while node != source:
        path.append(node)
        node = previous[node]
    path.append(source)
    path.reverse()
    return path, distances[destination]

def path_segments(graph, path):
    return [
        (path[i], path[i + 1], graph[path[i]][path[i + 1]])
        for i in range(len(path) - 1)
    ]

# ---------- Header ----------
st.markdown("""
<div class="hero">
    <h1>🧭 Campus Navigator</h1>
    <p>Find the shortest route across campus with Dijkstra's Algorithm.</p>
</div>
""", unsafe_allow_html=True)

if "routes_df" not in st.session_state:
    st.session_state.routes_df = make_default_df()

# ---------- Sidebar ----------
with st.sidebar:
    st.markdown("## Route planner")
    st.caption("Choose your start and destination.")
    if st.button("↺ Reset sample campus data", use_container_width=True):
        st.session_state.routes_df = make_default_df()
        st.rerun()

    st.markdown("---")
    st.markdown("### About this project")
    st.write("**Algorithm:** Dijkstra's shortest path")
    st.write("**Graph:** Python dictionary + priority queue")
    st.write("**Libraries:** Streamlit, Pandas, Matplotlib")
    st.markdown("---")
    st.caption("The included campus locations and distances are demonstration data.")

# ---------- Data editor ----------
st.markdown("### Plan your journey")
st.write("Pick two locations below. You can also edit the campus connections in the data section.")

route_df = st.session_state.routes_df.copy()
# Clean and validate editable table.
route_df["Start"] = route_df["Start"].fillna("").astype(str).str.strip()
route_df["End"] = route_df["End"].fillna("").astype(str).str.strip()
route_df["Distance (meters)"] = pd.to_numeric(
    route_df["Distance (meters)"], errors="coerce"
)
route_df = route_df[
    (route_df["Start"] != "")
    & (route_df["End"] != "")
    & (route_df["Start"] != route_df["End"])
    & route_df["Distance (meters)"].notna()
    & (route_df["Distance (meters)"] > 0)
].copy()

graph = build_graph(route_df)
locations = sorted(graph.keys())

if not locations:
    st.warning("No valid campus routes found. Add at least one connection below.")
    st.stop()

left, right = st.columns([1, 1], gap="large")
with left:
    source = st.selectbox("📍 Starting location", locations, index=0)
with right:
    destination = st.selectbox(
        "🏁 Destination",
        locations,
        index=(len(locations) - 1 if len(locations) > 1 else 0)
    )

search = st.button("Find my shortest route  →", type="primary", use_container_width=True)

if search:
    if source == destination:
        st.info("You're already at your destination. Total distance: 0 meters.")
    else:
        path, total_distance = dijkstra(graph, source, destination)
        if path is None:
            st.error(
                f"No connected route exists between **{source}** and **{destination}**. "
                "Add connecting paths in the campus route table."
            )
        else:
            segments = path_segments(graph, path)
            st.markdown("### Your route")
            m1, m2, m3 = st.columns(3)
            with m1:
                st.markdown(
                    f'<div class="metric-card"><div class="metric-label">Total walking distance</div>'
                    f'<div class="metric-value">{total_distance:,.0f} m</div></div>',
                    unsafe_allow_html=True
                )
            with m2:
                st.markdown(
                    f'<div class="metric-card"><div class="metric-label">Route segments</div>'
                    f'<div class="metric-value">{len(segments)}</div></div>',
                    unsafe_allow_html=True
                )
            with m3:
                st.markdown(
                    f'<div class="metric-card"><div class="metric-label">Locations on route</div>'
                    f'<div class="metric-value">{len(path)}</div></div>',
                    unsafe_allow_html=True
                )

            st.markdown("#### Step-by-step directions")
            for i, (start, end, distance) in enumerate(segments, start=1):
                st.markdown(
                    f'<div class="route-step"> <b>{i}. {start} → {end}</b>'
                    f'<span style="float:right;color:#0f766e;font-weight:700;">{distance:,.0f} m</span></div>',
                    unsafe_allow_html=True
                )
            st.markdown(
                f'<p class="small-note">Start: <b>{source}</b> &nbsp; • &nbsp; '
                f'Finish: <b>{destination}</b></p>',
                unsafe_allow_html=True
            )

            st.markdown("#### Campus route map")
            fig, ax = plt.subplots(figsize=(12, 6.5))
            # A deterministic layout makes the demo map stable between reruns.
            import random
            rng = random.Random(42)
            positions = {}
            nodes = list(graph.keys())
            for index, node in enumerate(nodes):
                positions[node] = (
                    rng.uniform(0.05, 0.95),
                    rng.uniform(0.08, 0.92)
                )

            # Draw all edges first.
            for node, neighbours in graph.items():
                for neighbour, weight in neighbours.items():
                    if node < neighbour:
                        x1, y1 = positions[node]
                        x2, y2 = positions[neighbour]
                        ax.plot([x1, x2], [y1, y2], linewidth=1.5, color="#cbd5e1", zorder=1)
                        ax.text((x1+x2)/2, (y1+y2)/2, f"{weight:g} m",
                                fontsize=7, color="#475569",
                                bbox=dict(facecolor="white", edgecolor="none", alpha=0.75, pad=1),
                                zorder=2)

            # Highlight shortest path.
            for start, end, weight in segments:
                x1, y1 = positions[start]
                x2, y2 = positions[end]
                ax.plot([x1, x2], [y1, y2], linewidth=4, color="#0f9d76", zorder=3)

            for node, (x, y) in positions.items():
                if node == source:
                    color = "#16a34a"
                elif node == destination:
                    color = "#ef4444"
                elif node in path:
                    color = "#0f9d76"
                else:
                    color = "#dbeafe"
                ax.scatter(x, y, s=1250, color=color, edgecolors="white", linewidths=2, zorder=4)
                ax.text(x, y, node, ha="center", va="center", fontsize=8,
                        color=("white" if node in path else "#102a43"),
                        fontweight="bold", wrap=True, zorder=5)

            ax.set_xlim(-0.04, 1.04)
            ax.set_ylim(-0.04, 1.04)
            ax.axis("off")
            fig.tight_layout()
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)
            st.caption(
                "Green lines show the shortest route. This is a schematic network diagram, "
                "not a geographically accurate campus map."
            )

st.markdown("---")
with st.expander("🛠️ Edit campus locations and distances", expanded=False):
    st.write(
        "Add one row for each walkway between two locations. The connection is treated as two-way. "
        "Use positive distances in meters."
    )
    edited_df = st.data_editor(
        st.session_state.routes_df,
        num_rows="dynamic",
        use_container_width=True,
        key="campus_route_editor",
        column_config={
            "Start": st.column_config.TextColumn("Start location", required=True),
            "End": st.column_config.TextColumn("End location", required=True),
            "Distance (meters)": st.column_config.NumberColumn(
                "Distance (meters)", min_value=1, step=10, required=True
            ),
        },
    )
    if st.button("Save route table", type="primary"):
        st.session_state.routes_df = edited_df
        st.success("Route table saved for this running session.")
        st.rerun()

st.markdown("### Campus connections")
st.dataframe(route_df, use_container_width=True, hide_index=True)
csv = route_df.to_csv(index=False).encode("utf-8")
st.download_button(
    "⬇️ Download route data (CSV)",
    data=csv,
    file_name="campus_routes.csv",
    mime="text/csv",
)

st.info(
    "Demo notice: locations and distances are examples. Replace them with verified "
    "Graphic Era campus buildings, walking paths, and measured distances before real use."
)

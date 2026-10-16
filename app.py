import streamlit as st
import pandas as pd
import numpy as np
import networkx as nx
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="Campus Navigation",
    page_icon="🗺️",
    layout="wide"
)

st.title("Campus Navigation and Shortest Path Finder")
st.write(
    "Select a starting point and destination to find the shortest "
    "campus route using Dijkstra's Algorithm."
)

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

@st.cache_data
def default_routes_frame():
    return pd.DataFrame(
        DEFAULT_ROUTES,
        columns=["Start", "End", "Distance (meters)"]
    )

if "routes_df" not in st.session_state:
    st.session_state.routes_df = default_routes_frame()

st.sidebar.header("Navigation")
st.sidebar.caption("Demo data is provided. Replace it with verified campus paths.")

if st.sidebar.button("Reset demo routes"):
    st.session_state.routes_df = default_routes_frame()
    st.rerun()

st.subheader("1. Campus route data")
st.write("Edit the table to add, remove, or update campus connections and distances.")
edited_df = st.data_editor(
    st.session_state.routes_df,
    num_rows="dynamic",
    use_container_width=True,
    key="route_editor",
    column_config={
        "Start": st.column_config.TextColumn("Start location", required=True),
        "End": st.column_config.TextColumn("End location", required=True),
        "Distance (meters)": st.column_config.NumberColumn(
            "Distance (meters)", min_value=1, step=1, required=True
        ),
    },
)

# Validate route data before building the graph.
valid_df = edited_df.copy()
valid_df["Start"] = valid_df["Start"].fillna("").astype(str).str.strip()
valid_df["End"] = valid_df["End"].fillna("").astype(str).str.strip()
valid_df["Distance (meters)"] = pd.to_numeric(
    valid_df["Distance (meters)"], errors="coerce"
)
valid_df = valid_df[
    (valid_df["Start"] != "")
    & (valid_df["End"] != "")
    & (valid_df["Start"] != valid_df["End"])
    & valid_df["Distance (meters)"].notna()
    & (valid_df["Distance (meters)"] > 0)
].copy()

if valid_df.empty:
    st.warning("Add at least one valid route with a positive distance.")
    st.stop()

valid_df["Distance (meters)"] = valid_df["Distance (meters)"].astype(float)
G = nx.Graph()

for _, row in valid_df.iterrows():
    start = row["Start"]
    end = row["End"]
    distance = float(row["Distance (meters)"])
    # If the same connection is entered more than once, keep the shorter one.
    if G.has_edge(start, end):
        if distance < G[start][end]["weight"]:
            G[start][end]["weight"] = distance
    else:
        G.add_edge(start, end, weight=distance)

locations = sorted(G.nodes())

st.subheader("2. Find the shortest route")
col1, col2 = st.columns(2)
with col1:
    source = st.selectbox("Starting location", locations, index=0)
with col2:
    destination = st.selectbox(
        "Destination",
        locations,
        index=(len(locations) - 1 if len(locations) > 1 else 0)
    )

find_route = st.button("Find Shortest Route", type="primary", use_container_width=True)

if find_route:
    if source == destination:
        st.info("Starting location and destination are the same. Total distance is 0 meters.")
    else:
        try:
            path = nx.dijkstra_path(G, source, destination, weight="weight")
            segment_distances = [
                float(G[path[i]][path[i + 1]]["weight"])
                for i in range(len(path) - 1)
            ]
            total_distance = float(np.sum(segment_distances))

            st.success("Shortest route found.")
            metric1, metric2, metric3 = st.columns(3)
            metric1.metric("Total distance", f"{total_distance:,.0f} m")
            metric2.metric("Route segments", str(len(path) - 1))
            metric3.metric("Locations visited", str(len(path)))

            st.markdown("#### Turn-by-turn route")
            for i, place in enumerate(path):
                if i < len(path) - 1:
                    st.write(
                        f"{i + 1}. **{place}** → **{path[i + 1]}** "
                        f"({segment_distances[i]:,.0f} m)"
                    )
                else:
                    st.write(f"{i + 1}. **Arrive at {place}**")

            st.markdown("#### Campus route graph")
            positions = nx.spring_layout(G, seed=42, weight="weight")
            fig, ax = plt.subplots(figsize=(12, 7))

            nx.draw_networkx_edges(
                G, positions, ax=ax, edge_color="#b8c0cc", width=1.5
            )
            path_edges = list(zip(path[:-1], path[1:]))
            nx.draw_networkx_edges(
                G, positions, ax=ax, edgelist=path_edges,
                edge_color="green", width=4
            )
            nx.draw_networkx_nodes(
                G, positions, ax=ax, node_color="#9ecae1", node_size=1500
            )
            nx.draw_networkx_nodes(
                G, positions, ax=ax, nodelist=[source],
                node_color="limegreen", node_size=1900
            )
            nx.draw_networkx_nodes(
                G, positions, ax=ax, nodelist=[destination],
                node_color="tomato", node_size=1900
            )
            nx.draw_networkx_labels(
                G, positions, ax=ax, font_size=8, font_weight="bold"
            )
            edge_labels = {
                (u, v): f"{data['weight']:g} m"
                for u, v, data in G.edges(data=True)
            }
            nx.draw_networkx_edge_labels(
                G, positions, edge_labels=edge_labels, font_size=7, ax=ax
            )
            ax.set_title("Green edges show the shortest route")
            ax.axis("off")
            st.pyplot(fig, use_container_width=True)
            plt.close(fig)

            st.caption(
                "The graph is a network diagram, not a geographically accurate map. "
                "Distances and locations are sample data."
            )

        except nx.NetworkXNoPath:
            st.error(
                f"No route connects {source} to {destination}. "
                "Add connecting paths in the route data table."
            )

st.divider()
st.subheader("3. Campus route database")
st.dataframe(valid_df, use_container_width=True, hide_index=True)

csv_data = valid_df.to_csv(index=False).encode("utf-8")
st.download_button(
    "Download route data as CSV",
    data=csv_data,
    file_name="campus_routes.csv",
    mime="text/csv"
)

st.info(
    "For real navigation, replace the example locations and distances with "
    "verified campus buildings, walkways, and measured distances."
)

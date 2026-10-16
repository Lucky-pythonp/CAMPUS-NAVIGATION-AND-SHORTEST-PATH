
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(
    page_title="Campus Navigation System",
    page_icon="🗺️",
    layout="wide"
)

st.title("Campus Navigation and Shortest Path Finder")
st.write(
    "Find the shortest route between two campus locations "
    "using Dijkstra's Algorithm."
)

# Sample campus locations and connections.
# Replace these example distances with actual campus measurements.
routes = [
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
    ("Computer Lab", "Sports Ground", 300)
]

df = pd.DataFrame(
    routes,
    columns=["Start", "End", "Distance (meters)"]
)

# Create campus graph
G = nx.Graph()

for _, row in df.iterrows():
    G.add_edge(
        row["Start"],
        row["End"],
        weight=int(row["Distance (meters)"])
    )

locations = sorted(G.nodes())

st.sidebar.header("Choose Your Route")

source = st.sidebar.selectbox(
    "Starting Location",
    locations,
    index=locations.index("Main Gate")
)

destination = st.sidebar.selectbox(
    "Destination",
    locations,
    index=locations.index("Computer Lab")
)

if st.sidebar.button("Find Shortest Route", type="primary"):

    if source == destination:
        st.info("Starting location and destination are the same.")

    else:
        try:
            path = nx.dijkstra_path(
                G, source, destination, weight="weight"
            )

            distances = [
                G[path[i]][path[i + 1]]["weight"]
                for i in range(len(path) - 1)
            ]

            total_distance = int(np.sum(distances))

            st.subheader("Your Navigation Result")

            col1, col2 = st.columns(2)

            col1.metric("Total Distance", f"{total_distance} meters")
            col2.metric("Locations on Route", len(path))

            st.success("Shortest route found successfully!")

            st.markdown("### Route Directions")

            for i, location in enumerate(path):
                if i < len(path) - 1:
                    st.write(
                        f"{i + 1}. {location} → {path[i + 1]} "
                        f"({distances[i]} meters)"
                    )
                else:
                    st.write(f"{i + 1}. Arrive at **{location}**")

            # Draw the campus network
            st.markdown("### Campus Route Map")

            pos = nx.spring_layout(G, seed=42, weight="weight")

            fig, ax = plt.subplots(figsize=(12, 7))

            nx.draw_networkx_edges(
                G, pos, ax=ax,
                edge_color="lightgray",
                width=1.5
            )

            nx.draw_networkx_edges(
                G, pos, ax=ax,
                edgelist=list(zip(path[:-1], path[1:])),
                edge_color="green",
                width=3
            )

            nx.draw_networkx_nodes(
                G, pos, ax=ax,
                node_color="skyblue",
                node_size=1800
            )

            nx.draw_networkx_nodes(
                G, pos, ax=ax,
                nodelist=[source],
                node_color="limegreen",
                node_size=2000
            )

            nx.draw_networkx_nodes(
                G, pos, ax=ax,
                nodelist=[destination],
                node_color="tomato",
                node_size=2000
            )

            nx.draw_networkx_labels(
                G, pos, ax=ax,
                font_size=8,
                font_weight="bold"
            )

            edge_labels = nx.get_edge_attributes(G, "weight")

            nx.draw_networkx_edge_labels(
                G, pos, edge_labels=edge_labels,
                font_size=8, ax=ax
            )

            ax.set_title("Green Line = Shortest Route")
            ax.axis("off")

            st.pyplot(fig)
            plt.close(fig)

        except nx.NetworkXNoPath:
            st.error("No route exists between these locations.")

st.divider()

st.subheader("Campus Route Database")
st.dataframe(df, use_container_width=True)

st.caption(
    "Note: Locations, connections and distances in this demo "
    "are sample data, not verified campus measurements."
)


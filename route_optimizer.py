import streamlit as st
import googlemaps
from ortools.constraint_solver import pywrapcp, routing_enums_pb2
import urllib.parse

# === SETUP GOOGLE API ===
API_KEY = "AIzaSyCw-nm6UTlOtlrrq-aQWUmNB52bRlMKogo"  # Replace this
gmaps = googlemaps.Client(key=API_KEY)

st.title("🗺️ Singapore Route Optimizer")
st.markdown("Enter multiple addresses and get the most efficient driving route.")

# === USER INPUT ===
addresses_input = st.text_area("Enter addresses (one per line):")
optimize = st.button("Optimize Route")

if optimize and addresses_input.strip():
    addresses = [a.strip() for a in addresses_input.strip().split('\n') if a.strip()]
    if len(addresses) < 2:
        st.error("Enter at least two addresses.")
    else:
        st.info("Getting distances from Google Maps...")
        
        # === CREATE DISTANCE MATRIX ===
        def create_distance_matrix(addresses):
            matrix = []
            for origin in addresses:
                result = gmaps.distance_matrix(origins=[origin], destinations=addresses, mode="driving")
                row = [el["duration"]["value"] for el in result["rows"][0]["elements"]]
                matrix.append(row)
            return matrix

        distance_matrix = create_distance_matrix(addresses)

        # === OPTIMIZE ROUTE ===
        def optimize_route(distance_matrix):
            manager = pywrapcp.RoutingIndexManager(len(distance_matrix), 1, 0)
            routing = pywrapcp.RoutingModel(manager)

            def callback(from_idx, to_idx):
                return distance_matrix[manager.IndexToNode(from_idx)][manager.IndexToNode(to_idx)]

            transit_index = routing.RegisterTransitCallback(callback)
            routing.SetArcCostEvaluatorOfAllVehicles(transit_index)

            search_params = pywrapcp.DefaultRoutingSearchParameters()
            search_params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC

            solution = routing.SolveWithParameters(search_params)

            if not solution:
                return None, None

            index = routing.Start(0)
            route = []
            total_time = 0
            while not routing.IsEnd(index):
                node = manager.IndexToNode(index)
                route.append(node)
                next_index = solution.Value(routing.NextVar(index))
                total_time += routing.GetArcCostForVehicle(index, next_index, 0)
                index = next_index
            route.append(manager.IndexToNode(index))  # Return to start
            return route, total_time

        route_idx, total_seconds = optimize_route(distance_matrix)

        if route_idx:
            st.success("Optimized Route:")
            ordered_addresses = [addresses[i] for i in route_idx]
            for i, addr in enumerate(ordered_addresses):
                st.write(f"{i+1}. {addr}")

            st.write(f"🚗 Estimated total travel time: **{total_seconds // 60} minutes**")

            # === GOOGLE MAPS LINK ===
            st.markdown("### 📍 View Route in Google Maps")
            base = "https://www.google.com/maps/dir/"
            encoded_addresses = [urllib.parse.quote_plus(addr) for addr in ordered_addresses]
            maps_url = base + "/".join(encoded_addresses)
            st.markdown(f"[🗺️ Open Google Maps Route]({maps_url})", unsafe_allow_html=True)
        else:
            st.error("Could not find an optimized route.")

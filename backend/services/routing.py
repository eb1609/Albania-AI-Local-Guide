import requests

def get_osrm_distance_matrix(coords: list[tuple[float, float]]) -> list[list[float]]:
    coord_str = ";".join([f"{lon},{lat}" for lon, lat in coords])
    url = f"http://router.project-osrm.org/table/v1/driving/{coord_str}?annotations=duration"
    response = requests.get(url)
    return response.json()["durations"]

def solve_tsp_nearest_neighbor(matrix: list[list[float]], start_idx: int = 0) -> list[int]:
    num_nodes = len(matrix)
    unvisited = set(range(num_nodes))
    unvisited.remove(start_idx)
    
    route = [start_idx]
    current = start_idx
    
    while unvisited:
        next_node = min(unvisited, key=lambda node: matrix[current][node])
        route.append(next_node)
        unvisited.remove(next_node)
        current = next_node
        
    return route
import heapq
from collections import defaultdict
from typing import List, Dict, Optional, Any

class CampusGraph:
    def __init__(self):
        self.nodes = {
            1: {"name": "Main Gate", "x": 100, "y": 300, "type": "entrance"},
            2: {"name": "CV Raman Block", "x": 200, "y": 300, "type": "academic"},
            3: {"name": "Visvesvaraya Block", "x": 300, "y": 300, "type": "academic"},
            4: {"name": "Aeronautics Block", "x": 400, "y": 300, "type": "academic"},
            5: {"name": "Architecture Block", "x": 500, "y": 300, "type": "academic"},
            6: {"name": "Swami Vivekananda Block", "x": 300, "y": 200, "type": "academic"},
            7: {"name": "Admin Block", "x": 300, "y": 100, "type": "admin"},
            8: {"name": "Business School", "x": 200, "y": 150, "type": "academic"},
            9: {"name": "PU College", "x": 200, "y": 50, "type": "academic"},
            10: {"name": "Saugandika", "x": 400, "y": 150, "type": "hostel"},
            11: {"name": "Guest House", "x": 100, "y": 50, "type": "hostel"},
            12: {"name": "Reva Hostel", "x": 400, "y": 50, "type": "hostel"},
            13: {"name": "Reva Mess", "x": 500, "y": 50, "type": "food"},
            14: {"name": "Ground", "x": 100, "y": 400, "type": "open_space"},
            15: {"name": "Basketball Court", "x": 50, "y": 450, "type": "sports"},
            16: {"name": "Volleyball Court", "x": 150, "y": 450, "type": "sports"},
            17: {"name": "Maggipoint", "x": 100, "y": 500, "type": "food"}
        }

        self.path_styles = {
            "paved_walkway": {"color": "#4285F4", "width": 5, "dash": []},
            "open_path": {"color": "#34A853", "width": 4, "dash": []},
            "crowded_area": {"color": "#FBBC05", "width": 4, "dash": [5, 5]},
            "stairs": {"color": "#EA4335", "width": 3, "dash": [3, 3]},
            "food_court": {"color": "#673AB7", "width": 4, "dash": []}
        }

        self.path_speeds = {
            "paved_walkway": 100,
            "open_path": 80,
            "crowded_area": 50,
            "stairs": 40,
            "food_court": 60
        }

        self.edges = defaultdict(dict)
        self._initialize_edges()

    def _initialize_edges(self):
        edge_definitions = {
            1: {2: {"distance": 100, "path_type": "paved_walkway"}, 14: {"distance": 100, "path_type": "open_path"}},
            2: {1: {"distance": 100, "path_type": "paved_walkway"}, 3: {"distance": 80, "path_type": "paved_walkway"}},
            3: {2: {"distance": 80, "path_type": "paved_walkway"}, 4: {"distance": 120, "path_type": "crowded_area"},
                6: {"distance": 50, "path_type": "stairs"}},
            4: {3: {"distance": 120, "path_type": "crowded_area"}, 5: {"distance": 100, "path_type": "paved_walkway"}},
            5: {4: {"distance": 100, "path_type": "paved_walkway"}},
            6: {3: {"distance": 50, "path_type": "stairs"}, 7: {"distance": 100, "path_type": "paved_walkway"},
                8: {"distance": 50, "path_type": "crowded_area"}, 9: {"distance": 150, "path_type": "paved_walkway"},
                10: {"distance": 50, "path_type": "paved_walkway"}},
            7: {6: {"distance": 100, "path_type": "paved_walkway"}},
            8: {6: {"distance": 50, "path_type": "crowded_area"}, 9: {"distance": 100, "path_type": "paved_walkway"}},
            9: {6: {"distance": 150, "path_type": "paved_walkway"}, 8: {"distance": 100, "path_type": "paved_walkway"},
                11: {"distance": 50, "path_type": "paved_walkway"}},
            10: {6: {"distance": 50, "path_type": "paved_walkway"}, 12: {"distance": 100, "path_type": "paved_walkway"}},
            11: {9: {"distance": 50, "path_type": "paved_walkway"}, 12: {"distance": 150, "path_type": "open_path"}},
            12: {10: {"distance": 100, "path_type": "paved_walkway"}, 11: {"distance": 150, "path_type": "open_path"},
                 13: {"distance": 50, "path_type": "paved_walkway"}},
            13: {12: {"distance": 50, "path_type": "paved_walkway"}, 14: {"distance": 150, "path_type": "open_path"}},
            14: {1: {"distance": 100, "path_type": "open_path"}, 13: {"distance": 150, "path_type": "open_path"},
                 15: {"distance": 50, "path_type": "open_path"}, 16: {"distance": 50, "path_type": "open_path"},
                 17: {"distance": 100, "path_type": "food_court"}},
            15: {14: {"distance": 50, "path_type": "open_path"}},
            16: {14: {"distance": 50, "path_type": "open_path"}},
            17: {14: {"distance": 100, "path_type": "food_court"}}
        }

        for from_node, connections in edge_definitions.items():
            for to_node, attrs in connections.items():
                self.edges[from_node][to_node] = {
                    "distance": attrs["distance"],
                    "path_type": attrs["path_type"],
                    "path_points": self._generate_path_points(from_node, to_node)
                }
                if to_node not in self.edges or from_node not in self.edges[to_node]:
                    self.edges[to_node][from_node] = {
                        "distance": attrs["distance"],
                        "path_type": attrs["path_type"],
                        "path_points": self._generate_path_points(to_node, from_node)
                    }

    def _generate_path_points(self, from_node: int, to_node: int, curve_factor: float = 0.2) -> List[Dict[str, float]]:
        start = self.nodes[from_node]
        end = self.nodes[to_node]

        mid_x = (start['x'] + end['x']) / 2
        mid_y = (start['y'] + end['y']) / 2

        if abs(start['x'] - end['x']) > abs(start['y'] - end['y']):
            mid_y += curve_factor * abs(start['x'] - end['x'])
        else:
            mid_x += curve_factor * abs(start['y'] - end['y'])

        return [
            {
                'x': (1 - t) ** 2 * start['x'] + 2 * (1 - t) * t * mid_x + t ** 2 * end['x'],
                'y': (1 - t) ** 2 * start['y'] + 2 * (1 - t) * t * mid_y + t ** 2 * end['y']
            }
            for t in [i / 10 for i in range(1, 10)]
        ]

    def find_shortest_path(self, start_node: int, end_node: int) -> Optional[List[int]]:
        if start_node not in self.nodes or end_node not in self.nodes:
            return None

        heap = [(0, start_node, [])]
        visited = set()

        while heap:
            current_time, node, path = heapq.heappop(heap)

            if node in visited:
                continue

            visited.add(node)
            path = path + [node]

            if node == end_node:
                return path

            for neighbor, attrs in self.edges.get(node, {}).items():
                if neighbor not in visited:
                    speed = self.path_speeds.get(attrs["path_type"], 50)
                    edge_time = attrs["distance"] / speed
                    heapq.heappush(heap, (current_time + edge_time, neighbor, path))

        return None

    def calculate_path_time(self, path: List[int]) -> float:
        if len(path) < 2:
            return 0

        total_time = 0
        for i in range(len(path) - 1):
            from_node = path[i]
            to_node = path[i + 1]
            edge = self.edges[from_node].get(to_node)
            if not edge:
                continue
            speed = self.path_speeds.get(edge["path_type"], 50)
            total_time += edge["distance"] / speed

        return total_time

    def get_path_details(self, path: List[int]) -> List[Dict[str, Any]]:
        if len(path) < 2:
            return []

        details = []

        for i in range(len(path) - 1):
            from_node = path[i]
            to_node = path[i + 1]

            if i == 0:
                details.append({
                    'x': self.nodes[from_node]['x'],
                    'y': self.nodes[from_node]['y'],
                    'type': 'node',
                    'node_id': from_node,
                    'name': self.nodes[from_node]['name'],
                    'from_node': from_node,
                    'to_node': to_node
                })

            edge = self.edges[from_node].get(to_node, {})
            for point in edge.get('path_points', []):
                details.append({
                    'x': point['x'],
                    'y': point['y'],
                    'type': 'path',
                    'path_type': edge.get('path_type', 'paved_walkway'),
                    'from_node': from_node,
                    'to_node': to_node
                })

            details.append({
                'x': self.nodes[to_node]['x'],
                'y': self.nodes[to_node]['y'],
                'type': 'node',
                'node_id': to_node,
                'name': self.nodes[to_node]['name'],
                'from_node': from_node,
                'to_node': to_node
            })

        return details

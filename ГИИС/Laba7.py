import tkinter as tk
from tkinter import messagebox
import random
from collections import defaultdict


class GeometryApp:
    def __init__(self, master):
        self.master = master
        master.title("Визуализация триангуляции и диаграммы Вороного")

        # Настройки
        self.canvas_width = 800
        self.canvas_height = 600
        self.point_radius = 4
        self.colors = {
            'points': 'black',
            'delaunay': 'red',
            'voronoi': 'blue',
            'background': 'white'
        }

        # Состояние программы
        self.points = []
        self.triangles = []
        self.voronoi_edges = []
        self.mode = "add"

        # Создание интерфейса
        self.create_widgets()

        # Ограничивающий прямоугольник
        self.bbox = (0, 0, self.canvas_width, self.canvas_height)

    def create_widgets(self):
        # Панель инструментов
        toolbar = tk.Frame(self.master, bd=1, relief=tk.RAISED)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        # Кнопки
        modes = [
            ("Добавить точки", "add"),
            ("Триангуляция", "triangulate"),
            ("Диаграмма Вороного", "voronoi"),
            ("Очистить", "clear"),
            ("Случайные точки", "random")
        ]

        for text, command in modes:
            btn = tk.Button(toolbar, text=text,
                            command=lambda cmd=command: self.handle_command(cmd))
            btn.pack(side=tk.LEFT, padx=2, pady=2)

        # Холст
        self.canvas = tk.Canvas(self.master,
                                width=self.canvas_width,
                                height=self.canvas_height,
                                bg=self.colors['background'])
        self.canvas.pack()
        self.canvas.bind("<Button-1>", self.canvas_click)

    def handle_command(self, command):
        if command == "add":
            self.mode = "add"
        elif command == "cursor":
            self.mode = "cursor"
        elif command == "triangulate":
            self.triangulate()
        elif command == "voronoi":
            self.calculate_voronoi()
        elif command == "clear":
            self.clear_all()
        elif command == "random":
            self.generate_random_points(15)

    def canvas_click(self, event):
        if self.mode == "add":
            x, y = event.x, event.y
            self.points.append((x, y))
            self.draw_point(x, y)

    def draw_point(self, x, y):
        r = self.point_radius
        self.canvas.create_oval(x - r, y - r, x + r, y + r,
                                fill=self.colors['points'],
                                outline=self.colors['points'])

    def triangulate(self):
        if len(self.points) < 3:
            messagebox.showerror("Ошибка", "Нужно минимум 3 точки")
            return

        self.triangles = self.delaunay_triangulation(self.points)
        self.draw_triangulation()

    def delaunay_triangulation(self, points):
        # Реализация алгоритма Bowyer-Watson
        if len(points) < 3:
            return []

        # Создаем супертреугольник
        min_x = min(p[0] for p in points)
        max_x = max(p[0] for p in points)
        min_y = min(p[1] for p in points)
        max_y = max(p[1] for p in points)

        dx = max_x - min_x
        dy = max_y - min_y
        delta = max(dx, dy) * 2

        p1 = (min_x - delta, min_y - delta)
        p2 = (min_x + dx + delta, min_y - delta)
        p3 = (min_x + dx / 2, min_y + dy + delta)

        super_triangle = Triangle(p1, p2, p3)
        triangles = [super_triangle]

        # Добавляем точки по одной
        for point in points:
            bad_triangles = []

            # Находим треугольники, чьи окружности содержат точку
            for triangle in triangles:
                if triangle.circumcircle_contains(point):
                    bad_triangles.append(triangle)

            # Находим границу многоугольника
            polygon = []
            for triangle in bad_triangles:
                for edge in triangle.edges():
                    shared = False
                    for other in bad_triangles:
                        if triangle == other:
                            continue
                        if other.has_edge(edge):
                            shared = True
                            break
                    if not shared:
                        polygon.append(edge)

            # Удаляем плохие треугольники
            triangles = [t for t in triangles if t not in bad_triangles]

            # Создаем новые треугольники
            for edge in polygon:
                new_tri = Triangle(edge[0], edge[1], point)
                triangles.append(new_tri)

        # Удаляем треугольники, связанные с супертреугольником
        triangles = [t for t in triangles if not t.shares_vertex_with(super_triangle)]

        return triangles

    def draw_triangulation(self):
        self.canvas.delete("delaunay")
        for tri in self.triangles:
            p1, p2, p3 = tri.vertices
            self.canvas.create_line(p1[0], p1[1], p2[0], p2[1],
                                    fill=self.colors['delaunay'], tags="delaunay")
            self.canvas.create_line(p2[0], p2[1], p3[0], p3[1],
                                    fill=self.colors['delaunay'], tags="delaunay")
            self.canvas.create_line(p3[0], p3[1], p1[0], p1[1],
                                    fill=self.colors['delaunay'], tags="delaunay")

    def calculate_voronoi(self):
        if not self.triangles:
            messagebox.showerror("Ошибка", "Сначала выполните триангуляцию")
            return

        self.voronoi_edges = self.voronoi_diagram(self.triangles, self.bbox)
        self.draw_voronoi()

    def voronoi_diagram(self, triangles, bbox):
        # Строим диаграмму Вороного из триангуляции Делоне
        edges = []
        edge_map = defaultdict(list)

        # Собираем все ребра треугольников
        for tri in triangles:
            for edge in tri.edges():
                edge_map[tuple(sorted(edge))].append(tri)

        # Обрабатываем каждое ребро
        for edge, tris in edge_map.items():
            if len(tris) == 2:
                # Ребро между двумя треугольниками
                p1 = tris[0].circumcenter
                p2 = tris[1].circumcenter
                edges.append((p1, p2))
            elif len(tris) == 1:
                # Граничное ребро
                tri = tris[0]
                p1, p2 = edge
                third = [v for v in tri.vertices if v not in edge][0]

                # Находим направление наружу
                midpoint = ((p1[0] + p2[0]) / 2, (p1[1] + p2[1]) / 2)
                direction = (midpoint[0] - third[0], midpoint[1] - third[1])

                # Находим пересечение с границей
                far_point = self.ray_box_intersection(tri.circumcenter, direction, bbox)
                if far_point:
                    edges.append((tri.circumcenter, far_point))

        return edges

    def ray_box_intersection(self, origin, direction, bbox):
        # Находит точку пересечения луча с прямоугольником
        xmin, ymin, xmax, ymax = bbox
        dx, dy = direction

        t_values = []
        if dx != 0:
            tx1 = (xmin - origin[0]) / dx
            tx2 = (xmax - origin[0]) / dx
            t_values.extend([tx1, tx2])

        if dy != 0:
            ty1 = (ymin - origin[1]) / dy
            ty2 = (ymax - origin[1]) / dy
            t_values.extend([ty1, ty2])

        # Находим минимальное положительное t
        valid_t = [t for t in t_values if t > 0]
        if not valid_t:
            return None

        t_min = min(valid_t)
        return (origin[0] + t_min * dx, origin[1] + t_min * dy)

    def draw_voronoi(self):
        self.canvas.delete("voronoi")
        for edge in self.voronoi_edges:
            p1, p2 = edge
            self.canvas.create_line(p1[0], p1[1], p2[0], p2[1],
                                    fill=self.colors['voronoi'],
                                    dash=(4, 2), tags="voronoi")

    def generate_random_points(self, n):
        self.clear_all()
        margin = 50
        for _ in range(n):
            x = random.randint(margin, self.canvas_width - margin)
            y = random.randint(margin, self.canvas_height - margin)
            self.points.append((x, y))
            self.draw_point(x, y)

    def clear_all(self):
        self.points = []
        self.triangles = []
        self.voronoi_edges = []
        self.canvas.delete("all")


class Triangle:
    def __init__(self, p1, p2, p3):
        self.vertices = (p1, p2, p3)
        self.circumcenter, self.radius_sq = self.calculate_circumcircle()

    def edges(self):
        p1, p2, p3 = self.vertices
        return [(p1, p2), (p2, p3), (p3, p1)]

    def has_edge(self, edge):
        return edge in self.edges() or (edge[1], edge[0]) in self.edges()

    def shares_vertex_with(self, other):
        return any(v in other.vertices for v in self.vertices)

    def calculate_circumcircle(self):
        # Вычисляет описанную окружность треугольника
        p1, p2, p3 = self.vertices
        A = p2[0] - p1[0]
        B = p2[1] - p1[1]
        C = p3[0] - p1[0]
        D = p3[1] - p1[1]

        E = A * (p1[0] + p2[0]) + B * (p1[1] + p2[1])
        F = C * (p1[0] + p3[0]) + D * (p1[1] + p3[1])

        G = 2 * (A * (p3[1] - p1[1]) - B * (p3[0] - p1[0]))

        if G == 0:
            # Коллинеарные точки
            return ((0, 0), float('inf'))

        cx = (D * E - B * F) / G
        cy = (A * F - C * E) / G
        center = (cx, cy)

        radius_sq = (p1[0] - cx) ** 2 + (p1[1] - cy) ** 2

        return (center, radius_sq)

    def circumcircle_contains(self, point):
        # Проверяет, находится ли точка внутри описанной окружности
        dx = point[0] - self.circumcenter[0]
        dy = point[1] - self.circumcenter[1]
        distance_sq = dx * dx + dy * dy
        return distance_sq <= self.radius_sq


if __name__ == "__main__":
    root = tk.Tk()
    app = GeometryApp(root)
    root.mainloop()
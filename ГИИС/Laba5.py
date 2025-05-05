import tkinter as tk
from tkinter import ttk, messagebox
from math import atan2, sqrt, isclose
from enum import Enum

CELL_SIZE = 20
CANVAS_WIDTH = 800
CANVAS_HEIGHT = 600


class Algorithm(Enum):
    CDA = "cda"
    BRESENHAM = "bresenham"
    WU = "wu"


class HullMethod(Enum):
    GRAHAM = "graham"
    JARVIS = "jarvis"


def draw_grid(canvas):
    for x in range(0, CANVAS_WIDTH, CELL_SIZE):
        canvas.create_line(x, 0, x, CANVAS_HEIGHT, fill='#ddd')
    for y in range(0, CANVAS_HEIGHT, CELL_SIZE):
        canvas.create_line(0, y, CANVAS_WIDTH, y, fill='#ddd')


class PolygonEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Графический редактор полигонов")

        self.canvas = tk.Canvas(root, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg='white')
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.algorithm = tk.StringVar(value=Algorithm.CDA.value)
        self.debug_mode = tk.BooleanVar(value=False)
        self.polygons = []
        self.current_polygon = []
        self.selected_point = None
        self.hull_method = tk.StringVar(value=HullMethod.GRAHAM.value)

        self.build_ui()
        self.setup_bindings()

        draw_grid(self.canvas)

    def build_ui(self):
        # Панель инструментов
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X)

        # Алгоритмы рисования линий
        ttk.Label(toolbar, text="Алгоритм:").pack(side=tk.LEFT, padx=5)
        for algo in Algorithm:
            ttk.Radiobutton(toolbar, text=algo.name, variable=self.algorithm,
                            value=algo.value).pack(side=tk.LEFT)

        # Режимы работы
        ttk.Button(toolbar, text="Новый полигон", command=self.start_new_polygon).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Замкнуть полигон", command=self.close_polygon).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(toolbar, text="Отладка", variable=self.debug_mode).pack(side=tk.LEFT, padx=5)

        # Проверка полигона
        ttk.Button(toolbar, text="Проверить выпуклость", command=self.check_convexity).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Найти нормали", command=self.find_normals).pack(side=tk.LEFT, padx=5)

        # Выпуклые оболочки
        ttk.Label(toolbar, text="Оболочка:").pack(side=tk.LEFT, padx=5)
        for method in HullMethod:
            ttk.Radiobutton(toolbar, text=method.name, variable=self.hull_method,
                            value=method.value).pack(side=tk.LEFT)
        ttk.Button(toolbar, text="Построить оболочку", command=self.build_convex_hull).pack(side=tk.LEFT, padx=5)

        # Дополнительные функции
        ttk.Button(toolbar, text="Пересечение с отрезком", command=self.intersect_with_line).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Принадлежность точки", command=self.point_in_polygon).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Очистить", command=self.clear_canvas).pack(side=tk.LEFT, padx=5)

        # Статусная строка
        self.status = ttk.Label(self.root, text="Готов к работе", relief=tk.SUNKEN)
        self.status.pack(fill=tk.X)

    def setup_bindings(self):
        self.canvas.bind('<Button-1>', self.on_click)
        self.canvas.bind('<B1-Motion>', self.on_drag)
        self.canvas.bind('<ButtonRelease-1>', self.on_release)
        self.canvas.bind('<Motion>', self.on_motion)

    def start_new_polygon(self):
        if self.current_polygon:
            self.polygons.append(self.current_polygon.copy())
        self.current_polygon = []
        self.status.config(text="Создание нового полигона: кликните для добавления точек")

    def close_polygon(self):
        if len(self.current_polygon) >= 3:
            self.polygons.append(self.current_polygon.copy())
            self.draw_polygon(self.current_polygon)
            self.current_polygon = []
            self.status.config(text="Полигон замкнут. Готов к работе")
        else:
            messagebox.showerror("Ошибка", "Для замыкания полигона нужно минимум 3 точки")

    def on_click(self, event):
        x, y = event.x // CELL_SIZE, event.y // CELL_SIZE

        if self.edit_mode():
            self.selected_point = self.find_nearest_point(x, y)
            if self.selected_point:
                return

        self.current_polygon.append((x, y))
        self.draw_point(x, y)

        if len(self.current_polygon) > 1:
            self.draw_line(self.current_polygon[-2], self.current_polygon[-1])

        self.status.config(text=f"Добавлена точка ({x}, {y}). Всего точек: {len(self.current_polygon)}")

    def on_drag(self, event):
        if not self.edit_mode() or not self.selected_point:
            return

        x, y = event.x // CELL_SIZE, event.y // CELL_SIZE
        poly_idx, point_idx = self.selected_point

        if poly_idx == -1:  # Текущий полигон
            self.current_polygon[point_idx] = (x, y)
        else:
            self.polygons[poly_idx][point_idx] = (x, y)

        self.redraw_all()

    def on_release(self, event):
        self.selected_point = None

    def on_motion(self, event):
        pass

    def edit_mode(self):
        return False  # Можно добавить переключение режима редактирования

    def find_nearest_point(self, x, y, threshold=1):
        # Поиск в текущем полигоне
        for i, (px, py) in enumerate(self.current_polygon):
            if abs(px - x) <= threshold and abs(py - y) <= threshold:
                return (-1, i)  # -1 означает текущий полигон

        # Поиск в завершенных полигонах
        for poly_idx, polygon in enumerate(self.polygons):
            for point_idx, (px, py) in enumerate(polygon):
                if abs(px - x) <= threshold and abs(py - y) <= threshold:
                    return (poly_idx, point_idx)

        return None

    def draw_point(self, x, y, color='red', tags=None):
        size = 3
        self.canvas.create_oval(
            (x * CELL_SIZE) - size, (y * CELL_SIZE) - size,
            (x * CELL_SIZE) + size, (y * CELL_SIZE) + size,
            fill=color, outline=color, tags=tags
        )

    def draw_line(self, p1, p2, color='black', dash=None, tags=None):
        x1, y1 = p1
        x2, y2 = p2
        self.canvas.create_line(
            x1 * CELL_SIZE, y1 * CELL_SIZE,
            x2 * CELL_SIZE, y2 * CELL_SIZE,
            fill=color, dash=dash, tags=tags
        )

    def draw_polygon(self, points, color='blue', fill='', width=2):
        scaled = []
        for x, y in points:
            scaled.extend([x * CELL_SIZE, y * CELL_SIZE])

        if len(points) >= 3:
            self.canvas.create_polygon(
                *scaled, outline=color, fill=fill, width=width
            )

    def redraw_all(self):
        self.canvas.delete('all')
        draw_grid(self.canvas)

        # Рисуем завершенные полигоны
        for polygon in self.polygons:
            self.draw_polygon(polygon)
            for point in polygon:
                self.draw_point(*point)

        # Рисуем текущий полигон
        if self.current_polygon:
            for i in range(len(self.current_polygon)):
                self.draw_point(*self.current_polygon[i])
                if i > 0:
                    self.draw_line(self.current_polygon[i - 1], self.current_polygon[i])

    def check_convexity(self):
        if not self.current_polygon and not self.polygons:
            messagebox.showerror("Ошибка", "Нет полигонов для проверки")
            return

        polygons_to_check = self.polygons.copy()
        if self.current_polygon and len(self.current_polygon) >= 3:
            polygons_to_check.append(self.current_polygon)

        for i, polygon in enumerate(polygons_to_check):
            if len(polygon) < 3:
                continue

            is_convex = True
            n = len(polygon)
            prev_cross = 0

            for i in range(n):
                p0 = polygon[i]
                p1 = polygon[(i + 1) % n]
                p2 = polygon[(i + 2) % n]

                # Векторы между точками
                dx1 = p1[0] - p0[0]
                dy1 = p1[1] - p0[1]
                dx2 = p2[0] - p1[0]
                dy2 = p2[1] - p1[1]

                # Векторное произведение
                cross = dx1 * dy2 - dy1 * dx2

                if abs(cross) < 1e-10:  # Коллинеарные точки
                    continue

                if prev_cross == 0:
                    prev_cross = cross
                else:
                    if cross * prev_cross < 0:
                        is_convex = False
                        break

            if is_convex:
                messagebox.showinfo("Результат", f"Полигон {i + 1} выпуклый")
            else:
                messagebox.showinfo("Результат", f"Полигон {i + 1} невыпуклый")

    def find_normals(self):
        if not self.current_polygon and not self.polygons:
            messagebox.showerror("Ошибка", "Нет полигонов для анализа")
            return

        polygons_to_check = self.polygons.copy()
        if self.current_polygon and len(self.current_polygon) >= 3:
            polygons_to_check.append(self.current_polygon)

        self.canvas.delete('normals')

        for polygon in polygons_to_check:
            if len(polygon) < 3:
                continue

            n = len(polygon)
            for i in range(n):
                p0 = polygon[i]
                p1 = polygon[(i + 1) % n]

                # Вектор стороны
                dx = p1[0] - p0[0]
                dy = p1[1] - p0[1]

                # Нормаль (повернутый на 90 градусов вектор)
                nx = -dy
                ny = dx

                # Нормализуем вектор
                length = sqrt(nx * nx + ny * ny)
                if length > 0:
                    nx /= length
                    ny /= length

                # Центр стороны для рисования
                cx = (p0[0] + p1[0]) / 2
                cy = (p0[1] + p1[1]) / 2

                # Рисуем нормаль (уменьшенную для наглядности)
                self.canvas.create_line(
                    cx * CELL_SIZE, cy * CELL_SIZE,
                    (cx + nx * 3) * CELL_SIZE, (cy + ny * 3) * CELL_SIZE,
                    arrow=tk.LAST, fill='green', width=2, tags='normals'
                )

        self.status.config(text="Нормали показаны (зеленые стрелки)")

    def build_convex_hull(self):
        if not self.current_polygon and not self.polygons:
            messagebox.showerror("Ошибка", "Нет точек для построения оболочки")
            return

        points = []
        if self.current_polygon:
            points.extend(self.current_polygon)
        for polygon in self.polygons:
            points.extend(polygon)

        if len(points) < 3:
            messagebox.showerror("Ошибка", "Нужно минимум 3 точки для построения оболочки")
            return

        method = self.hull_method.get()
        if method == HullMethod.GRAHAM.value:
            hull = self.graham_scan(points)
        else:
            hull = self.jarvis_march(points)

        # Рисуем оболочку
        self.canvas.delete('hull')
        self.draw_polygon(hull, color='red', fill='', width=3, tags='hull')

        self.status.config(text=f"Построена выпуклая оболочка методом {method}")

    def graham_scan(self, points):
        # Находим точку с минимальной y-координатой (и минимальной x, если есть совпадения)
        pivot = min(points, key=lambda p: (p[1], p[0]))

        # Сортируем точки по полярному углу относительно pivot
        sorted_points = sorted(points, key=lambda p: (atan2(p[1] - pivot[1], p[0] - pivot[0]), p[0]))

        # Алгоритм Грэхема
        hull = []
        for p in sorted_points:
            while len(hull) >= 2 and self.cross_product(hull[-2], hull[-1], p) <= 0:
                hull.pop()
            hull.append(p)

        return hull

    def jarvis_march(self, points):
        # Находим самую левую точку
        leftmost = min(points, key=lambda p: p[0])

        hull = []
        current = leftmost

        while True:
            hull.append(current)
            next_point = points[0]

            for candidate in points[1:]:
                if next_point == current or self.cross_product(current, next_point, candidate) < 0:
                    next_point = candidate

            if next_point == leftmost:
                break

            current = next_point

        return hull

    def cross_product(self, a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

    def intersect_with_line(self):
        if not self.current_polygon and not self.polygons:
            messagebox.showerror("Ошибка", "Нет полигонов для проверки пересечения")
            return

        self.status.config(text="Кликните две точки для отрезка")
        self.canvas.bind('<Button-1>', self.line_intersection_click)

    def line_intersection_click(self, event):
        if not hasattr(self, 'line_points'):
            self.line_points = []

        x, y = event.x // CELL_SIZE, event.y // CELL_SIZE
        self.line_points.append((x, y))
        self.draw_point(x, y, color='purple', tags='intersection')

        if len(self.line_points) == 1:
            self.status.config(text="Кликните вторую точку отрезка")
        elif len(self.line_points) == 2:
            self.canvas.unbind('<Button-1>')
            self.find_intersections()

    def find_intersections(self):
        p1, p2 = self.line_points
        intersections = []

        polygons_to_check = self.polygons.copy()
        if self.current_polygon and len(self.current_polygon) >= 3:
            polygons_to_check.append(self.current_polygon)

        for polygon in polygons_to_check:
            n = len(polygon)
            for i in range(n):
                p3 = polygon[i]
                p4 = polygon[(i + 1) % n]

                # Проверяем пересечение отрезков (p1,p2) и (p3,p4)
                intersect, point = self.segment_intersection(p1, p2, p3, p4)
                if intersect:
                    intersections.append(point)
                    self.draw_point(*point, color='orange', tags='intersection')

        # Рисуем отрезок
        self.draw_line(p1, p2, color='purple', tags='intersection')

        if intersections:
            self.status.config(text=f"Найдено {len(intersections)} точек пересечения")
        else:
            self.status.config(text="Пересечений не найдено")

        del self.line_points

    def segment_intersection(self, p1, p2, p3, p4):
        x1, y1 = p1
        x2, y2 = p2
        x3, y3 = p3
        x4, y4 = p4

        denom = (y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1)

        if denom == 0:  # Параллельны или коллинеарны
            return False, None

        ua = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / denom
        ub = ((x2 - x1) * (y1 - y3) - (y2 - y1) * (x1 - x3)) / denom

        if ua >= 0 and ua <= 1 and ub >= 0 and ub <= 1:
            x = x1 + ua * (x2 - x1)
            y = y1 + ua * (y2 - y1)
            return True, (x, y)

        return False, None

    def point_in_polygon(self):
        if not self.current_polygon and not self.polygons:
            messagebox.showerror("Ошибка", "Нет полигонов для проверки")
            return

        self.status.config(text="Кликните точку для проверки принадлежности полигону")
        self.canvas.bind('<Button-1>', self.point_in_polygon_click)

    def point_in_polygon_click(self, event):
        x, y = event.x // CELL_SIZE, event.y // CELL_SIZE
        point = (x, y)

        polygons_to_check = self.polygons.copy()
        if self.current_polygon and len(self.current_polygon) >= 3:
            polygons_to_check.append(self.current_polygon)

        self.canvas.unbind('<Button-1>')
        self.draw_point(x, y, color='magenta', tags='point_check')

        inside_any = False
        for i, polygon in enumerate(polygons_to_check):
            if self.is_point_in_polygon(point, polygon):
                inside_any = True
                self.status.config(text=f"Точка ({x}, {y}) внутри полигона {i + 1}")
                break

        if not inside_any:
            self.status.config(text=f"Точка ({x}, {y}) не внутри ни одного полигона")

    def is_point_in_polygon(self, point, polygon):
        x, y = point
        n = len(polygon)
        inside = False

        for i in range(n):
            x1, y1 = polygon[i]
            x2, y2 = polygon[(i + 1) % n]

            # Проверяем, лежит ли точка на границе
            if self.point_on_segment((x, y), (x1, y1), (x2, y2)):
                return True

            # Проверяем пересечение луча
            if ((y1 > y) != (y2 > y)):
                x_intersect = (y - y1) * (x2 - x1) / (y2 - y1) + x1
                if x <= x_intersect:
                    inside = not inside

        return inside

    def point_on_segment(self, p, p1, p2):
        x, y = p
        x1, y1 = p1
        x2, y2 = p2

        # Проверяем коллинеарность
        cross = (x2 - x1) * (y - y1) - (y2 - y1) * (x - x1)
        if abs(cross) > 1e-10:
            return False

        if min(x1, x2) <= x <= max(x1, x2) and min(y1, y2) <= y <= max(y1, y2):
            return True

        return False

    def clear_canvas(self):
        self.canvas.delete('all')
        self.polygons = []
        self.current_polygon = []
        self.selected_point = None
        draw_grid(self.canvas)
        self.status.config(text="Холст очищен. Готов к работе")


if __name__ == "__main__":
    root = tk.Tk()
    app = PolygonEditor(root)
    root.mainloop()
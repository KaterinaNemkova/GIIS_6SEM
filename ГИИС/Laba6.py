import tkinter as tk
from tkinter import ttk, messagebox
from math import atan2, sqrt, isclose
from enum import Enum

CELL_SIZE = 20
CANVAS_WIDTH = 800
CANVAS_HEIGHT = 600


class Algorithm(Enum):
    CDA = "cda"


class HullMethod(Enum):
    GRAHAM = "graham"


class FillAlgorithm(Enum):
    ORDERED_EDGE_LIST = "ordered_edge_list"
    ACTIVE_EDGE_LIST = "active_edge_list"
    SIMPLE_SEED = "simple_seed"
    SCANLINE_SEED = "scanline_seed"


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
        self.fill_algorithm = tk.StringVar(value=FillAlgorithm.ORDERED_EDGE_LIST.value)
        self.polygons = []
        self.current_polygon = []
        self.selected_point = None
        self.hull_method = tk.StringVar(value=HullMethod.GRAHAM.value)
        self.fill_color = 'blue'
        self.debug_delay = 10  # Уменьшена задержка для отладки

        self.build_ui()
        self.setup_bindings()

        draw_grid(self.canvas)

    def build_ui(self):
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X)

        ttk.Label(toolbar, text="Алгоритм:").pack(side=tk.LEFT, padx=5)
        for algo in Algorithm:
            ttk.Radiobutton(toolbar, text=algo.name, variable=self.algorithm,
                            value=algo.value).pack(side=tk.LEFT)

        ttk.Label(toolbar, text="Заполнение:").pack(side=tk.LEFT, padx=5)
        self.fill_algo_combo = ttk.Combobox(toolbar, textvariable=self.fill_algorithm,
                                            state='readonly', width=20)
        self.fill_algo_combo['values'] = [algo.value for algo in FillAlgorithm]
        self.fill_algo_combo.pack(side=tk.LEFT, padx=5)

        ttk.Button(toolbar, text="Заполнить", command=self.fill_polygon).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Новый полигон", command=self.start_new_polygon).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Замкнуть полигон", command=self.close_polygon).pack(side=tk.LEFT, padx=5)
        ttk.Checkbutton(toolbar, text="Отладка", variable=self.debug_mode).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text="Очистить", command=self.clear_canvas).pack(side=tk.LEFT, padx=5)

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

    def draw_pixel(self, x, y, color='blue', tags=None):
        """Рисует 1 пиксель на холсте"""
        self.canvas.create_line(x, y, x + 1, y, fill=color, tags=tags)

    def draw_polygon_fill(self, polygon, color='blue'):
        # Создаем временный холст для точного заполнения
        temp_canvas = tk.Canvas(self.root, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg='white')

        # Масштабируем координаты
        scaled_points = []
        for x, y in polygon:
            scaled_points.extend([x * CELL_SIZE, y * CELL_SIZE])

        # Рисуем полигон на временном холсте
        temp_canvas.create_polygon(*scaled_points, fill=color, outline='')

        # Получаем изображение с холста
        temp_canvas.update()
        temp_canvas.postscript(file="temp.ps", colormode='color')

        # Удаляем временный холст
        temp_canvas.destroy()

        # Загружаем изображение на основной холст
        from PIL import Image, ImageTk
        img = Image.open("temp.ps")
        img = ImageTk.PhotoImage(img)
        self.canvas.create_image(0, 0, image=img, anchor='nw', tags='fill')
        self.canvas.image = img  # Сохраняем ссылку


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

    def fill_polygon(self):
        if not self.current_polygon and not self.polygons:
            messagebox.showerror("Ошибка", "Нет полигонов для заполнения")
            return

        polygons_to_fill = self.polygons.copy()
        if self.current_polygon and len(self.current_polygon) >= 3:
            polygons_to_fill.append(self.current_polygon)

        algorithm = self.fill_algorithm.get()

        for polygon in polygons_to_fill:
            if algorithm in [FillAlgorithm.ORDERED_EDGE_LIST.value, FillAlgorithm.ACTIVE_EDGE_LIST.value]:
                # Прямое заполнение через canvas (без Ghostscript)
                self.draw_polygon(polygon, color='black', fill=self.fill_color, width=1)
            elif algorithm == FillAlgorithm.SIMPLE_SEED.value:
                self.simple_seed_fill(polygon)
            elif algorithm == FillAlgorithm.SCANLINE_SEED.value:
                self.scanline_seed_fill(polygon)

    def ordered_edge_list_fill(self, polygon):
        scaled_polygon = [(x * CELL_SIZE, y * CELL_SIZE) for x, y in polygon]
        edges = []
        n = len(scaled_polygon)

        for i in range(n):
            p1 = scaled_polygon[i]
            p2 = scaled_polygon[(i + 1) % n]
            if p1[1] > p2[1]:
                p1, p2 = p2, p1
            if p1[1] != p2[1]:
                dx = (p2[0] - p1[0]) / (p2[1] - p1[1])
                edges.append({'y_min': int(p1[1]), 'y_max': int(p2[1]), 'x': p1[0], 'dx': dx})

        edges.sort(key=lambda e: e['y_min'])
        y_min = min(p[1] for p in scaled_polygon)
        y_max = max(p[1] for p in scaled_polygon)

        active_edges = []
        debug_counter = 0
        refresh_rate = 1

        for y in range(int(y_min), int(y_max) + 1):
            for edge in edges:
                if edge['y_min'] == y:
                    active_edges.append(edge.copy())
            active_edges = [e for e in active_edges if e['y_max'] > y]
            active_edges.sort(key=lambda e: e['x'])

            if self.debug_mode.get():
                self.canvas.delete('debug')
                for edge in active_edges:
                    self.draw_pixel(int(edge['x']), y, color='green', tags='debug')
                self.canvas.update_idletasks()
                self.root.update()
                self.root.after(self.debug_delay)

            for i in range(0, len(active_edges), 2):
                if i + 1 >= len(active_edges): break
                x_start = int(active_edges[i]['x'])
                x_end = int(active_edges[i + 1]['x'])

                for x in range(x_start, x_end + 1):
                    self.draw_pixel(x, y, color=self.fill_color, tags='fill')
                    debug_counter += 1
                    if self.debug_mode.get() and debug_counter % refresh_rate == 0:
                        self.canvas.update_idletasks()
                        self.root.update()
                        self.root.after(self.debug_delay)

            for edge in active_edges:
                edge['x'] += edge['dx']

    def active_edge_list_fill(self, polygon):
        scaled_polygon = [(x * CELL_SIZE, y * CELL_SIZE) for x, y in polygon]
        edges = []
        for i in range(len(scaled_polygon)):
            p1 = scaled_polygon[i]
            p2 = scaled_polygon[(i + 1) % len(scaled_polygon)]
            if p1[1] > p2[1]:
                p1, p2 = p2, p1
            if p1[1] != p2[1]:
                edges.append({
                    'y_min': int(p1[1]), 'y_max': int(p2[1]),
                    'x': p1[0], 'dx': (p2[0] - p1[0]) / (p2[1] - p1[1])
                })

        edges.sort(key=lambda e: e['y_min'])

        y_min = int(min(p[1] for p in scaled_polygon))
        y_max = int(max(p[1] for p in scaled_polygon))
        active_edges = []
        current_edge = 0
        debug_counter = 0
        refresh_rate = 1

        for y in range(y_min, y_max + 1):
            while current_edge < len(edges) and edges[current_edge]['y_min'] == y:
                active_edges.append(edges[current_edge].copy())
                current_edge += 1

            active_edges = [e for e in active_edges if e['y_max'] > y]
            active_edges.sort(key=lambda e: e['x'])

            if self.debug_mode.get():
                self.canvas.delete('debug')
                for edge in active_edges:
                    self.draw_pixel(int(edge['x']), y, color='green', tags='debug')
                self.canvas.update_idletasks()
                self.root.update()
                self.root.after(self.debug_delay)

            for i in range(0, len(active_edges), 2):
                if i + 1 >= len(active_edges): break
                x_start = int(active_edges[i]['x'])
                x_end = int(active_edges[i + 1]['x'])

                for x in range(x_start, x_end + 1):
                    self.draw_pixel(x, y, color=self.fill_color, tags='fill')
                    debug_counter += 1
                    if self.debug_mode.get() and debug_counter % refresh_rate == 0:
                        self.canvas.update_idletasks()
                        self.root.update()
                        self.root.after(self.debug_delay)

            for edge in active_edges:
                edge['x'] += edge['dx']

    def simple_seed_fill(self, polygon):
        scaled_polygon = [(x * CELL_SIZE, y * CELL_SIZE) for x, y in polygon]

        if polygon[0] != polygon[-1]:
            scaled_polygon.append(scaled_polygon[0])

        cx = sum(p[0] for p in scaled_polygon) // len(scaled_polygon)
        cy = sum(p[1] for p in scaled_polygon) // len(scaled_polygon)

        if not self.is_point_in_polygon((cx, cy), scaled_polygon):
            found = False
            for y in range(int(min(p[1] for p in scaled_polygon)), int(max(p[1] for p in scaled_polygon))):
                for x in range(int(min(p[0] for p in scaled_polygon)), int(max(p[0] for p in scaled_polygon))):
                    if self.is_point_in_polygon((x, y), scaled_polygon):
                        cx, cy = x, y
                        found = True
                        break
                if found:
                    break
            if not found:
                return

        stack = [(cx, cy)]
        filled = set()
        counter = 0
        refresh_rate = 100  # каждые 100 пикселей

        while stack:
            x, y = stack.pop()
            if (x, y) in filled or not self.is_point_in_polygon((x, y), scaled_polygon):
                continue

            self.draw_pixel(x, y, color=self.fill_color, tags='fill')
            filled.add((x, y))
            counter += 1

            if self.debug_mode.get() and counter % refresh_rate == 0:
                self.canvas.update_idletasks()
                self.root.update()
                self.root.after(self.debug_delay)

            for dx, dy in [(1, 0), (-1, 0), (0, 1), (0, -1)]:
                nx, ny = x + dx, y + dy
                if (nx, ny) not in filled:
                    stack.append((nx, ny))

    def scanline_seed_fill(self, polygon):
        scaled_polygon = [(x * CELL_SIZE, y * CELL_SIZE) for x, y in polygon]

        if polygon[0] != polygon[-1]:
            scaled_polygon.append(scaled_polygon[0])

        cx = sum(p[0] for p in scaled_polygon) // len(scaled_polygon)
        cy = sum(p[1] for p in scaled_polygon) // len(scaled_polygon)

        if not self.is_point_in_polygon((cx, cy), scaled_polygon):
            found = False
            for y in range(int(min(p[1] for p in scaled_polygon)), int(max(p[1] for p in scaled_polygon))):
                for x in range(int(min(p[0] for p in scaled_polygon)), int(max(p[0] for p in scaled_polygon))):
                    if self.is_point_in_polygon((x, y), scaled_polygon):
                        cx, cy = x, y
                        found = True
                        break
                if found:
                    break
            if not found:
                return

        stack = [(cx, cy)]
        filled = set()
        debug_counter = 0
        refresh_rate = 100

        while stack:
            x, y = stack.pop()
            if (x, y) in filled:
                continue

            left = x
            while left >= 0 and self.is_point_in_polygon((left, y), scaled_polygon):
                left -= 1
            left += 1

            right = x
            while self.is_point_in_polygon((right, y), scaled_polygon):
                right += 1
            right -= 1

            for px in range(left, right + 1):
                if (px, y) not in filled:
                    self.draw_pixel(px, y, color=self.fill_color, tags='fill')
                    filled.add((px, y))
                    debug_counter += 1
                    if self.debug_mode.get() and debug_counter % refresh_rate == 0:
                        self.canvas.update_idletasks()
                        self.root.update()
                        self.root.after(self.debug_delay)

            for dy in [-1, 1]:
                new_y = y + dy
                px = left
                while px <= right:
                    while px <= right and (
                            (px, new_y) in filled or not self.is_point_in_polygon((px, new_y), scaled_polygon)):
                        px += 1
                    if px <= right:
                        seed = px
                        while px <= right and (px, new_y) not in filled and self.is_point_in_polygon((px, new_y),
                                                                                                     scaled_polygon):
                            px += 1
                        stack.append((seed, new_y))
                    px += 1

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

    def cross_product(self, a, b, c):
        return (b[0] - a[0]) * (c[1] - a[1]) - (b[1] - a[1]) * (c[0] - a[0])

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
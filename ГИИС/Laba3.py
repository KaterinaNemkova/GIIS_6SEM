import tkinter as tk
from tkinter import ttk
import numpy as np
from math import factorial

CELL_SIZE = 20
CANVAS_WIDTH = 800
CANVAS_HEIGHT = 600


class ParametricCurvesEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Редактор параметрических кривых")

        # Основные переменные
        self.curve_type = tk.StringVar(value='hermite')
        self.edit_mode = tk.BooleanVar(value=False)
        self.points = []
        self.curves = []
        self.current_curve = None
        self.selected_point = None
        self.preview_id = None
        self.tangent_mode = False

        # Создание интерфейса
        self.create_widgets()

        # Привязка событий
        self.canvas.bind('<Button-1>', self.on_click)
        self.canvas.bind('<B1-Motion>', self.on_drag)
        self.canvas.bind('<Motion>', self.on_motion)
        self.canvas.bind('<ButtonRelease-1>', self.on_release)

        # Инициализация
        self.draw_grid()

    def create_widgets(self):
        # Панель инструментов
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X)

        # Меню выбора кривой
        curve_menu = ttk.OptionMenu(toolbar, self.curve_type, 'hermite',
                                    'hermite', 'bezier', 'bspline',
                                    command=self.update_curve_type)
        curve_menu.pack(side=tk.LEFT, padx=5)

        # Кнопки управления
        ttk.Checkbutton(toolbar, text='Режим редактирования', variable=self.edit_mode).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text='Очистить', command=self.clear_canvas).pack(side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text='Соединить кривые', command=self.connect_curves).pack(side=tk.LEFT, padx=5)

        # Холст для рисования
        self.canvas = tk.Canvas(self.root, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg='white')
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Статусная строка
        self.status = ttk.Label(self.root, text="Готов к работе", relief=tk.SUNKEN)
        self.status.pack(fill=tk.X)

    def update_curve_type(self, *args):
        self.clear_preview()
        self.points = []
        self.tangent_mode = False
        self.status.config(text=f"Выбран тип кривой: {self.curve_type.get()}")

    def draw_grid(self):
        self.canvas.delete('grid')
        for x in range(0, CANVAS_WIDTH, CELL_SIZE):
            self.canvas.create_line(x, 0, x, CANVAS_HEIGHT, fill='#eee', tags='grid')
        for y in range(0, CANVAS_HEIGHT, CELL_SIZE):
            self.canvas.create_line(0, y, CANVAS_WIDTH, y, fill='#eee', tags='grid')

    def on_click(self, event):
        x, y = event.x // CELL_SIZE, event.y // CELL_SIZE

        if self.edit_mode.get():
            self.selected_point = self.find_nearest_point(x, y)
            if self.selected_point:
                return

        if self.curve_type.get() == 'hermite':
            if not self.tangent_mode:
                if len(self.points) < 2:
                    self.points.append((x, y))
                    self.draw_point(x, y)

                    if len(self.points) == 1:
                        self.status.config(text="Укажите конечную точку")
                    elif len(self.points) == 2:
                        self.current_curve = {
                            'type': 'hermite',
                            'points': self.points.copy(),
                            'tangents': []
                        }
                        self.status.config(text="Задайте касательную: перетащите от начальной точки")
                        self.tangent_mode = True
            return

        # Для Безье и B-сплайнов просто добавляем точки
        self.points.append((x, y))
        self.draw_point(x, y, color='red' if len(self.points) in (1, 4) else 'green')

        if self.curve_type.get() == 'bezier' and len(self.points) >= 4:
            self.finalize_bezier_curve()
        elif self.curve_type.get() == 'bspline' and len(self.points) >= 4:
            self.finalize_bspline()

    def on_drag(self, event):
        if not self.edit_mode.get() or not self.selected_point:
            return

        x, y = event.x // CELL_SIZE, event.y // CELL_SIZE
        curve_idx, point_key = self.selected_point

        curve = self.curves[curve_idx]

        if isinstance(point_key, int):
            # Редактирование обычной точки (как было)
            curve['points'][point_key] = (x, y)
        elif point_key == 'tangent_0':
            # Редактирование ПЕРВОЙ касательной (возле p0)
            p0 = curve['points'][0]
            curve['tangents'][0] = ((x - p0[0]) * 3, (y - p0[1]) * 3)
        elif point_key == 'tangent_1':
            # Редактирование ВТОРОЙ касательной (возле p1)
            p1 = curve['points'][1]
            curve['tangents'][1] = ((x - p1[0]) * 3, (y - p1[1]) * 3)

        self.redraw_all_curves()

    def on_motion(self, event):
        if self.edit_mode.get() or not self.points:
            return

        self.clear_preview()
        x, y = event.x // CELL_SIZE, event.y // CELL_SIZE

        if self.curve_type.get() == 'hermite':
            if len(self.points) == 1:
                self.preview_id = self.draw_line(self.points[0][0], self.points[0][1], x, y, preview=True)
            elif len(self.points) == 2 and self.tangent_mode:
                if len(self.current_curve['tangents']) == 0:
                    # Предпросмотр первой касательной
                    t0 = (x - self.points[0][0], y - self.points[0][1])
                    self.preview_id = self.draw_hermite(self.points[0], self.points[1], t0, (0, 0), preview=True)
                else:
                    # Предпросмотр обеих касательных
                    t0 = self.current_curve['tangents'][0]
                    t1 = (x - self.points[1][0], y - self.points[1][1])
                    self.preview_id = self.draw_hermite(self.points[0], self.points[1], t0, t1, preview=True)
        elif self.curve_type.get() == 'bezier' and len(self.points) >= 1:
            control_points = self.points + [(x, y)]
            if len(control_points) >= 2:
                self.draw_control_polygon(control_points, preview=True)
            if len(control_points) >= 4:
                self.preview_id = self.draw_bezier(control_points, preview=True)
        elif self.curve_type.get() == 'bspline' and len(self.points) >= 1:
            control_points = self.points + [(x, y)]
            if len(control_points) >= 4:
                self.preview_id = self.draw_bspline(control_points, preview=True)

    def on_release(self, event):
        if self.edit_mode.get():
            self.selected_point = None
            return

        if not self.points or self.curve_type.get() != 'hermite':
            return

        if self.tangent_mode:
            x, y = event.x // CELL_SIZE, event.y // CELL_SIZE

            if len(self.current_curve['tangents']) == 0:
                # Первая касательная
                t0 = (x - self.points[0][0], y - self.points[0][1])
                self.current_curve['tangents'].append(t0)
                self.status.config(text="Теперь задайте касательную у конечной точки")
            else:
                # Вторая касательная
                t1 = (x - self.points[1][0], y - self.points[1][1])
                self.current_curve['tangents'].append(t1)

                # Финализируем кривую
                self.curves.append(self.current_curve)
                self.draw_hermite(self.points[0], self.points[1],
                                  self.current_curve['tangents'][0],
                                  self.current_curve['tangents'][1])

                self.points = []
                self.current_curve = None
                self.tangent_mode = False
                self.status.config(text="Кривая Эрмита построена. Готов к работе")

        self.clear_preview()

    def finalize_bezier_curve(self):
        self.current_curve = {
            'type': 'bezier',
            'points': self.points.copy()
        }
        self.curves.append(self.current_curve)
        self.draw_bezier(self.points)
        self.points = []
        self.current_curve = None
        self.status.config(text="Кривая Безье построена. Готов к работе")

    def finalize_bspline(self):
        self.current_curve = {
            'type': 'bspline',
            'points': self.points.copy()
        }
        self.curves.append(self.current_curve)
        self.draw_bspline(self.points)
        self.points = []
        self.current_curve = None
        self.status.config(text="B-сплайн построен. Готов к работе")

    def find_nearest_point(self, x, y, threshold=2):
        # Поиск обычных точек (как было)
        for curve_idx, curve in enumerate(self.curves):
            for point_idx, (px, py) in enumerate(curve['points']):
                if abs(px - x) <= threshold and abs(py - y) <= threshold:
                    return (curve_idx, point_idx)

        # ДОБАВЛЯЕМ: Поиск синих точек касательных (только для Эрмита)
        for curve_idx, curve in enumerate(self.curves):
            if curve['type'] == 'hermite' and 'tangents' in curve:
                p0, p1 = curve['points']
                t0, t1 = curve['tangents']

                # Проверяем первую касательную (возле p0)
                tangent_x = p0[0] + t0[0] / 3
                tangent_y = p0[1] + t0[1] / 3
                if abs(tangent_x - x) <= threshold and abs(tangent_y - y) <= threshold:
                    return (curve_idx, 'tangent_0')  # Возвращаем спец.ключ

                # Проверяем вторую касательную (возле p1)
                tangent_x = p1[0] + t1[0] / 3
                tangent_y = p1[1] + t1[1] / 3
                if abs(tangent_x - x) <= threshold and abs(tangent_y - y) <= threshold:
                    return (curve_idx, 'tangent_1')

        return None

    def draw_point(self, x, y, color='red', tags=None):
        size = 3
        self.canvas.create_oval(
            (x * CELL_SIZE) - size, (y * CELL_SIZE) - size,
            (x * CELL_SIZE) + size, (y * CELL_SIZE) + size,
            fill=color, outline=color, tags=tags
        )

    def draw_line(self, x0, y0, x1, y1, color='black', dash=None, preview=False, tags=None):
        return self.canvas.create_line(
            x0 * CELL_SIZE, y0 * CELL_SIZE,
            x1 * CELL_SIZE, y1 * CELL_SIZE,
            fill='gray' if preview else color,
            dash=(2, 2) if preview else dash,
            tags='preview' if preview else tags
        )

    def draw_curve(self, points, color='black', dash=None, preview=False, tags=None):
        scaled = []
        for x, y in points:
            scaled.extend([x * CELL_SIZE, y * CELL_SIZE])

        return self.canvas.create_line(*scaled,
                                       fill='gray' if preview else color,
                                       dash=(2, 2) if preview else dash,
                                       tags='preview' if preview else tags,
                                       smooth=True)

    def draw_hermite(self, p0, p1, t0, t1, preview=False):
        # Матрица Эрмита
        hermite_matrix = np.array([
            [2, -2, 1, 1],
            [-3, 3, -2, -1],
            [0, 0, 1, 0],
            [1, 0, 0, 0]
        ])

        # Вектор параметров
        geometry_vector = np.array([
            [p0[0], p0[1]],
            [p1[0], p1[1]],
            [t0[0], t0[1]],
            [t1[0], t1[1]]
        ])

        # Вычисляем коэффициенты
        coefficients = np.dot(hermite_matrix, geometry_vector)

        # Генерируем точки кривой
        points = []
        for t in np.linspace(0, 1, 50):
            t_vector = np.array([t ** 3, t ** 2, t, 1])
            point = np.dot(t_vector, coefficients)
            points.append((point[0], point[1]))

        # Рисуем кривую
        curve_id = self.draw_curve(points, preview=preview)

        # Рисуем контрольные элементы
        if not preview:
            self.draw_point(p0[0], p0[1], color='red')
            self.draw_point(p1[0], p1[1], color='red')

            # Касательные
            self.draw_line(p0[0], p0[1], p0[0] + t0[0] / 3, p0[1] + t0[1] / 3, color='blue', dash=(2, 2))
            self.draw_line(p1[0], p1[1], p1[0] + t1[0] / 3, p1[1] + t1[1] / 3, color='blue', dash=(2, 2))

            # Точки касательных
            self.draw_point(p0[0] + t0[0] / 3, p0[1] + t0[1] / 3, color='blue')
            self.draw_point(p1[0] + t1[0] / 3, p1[1] + t1[1] / 3, color='blue')

        return curve_id

    def draw_bezier(self, control_points, preview=False):
        n = len(control_points) - 1
        points = []

        for t in np.linspace(0, 1, 100):
            x, y = 0, 0
            for i in range(n + 1):
                basis = self.bernstein_basis(n, i, t)
                x += control_points[i][0] * basis
                y += control_points[i][1] * basis
            points.append((x, y))

        # Рисуем кривую
        curve_id = self.draw_curve(points, preview=preview)

        # Рисуем контрольные точки и ломаную
        if not preview:
            for i, (x, y) in enumerate(control_points):
                color = 'red' if i in (0, len(control_points) - 1) else 'green'
                self.draw_point(x, y, color=color)
            self.draw_control_polygon(control_points)

        return curve_id

    def draw_bspline(self, control_points, preview=False, degree=3):
        n = len(control_points)
        if n < degree + 1:
            return None

        # Равномерный узловой вектор
        knots = list(range(n + degree + 1))

        points = []
        for t in np.linspace(degree, n, 100):
            x, y = 0, 0
            for i in range(n):
                basis = self.bspline_basis(i, degree, t, knots)
                x += control_points[i][0] * basis
                y += control_points[i][1] * basis
            points.append((x, y))

        # Рисуем кривую
        curve_id = self.draw_curve(points, preview=preview)

        # Рисуем контрольные точки и ломаную
        if not preview:
            for x, y in control_points:
                self.draw_point(x, y, color='green')
            self.draw_control_polygon(control_points)

        return curve_id

    def bernstein_basis(self, n, i, t):
        binom = factorial(n) / (factorial(i) * factorial(n - i))
        return binom * (t ** i) * ((1 - t) ** (n - i))

    def bspline_basis(self, i, k, t, knots):
        if k == 0:
            return 1 if knots[i] <= t < knots[i + 1] else 0

        denom1 = knots[i + k] - knots[i]
        term1 = 0 if denom1 == 0 else ((t - knots[i]) / denom1) * self.bspline_basis(i, k - 1, t, knots)

        denom2 = knots[i + k + 1] - knots[i + 1]
        term2 = 0 if denom2 == 0 else ((knots[i + k + 1] - t) / denom2) * self.bspline_basis(i + 1, k - 1, t, knots)

        return term1 + term2

    def draw_control_polygon(self, points, preview=False):
        for i in range(len(points) - 1):
            x0, y0 = points[i]
            x1, y1 = points[i + 1]
            self.draw_line(x0, y0, x1, y1, color='blue', dash=(2, 2),
                           tags='preview' if preview else 'control')

    def clear_preview(self):
        if self.preview_id:
            self.canvas.delete(self.preview_id)
            self.preview_id = None
        self.canvas.delete('preview')

    def redraw_all_curves(self):
        self.canvas.delete('all')
        self.draw_grid()

        for curve in self.curves:
            if curve['type'] == 'hermite':
                p0, p1 = curve['points']
                t0, t1 = curve['tangents']
                self.draw_hermite(p0, p1, t0, t1)
            elif curve['type'] == 'bezier':
                self.draw_bezier(curve['points'])
            elif curve['type'] == 'bspline':
                self.draw_bspline(curve['points'])

    def connect_curves(self):
        if len(self.curves) < 2:
            self.status.config(text="Недостаточно кривых для соединения")
            return

        curve1 = self.curves[-2]
        curve2 = self.curves[-1]

        if curve1['type'] != curve2['type']:
            self.status.config(text="Нельзя соединять кривые разных типов")
            return

        if curve1['type'] == 'hermite':
            if len(curve1['points']) < 2 or len(curve2['points']) < 2:
                self.status.config(text="Недостаточно точек для соединения кривых Эрмита")
                return

            p0 = curve1['points'][1]  # Конечная точка первой кривой
            p1 = curve2['points'][0]  # Начальная точка второй кривой
            t0 = curve1['tangents'][1] if len(curve1['tangents']) > 1 else (0, 0)
            t1 = curve2['tangents'][0] if len(curve2['tangents']) > 0 else (0, 0)

            # Создаем соединительную кривую
            new_curve = {
                'type': 'hermite',
                'points': [p0, p1],
                'tangents': [t0, t1]
            }
            self.curves.append(new_curve)
            self.redraw_all_curves()
            self.status.config(text="Кривые Эрмита соединены")

        elif curve1['type'] == 'bezier':
            if len(curve1['points']) < 4 or len(curve2['points']) < 4:
                self.status.config(text="Нужны кривые Безье с 4 точками")
                return

            # Объединяем последние 2 точки первой кривой и первые 2 второй
            new_points = curve1['points'][-2:] + curve2['points'][:2]
            if len(new_points) < 4:
                self.status.config(text="Недостаточно точек для соединения")
                return

            new_curve = {
                'type': 'bezier',
                'points': new_points
            }
            self.curves.append(new_curve)
            self.redraw_all_curves()
            self.status.config(text="Кривые Безье соединены")

        elif curve1['type'] == 'bspline':
            # Просто объединяем все точки
            new_points = curve1['points'] + curve2['points']
            if len(new_points) < 4:
                self.status.config(text="Недостаточно точек для B-сплайна")
                return

            new_curve = {
                'type': 'bspline',
                'points': new_points
            }
            self.curves.append(new_curve)
            self.redraw_all_curves()
            self.status.config(text="B-сплайны соединены")

    def clear_canvas(self):
        self.canvas.delete('all')
        self.points = []
        self.curves = []
        self.current_curve = None
        self.selected_point = None
        self.tangent_mode = False
        self.draw_grid()
        self.status.config(text="Холст очищен. Готов к работе")


if __name__ == "__main__":
    root = tk.Tk()
    app = ParametricCurvesEditor(root)
    root.mainloop()
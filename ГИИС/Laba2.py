import tkinter as tk
from tkinter import ttk
from math import sqrt, cos, sin, pi

CELL_SIZE = 20
CANVAS_WIDTH = 800
CANVAS_HEIGHT = 600


class SecondOrderCurvesEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Графический редактор линий второго порядка")

        self.curve_type = tk.StringVar(value='Окружность')
        self.debug_mode = tk.BooleanVar(value=False)
        self.points = []
        self.curves = []
        self.preview_id = []
        self.debug_window = None
        self.debug_text = None

        self.create_widgets()

        self.canvas.bind('<Button-1>', self.on_click)
        self.canvas.bind('<Motion>', self.on_motion)
        self.canvas.bind('<ButtonRelease-1>', self.on_release)

    def create_widgets(self):
        toolbar = ttk.Frame(self.root)
        toolbar.pack(fill=tk.X)

        curve_menu = ttk.OptionMenu(toolbar, self.curve_type, 'Окружность',
                                    'Окружность', 'Эллипс', 'Гипербола', 'Парабола')
        curve_menu.pack(side=tk.LEFT, padx=5)

        ttk.Checkbutton(toolbar, text='Режим отладки', variable=self.debug_mode, command=self.draw_grid).pack(
            side=tk.LEFT, padx=5)
        ttk.Button(toolbar, text='Очистить', command=self.clear_canvas).pack(side=tk.LEFT, padx=5)

        self.canvas = tk.Canvas(self.root, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg='white')
        self.canvas.pack(fill=tk.BOTH, expand=True)

        self.draw_grid()

    def draw_grid(self):
        self.canvas.delete('grid')
        if not self.debug_mode.get():
            if self.debug_window:
                self.debug_window.destroy()
                self.debug_window = None
            return
        for x in range(0, CANVAS_WIDTH, CELL_SIZE):
            self.canvas.create_line(x, 0, x, CANVAS_HEIGHT, fill='#ddd', tags='grid')
        for y in range(0, CANVAS_HEIGHT, CELL_SIZE):
            self.canvas.create_line(0, y, CANVAS_WIDTH, y, fill='#ddd', tags='grid')

    def create_debug_window(self):
        if self.debug_window:
            self.debug_window.destroy()

        self.debug_window = tk.Toplevel(self.root)
        self.debug_window.title("Отладочная информация")
        self.debug_window.geometry("800x400")

        self.debug_text = tk.Text(self.debug_window, wrap=tk.NONE, font=('Courier New', 10))
        scroll_x = ttk.Scrollbar(self.debug_window, orient=tk.HORIZONTAL, command=self.debug_text.xview)
        scroll_y = ttk.Scrollbar(self.debug_window, orient=tk.VERTICAL, command=self.debug_text.yview)
        self.debug_text.configure(xscrollcommand=scroll_x.set, yscrollcommand=scroll_y.set)

        scroll_x.pack(side=tk.BOTTOM, fill=tk.X)
        scroll_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.debug_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

    def print_debug_table(self, title, headers, rows):
        if not hasattr(self, 'debug_window') or self.debug_window is None or not self.debug_window.winfo_exists():
            self.debug_window = tk.Toplevel(self.root)
            self.debug_window.title("Таблица отладки")
            self.debug_text = tk.Text(self.debug_window, height=30, width=200, font=("Courier", 10))
            self.debug_text.pack()

        self.debug_text.delete("1.0", tk.END)
        self.debug_text.insert(tk.END, f"\n{title}\n")
        self.debug_text.insert(tk.END, "-" * 200 + "\n")

        header_line = "".join(f"{h:<20}" for h in headers)
        self.debug_text.insert(tk.END, header_line + "\n")
        self.debug_text.insert(tk.END, "-" * 200 + "\n")

        for row in rows:
            row_line = "".join(f"{str(cell):<20}" for cell in row)
            self.debug_text.insert(tk.END, row_line + "\n")

    def on_click(self, event):
        x, y = event.x // CELL_SIZE, event.y // CELL_SIZE
        self.points = [(x, y)]

    def on_motion(self, event):
        if not self.points:
            return

        self.clear_preview()
        x0, y0 = self.points[0]
        x1, y1 = event.x // CELL_SIZE, event.y // CELL_SIZE
        curve_name = self.curve_type.get()

        if curve_name == 'Окружность':
            r = int(sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2))
            self.preview_id = self.draw_circle(x0, y0, r, preview=True)
        elif curve_name == 'Эллипс':
            a = abs(x1 - x0)
            b = abs(y1 - y0)
            self.preview_id = self.draw_ellipse(x0, y0, a, b, preview=True)
        elif curve_name == 'Гипербола':
            a = max(1, abs(x1 - x0))
            b = max(1, abs(y1 - y0))
            self.preview_id = self.draw_hyperbola(x0, y0, a, b, preview=True)
        elif curve_name == 'Парабола':
            p = max(1, abs(y1 - y0))
            self.preview_id = self.draw_parabola(x0, y0, p, preview=True)

    def on_release(self, event):
        if not self.points:
            return

        x0, y0 = self.points[0]
        x1, y1 = event.x // CELL_SIZE, event.y // CELL_SIZE
        curve_name = self.curve_type.get()

        if curve_name == 'Окружность':
            r = int(sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2))
            self.draw_circle(x0, y0, r)
        elif curve_name == 'Эллипс':
            a = abs(x1 - x0)
            b = abs(y1 - y0)
            self.draw_ellipse(x0, y0, a, b)
        elif curve_name == 'Гипербола':
            a = max(1, abs(x1 - x0))
            b = max(1, abs(y1 - y0))
            self.draw_hyperbola(x0, y0, a, b)
        elif curve_name == 'Парабола':
            p = max(1, abs(y1 - y0))
            self.draw_parabola(x0, y0, p)

        self.points = []
        self.clear_preview()

        self.print_debug_table_for_curve(curve_name)

    def clear_preview(self):
        for item in self.preview_id:
            self.canvas.delete(item)
        self.preview_id = []

    def print_debug_table_for_curve(self, curve_name):
        if not self.debug_mode.get():
            return


    def clear_preview(self):
        for item in self.preview_id:
            self.canvas.delete(item)
        self.preview_id = []

    def draw_circle(self, x0, y0, radius, preview=False):
        points = []
        debug_rows = []

        if self.debug_mode.get() and not preview:
            x = 0
            y = radius
            delta = 2 - 2 * radius
            error = 0
            step = 0

            while y >= 0:
                step += 1
                debug_rows.append([
                    step,
                    delta,
                    error,
                    x, y,
                    f"({x0 + x}, {y0 + y})",
                    f"({x0 - x}, {y0 + y})",
                    f"({x0 + x}, {y0 - y})",
                    f"({x0 - x}, {y0 - y})"
                ])

                error = 2 * (delta + y) - 1
                if delta < 0 and error <= 0:
                    x += 1
                    delta += 2 * x + 1
                    continue

                error = 2 * (delta - x) - 1
                if delta > 0 and error > 0:
                    y -= 1
                    delta += 1 - 2 * y
                    continue

                x += 1
                delta += 2 * (x - y)
                y -= 1

            headers = ["Шаг", "Δi", "δ", "x", "y", "Пиксель 1", "Пиксель 2", "Пиксель 3", "Пиксель 4"]
            self.print_debug_table("Окружность", headers, debug_rows)

        # Parametric drawing for visualization
        for t in range(0, 361):
            angle = pi * t / 180
            x = x0 + radius * cos(angle)
            y = y0 + radius * sin(angle)
            points.append((x, y))
        return self.draw_line(points, preview)

    def draw_ellipse(self, x0, y0, a, b, preview=False):
        points = []
        debug_rows = []

        # Midpoint ellipse algorithm for debug table
        if self.debug_mode.get() and not preview:
            x = 0
            y = b
            a_sqr = a * a
            b_sqr = b * b
            step = 0

            # Region 1
            dx = 2 * b_sqr * x
            dy = 2 * a_sqr * y
            delta = b_sqr - a_sqr * b + 0.25 * a_sqr
            debug_rows.append([step, "Region 1", delta, dx, dy, x, y, f"({x0 + x}, {y0 + y})"])

            while dx < dy:
                step += 1
                if delta < 0:
                    x += 1
                    dx += 2 * b_sqr
                    delta += dx + b_sqr
                else:
                    x += 1
                    y -= 1
                    dx += 2 * b_sqr
                    dy -= 2 * a_sqr
                    delta += dx - dy + b_sqr

                debug_rows.append([step, "Region 1", delta, dx, dy, x, y, f"({x0 + x}, {y0 + y})"])

            # Region 2
            delta = b_sqr * (x + 0.5) * (x + 0.5) + a_sqr * (y - 1) * (y - 1) - a_sqr * b_sqr
            debug_rows.append([step, "Region 2", delta, dx, dy, x, y, f"({x0 + x}, {y0 + y})"])

            while y >= 0:
                step += 1
                if delta > 0:
                    y -= 1
                    dy -= 2 * a_sqr
                    delta += a_sqr - dy
                else:
                    y -= 1
                    x += 1
                    dx += 2 * b_sqr
                    dy -= 2 * a_sqr
                    delta += dx - dy + a_sqr

                debug_rows.append([step, "Region 2", delta, dx, dy, x, y, f"({x0 + x}, {y0 + y})"])

            headers = ["Шаг", "Регион", "Δ", "dx", "dy", "x", "y", "Пиксель"]
            self.print_debug_table("Эллипс", headers, debug_rows)

        # Parametric drawing for visualization
        for t in range(0, 361):
            angle = pi * t / 180
            x = x0 + a * cos(angle)
            y = y0 + b * sin(angle)
            points.append((x, y))
        return self.draw_line(points, preview)

    def draw_hyperbola(self, x0, y0, a, b, preview=False):
        points1 = []
        points2 = []
        debug_rows = []

        # Hyperbola algorithm for debug table
        if self.debug_mode.get() and not preview:
            x = a
            y = 0
            step = 0
            a_sqr = a * a
            b_sqr = b * b

            # Initial point
            debug_rows.append([step, x, y, f"({x0 + x}, {y0 + y})", f"({x0 + x}, {y0 - y})"])

            # First region (|x| >= a)
            while x < 100 and step < 100:  # Limit steps for display
                step += 1
                delta = b_sqr * x * x - a_sqr * y * y - a_sqr * b_sqr

                if delta >= 0:
                    y += 1
                x += 1

                debug_rows.append([step, x, y, f"({x0 + x}, {y0 + y})", f"({x0 + x}, {y0 - y})"])

            headers = ["Шаг", "x", "y", "Пиксель 1", "Пиксель 2"]
            self.print_debug_table("Гипербола", headers, debug_rows)

        # Parametric drawing for visualization
        for t in range(-100, -1):
            x = t / 10
            y = sqrt((x ** 2 * b ** 2 / a ** 2) + b ** 2)
            points1.append((x0 + x, y0 + y))
            points2.append((x0 + x, y0 - y))
        for t in range(1, 100):
            x = t / 10
            y = sqrt((x ** 2 * b ** 2 / a ** 2) + b ** 2)
            points1.append((x0 + x, y0 + y))
            points2.append((x0 + x, y0 - y))
        id1 = self.draw_line(points1, preview)
        id2 = self.draw_line(points2, preview)
        return id1 + id2 if preview else None

    def draw_parabola(self, x0, y0, p, preview=False):
        points = []
        debug_rows = []

        # Parabola algorithm for debug table
        if self.debug_mode.get() and not preview:
            x = 0
            y = 0
            step = 0
            delta = 1 - 2 * p

            # Initial point
            debug_rows.append([step, delta, x, y, f"({x0 + x}, {y0 + y})"])

            while x < 100 and step < 100:  # Limit steps for display
                step += 1
                if delta < 0:
                    delta += 2 * x + 3
                else:
                    delta += 2 * (x - p) + 3
                    y += 1
                x += 1

                debug_rows.append([step, delta, x, y, f"({x0 + x}, {y0 + y})"])

            headers = ["Шаг", "Δ", "x", "y", "Пиксель"]
            self.print_debug_table("Парабола", headers, debug_rows)

        # Parametric drawing for visualization
        for x in range(-100, 101):
            y = (x ** 2) / (2 * p)
            points.append((x0 + x / 10, y0 + y / 10))
        return self.draw_line(points, preview)

    def draw_line(self, points, preview=False):
        ids = []
        for i in range(len(points) - 1):
            x1, y1 = points[i][0] * CELL_SIZE, points[i][1] * CELL_SIZE
            x2, y2 = points[i + 1][0] * CELL_SIZE, points[i + 1][1] * CELL_SIZE
            ids.append(self.canvas.create_line(x1, y1, x2, y2,
                                               fill='gray' if preview else 'black',
                                               dash=(2, 2) if preview else None,
                                               tags='preview' if preview else 'curve'))
        return ids

    def clear_canvas(self):
        self.canvas.delete('all')
        self.draw_grid()


if __name__ == "__main__":
    root = tk.Tk()
    app = SecondOrderCurvesEditor(root)
    root.mainloop()
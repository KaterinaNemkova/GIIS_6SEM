import tkinter as tk
from tkinter import ttk
from fractions import Fraction

CELL_SIZE = 20
CANVAS_WIDTH = 800
CANVAS_HEIGHT = 400


def draw_grid(canvas):
    for x in range(0, CANVAS_WIDTH, CELL_SIZE):
        canvas.create_line(x, 0, x, CANVAS_HEIGHT, fill='#ddd')
    for y in range(0, CANVAS_HEIGHT, CELL_SIZE):
        canvas.create_line(0, y, CANVAS_WIDTH, y, fill='#ddd')


# Алгоритм ЦДА
def dda(canvas, x0, y0, x1, y1, debug=False, debug_table=None):
    dx = x1 - x0
    dy = y1 - y0
    steps = max(abs(dx), abs(dy))

    if debug and debug_table:
        debug_table.insert(tk.END, f"{'Шаг':<5} {'X':<10} {'Y':<10} {'Plot(x, y)':<15}\n")
        debug_table.insert(tk.END, "-"*40 + "\n")
        debug_table.yview(tk.END)

    if steps == 0:
        canvas.create_oval(
            x0 * CELL_SIZE, y0 * CELL_SIZE,
            x0 * CELL_SIZE + 1, y0 * CELL_SIZE + 1,
            fill="black"
        )
        if debug and debug_table:
            debug_table.insert(tk.END, f"0     {x0:<10} {y0:<10} Plot({x0}, {y0})\n")
            debug_table.yview(tk.END)
        return

    x_inc = dx / steps
    y_inc = dy / steps

    x, y = x0, y0
    points = [(x, y)]

    for i in range(int(steps) + 1):
        plot_x = round(x)
        plot_y = round(y)

        points.append((plot_x, plot_y))

        if debug and debug_table:
            x_frac = Fraction(x).limit_denominator(100)
            y_frac = Fraction(y).limit_denominator(100)

            debug_table.insert(
                tk.END,
                f"{i:<5} {str(x_frac):<10} {str(y_frac):<10} Plot({plot_x}, {plot_y})\n"
            )
            debug_table.yview(tk.END)

        x += x_inc
        y += y_inc

    canvas.create_line(
        x0 * CELL_SIZE, y0 * CELL_SIZE,
        x1 * CELL_SIZE, y1 * CELL_SIZE,
        fill="black"
    )

    if debug:
        canvas.update()
        canvas.after(50)

# Алгоритм Брезенхема
def bresenham(canvas, x0, y0, x1, y1, debug=False, debug_table=None):
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    x, y = x0, y0
    sx = 1 if x1 > x0 else -1
    sy = 1 if y1 > y0 else -1

    points = []

    if debug and debug_table:
        debug_table.insert(tk.END, f"{'i':<3} | {'шаг':<4} | {'итерации':<10} | {'e':<8} | {'x':<3} | {'y':<3} | {'e’':<10} | {'Plot(x, y)':<10}\n")
        debug_table.insert(tk.END, "-" * 70 + "\n")

    if dx > dy:
        err = dx / 2.0
        i = 0
        while x != x1:
            if debug:
                e_before = err
            points.append((x, y))
            err -= dy
            e_after = err
            if err < 0:
                y += sy
                err += dx
            if debug:
                debug_table.insert(tk.END,
                                   f"{i:<3} | {i:<4} | итерация {i:<5} | {e_before:<8.2f} | {x:<3} | {y:<3} | {e_after:<10.2f} | Plot({x}, {y})\n")
                debug_table.yview(tk.END)
            x += sx
            i += 1
    else:
        err = dy / 2.0
        i = 0
        while y != y1:
            if debug:
                e_before = err
            points.append((x, y))
            err -= dx
            e_after = err
            if err < 0:
                x += sx
                err += dy
            if debug:
                debug_table.insert(tk.END,
                                   f"{i:<3} | {i:<4} | итерация {i:<5} | {e_before:<8.2f} | {x:<3} | {y:<3} | {e_after:<10.2f} | Plot({x}, {y})\n")
                debug_table.yview(tk.END)
            y += sy
            i += 1
    points.append((x, y))
    canvas.create_line(
        [round(x0 * CELL_SIZE), round(y0 * CELL_SIZE), round(x1 * CELL_SIZE), round(y1 * CELL_SIZE)], fill="black"
    )
    if debug:
        canvas.update()
        canvas.after(50)



# Алгоритм Ву
def wu(canvas, x0, y0, x1, y1, debug=False, debug_table=None):
    from math import floor, ceil, modf
    def fpart(x): return modf(x)[0]
    def rfpart(x): return 1 - fpart(x)

    steep = abs(y1 - y0) > abs(x1 - x0)
    if steep:
        x0, y0 = y0, x0
        x1, y1 = y1, x1

    if x0 > x1:
        x0, x1 = x1, x0
        y0, y1 = y1, y0

    dx = x1 - x0
    dy = y1 - y0
    gradient = dy / dx if dx != 0 else 1

    xend = round(x0)
    yend = y0 + gradient * (xend - x0)
    xpxl1 = xend
    ypxl1 = int(yend)

    points = []
    if steep:
        points.append((ypxl1, xpxl1))
        points.append((ypxl1 + 1, xpxl1))
    else:
        points.append((xpxl1, ypxl1))
        points.append((xpxl1, ypxl1 + 1))

    if debug and debug_table:
        debug_table.insert(tk.END, f"{'i':<3} | {'шаг':<4} | {'итерации':<10} | {'e':<8} | {'x':<3} | {'y':<3} | {'e’':<10} | {'Plot(x, y)':<10}\n")
        debug_table.insert(tk.END, "-" * 70 + "\n")

    intery = yend + gradient
    i = 0

    for x in range(xpxl1 + 1, round(x1)):
        y_before = intery
        plot_x = x
        plot_y = int(intery)

        if steep:
            points.append((plot_y, plot_x))
            points.append((plot_y + 1, plot_x))
            plot_coords = f"Plot({plot_y}, {plot_x})"
        else:
            points.append((plot_x, plot_y))
            points.append((plot_x, plot_y + 1))
            plot_coords = f"Plot({plot_x}, {plot_y})"

        y_after = intery + gradient

        if debug and debug_table:
            debug_table.insert(tk.END,
                f"{i:<3} | {i:<4} | итерация {i:<5} | {y_before:<8.2f} | {plot_x:<3} | {plot_y:<3} | {y_after:<10.2f} | {plot_coords:<10}\n"
            )
            debug_table.yview(tk.END)

        intery = y_after
        i += 1

    xend = round(x1)
    yend = y1 + gradient * (xend - x1)
    xpxl2 = xend
    ypxl2 = int(yend)

    if steep:
        points.append((ypxl2, xpxl2))
        points.append((ypxl2 + 1, xpxl2))
    else:
        points.append((xpxl2, ypxl2))
        points.append((xpxl2, ypxl2 + 1))

    canvas.create_line(
        [round(x0 * CELL_SIZE), round(y0 * CELL_SIZE), round(x1 * CELL_SIZE), round(y1 * CELL_SIZE)],
        fill="black"
    )
    if debug:
        canvas.update()
        canvas.after(50)


class LineDrawer:
    def __init__(self, root):
        self.root = root
        self.root.title("Графический редактор отрезков")

        self.canvas = tk.Canvas(root, width=CANVAS_WIDTH, height=CANVAS_HEIGHT, bg='white')
        self.canvas.pack()

        self.algorithm = tk.StringVar(value='dda')
        self.debug_mode = tk.BooleanVar(value=False)
        self.start = None
        self.lines = []

        self.build_toolbar()

        scrollbar = tk.Scrollbar(self.root)
        scrollbar.pack(side='right', fill='y')

        self.debug_table = tk.Text(self.root, height=20, width=70, yscrollcommand=scrollbar.set)
        self.debug_table.pack(side='left', fill='both', expand=True)

        scrollbar.config(command=self.debug_table.yview)
        self.canvas.bind('<Button-1>', self.click)
        self.canvas.bind('<Motion>', self.on_line_motion)

    def build_toolbar(self):
        toolbar = ttk.Frame(self.root)
        toolbar.pack()

        ttk.Label(toolbar, text='Алгоритм:').pack(side='left')
        for algo in [('ЦДА', 'dda'), ('Брезенхем', 'bresenham'), ('Ву', 'wu')]:
            ttk.Radiobutton(toolbar, text=algo[0], variable=self.algorithm, value=algo[1]).pack(side='left')

        ttk.Checkbutton(toolbar, text='Отладка', variable=self.debug_mode).pack(side='left')
        ttk.Button(toolbar, text='Очистить', command=self.clear).pack(side='left')

    def on_line_motion(self, event):
        if self.start is None:
            return
        self.canvas.delete("preview_line")
        x0, y0 = self.start
        self.canvas.create_line(x0 * CELL_SIZE, y0 * CELL_SIZE, event.x, event.y, fill="gray", dash=(2, 2),
                                tags="preview_line")

    def click(self, event):
        x = event.x // CELL_SIZE
        y = event.y // CELL_SIZE
        if self.start is None:
            self.start = (x, y)
        else:
            x0, y0 = self.start
            x1, y1 = x, y
            self.lines.append((x0, y0, x1, y1))
            self.start = None

            self.debug_table.delete(1.0, tk.END)

            if self.algorithm.get() == 'dda':
                dda(self.canvas, x0, y0, x1, y1, self.debug_mode.get(), self.debug_table)
            elif self.algorithm.get() == 'bresenham':
                bresenham(self.canvas, x0, y0, x1, y1, self.debug_mode.get(), self.debug_table)
            elif self.algorithm.get() == 'wu':
                wu(self.canvas, x0, y0, x1, y1, self.debug_mode.get(), self.debug_table)

    def redraw_lines(self):
        self.canvas.delete("all")
        if self.debug_mode.get():
            draw_grid(self.canvas)

        for x0, y0, x1, y1 in self.lines:
            if self.algorithm.get() == 'dda':
                dda(self.canvas, x0, y0, x1, y1, False, None)
            elif self.algorithm.get() == 'bresenham':
                bresenham(self.canvas, x0, y0, x1, y1, False, None)
            elif self.algorithm.get() == 'wu':
                wu(self.canvas, x0, y0, x1, y1, False, None)

    def clear(self):
        self.canvas.delete("all")
        self.lines = []
        self.start = None
        if self.debug_mode.get():
            draw_grid(self.canvas)
        self.debug_table.delete(1.0, tk.END)


if __name__ == "__main__":
    root = tk.Tk()
    app = LineDrawer(root)
    root.mainloop()

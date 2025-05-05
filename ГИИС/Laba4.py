import tkinter as tk
from tkinter import ttk, filedialog
import numpy as np
from math import cos, sin, radians


class ThreeDEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("3D Geometry Editor")
        self.root.bind("<Key>", self.on_key_press)

        # Инициализация параметров трансформации
        self.translation = np.array([0.0, 0.0, 0.0])
        self.rotation = np.array([0.0, 0.0, 0.0])  # Углы в градусах
        self.scale = 1.0
        self.zoom = 1.0

        self.vertices = np.empty((0, 4))
        self.original_vertices = self.vertices.copy()
        self.edges = []
        self.projection = 'orthographic'

        self.create_widgets()
        self.update_3d_view()

    def create_widgets(self):
        self.canvas = tk.Canvas(self.root, width=600, height=600, bg='white')
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        control_frame = ttk.Frame(self.root, padding=10)
        control_frame.pack(side=tk.RIGHT, fill=tk.Y)

        # Панель загрузки
        ttk.Label(control_frame, text="Загрузка").pack(pady=(0, 5))
        ttk.Button(control_frame, text="Загрузить файл", command=self.load_from_file).pack(fill=tk.X)

        # Панель проекции
        ttk.Label(control_frame, text="Проекция").pack(pady=(10, 0))
        ttk.Button(control_frame, text="Перспектива", command=lambda: self.set_projection('perspective')).pack(
            fill=tk.X)
        ttk.Button(control_frame, text="Ортографическая", command=lambda: self.set_projection('orthographic')).pack(
            fill=tk.X)

        # Панель перемещения
        ttk.Label(control_frame, text="Перемещение").pack(pady=(10, 0))
        self.tx = ttk.Scale(control_frame, from_=-100, to=100, orient=tk.HORIZONTAL,
                            command=lambda v: self.set_translation(float(v) / 50, 0, 0))
        self.tx.pack(fill=tk.X)
        self.ty = ttk.Scale(control_frame, from_=-100, to=100, orient=tk.HORIZONTAL,
                            command=lambda v: self.set_translation(0, float(v) / 50, 0))
        self.ty.pack(fill=tk.X)
        self.tz = ttk.Scale(control_frame, from_=-100, to=100, orient=tk.HORIZONTAL,
                            command=lambda v: self.set_translation(0, 0, float(v) / 50))
        self.tz.pack(fill=tk.X)

        # Панель вращения
        ttk.Label(control_frame, text="Поворот").pack(pady=(10, 0))
        self.rx = ttk.Scale(control_frame, from_=0, to=360, orient=tk.HORIZONTAL,
                            command=lambda v: self.set_rotation('x', float(v)))
        self.rx.pack(fill=tk.X)
        self.ry = ttk.Scale(control_frame, from_=0, to=360, orient=tk.HORIZONTAL,
                            command=lambda v: self.set_rotation('y', float(v)))
        self.ry.pack(fill=tk.X)
        self.rz = ttk.Scale(control_frame, from_=0, to=360, orient=tk.HORIZONTAL,
                            command=lambda v: self.set_rotation('z', float(v)))
        self.rz.pack(fill=tk.X)

        # Панель масштабирования
        ttk.Label(control_frame, text="Масштаб").pack(pady=(10, 0))
        self.scale_slider = ttk.Scale(control_frame, from_=10, to=200, orient=tk.HORIZONTAL,
                                      command=lambda v: self.set_scale(float(v) / 100))
        self.scale_slider.set(100)
        self.scale_slider.pack(fill=tk.X)

        # Кнопка сброса
        ttk.Button(control_frame, text="Сброс", command=self.reset).pack(pady=(20, 0))

    def load_from_file(self):
        file_path = filedialog.askopenfilename()
        if not file_path:
            return

        with open(file_path, 'r') as f:
            verts = []
            edges = []
            for line in f:
                parts = line.strip().split()
                if not parts:
                    continue
                if parts[0] == 'v' and len(parts) == 4:
                    verts.append([float(parts[1]), float(parts[2]), float(parts[3]), 1])
                elif parts[0] == 'e' and len(parts) == 3:
                    edges.append((int(parts[1]), int(parts[2])))

            self.vertices = np.array(verts)
            self.original_vertices = self.vertices.copy()
            self.edges = edges
            self.reset_transforms()
            self.update_3d_view()

    def get_transformation_matrix(self):
        """Собираем итоговую матрицу трансформации"""
        # Матрица перемещения
        translate_mat = np.array([
            [1, 0, 0, self.translation[0]],
            [0, 1, 0, self.translation[1]],
            [0, 0, 1, self.translation[2]],
            [0, 0, 0, 1]
        ])

        # Матрицы вращения
        rx = radians(self.rotation[0])
        ry = radians(self.rotation[1])
        rz = radians(self.rotation[2])

        rot_x = np.array([
            [1, 0, 0, 0],
            [0, cos(rx), -sin(rx), 0],
            [0, sin(rx), cos(rx), 0],
            [0, 0, 0, 1]
        ])

        rot_y = np.array([
            [cos(ry), 0, sin(ry), 0],
            [0, 1, 0, 0],
            [-sin(ry), 0, cos(ry), 0],
            [0, 0, 0, 1]
        ])

        rot_z = np.array([
            [cos(rz), -sin(rz), 0, 0],
            [sin(rz), cos(rz), 0, 0],
            [0, 0, 1, 0],
            [0, 0, 0, 1]
        ])

        # Матрица масштабирования
        scale_mat = np.array([
            [self.scale * self.zoom, 0, 0, 0],
            [0, self.scale * self.zoom, 0, 0],
            [0, 0, self.scale * self.zoom, 0],
            [0, 0, 0, 1]
        ])

        # Порядок преобразований: масштаб -> вращение -> перемещение
        return translate_mat @ rot_z @ rot_y @ rot_x @ scale_mat

    def update_3d_view(self):
        self.canvas.delete("all")
        if self.vertices.size == 0:
            return

        # Применяем преобразования
        transform_matrix = self.get_transformation_matrix()
        transformed = self.vertices @ transform_matrix.T

        # Проекция
        if self.projection == 'perspective':
            projected = self.perspective_project(transformed)
        else:
            projected = transformed[:, :2]

        # Масштабирование для отображения
        display_scale = 50  # Фиксированный коэффициент визуализации
        scaled = projected * display_scale

        # Центрирование
        centered = scaled + np.array([300, 300])

        # Отрисовка ребер
        for edge in self.edges:
            if edge[0] >= len(centered) or edge[1] >= len(centered):
                continue
            x1, y1 = centered[edge[0]]
            x2, y2 = centered[edge[1]]
            self.canvas.create_line(x1, y1, x2, y2, fill='black', width=2)

        # Отрисовка вершин
        for x, y in centered:
            self.canvas.create_oval(x - 3, y - 3, x + 3, y + 3, fill='red')

    def perspective_project(self, vertices):
        result = []
        for v in vertices:
            x, y, z, w = v
            z = z + 5  # Смещение для избежания деления на 0
            if z != 0:
                result.append([x / z, y / z])
            else:
                result.append([x, y])
        return np.array(result)

    def set_translation(self, dx, dy, dz):
        self.translation = np.array([dx, dy, dz])
        self.update_3d_view()

    def set_rotation(self, axis, angle):
        if axis == 'x':
            self.rotation[0] = angle
        elif axis == 'y':
            self.rotation[1] = angle
        elif axis == 'z':
            self.rotation[2] = angle
        self.update_3d_view()

    def set_scale(self, scale):
        self.scale = max(0.1, min(2.0, scale))
        self.update_3d_view()

    def set_projection(self, proj):
        self.projection = proj
        self.update_3d_view()

    def reset_transforms(self):
        self.translation = np.array([0.0, 0.0, 0.0])
        self.rotation = np.array([0.0, 0.0, 0.0])
        self.scale = 1.0
        self.zoom = 1.0
        self.tx.set(0)
        self.ty.set(0)
        self.tz.set(0)
        self.rx.set(0)
        self.ry.set(0)
        self.rz.set(0)
        self.scale_slider.set(100)

    def reset(self):
        self.reset_transforms()
        self.update_3d_view()

    def on_key_press(self, event):
        key = event.keysym.lower()
        if key == 'w':
            self.set_translation(self.translation[0], self.translation[1] + 0.1, self.translation[2])
        elif key == 's':
            self.set_translation(self.translation[0], self.translation[1] - 0.1, self.translation[2])
        elif key == 'a':
            self.set_translation(self.translation[0] - 0.1, self.translation[1], self.translation[2])
        elif key == 'd':
            self.set_translation(self.translation[0] + 0.1, self.translation[1], self.translation[2])
        elif key == 'q':
            self.set_rotation('y', (self.rotation[1] - 5) % 360)
        elif key == 'e':
            self.set_rotation('y', (self.rotation[1] + 5) % 360)
        elif key == 'r':
            self.set_scale(min(self.scale * 1.1, 2.0))
        elif key == 'f':
            self.set_scale(max(self.scale * 0.9, 0.1))


if __name__ == "__main__":
    root = tk.Tk()
    app = ThreeDEditor(root)
    root.mainloop()
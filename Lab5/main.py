import tkinter as tk
from tkinter import Menu, messagebox
import numpy as np


class LineEditor:
    def __init__(self, canvas):
        self.canvas = canvas
        self.lines = []
        self.drawing_mode = "CDA"

    def set_cda_mode(self):
        self.drawing_mode = "CDA"
        print("Выбран алгоритм ЦДА")

    def set_bresenham_mode(self):
        self.drawing_mode = "Bresenham"
        print("Выбран алгоритм Брезенхема")

    def set_wu_mode(self):
        self.drawing_mode = "Wu"
        print("Выбран алгоритм Ву")

    def draw_line_cda(self, x1, y1, x2, y2, color="black"):
        dx = x2 - x1
        dy = y2 - y1
        steps = max(abs(dx), abs(dy))
        x_inc = dx / steps
        y_inc = dy / steps
        x, y = x1, y1
        for _ in range(steps + 1):
            self.canvas.create_line(round(x), round(y), round(x) + 1, round(y) + 1, fill=color)
            x += x_inc
            y += y_inc

    def draw_line_bresenham(self, x1, y1, x2, y2, color="black"):
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        while True:
            self.canvas.create_line(x1, y1, x1 + 1, y1 + 1, fill=color)
            if x1 == x2 and y1 == y2:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy

    def draw_line_wu(self, x1, y1, x2, y2, color="black"):
        def plot(x, y, c):
            self.canvas.create_line(x, y, x + 1, y + 1, fill=self._color_from_intensity(c))

        def fpart(x):
            return x - int(x)

        def rfpart(x):
            return 1 - fpart(x)

        steep = abs(y2 - y1) > abs(x2 - x1)
        if steep:
            x1, y1 = y1, x1
            x2, y2 = y2, x2
        if x1 > x2:
            x1, x2 = x2, x1
            y1, y2 = y2, y1
        dx = x2 - x1
        dy = y2 - y1
        if dx == 0:
            gradient = 1
        else:
            gradient = dy / dx
        x_end = round(x1)
        y_end = y1 + gradient * (x_end - x1)
        x_gap = rfpart(x1 + 0.5)
        xpxl1 = x_end
        ypxl1 = int(y_end)
        if steep:
            plot(ypxl1, xpxl1, rfpart(y_end) * x_gap)
            plot(ypxl1 + 1, xpxl1, fpart(y_end) * x_gap)
        else:
            plot(xpxl1, ypxl1, rfpart(y_end) * x_gap)
            plot(xpxl1, ypxl1 + 1, fpart(y_end) * x_gap)
        intery = y_end + gradient
        x_end = round(x2)
        y_end = y2 + gradient * (x_end - x2)
        x_gap = fpart(x2 + 0.5)
        xpxl2 = x_end
        ypxl2 = int(y_end)
        if steep:
            plot(ypxl2, xpxl2, rfpart(y_end) * x_gap)
            plot(ypxl2 + 1, xpxl2, fpart(y_end) * x_gap)
        else:
            plot(xpxl2, ypxl2, rfpart(y_end) * x_gap)
            plot(xpxl2, ypxl2 + 1, fpart(y_end) * x_gap)
        for x in range(xpxl1 + 1, xpxl2):
            if steep:
                plot(int(intery), x, rfpart(intery))
                plot(int(intery) + 1, x, fpart(intery))
            else:
                plot(x, int(intery), rfpart(intery))
                plot(x, int(intery) + 1, fpart(intery))
            intery += gradient

    def _color_from_intensity(self, intensity):
        grayscale = int(255 * intensity)
        grayscale = max(0, min(255, grayscale))
        return f"#{grayscale:02x}{grayscale:02x}{grayscale:02x}"


class PolygonEditor(LineEditor):
    def __init__(self, root):
        self.root = root
        self.root.title("Графический редактор полигонов")
        self.canvas = tk.Canvas(self.root, width=800, height=600, bg="white")
        self.canvas.pack()

        super().__init__(self.canvas)

        self.points = []
        self.polygon = None
        self.normals = []
        self.intersect_point = None
        self.intersect_line = None
        self.debug_mode = False

        self.create_menu()
        self.create_toolbar()
        self.canvas.bind("<Button-1>", self.add_point)
        self.canvas.bind("<Button-3>", self.delete_point)

    def create_menu(self):
        menu = Menu(self.root)
        self.root.config(menu=menu)

        line_menu = Menu(menu, tearoff=0)
        line_menu.add_command(label="Алгоритм ЦДА", command=self.set_cda_mode)
        line_menu.add_command(label="Алгоритм Брезенхема", command=self.set_bresenham_mode)
        line_menu.add_command(label="Алгоритм Ву", command=self.set_wu_mode)

        menu.add_cascade(label="Отрезки", menu=line_menu)

        polygon_menu = Menu(menu, tearoff=0)
        polygon_menu.add_command(label="Проверить выпуклость", command=self.check_convexity)
        polygon_menu.add_command(label="Выпуклая оболочка (Грэхем)", command=self.convex_hull_graham)
        polygon_menu.add_command(label="Выпуклая оболочка (Джарвис)", command=self.convex_hull_jarvis)
        polygon_menu.add_command(label="Принадлежность точки полигону", command=self.check_point_inside)
        menu.add_cascade(label="Построение полигонов", menu=polygon_menu)

        intersect_menu = Menu(menu, tearoff=0)
        intersect_menu.add_command(label="Найти точку пересечения", command=self.find_intersection)
        menu.add_cascade(label="Отрезки и полигоны", menu=intersect_menu)

    def create_toolbar(self):
        toolbar = tk.Frame(self.root, bg="lightgrey")
        toolbar.pack(side=tk.TOP, fill=tk.X)

        self.clear_btn = tk.Button(toolbar, text="Очистить", command=self.clear_canvas)
        self.clear_btn.pack(side=tk.LEFT, padx=2, pady=2)

    def add_point(self, event):
        x, y = event.x, event.y
        self.points.append((x, y))
        self.canvas.create_oval(x - 2, y - 2, x + 2, y + 2, fill="black")
        if len(self.points) > 1:
            self.canvas.create_line(self.points[-2], self.points[-1], fill="black")

    def delete_point(self, event):
        if self.points:
            self.points.pop()
            self.canvas.delete("all")
            if self.debug_mode:
                self.draw_grid()
            for i in range(len(self.points) - 1):
                self.canvas.create_line(self.points[i], self.points[i + 1], fill="black")
            if len(self.points) > 0:
                self.canvas.create_oval(self.points[-1][0] - 2, self.points[-1][1] - 2, self.points[-1][0] + 2,
                                        self.points[-1][1] + 2, fill="black")
            for line, mode in self.lines:
                x1, y1, x2, y2 = line
                if mode == "CDA":
                    self.draw_line_cda(x1, y1, x2, y2)
                elif mode == "Bresenham":
                    self.draw_line_bresenham(x1, y1, x2, y2)
                elif mode == "Wu":
                    self.draw_line_wu(x1, y1, x2, y2)

    def get_internal_normals(self):
        if len(self.points) < 3:
            messagebox.showerror("Ошибка", "Недостаточно точек для полигона")
            return []

        normals = []
        n = len(self.points)
        for i in range(n):
            p1, p2 = self.points[i], self.points[(i + 1) % n]
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            normals.append((-dy, dx))  # Вектор нормали
        return normals

    def draw_normals(self, normals):
        if not normals:
            return
        for i, p in enumerate(self.points):
            normal = normals[i]
            center_x = (self.points[i][0] + self.points[(i + 1) % len(self.points)][0]) / 2
            center_y = (self.points[i][1] + self.points[(i + 1) % len(self.points)][1]) / 2

            self.canvas.create_line(center_x, center_y, center_x + normal[0] * 20, center_y + normal[1] * 20,
                                    fill="green", width=1)

    def check_convexity(self):
        if len(self.points) < 3:
            messagebox.showerror("Ошибка", "Недостаточно точек для полигона")
            return

        def cross_product(o, a, b):
            return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

        signs = []
        n = len(self.points)
        for i in range(n):
            o, a, b = self.points[i], self.points[(i + 1) % n], self.points[(i + 2) % n]
            signs.append(np.sign(cross_product(o, a, b)))

        if all(s >= 0 for s in signs) or all(s <= 0 for s in signs):
            messagebox.showinfo("Результат", "Полигон выпуклый")
            normals = self.get_internal_normals()
            self.draw_normals(normals)
        else:
            messagebox.showinfo("Результат", "Полигон невыпуклый")

    def convex_hull_graham(self):
        if len(self.points) < 3:
            messagebox.showerror("Ошибка", "Недостаточно точек для построения выпуклой оболочки")
            return
        points = sorted(self.points, key=lambda p: (p[0], p[1]))

        def cross(o, a, b):
            return (a[0] - o[0]) * (b[1] - o[1]) - (a[1] - o[1]) * (b[0] - o[0])

        lower = []
        for p in points:
            while len(lower) >= 2 and cross(lower[-2], lower[-1], p) <= 0:
                lower.pop()
            lower.append(p)
        upper = []
        for p in reversed(points):
            while len(upper) >= 2 and cross(upper[-2], upper[-1], p) <= 0:
                upper.pop()
            upper.append(p)
        hull = lower[:-1] + upper[:-1]
        self.draw_polygon(hull, "blue")

    def convex_hull_jarvis(self):
        if len(self.points) < 3:
            messagebox.showerror("Ошибка", "Недостаточно точек для построения выпуклой оболочки")
            return

        def orientation(p, q, r):
            return (q[1] - p[1]) * (r[0] - q[0]) - (q[0] - p[0]) * (r[1] - q[1])

        hull = []
        leftmost = min(self.points, key=lambda p: p[0])
        p = leftmost
        while True:
            hull.append(p)
            q = self.points[0]
            for r in self.points:
                if q == p or orientation(p, q, r) < 0:
                    q = r
            p = q
            if p == leftmost:
                break
        self.draw_polygon(hull, "red")

    def is_point_inside(self, x, y):
        if len(self.points) < 3:
            return False

        n = len(self.points)
        inside = False

        for i in range(n):
            p1 = self.points[i]
            p2 = self.points[(i + 1) % n]

            # Проверяем, лежит ли точка на текущем ребре
            if self.point_on_segment((x, y), p1, p2):
                return True  # Считаем точки на границе как внутри

            # Проверяем пересечение луча с ребром
            if (p1[1] > y) != (p2[1] > y):
                try:
                    x_inters = ((y - p1[1]) * (p2[0] - p1[0])) / (p2[1] - p1[1]) + p1[0]
                except ZeroDivisionError:
                    continue  # Горизонтальное ребро, пропускаем

                if x <= x_inters:
                    inside = not inside

        return inside

    def point_on_segment(self, pt, p1, p2):
        x, y = pt
        x1, y1 = p1
        x2, y2 = p2

        # Проверка нахождения в ограничивающем прямоугольнике
        if (x < min(x1, x2) - 1e-8 or x > max(x1, x2) + 1e-8 or
                y < min(y1, y2) - 1e-8 or y > max(y1, y2) + 1e-8):
            return False

        # Проверка коллинеарности
        cross_product = (x - x1) * (y2 - y1) - (y - y1) * (x2 - x1)
        if abs(cross_product) > 1e-8:
            return False

        return True

    def check_point_inside(self):
        if not self.points:
            messagebox.showerror("Ошибка", "Необходимо создать полигон.")
            return

        def on_click(event):
            x, y = event.x, event.y
            if self.is_point_inside(x, y):
                messagebox.showinfo("Результат", f"Точка ({x}, {y}) находится внутри полигона.")
            else:
                messagebox.showinfo("Результат", f"Точка ({x}, {y}) находится вне полигона.")
            self.canvas.unbind("<Button-1>")  # Отключаем обработчик кликов
            self.canvas.bind("<Button-1>", self.add_point)

        self.canvas.bind("<Button-1>", on_click)
        messagebox.showinfo("Подсказка", "Теперь нажмите на любую точку чтобы проверить ее принадлежность полигону")

    def find_intersection(self):
        if len(self.points) < 3:
            messagebox.showerror("Ошибка", "Недостаточно точек для полигона")
            return

        if self.intersect_line:
            self.canvas.delete(self.intersect_line)
            self.intersect_line = None

        def on_first_click(event):
            self.intersect_point = (event.x, event.y)
            self.canvas.unbind("<Button-1>")
            self.canvas.bind("<Button-1>", on_second_click)
            messagebox.showinfo("Подсказка", "Теперь нажмите на вторую точку чтобы получить отрезок")

        def on_second_click(event):
            x1, y1 = self.intersect_point
            x2, y2 = event.x, event.y

            if self.drawing_mode == "CDA":
                self.draw_line_cda(x1, y1, x2, y2, "blue")
            elif self.drawing_mode == "Bresenham":
                self.draw_line_bresenham(x1, y1, x2, y2, "blue")
            elif self.drawing_mode == "Wu":
                self.draw_line_wu(x1, y1, x2, y2, "blue")

            self.canvas.unbind("<Button-1>")
            self.canvas.bind("<Button-1>", self.add_point)

            def calculate_intersection(p1, p2, poly):
                intersection_points = []
                x1, y1 = p1
                x2, y2 = p2
                for i in range(len(poly)):
                    x3, y3 = poly[i]
                    x4, y4 = poly[(i + 1) % len(poly)]

                    d = (x1 - x2) * (y3 - y4) - (y1 - y2) * (x3 - x4)
                    if d == 0:
                        continue

                    t = ((x1 - x3) * (y3 - y4) - (y1 - y3) * (x3 - x4)) / d
                    u = ((x1 - x3) * (y1 - y2) - (y1 - y3) * (x1 - x2)) / d
                    if 0 <= t <= 1 and 0 <= u <= 1:
                        x = x1 + t * (x2 - x1)
                        y = y1 + t * (y2 - y1)
                        intersection_points.append((x, y))
                return intersection_points

            intersections = calculate_intersection((x1, y1), (x2, y2), self.points)
            if intersections:
                for intersection in intersections:
                    x, y = intersection
                    self.canvas.create_oval(x - 2, y - 2, x + 2, y + 2, fill="red", tags="intersect")
                messagebox.showinfo("Результат",
                                    f"Точки пересечения: {[f'({x:.2f}, {y:.2f})' for x, y in intersections]}")
            else:
                messagebox.showinfo("Результат", "Пересечение не найдено")
            self.intersect_line = self.canvas.create_line(x1, y1, x2, y2, fill="blue")

        self.canvas.bind("<Button-1>", on_first_click)
        messagebox.showinfo("Подсказка", "Нажмите на первую точку отрезка")

    def draw_polygon(self, points, color):
        self.canvas.delete("polygon")
        for i in range(len(points)):
            self.canvas.create_line(points[i], points[(i + 1) % len(points)], fill=color, tags="polygon")

    def clear_canvas(self):
        self.canvas.delete("all")
        self.points.clear()
        self.polygon = None
        self.normals = []
        self.intersect_point = None
        self.intersect_line = None


if __name__ == "__main__":
    root = tk.Tk()
    app = PolygonEditor(root)
    root.mainloop()
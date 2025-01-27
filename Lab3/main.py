import tkinter as tk
import math
from math import pow


def create_matrix(rows, cols, data):
    """Создает матрицу размером rows x cols, заполняя ее данными из data."""
    return [data[i * cols:(i + 1) * cols] for i in range(rows)]


def matrix_mult(a, b):
    """Умножение двух матриц."""
    rows_a, cols_a = len(a), len(a[0])
    rows_b, cols_b = len(b), len(b[0])

    if cols_a != rows_b:
        raise ValueError("Матрицы нельзя перемножить")

    result = create_matrix(rows_a, cols_b, [0] * (rows_a * cols_b))
    for i in range(rows_a):
        for j in range(cols_b):
            for k in range(cols_a):
                result[i][j] += a[i][k] * b[k][j]
    return result


def my_linspace(start, stop, num):
    """Генерация num равномерно распределенных значений от start до stop."""
    step = (stop - start) / (num - 1)
    return [start + i * step for i in range(num)]


class Point:
    def __init__(self, x, y):
        self.x = x
        self.y = y


class ControlPoint:
    def __init__(self, x, y, radius=5, color="red"):
        self.x = x
        self.y = y
        self.radius = radius
        self.color = color
        self.oval = None  # id созданного объекта на канве

    def draw(self, canvas):
        x1, y1 = self.x - self.radius, self.y - self.radius
        x2, y2 = self.x + self.radius, self.y + self.radius
        if self.oval:
            canvas.coords(self.oval, x1, y1, x2, y2)
        else:
            self.oval = canvas.create_oval(x1, y1, x2, y2, fill=self.color)


class CurveEditor(tk.Tk):
    def __init__(self):
        super().__init__()

        self.title("Графический редактор кривых")
        self.geometry("1000x700")

        self.points = []  # Теперь список объектов ControlPoint
        self.current_curve_type = "Эрмит"
        self.curve_lines = []
        self.selected_point = None
        self.is_dragging = False
        self.point_limit_reached = False  # Добавляем флаг ограничения

        self.create_menu()
        self.create_canvas()

    def create_menu(self):
        menubar = tk.Menu(self)
        filemenu = tk.Menu(menubar, tearoff=0)
        filemenu.add_command(label="Очистить", command=self.clear_canvas)
        menubar.add_cascade(label="Файл", menu=filemenu)

        curvemenu = tk.Menu(menubar, tearoff=0)
        curvemenu.add_command(label="Эрмит", command=lambda: self.set_curve_type("Эрмит"))
        curvemenu.add_command(label="Безье", command=lambda: self.set_curve_type("Безье"))
        curvemenu.add_command(label="B-сплайн", command=lambda: self.set_curve_type("B-сплайн"))
        menubar.add_cascade(label="Кривые", menu=curvemenu)
        self.config(menu=menubar)

    def create_canvas(self):
        self.canvas = tk.Canvas(self, bg="white")
        self.canvas.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        self.canvas.bind("<Button-1>", self.on_canvas_click)
        self.canvas.bind("<B1-Motion>", self.on_canvas_drag)
        self.canvas.bind("<ButtonRelease-1>", self.on_canvas_release)

    def set_curve_type(self, curve_type):
        self.current_curve_type = curve_type
        print(f"Выбран тип кривой: {curve_type}")
        self.point_limit_reached = False  # Сбрасываем флаг при смене типа кривой

    def clear_canvas(self):
        self.points = []
        self.canvas.delete("all")
        self.curve_lines = []
        self.selected_point = None
        self.point_limit_reached = False  # Сбрасываем флаг при очистке
        print("Очистка полотна")

    def on_canvas_click(self, event):
        x, y = event.x, event.y

        if self.current_curve_type in ("Эрмит", "Безье") and len(self.points) >= 4:
            self.point_limit_reached = True  # Устанавливаем флаг, что больше точек не надо

        if self.point_limit_reached:
            # Для Безье и Эрмита больше 4 точек не добавится
            clicked_point = self.find_point_near(x, y)
            if clicked_point:
                self.selected_point = clicked_point
                self.is_dragging = True
            else:
                self.selected_point = None
        else:
            clicked_point = self.find_point_near(x, y)
            if clicked_point:
                self.selected_point = clicked_point
                self.is_dragging = True
            else:
                self.selected_point = None
                point = ControlPoint(x, y)
                self.points.append(point)
                point.draw(self.canvas)

                if len(self.points) > 1:
                    self.draw_curve()

    def on_canvas_drag(self, event):
        if self.selected_point and self.is_dragging:
            self.selected_point.x = event.x
            self.selected_point.y = event.y
            self.selected_point.draw(self.canvas)
            self.draw_curve()

    def on_canvas_release(self, event):
        self.is_dragging = False
        self.selected_point = None

    def find_point_near(self, x, y, threshold=10):
        for point in self.points:
            distance = math.sqrt((x - point.x) ** 2 + (y - point.y) ** 2)
            if distance < threshold:
                return point
        return None

    def draw_curve(self):
        # Очищаем предыдущие линии кривых
        for line in self.curve_lines:
            self.canvas.delete(line)
        self.curve_lines = []

        if self.current_curve_type == "Эрмит":
            if len(self.points) >= 4:
                self.draw_hermite_curve()
        elif self.current_curve_type == "Безье":
            if len(self.points) >= 4:  # Теперь нужно 4 точки
                self.draw_bezier_curve()
        elif self.current_curve_type == "B-сплайн":
            if len(self.points) >= 2:
                self.draw_bspline_curve()

    def draw_hermite_curve(self):
        """Рисует кривую Эрмита для последних четырех точек."""
        if len(self.points) < 4:
            return

        p0 = [self.points[-4].x, self.points[-4].y]
        p1 = [self.points[-3].x, self.points[-3].y]
        r0 = [self.points[-2].x - p0[0], self.points[-2].y - p0[1]]
        r1 = [self.points[-1].x - p1[0], self.points[-1].y - p1[1]]

        t = my_linspace(0, 1, 100)

        # Матрица Эрмита
        m_hermite = create_matrix(4, 4, [
            2, -2, 1, 1,
            -3, 3, -2, -1,
            0, 0, 1, 0,
            1, 0, 0, 0
        ])

        # Формирование матрицы параметров t
        t_vector_data = [[pow(val, 3), pow(val, 2), val, 1] for val in t]

        # Вычисление значений кривой
        hermite_x = matrix_mult(m_hermite, create_matrix(4, 1, [p0[0], p1[0], r0[0], r1[0]]))
        hermite_y = matrix_mult(m_hermite, create_matrix(4, 1, [p0[1], p1[1], r0[1], r1[1]]))

        curve_x = [sum(ti[j] * hermite_x[j][0] for j in range(4)) for ti in t_vector_data]
        curve_y = [sum(ti[j] * hermite_y[j][0] for j in range(4)) for ti in t_vector_data]

        # Рисование кривой
        for i in range(len(curve_x) - 1):
            x1, y1 = curve_x[i], curve_y[i]
            x2, y2 = curve_x[i + 1], curve_y[i + 1]
            line = self.canvas.create_line(x1, y1, x2, y2, fill="blue")
            self.curve_lines.append(line)

    def draw_bezier_curve(self):
        """Рисует кривую Безье для последних четырех точек."""
        if len(self.points) < 4:
            return

        p0 = [self.points[-4].x, self.points[-4].y]
        p3 = [self.points[-3].x, self.points[-3].y]
        p1 = [self.points[-2].x, self.points[-2].y]
        p2 = [self.points[-1].x, self.points[-1].y]

        t = my_linspace(0, 1, 100)

        m_bezier = create_matrix(4, 4, [
            -1, 3, -3, 1,
            3, -6, 3, 0,
            -3, 3, 0, 0,
            1, 0, 0, 0
        ])

        t_vector_data = [[pow(val, 3), pow(val, 2), val, 1] for val in t]

        bezier_x = matrix_mult(m_bezier, create_matrix(4, 1, [p0[0], p1[0], p2[0], p3[0]]))
        bezier_y = matrix_mult(m_bezier, create_matrix(4, 1, [p0[1], p1[1], p2[1], p3[1]]))

        curve_x = [sum(ti[j] * bezier_x[j][0] for j in range(4)) for ti in t_vector_data]
        curve_y = [sum(ti[j] * bezier_y[j][0] for j in range(4)) for ti in t_vector_data]

        for i in range(len(curve_x) - 1):
            x1, y1 = curve_x[i], curve_y[i]
            x2, y2 = curve_x[i + 1], curve_y[i + 1]
            line = self.canvas.create_line(x1, y1, x2, y2, fill="green")
            self.curve_lines.append(line)

    def draw_bspline_curve(self):
        if len(self.points) < 2:
            return

        points = [[point.x, point.y] for point in self.points]
        n = len(points) - 1

        if len(points) >= 3:
            extended_points = points + [points[0], points[1], points[2]]
        else:
            extended_points = points

        all_curve_segments = []
        for i in range(len(extended_points) - 3):
            p0 = extended_points[i]
            p1 = extended_points[i + 1]
            p2 = extended_points[i + 2]
            p3 = extended_points[i + 3]

            t = my_linspace(0, 1, 100)

            m_bspline = create_matrix(4, 4, [
                -1 / 6, 3 / 6, -3 / 6, 1 / 6,
                3 / 6, -6 / 6, 3 / 6, 0,
                -3 / 6, 0, 3 / 6, 0,
                1 / 6, 4 / 6, 1 / 6, 0
            ])

            t_vector_data = [[pow(val, 3), pow(val, 2), val, 1] for val in t]

            bspline_x = matrix_mult(m_bspline, create_matrix(4, 1, [p0[0], p1[0], p2[0], p3[0]]))
            bspline_y = matrix_mult(m_bspline, create_matrix(4, 1, [p0[1], p1[1], p2[1], p3[1]]))

            curve_x = [sum(ti[j] * bspline_x[j][0] for j in range(4)) for ti in t_vector_data]
            curve_y = [sum(ti[j] * bspline_y[j][0] for j in range(4)) for ti in t_vector_data]

            all_curve_segments.append(list(zip(curve_x, curve_y)))

        for curve in all_curve_segments:
            for i in range(len(curve) - 1):
                x1, y1 = curve[i][0], curve[i][1]
                x2, y2 = curve[i + 1][0], curve[i + 1][1]
                line = self.canvas.create_line(x1, y1, x2, y2, fill="magenta")
                self.curve_lines.append(line)


if __name__ == "__main__":
    app = CurveEditor()
    app.mainloop()
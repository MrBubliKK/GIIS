import tkinter as tk
from tkinter import ttk
import math


class GraphicEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Элементарный графический редактор")

        # Создание Canvas для рисования
        self.canvas = tk.Canvas(self.root, bg="white", width=800, height=600)
        self.canvas.pack(fill=tk.BOTH, expand=True)

        # Переменные
        self.current_shape = tk.StringVar(value="Circle")
        self.start_x = None
        self.start_y = None
        self.shapes = []  # Список для хранения нарисованных фигур (хранит id фигур canvas)
        self.debug_mode = False  # Переменная для отслеживания состояния отладки
        self.grid_lines = []  # Список для хранения линий сетки

        # Создание меню
        self.create_menu()

        # Панель инструментов
        self.create_toolbar()

        # Привязка событий
        self.canvas.bind("<Button-1>", self.start_drawing)
        self.canvas.bind("<B1-Motion>", self.draw_shape)
        self.canvas.bind("<ButtonRelease-1>", self.finish_drawing)

    def create_menu(self):
        menu_bar = tk.Menu(self.root)
        shape_menu = tk.Menu(menu_bar, tearoff=0)

        for shape in ["Circle", "Ellipse", "Hyperbola", "Parabola"]:
            shape_menu.add_radiobutton(label=shape, variable=self.current_shape, value=shape)

        menu_bar.add_cascade(label="Линии второго порядка", menu=shape_menu)
        self.root.config(menu=menu_bar)

    def create_toolbar(self):
        toolbar = ttk.Frame(self.root, relief=tk.RAISED)
        toolbar.pack(side=tk.TOP, fill=tk.X)

        self.debug_button = ttk.Button(toolbar, text="Включить отладку", command=self.toggle_debug_mode)
        self.debug_button.pack(side=tk.LEFT, padx=5)

    def start_drawing(self, event):
        self.start_x = event.x
        self.start_y = event.y

    def draw_shape(self, event):
        self.canvas.delete("preview")
        if self.start_x is None or self.start_y is None:
            return

        shape = self.current_shape.get()
        x0, y0 = self.start_x, self.start_y
        x1, y1 = event.x, event.y

        if shape == "Circle":
            radius = math.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2)
            self.canvas.create_oval(x0 - radius, y0 - radius, x0 + radius, y0 + radius,
                                    outline="black", tags="preview")

        elif shape == "Ellipse":
            self.canvas.create_oval(x0, y0, x1, y1, outline="black", tags="preview")

        elif shape == "Hyperbola":
            self.draw_hyperbola(x0, y0, x1, y1, preview=True)

        elif shape == "Parabola":
            self.draw_parabola(x0, y0, x1, y1, preview=True)

    def finish_drawing(self, event):
        self.canvas.delete("preview")
        if self.start_x is None or self.start_y is None:
            return

        shape = self.current_shape.get()
        x0, y0 = self.start_x, self.start_y
        x1, y1 = event.x, event.y

        shape_ids = []
        if shape == "Circle":
            radius = math.sqrt((x1 - x0) ** 2 + (y1 - y0) ** 2)
            shape_ids.append(self.canvas.create_oval(x0 - radius, y0 - radius, x0 + radius, y0 + radius,
                                                     outline="black"))

        elif shape == "Ellipse":
            shape_ids.append(self.canvas.create_oval(x0, y0, x1, y1, outline="black"))

        elif shape == "Hyperbola":
            shape_ids = self.draw_hyperbola(x0, y0, x1, y1, preview=False)

        elif shape == "Parabola":
            shape_ids = self.draw_parabola(x0, y0, x1, y1, preview=False)

        self.shapes.append(
            {"shape_ids": shape_ids, "type": shape, "coords": [self.canvas.coords(shape_id) for shape_id in shape_ids]})

        if self.debug_mode:
            self.print_shapes_coordinates()

    def draw_hyperbola(self, x0, y0, x1, y1, preview):
        a = max(abs(x1 - x0), 1)  # Избежание деления на 0
        b = max(abs(y1 - y0) / 2, 1)
        shape_ids = []
        for x in range(-a, a + 1):
            try:
                y = b * math.sqrt(1 + (x / a) ** 2)
                tag = "preview" if preview else None
                oval1 = self.canvas.create_oval(x0 + x, y0 + y, x0 + x + 1, y0 + y + 1, outline="black", tags=tag)
                oval2 = self.canvas.create_oval(x0 + x, y0 - y, x0 + x + 1, y0 - y + 1, outline="black", tags=tag)
                if not preview:
                    shape_ids.extend([oval1, oval2])
            except ValueError:
                continue
        return shape_ids

    def draw_parabola(self, x0, y0, x1, y1, preview):
        p = max(abs(y1 - y0) / 2, 1)  # Избежание деления на 0
        shape_ids = []
        for x in range(-abs(x1 - x0), abs(x1 - x0) + 1):
            try:
                y = (x ** 2) / (4 * p)
                tag = "preview" if preview else None
                oval = self.canvas.create_oval(x0 + x, y0 + y, x0 + x + 1, y0 + y + 1, outline="black", tags=tag)
                if not preview:
                    shape_ids.append(oval)
            except ValueError:
                continue
        return shape_ids

    def toggle_debug_mode(self):
        # Включаем/выключаем отладку
        self.debug_mode = not self.debug_mode

        if self.debug_mode:
            self.debug_button.config(text="Выключить отладку")
            self.show_grid()  # Показать сетку
            self.print_shapes_coordinates()
        else:
            self.debug_button.config(text="Включить отладку")
            self.hide_grid()  # Скрыть сетку

    def show_grid(self):
        """Отображение дискретной сетки"""
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        grid_spacing = 20

        for x in range(0, width, grid_spacing):
            line = self.canvas.create_line(x, 0, x, height, fill="gray", dash=(2, 2), tags="grid")
            self.grid_lines.append(line)

        for y in range(0, height, grid_spacing):
            line = self.canvas.create_line(0, y, width, y, fill="gray", dash=(2, 2), tags="grid")
            self.grid_lines.append(line)

    def hide_grid(self):
        """Скрытие сетки"""
        for line in self.grid_lines:
            self.canvas.delete(line)
        self.grid_lines.clear()

    def print_shapes_coordinates(self):
        """Вывод координат всех фигур на консоль"""
        print("--- Координаты фигур ---")
        for shape_data in self.shapes:
            print(f"Тип: {shape_data['type']}")
            for idx, shape_id in enumerate(shape_data["shape_ids"]):
                coords = self.canvas.coords(shape_id)
                print(f"  Фигура {idx + 1} ID {shape_id}: {coords}")
        print("--- Конец координат ---")


if __name__ == "__main__":
    root = tk.Tk()
    app = GraphicEditor(root)
    root.mainloop()
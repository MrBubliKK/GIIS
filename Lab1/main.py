import tkinter as tk
from tkinter import Menu


class LineEditor:
    def __init__(self, root):
        self.root = root
        self.root.title("Графический редактор")

        self.canvas = tk.Canvas(self.root, width=800, height=600, bg="white")
        self.canvas.pack()

        self.lines = []
        self.deleted_lines = []

        self.start_x = None
        self.start_y = None
        self.current_line = None

        self.drawing_mode = "CDA"
        self.debug_mode = False
        self.grid_lines = []
        self.grid_spacing = 20

        self.create_menu()
        self.create_toolbar()

        self.canvas.bind("<Button-1>", self.start_drawing)
        self.canvas.bind("<B1-Motion>", self.update_drawing)
        self.canvas.bind("<ButtonRelease-1>", self.finish_drawing)

    def create_menu(self):
        menu = Menu(self.root)
        self.root.config(menu=menu)

        line_menu = Menu(menu, tearoff=0)
        line_menu.add_command(label="Алгоритм ЦДА", command=self.set_cda_mode)
        line_menu.add_command(label="Алгоритм Брезенхема", command=self.set_bresenham_mode)
        line_menu.add_command(label="Алгоритм Ву", command=self.set_wu_mode)

        menu.add_cascade(label="Отрезки", menu=line_menu)

    def create_toolbar(self):
        toolbar = tk.Frame(self.root, bg="lightgrey")
        toolbar.pack(side=tk.TOP, fill=tk.X)

        self.delete_btn = tk.Button(toolbar, text="Предыдущий шаг", command=self.delete_last_line)
        self.delete_btn.pack(side=tk.LEFT, padx=2, pady=2)

        self.restore_btn = tk.Button(toolbar, text="Следующий шаг", command=self.restore_last_line)
        self.restore_btn.pack(side=tk.LEFT, padx=2, pady=2)

        self.debug_btn = tk.Button(toolbar, text="Включить отладку", command=self.toggle_debug_mode)
        self.debug_btn.pack(side=tk.LEFT, padx=2, pady=2)

        self.update_buttons()

    def set_cda_mode(self):
        self.drawing_mode = "CDA"
        print("Выбран алгоритм ЦДА")

    def set_bresenham_mode(self):
        self.drawing_mode = "Bresenham"
        print("Выбран алгоритм Брезенхема")

    def set_wu_mode(self):
        self.drawing_mode = "Wu"
        print("Выбран алгоритм Ву")

    def draw_line_cda(self, x1, y1, x2, y2):
        dx = x2 - x1
        dy = y2 - y1
        steps = max(abs(dx), abs(dy))
        x_inc = dx / steps
        y_inc = dy / steps
        x, y = x1, y1
        for _ in range(steps + 1):
            self.canvas.create_line(round(x), round(y), round(x) + 1, round(y) + 1, fill="black")
            x += x_inc
            y += y_inc

    def draw_line_bresenham(self, x1, y1, x2, y2):
        dx = abs(x2 - x1)
        dy = abs(y2 - y1)
        sx = 1 if x1 < x2 else -1
        sy = 1 if y1 < y2 else -1
        err = dx - dy
        while True:
            self.canvas.create_line(x1, y1, x1 + 1, y1 + 1, fill="black")
            if x1 == x2 and y1 == y2:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x1 += sx
            if e2 < dx:
                err += dx
                y1 += sy

    def draw_line_wu(self, x1, y1, x2, y2):
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

    def start_drawing(self, event):
        if self.debug_mode:
            print("Режим отладки включен: рисование отключено")
            return
        self.start_x = event.x
        self.start_y = event.y

    def update_drawing(self, event):
        if self.debug_mode:
            return
        if self.current_line:
            self.canvas.delete(self.current_line)
        self.current_line = self.canvas.create_line(self.start_x, self.start_y, event.x, event.y, fill="black")

    def finish_drawing(self, event):
        if self.debug_mode:
            return
        if self.current_line:
            x1, y1, x2, y2 = self.start_x, self.start_y, event.x, event.y
            self.canvas.delete(self.current_line)
            if self.drawing_mode == "CDA":
                self.draw_line_cda(x1, y1, x2, y2)
            elif self.drawing_mode == "Bresenham":
                self.draw_line_bresenham(x1, y1, x2, y2)
            elif self.drawing_mode == "Wu":
                self.draw_line_wu(x1, y1, x2, y2)
            self.lines.append(((x1, y1, x2, y2), self.drawing_mode))
            self.current_line = None
            self.update_buttons()

    def delete_last_line(self):
        if self.debug_mode and self.lines:
            line_data = self.lines.pop()
            self.deleted_lines.append(line_data)
            self.canvas.delete("all")
            if self.debug_mode:
                self.draw_grid()
            for line, mode in self.lines:
                x1, y1, x2, y2 = line
                if mode == "CDA":
                    self.draw_line_cda(x1, y1, x2, y2)
                elif mode == "Bresenham":
                    self.draw_line_bresenham(x1, y1, x2, y2)
                elif mode == "Wu":
                    self.draw_line_wu(x1, y1, x2, y2)
            self.update_buttons()

    def restore_last_line(self):
        if self.debug_mode and self.deleted_lines:
            line_data, mode = self.deleted_lines.pop()
            x1, y1, x2, y2 = line_data
            self.lines.append((line_data, mode))
            if mode == "CDA":
                self.draw_line_cda(x1, y1, x2, y2)
            elif mode == "Bresenham":
                self.draw_line_bresenham(x1, y1, x2, y2)
            elif mode == "Wu":
                self.draw_line_wu(x1, y1, x2, y2)
            self.update_buttons()

    def toggle_debug_mode(self):
        self.debug_mode = not self.debug_mode
        if self.debug_mode:
            self.debug_btn.config(text="Выключить отладку")
            self.draw_grid()
        else:
            self.debug_btn.config(text="Включить отладку")
            self.clear_grid()
            while self.deleted_lines:
                line_data, mode = self.deleted_lines.pop()
                x1, y1, x2, y2 = line_data
                self.lines.append((line_data, mode))
                if mode == "CDA":
                    self.draw_line_cda(x1, y1, x2, y2)
                elif mode == "Bresenham":
                    self.draw_line_bresenham(x1, y1, x2, y2)
                elif mode == "Wu":
                    self.draw_line_wu(x1, y1, x2, y2)
        self.update_buttons()

    def draw_grid(self):
        self.clear_grid()
        width = self.canvas.winfo_width()
        height = self.canvas.winfo_height()
        for i in range(self.grid_spacing, width, self.grid_spacing):
            line_id = self.canvas.create_line(i, 0, i, height, fill="lightgrey")
            self.grid_lines.append(line_id)
        for j in range(self.grid_spacing, height, self.grid_spacing):
            line_id = self.canvas.create_line(0, j, width, j, fill="lightgrey")
            self.grid_lines.append(line_id)

    def clear_grid(self):
        for line_id in self.grid_lines:
            self.canvas.delete(line_id)
        self.grid_lines = []

    def update_buttons(self):
        if not self.debug_mode or not self.lines:
            self.delete_btn.config(state=tk.DISABLED)
        else:
            self.delete_btn.config(state=tk.NORMAL)

        if not self.debug_mode or not self.deleted_lines:
            self.restore_btn.config(state=tk.DISABLED)
        else:
            self.restore_btn.config(state=tk.NORMAL)


if __name__ == "__main__":
    root = tk.Tk()
    editor = LineEditor(root)
    root.mainloop()
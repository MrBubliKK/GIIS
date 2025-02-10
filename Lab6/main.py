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
        self.current_fill_algorithm = None
        self.fill_algorithm_state = {}
        self.fill_debug_color = "#FF69B4"

        self.create_menu()
        self.create_toolbar()
        self.canvas.bind("<Button-1>", self.add_point)
        self.canvas.bind("<Button-3>", self.delete_point)

    def create_menu(self):
        menu = Menu(self.root)
        self.root.config(menu=menu)

        # Меню для алгоритмов отрезков
        line_menu = Menu(menu, tearoff=0)
        line_menu.add_command(label="Алгоритм ЦДА", command=self.set_cda_mode)
        line_menu.add_command(label="Алгоритм Брезенхема", command=self.set_bresenham_mode)
        line_menu.add_command(label="Алгоритм Ву", command=self.set_wu_mode)
        menu.add_cascade(label="Алгоритмы отрезков", menu=line_menu)

        # Меню для операций с полигонами
        polygon_menu = Menu(menu, tearoff=0)
        polygon_menu.add_command(label="Проверить выпуклость", command=self.check_convexity)
        polygon_menu.add_command(label="Выпуклая оболочка (Грэхем)", command=self.convex_hull_graham)
        polygon_menu.add_command(label="Выпуклая оболочка (Джарвис)", command=self.convex_hull_jarvis)
        polygon_menu.add_command(label="Принадлежность точки полигону", command=self.check_point_inside)
        menu.add_cascade(label="Операции с полигонами", menu=polygon_menu)

        # Меню для алгоритмов заливки
        fill_menu = Menu(menu, tearoff=0)
        fill_menu.add_command(label="Алгоритм с ET", command=lambda: self.start_fill('ET'))
        fill_menu.add_command(label="Алгоритм с AEL", command=lambda: self.start_fill('AEL'))
        fill_menu.add_command(label="Алгоритм с затравкой", command=self.start_flood_fill)
        fill_menu.add_command(label="Построчное заполнение", command=self.start_scanline_fill)
        menu.add_cascade(label="Алгоритмы заливки", menu=fill_menu)

        # Меню для пересечений
        intersect_menu = Menu(menu, tearoff=0)
        intersect_menu.add_command(label="Найти точку пересечения", command=self.find_intersection)
        menu.add_cascade(label="Пересечения", menu=intersect_menu)

    def start_fill(self, algorithm):
        if len(self.points) < 3:
            messagebox.showinfo("Ошибка", "Сначала нарисуйте полигон")
            return

        if self.debug_mode:
            self.prepare_fill_debug(algorithm)
            self.step_fill()
        else:
            if algorithm == 'AEL':
                self.fill_polygon_ael()
            elif algorithm == 'ET':
                self.fill_polygon()

    def _set_flood_start_point(self, event):
        x, y = event.x, event.y
        if not self.is_point_inside(x, y):
            messagebox.showerror("Ошибка", "Точка должна быть внутри полигона")
            return

        self.fill_algorithm_state['stack'] = [(x, y)]
        self.canvas.unbind("<Button-1>")
        if self.debug_mode:
            self.step_fill()
        else:
            self.flood_fill(x, y)

    def create_toolbar(self):
        toolbar = tk.Frame(self.root, bg="lightgrey")
        toolbar.pack(side=tk.TOP, fill=tk.X)

        self.clear_btn = tk.Button(toolbar, text="Очистить", command=self.clear_canvas)
        self.clear_btn.pack(side=tk.LEFT, padx=2, pady=2)

        # Кнопки для отладки
        self.debug_btn = tk.Button(toolbar, text="Режим отладки", command=self.toggle_debug_mode)
        self.debug_btn.pack(side=tk.LEFT, padx=2, pady=2)

        self.step_btn = tk.Button(toolbar, text="Следующий шаг", command=self.step_fill)
        self.step_btn.pack(side=tk.LEFT, padx=2, pady=2)
        self.step_btn.config(state=tk.DISABLED)

    def toggle_debug_mode(self):
        self.debug_mode = not self.debug_mode
        state = "включен" if self.debug_mode else "выключен"
        self.debug_btn.config(relief=tk.SUNKEN if self.debug_mode else tk.RAISED)
        self.step_btn.config(state=tk.NORMAL if self.debug_mode else tk.DISABLED)
        print(f"Режим отладки {state}")

        if not self.debug_mode:
            self.fill_algorithm_state = {}
            self.current_fill_algorithm = None
            self.canvas.delete("debug")

    def start_fill_debug(self, algorithm):
        if not self.debug_mode:
            messagebox.showinfo("Ошибка", "Включите режим отладки")
            return

        if len(self.points) < 3:
            messagebox.showinfo("Ошибка", "Сначала нарисуйте полигон")
            return

        self.prepare_fill_debug(algorithm)
        self.step_fill()

    def prepare_fill_debug(self, algorithm):
        if algorithm == 'AEL':
            self._prepare_ael_debug()
        elif algorithm == 'ET':
            self._prepare_et_debug()
        elif algorithm == 'Flood':
            self._prepare_flood_debug()
        elif algorithm == 'Scanline':
            self._prepare_scanline_debug()
        self.current_fill_algorithm = algorithm

    def _prepare_flood_debug(self):
        if len(self.points) < 3:
            return
        self.fill_algorithm_state = {
            'stack': [],
            'filled': set(),
            'current_point': None,
            'done': False
        }

    def _prepare_scanline_debug(self):
        if len(self.points) < 3:
            return

        # Рассчитываем границы полигона
        min_y = min(p[1] for p in self.points)
        max_y = max(p[1] for p in self.points)

        self.fill_algorithm_state = {
            'current_y': int(min_y),
            'max_y': int(max_y),
            'intersections': [],
            'done': False
        }

    # Реализация пошаговой заливки для алгоритма AEL
    def _prepare_ael_debug(self):
        et = {}
        for i in range(len(self.points)):
            p1 = self.points[i]
            p2 = self.points[(i + 1) % len(self.points)]

            if p1[1] == p2[1]:
                continue

            if p1[1] > p2[1]:
                p1, p2 = p2, p1

            y_min = int(p1[1])
            y_max = int(p2[1])
            x = p1[0]
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            slope = dx / dy if dy != 0 else 0

            if y_min not in et:
                et[y_min] = []
            et[y_min].append({'y_max': y_max, 'x': x, 'slope': slope})

        current_y = min(et.keys()) if et else 0
        self.fill_algorithm_state = {
            'et': et,
            'ael': [],
            'current_y': current_y,
            'done': False
        }

    def _prepare_et_debug(self):
        et = {}
        for i in range(len(self.points)):
            p1 = self.points[i]
            p2 = self.points[(i + 1) % len(self.points)]

            # Пропускаем горизонтальные ребра
            if p1[1] == p2[1]:
                continue

            # Упорядочиваем точки по Y
            if p1[1] > p2[1]:
                p1, p2 = p2, p1

            y_min = int(p1[1])
            y_max = int(p2[1])
            x = p1[0]
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]

            if dy == 0:
                continue

            slope = dx / dy  # Δx/Δy

            if y_min not in et:
                et[y_min] = []
            et[y_min].append({
                'y_max': y_max,
                'x': x,
                'dx': dx,
                'dy': dy,
                'slope': slope
            })

        if not et:
            self.fill_algorithm_state = {
                'et': {},
                'ael': [],
                'current_y': 0,
                'done': True
            }
            return
        current_y = min(et.keys())
        self.fill_algorithm_state = {
            'et': et,
            'ael': [],
            'current_y': current_y,
            'done': False
        }

    def step_fill(self):
        if self.current_fill_algorithm == 'AEL':
            self._step_ael_fill()
        elif self.current_fill_algorithm == 'ET':
            self._step_et_fill()
        elif self.current_fill_algorithm == 'Flood':
            self._step_flood_fill()
        elif self.current_fill_algorithm == 'Scanline':
            self._step_scanline_fill()
        else:
            messagebox.showerror("Ошибка", "Алгоритм не выбран")

    def _step_flood_fill(self):
        state = self.fill_algorithm_state
        if state.get('done', False):
            messagebox.showinfo("Готово", "Заливка завершена!")
            return

        if not state['stack'] and not state['current_point']:
            # Начало алгоритма - запрашиваем стартовую точку
            self.canvas.bind("<Button-1>", self._set_flood_start_point)
            messagebox.showinfo("Инструкция", "Выберите стартовую точку внутри полигона")
            return

        # Обработка текущей точки
        if state['current_point']:
            x, y = state['current_point']
            neighbors = [
                (x + 1, y),  # Вправо
                (x - 1, y),  # Влево
                (x, y + 1),  # Вниз
                (x, y - 1),  # Вверх
            ]

            # Добавляем соседей в стек
            for n in neighbors:
                if n not in state['filled'] and self.is_point_inside(n[0], n[1]) and not self.is_on_boundary(n[0],
                                                                                                             n[1]):
                    state['stack'].append(n)

            # Помечаем как обработанную
            state['filled'].add((x, y))
            self.canvas.create_line(x, y, x + 1, y + 1, fill=self.fill_debug_color)
            state['current_point'] = None

        # Берем следующую точку из стека
        while state['stack']:
            x, y = state['stack'].pop()

            if (x, y) in state['filled']:
                continue

            if not self.is_point_inside(x, y) or self.is_on_boundary(x, y):
                continue

            state['current_point'] = (x, y)
            # Визуализация текущей точки
            self.canvas.delete("debug")
            self.canvas.create_oval(x - 2, y - 2, x + 2, y + 2,
                                    fill="red", outline="red", tags="debug")
            return

        state['done'] = True
        messagebox.showinfo("Готово", "Заливка завершена!")

    def _set_flood_start_point(self, event):
        x, y = event.x, event.y
        if not self.is_point_inside(x, y):
            messagebox.showerror("Ошибка", "Точка должна быть внутри полигона")
            return

        self.fill_algorithm_state['stack'] = [(x, y)]
        self.canvas.unbind("<Button-1>")
        self.step_fill()

    def _step_scanline_fill(self):
        state = self.fill_algorithm_state
        if state.get('done', False):
            messagebox.showinfo("Готово", "Заливка завершена!")
            return

        # Инициализация при первом запуске
        if not state.get('initialized', False):
            if not self._init_scanline_state():
                state['done'] = True
                return
            state['initialized'] = True

        # Обработка текущей строки
        current_y = state['current_y']
        intersections = state['intersections']

        # Визуализация текущей строки
        self.canvas.delete("debug")
        self.canvas.create_line(0, current_y, 800, current_y, fill="red", tags="debug")

        # Закрашивание отрезков
        for i in range(0, len(intersections), 2):
            if i + 1 >= len(intersections):
                break
            x1 = int(intersections[i])
            x2 = int(intersections[i + 1])
            self.canvas.create_line(x1, current_y, x2, current_y, fill=self.fill_debug_color)

        # Переход к следующей строке
        state['current_y'] += 1
        if state['current_y'] > state['max_y']:
            state['done'] = True
            return

        # Расчет новых пересечений
        self._calculate_intersections(state['current_y'])

    def _init_scanline_state(self):
        state = self.fill_algorithm_state
        state['current_y'] = int(min(p[1] for p in self.points))
        state['max_y'] = int(max(p[1] for p in self.points))
        self._calculate_intersections(state['current_y'])
        return True

    def _calculate_intersections(self, y):
        intersections = []
        for i in range(len(self.points)):
            p1 = self.points[i]
            p2 = self.points[(i + 1) % len(self.points)]

            if p1[1] == p2[1]:
                continue

            if (p1[1] <= y < p2[1]) or (p2[1] <= y < p1[1]):
                try:
                    x_intersect = (y - p1[1]) * (p2[0] - p1[0]) / (p2[1] - p1[1]) + p1[0]
                    intersections.append(x_intersect)
                except ZeroDivisionError:
                    continue

        intersections.sort()
        self.fill_algorithm_state['intersections'] = intersections

    def _step_ael_fill(self):
        state = self.fill_algorithm_state
        if state.get('done', False):
            messagebox.showinfo("Готово", "Заливка завершена!")
            return

        et = state['et']
        ael = state['ael']
        current_y = state['current_y']

        # Добавляем новые рёбра в AEL
        if current_y in et:
            ael.extend(et[current_y])
            del et[current_y]

        # Сортируем AEL по X
        ael.sort(key=lambda e: e['x'])

        # Закрашиваем интервал
        for i in range(0, len(ael), 2):
            if i + 1 >= len(ael):
                break
            x1 = int(ael[i]['x'])
            x2 = int(ael[i + 1]['x'])
            self.canvas.create_line(x1, current_y, x2, current_y, fill=self.fill_debug_color)

        # Обновляем AEL и Y
        current_y += 1
        new_ael = []
        for edge in ael:
            if edge['y_max'] > current_y:
                edge['x'] += edge['slope']
                new_ael.append(edge)

        done = not new_ael and not et

        self.fill_algorithm_state = {
            'et': et,
            'ael': new_ael,
            'current_y': current_y,
            'done': done
        }

        if done:
            messagebox.showinfo("Готово", "Заливка завершена!")

    def _step_et_fill(self):
        state = self.fill_algorithm_state
        if state.get('done', False):
            messagebox.showinfo("Готово", "Заливка завершена!")
            return

        et = state['et']
        ael = state['ael']
        current_y = state['current_y']

        # Добавляем новые рёбра
        if current_y in et:
            ael.extend(et[current_y])
            del et[current_y]

        # Сортируем AEL по X
        ael.sort(key=lambda e: e['x'])

        # Закрашиваем отрезки
        i = 0
        while i < len(ael) - 1:
            x1 = int(ael[i]['x'])
            x2 = int(ael[i + 1]['x'])
            self.canvas.create_line(x1, current_y, x2, current_y, fill=self.fill_debug_color)
            i += 2

        # Обновляем AEL
        current_y += 1
        new_ael = []
        for edge in ael:
            if edge['y_max'] > current_y:
                edge['x'] += edge['slope']
                new_ael.append(edge)

        done = not new_ael and not et

        self.fill_algorithm_state = {
            'et': et,
            'ael': new_ael,
            'current_y': current_y,
            'done': done
        }

        if done:
            messagebox.showinfo("Готово", "Заливка завершена!")

    def is_on_boundary(self, x, y):
        """Проверяет, находится ли точка на границе полигона"""
        for i in range(len(self.points)):
            p1 = self.points[i]
            p2 = self.points[(i + 1) % len(self.points)]
            if self.point_on_segment((x, y), p1, p2):
                return True
        return False

    def flood_fill(self, start_x, start_y, fill_color="blue"):
        """Алгоритм заполнения с затравкой"""
        stack = [(start_x, start_y)]
        filled = set()

        while stack:
            x, y = stack.pop()
            if (x, y) in filled:
                continue
            if not self.is_point_inside(x, y) or self.is_on_boundary(x, y):
                continue

            # Заливаем пиксель
            self.canvas.create_line(x, y, x + 1, y + 1, fill=fill_color)
            filled.add((x, y))

            # Добавляем соседние пиксели
            stack.append((x + 1, y))  # Вправо
            stack.append((x - 1, y))  # Влево
            stack.append((x, y + 1))  # Вниз
            stack.append((x, y - 1))  # Вверх

    def start_flood_fill(self):
        """Запуск процесса выбора точки затравки для flood fill"""
        if len(self.points) < 3:
            messagebox.showerror("Ошибка", "Сначала постройте полигон")
            return

        if self.debug_mode:
            self.prepare_fill_debug('Flood')
            self.step_fill()
        else:
            # Оригинальный код для обычной заливки
            def on_click(event):
                x, y = event.x, event.y
                if not self.is_point_inside(x, y):
                    messagebox.showerror("Ошибка", "Точка должна быть внутри полигона")
                else:
                    self.flood_fill(x, y)
                self.canvas.unbind("<Button-1>")
                self.canvas.bind("<Button-1>", self.add_point)

            self.canvas.bind("<Button-1>", on_click)
            messagebox.showinfo("Инструкция", "Кликните внутри полигона для выбора точки затравки")

    def scanline_fill(self, x, y, fill_color="blue"):
        """Построчное заполнение полигона с затравкой."""
        if len(self.points) < 3:
            messagebox.showerror("Ошибка", "Сначала постройте полигон.")
            return

        # 1. Находим минимальный и максимальный Y
        min_y = min(p[1] for p in self.points)
        max_y = max(p[1] for p in self.points)

        # 2. Проходим по каждой строке (y)
        for current_y in range(int(min_y), int(max_y) + 1):
            intersections = []
            for i in range(len(self.points)):
                p1 = self.points[i]
                p2 = self.points[(i + 1) % len(self.points)]

                # Проверяем пересечение с горизонтальной линией
                if (p1[1] <= current_y < p2[1]) or (p2[1] <= current_y < p1[1]):
                    # Вычисляем X пересечения
                    x_intersect = (current_y - p1[1]) * (p2[0] - p1[0]) / (p2[1] - p1[1]) + p1[0]
                    intersections.append(x_intersect)

            # Сортируем точки пересечения по X
            intersections.sort()

            # Заполняем отрезки между парами точек
            for i in range(0, len(intersections) - 1, 2):
                x1 = int(intersections[i])
                x2 = int(intersections[i + 1])
                for x in range(x1, x2 + 1):
                    if self.is_point_inside(x, current_y):
                        self.canvas.create_line(x, current_y, x + 1, current_y + 1, fill=fill_color)

    def start_scanline_fill(self):
        """Запуск построчного заполнения"""
        if len(self.points) < 3:
            messagebox.showerror("Ошибка", "Сначала постройте полигон")
            return

        if self.debug_mode:
            self.prepare_fill_debug('Scanline')
            self.step_fill()
        else:
            # Оригинальный код для обычной заливки
            def on_click(event):
                x, y = event.x, event.y
                if not self.is_point_inside(x, y):
                    messagebox.showerror("Ошибка", "Точка должна быть внутри полигона")
                else:
                    self.scanline_fill(x, y)
                self.canvas.unbind("<Button-1>")
                self.canvas.bind("<Button-1>", self.add_point)

            self.canvas.bind("<Button-1>", on_click)
            messagebox.showinfo("Инструкция", "Кликните внутри полигона для выбора точки затравки")

    def fill_polygon_ael(self):
        if len(self.points) < 3:
            messagebox.showerror("Ошибка", "Недостаточно точек для полигона")
            return

        if self.debug_mode:
            self.prepare_fill_debug('AEL')
            self._step_ael_fill()
        else:
            # Создаем таблицу ребер (ET)
            et = {}
            for i in range(len(self.points)):
                p1 = self.points[i]
                p2 = self.points[(i + 1) % len(self.points)]

                if p1[1] == p2[1]:
                    continue  # Пропускаем горизонтальные ребра

                # Упорядочиваем точки по Y
                if p1[1] > p2[1]:
                    p1, p2 = p2, p1

                y_min = int(p1[1])
                y_max = int(p2[1])
                x = p1[0]
                dx = p2[0] - p1[0]
                dy = p2[1] - p1[1]
                slope = dx / dy  # Δx/Δy

                if y_min not in et:
                    et[y_min] = []
                et[y_min].append({'y_max': y_max, 'x': x, 'slope': slope})

            # Инициализация активного списка ребер (AEL)
            ael = []
            current_y = min(et.keys()) if et else 0

            while True:
                # Добавляем новые ребра в AEL
                if current_y in et:
                    ael.extend(et[current_y])
                    del et[current_y]

                # Сортируем AEL по x
                ael.sort(key=lambda e: e['x'])

                # Закрашиваем горизонтальные отрезки между парами ребер
                i = 0
                while i < len(ael):
                    if i + 1 >= len(ael):
                        break
                    e1 = ael[i]
                    e2 = ael[i + 1]
                    x_start = int(e1['x'])
                    x_end = int(e2['x'])
                    if x_start < x_end:
                        self.canvas.create_line(x_start, current_y, x_end, current_y, fill="blue")
                    i += 2

                # Переходим к следующему Y
                current_y += 1

                # Удаляем завершенные ребра и обновляем координаты
                new_ael = []
                for edge in ael:
                    if edge['y_max'] > current_y:
                        edge['x'] += edge['slope']
                        new_ael.append(edge)
                ael = new_ael

                # Проверяем завершение
                if not ael and not et:
                    break

    def fill_polygon(self):
        if len(self.points) < 3:
            messagebox.showerror("Ошибка", "Недостаточно точек для полигона")
            return

        if self.debug_mode:
            self.prepare_fill_debug('ET')
            self._step_et_fill()
        else:
            # Создаем таблицу ребер (ET)
            et = {}
            for i in range(len(self.points)):
                p1 = self.points[i]
                p2 = self.points[(i + 1) % len(self.points)]

                # Пропускаем горизонтальные ребра
                if p1[1] == p2[1]:
                    continue

                # Упорядочиваем точки по Y
                if p1[1] > p2[1]:
                    p1, p2 = p2, p1

                y_min = int(p1[1])
                y_max = int(p2[1])
                x = p1[0]
                dx = p2[0] - p1[0]
                dy = p2[1] - p1[1]

                if dy == 0:
                    continue

                slope = dx / dy  # Δx/Δy

                if y_min not in et:
                    et[y_min] = []
                et[y_min].append({
                    'y_max': y_max,
                    'x': x,
                    'dx': dx,
                    'dy': dy,
                    'slope': slope
                })

            if not et:
                return

            # Инициализация активного списка ребер (AEL)
            ael = []
            current_y = min(et.keys())

            while True:
                # Добавляем новые ребра в AEL
                if current_y in et:
                    for edge in et[current_y]:
                        ael.append(edge)
                    del et[current_y]

                # Сортируем AEL по x
                ael.sort(key=lambda e: e['x'])

                # Закрашиваем горизонтальные отрезки
                i = 0
                while i < len(ael):
                    e1 = ael[i]
                    if i + 1 >= len(ael):
                        break
                    e2 = ael[i + 1]

                    # Рисуем линию между e1.x и e2.x
                    x_start = int(e1['x'])
                    x_end = int(e2['x'])

                    if x_start > x_end:
                        x_start, x_end = x_end, x_start

                    self.canvas.create_line(
                        x_start, current_y,
                        x_end, current_y,
                        fill="black"
                    )
                    i += 2

                # Увеличиваем Y и обновляем AEL
                current_y += 1

                # Удаляем завершенные ребра
                ael = [e for e in ael if e['y_max'] > current_y]

                # Обновляем координаты X для оставшихся ребер
                for edge in ael:
                    edge['x'] += edge['slope']

                # Проверяем завершение
                if not ael and not et:
                    break

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
        self.fill_algorithm_state = {}  # Сброс состояния заливки
        self.current_fill_algorithm = None
        self.canvas.unbind("<Button-1>")
        self.canvas.bind("<Button-1>", self.add_point)

if __name__ == "__main__":
    root = tk.Tk()
    app = PolygonEditor(root)
    root.mainloop()
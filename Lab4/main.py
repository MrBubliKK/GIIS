import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
import numpy as np
import time
import tkinter as tk
from tkinter import filedialog


def load_object(filename):
    """Загружает 3D-объект из текстового файла."""
    vertices = []
    faces = []
    try:
        with open(filename, 'r') as f:
            for line in f:
                parts = line.split()
                if not parts:
                    continue
                if parts[0] == 'v':  # Вершины
                    vertices.append([float(x) for x in parts[1:4]] + [1])  # Добавляем 1 для гомогенных координат
                elif parts[0] == 'f':  # Грани
                    faces.append([int(x.split('/')[0]) - 1 for x in parts[1:]])
        if not vertices or not faces:
            raise ValueError("Файл не содержит вершин или граней")
        return np.array(vertices, dtype=np.float32), faces
    except FileNotFoundError:
        raise FileNotFoundError(f"Файл не найден: {filename}")
    except ValueError as e:
        raise ValueError(f"Ошибка при чтении файла: {e}")


def apply_transformation(vertices, matrix):
    """Применяет матричное преобразование к вершинам."""
    # Преобразуем вершины с добавленным 1 в 4xN
    vertices_homogeneous = np.hstack((vertices[:, :3], np.ones((vertices.shape[0], 1))))  # Преобразуем в гомогенные координаты
    transformed_vertices = np.dot(vertices_homogeneous, matrix.T)  # Применяем преобразование
    return transformed_vertices


def draw_object(vertices, faces):
    """Отрисовывает 3D-объект."""
    glBegin(GL_LINES)
    for face in faces:
        for i in range(len(face)):
            glVertex3fv(vertices[face[i]][:3])  # Отправляем только x, y, z
            glVertex3fv(vertices[face[(i + 1) % len(face)]][:3])
    glEnd()


def get_perspective_matrix(fov, aspect, near, far):
    """Создает матрицу перспективной проекции."""
    f = 1.0 / np.tan(np.radians(fov) / 2.0)
    return np.array([[f / aspect, 0, 0, 0],
                     [0, f, 0, 0],
                     [0, 0, (far + near) / (near - far), 2 * far * near / (near - far)],
                     [0, 0, -1, 0]], dtype=np.float32)


def get_rotation_matrix(axis, angle):
    """Создает матрицу поворота вокруг заданной оси."""
    if axis == 'x':
        return np.array(
            [[1, 0, 0, 0], [0, np.cos(angle), -np.sin(angle), 0], [0, np.sin(angle), np.cos(angle), 0],
             [0, 0, 0, 1]], dtype=np.float32)
    if axis == 'y':
        return np.array(
            [[np.cos(angle), 0, np.sin(angle), 0], [0, 1, 0, 0], [-np.sin(angle), 0, np.cos(angle), 0],
             [0, 0, 0, 1]], dtype=np.float32)
    if axis == 'z':
        return np.array(
            [[np.cos(angle), -np.sin(angle), 0, 0], [np.sin(angle), np.cos(angle), 0, 0], [0, 0, 1, 0],
             [0, 0, 0, 1]], dtype=np.float32)
    return np.eye(4, dtype=np.float32)


def get_mirror_matrix(axis):
    """Создает матрицу отражения относительно заданной оси."""
    if axis == 'x':
        return np.array([[-1, 0, 0, 0], [0, 1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], dtype=np.float32)
    if axis == 'y':
        return np.array([[1, 0, 0, 0], [0, -1, 0, 0], [0, 0, 1, 0], [0, 0, 0, 1]], dtype=np.float32)
    if axis == 'z':
        return np.array([[1, 0, 0, 0], [0, 1, 0, 0], [0, 0, -1, 0], [0, 0, 0, 1]], dtype=np.float32)
    return np.eye(4, dtype=np.float32)


def choose_file():
    """Открывает диалоговое окно для выбора файла и возвращает его путь."""
    file_path = filedialog.askopenfilename(title="Выберите файл 3D-объекта", filetypes=[("Text Files", "*.txt")])
    return file_path


def open_file_button_action():
    """Обработчик нажатия на кнопку для открытия файла."""
    file_path = choose_file()  # Выбираем файл
    if file_path:
        try:
            vertices, faces = load_object(file_path)  # Загружаем объект из выбранного файла
            print(f"Файл {file_path} загружен успешно.")
            # Теперь загружаем объект в OpenGL
            open_gl_view(vertices, faces)
        except Exception as e:
            print(f"Ошибка при загрузке файла: {e}")


def open_gl_view(vertices, faces):
    """Открывает окно с OpenGL и отображает 3D-объект."""
    pygame.init()
    display = (800, 600)
    pygame.display.set_mode(display, DOUBLEBUF | OPENGL)
    glEnable(GL_DEPTH_TEST)

    fov = 45  # Угол обзора
    aspect = display[0] / display[1]  # Соотношение сторон
    near = 0.1  # Ближняя плоскость
    far = 50.0  # Дальняя плоскость
    projection_matrix = get_perspective_matrix(fov, aspect, near, far)

    # Начальная трансформация объекта
    object_transformation = np.eye(4, dtype=np.float32)
    object_transformation[3][2] = -5  # Начальная трансляция для видимости

    rotation_speed = np.radians(150)  # Фиксированная скорость вращения
    last_time = pygame.time.get_ticks()  # Для корректного поворота

    # Флаги для отслеживания зеркалирования
    mirror_x_triggered = False
    mirror_y_triggered = False
    mirror_z_triggered = False

    running = True
    while running:
        now_time = pygame.time.get_ticks()  # Время на каждом кадре
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        keys = pygame.key.get_pressed()  # Получаем состояние клавиш
        transformation = np.eye(4, dtype=np.float32)  # Начальная матрица преобразования

        # Поворот
        if keys[K_w] or keys[K_s] or keys[K_a] or keys[K_d] or keys[K_z] or keys[K_x]:
            delta_time = (now_time - last_time) / 1000.0  # Время между кадрами
            angle = rotation_speed * delta_time
            if keys[K_w]:
                transformation = get_rotation_matrix('y', angle)
            if keys[K_s]:
                transformation = get_rotation_matrix('y', -angle)
            if keys[K_a]:
                transformation = get_rotation_matrix('x', angle)
            if keys[K_d]:
                transformation = get_rotation_matrix('x', -angle)
            if keys[K_z]:
                transformation = get_rotation_matrix('z', angle)
            if keys[K_x]:
                transformation = get_rotation_matrix('z', -angle)

        # Масштабирование
        if keys[K_q]:
            scale_factor = 1.1
            transformation = np.array(
                [[scale_factor, 0, 0, 0], [0, scale_factor, 0, 0], [0, 0, scale_factor, 0], [0, 0, 0, 1]],
                dtype=np.float32)
        if keys[K_e]:
            scale_factor = 0.9
            transformation = np.array(
                [[scale_factor, 0, 0, 0], [0, scale_factor, 0, 0], [0, 0, scale_factor, 0], [0, 0, 0, 1]],
                dtype=np.float32)

        # Зеркалирование
        if keys[K_1] and not mirror_x_triggered:
            mirror_matrix = get_mirror_matrix('x')
            print("Зеркалирование по оси X")
            transformation = np.dot(transformation, mirror_matrix)  # Применяем зеркалирование
            mirror_x_triggered = True  # Устанавливаем флаг

        elif keys[K_2] and not mirror_y_triggered:
            mirror_matrix = get_mirror_matrix('y')
            print("Зеркалирование по оси Y")
            transformation = np.dot(transformation, mirror_matrix)  # Применяем зеркалирование
            mirror_y_triggered = True  # Устанавливаем флаг

        elif keys[K_3] and not mirror_z_triggered:
            mirror_matrix = get_mirror_matrix('z')
            print("Зеркалирование по оси Z")
            transformation = np.dot(transformation, mirror_matrix)  # Применяем зеркалирование
            mirror_z_triggered = True  # Устанавливаем флаг

        # Сброс флагов при отпускании клавиш
        if not keys[K_1]:
            mirror_x_triggered = False
        if not keys[K_2]:
            mirror_y_triggered = False
        if not keys[K_3]:
            mirror_z_triggered = False

        # Применяем трансформацию
        object_transformation = np.dot(transformation, object_transformation)
        transformed_vertices = apply_transformation(vertices, np.dot(object_transformation, projection_matrix))

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        draw_object(transformed_vertices, faces)
        pygame.display.flip()
        pygame.time.wait(10)
        last_time = now_time  # Обновляем время для следующего кадра

    pygame.quit()


def main():
    """Основная функция."""
    root = tk.Tk()
    root.withdraw()  # Прячем главное окно tkinter

    # Создаем окно для запуска программы с кнопкой
    open_file_button = tk.Button(root, text="Открыть файл", command=open_file_button_action)
    open_file_button.pack(pady=20)
    root.deiconify()  # Показываем окно

    root.mainloop()


if __name__ == "__main__":
    main()

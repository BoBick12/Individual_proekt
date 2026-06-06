import sys
import math
import numpy as np
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as FigureCanvas
from matplotlib.figure import Figure
from PyQt6.QtWidgets import (
    QApplication, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QLineEdit,
    QTextEdit, QMessageBox, QDialog, QComboBox, QStatusBar)
from PyQt6.QtCore import Qt, QRegularExpression
from PyQt6.QtGui import QRegularExpressionValidator


def format_equation_string(coeffs):
    degree = len(coeffs) - 1
    superscripts = {4: "⁴", 3: "³", 2: "²", 1: "", 0: ""}
    terms = []
    for i, c in enumerate(coeffs):
        if c == 0 and i != degree: continue
        power = degree - i
        abs_c = abs(c)
        sign = (" + " if c > 0 else " - ") if terms else ("-" if c < 0 else "")
        val_str = f"{abs_c:g}" if (abs_c != 1.0 or power == 0) else ""
        var_str = ("x" + superscripts.get(power, "")) if power > 0 else ""
        terms.append(f"{sign}{val_str}{var_str}")
    return "".join(terms) + " = 0" if terms else "0 = 0"


# Математические методы

def solve_linear(a, b):
    eq_str = format_equation_string([a, b])
    steps = f"Тип: Линейное уравнение ({eq_str})\n"
    steps += f"Этап 1: Перенос b в правую часть: {a}x = {-b}\n"
    x = -b / a
    steps += f"Этап 2: Нахождение x = {-b}/{a} = {x:.4f}\n"
    steps += "Результат: x = {:.4f}\nКомплексных корней нет.".format(x)
    return steps, [x]


def solve_quadratic(a, b, c):
    eq_str = format_equation_string([a, b, c])
    steps = f"Тип: Квадратное уравнение ({eq_str})\n"
    D = b ** 2 - 4 * a * c
    steps += f"Этап 1: Нахождение дискриминанта D = b² - 4ac = {D:g}\n"
    if D < 0:
        steps += "Этап 2: D < 0. Действительных корней нет.\nОповещение: Существует 2 комплексных корня."
        return steps, []
    elif D == 0:
        x = -b / (2 * a)
        steps += f"Этап 2: D = 0. Корень x = -b/2a = {x:.4f}\nКомплексных корней нет."
        return steps, [x]
    else:
        sd = math.sqrt(D)
        x1, x2 = (-b + sd) / (2 * a), (-b - sd) / (2 * a)
        steps += f"Этап 2: x = (-b ± √D)/2a. Корни: x1={x1:.4f}, x2={x2:.4f}\nКомплексных корней нет."
        return steps, [x1, x2]


def solve_cubic(a, b, c, d):
    eq_str = format_equation_string([a, b, c, d])
    steps = f"Тип: Кубическое уравнение ({eq_str})\n"
    steps += "Метод: Формула Кардано.\n"
    steps += f"Этап 1: Нормировка и замена x = y - b/3a для исключения x².\n"
    p = (3 * a * c - b ** 2) / (3 * a ** 2)
    q = (2 * b ** 3 - 9 * a * b * c + 27 * a ** 2 * d) / (27 * a ** 3)
    steps += f"Этап 2: Получены параметры p = {p:.4f}, q = {q:.4f}\n"
    Q = (p / 3) ** 3 + (q / 2) ** 2
    steps += f"Этап 3: Нахождение дискриминанта Кардано Q = (p/3)³ + (q/2)² = {Q:.4f}\n"

    roots = np.roots([a, b, c, d])
    reals = sorted([r.real for r in roots if abs(r.imag) < 1e-7])

    steps += "Этап 4: Анализ корней.\nДействительные корни:\n"
    for i, r in enumerate(reals): steps += f"x{i + 1} = {r:.4f}\n"

    if len(reals) < 3:
        steps += f"Оповещение: Найдено {len(reals)} действ. корня. Остальные 2 корня — комплексные."
    else:
        steps += "Комплексных корней нет."
    return steps, reals


def solve_quartic(a, b, c, d, e):
    eq_str = format_equation_string([a, b, c, d, e])
    steps = f"Тип: Уравнение 4-й степени ({eq_str})\n"
    steps += "Метод: Декарта-Эйлера.\n"
    steps += "Этап 1: Приведение к каноническому виду y⁴ + py² + qy + r = 0.\n"

    p = (8 * a * c - 3 * b ** 2) / (8 * a ** 2)
    q = (b ** 3 - 4 * a * b * c + 8 * a ** 2 * d) / (8 * a ** 3)
    r = (-3 * b ** 4 + 256 * a ** 3 * e - 64 * a ** 2 * b * d + 16 * a * b ** 2 * c) / (256 * a ** 4)
    steps += f"Этап 2: Параметры: p={p:.4f}, q={q:.4f}, r={r:.4f}\n"

    steps += "Этап 3: Составление кубической резольвенты и нахождение ее корней.\n"
    steps += "Этап 4: Извлечение корней через комбинации значений √z.\n"

    roots = np.roots([a, b, c, d, e])
    reals = sorted([r.real for r in roots if abs(r.imag) < 1e-7])

    steps += "Результат (действительные корни):\n"
    if not reals:
        steps += "Действительных корней нет. Все 4 корня — комплексные."
    else:
        for i, r in enumerate(reals): steps += f"x{i + 1} = {r:.4f}\n"
        if len(reals) < 4:
            steps += f"Оповещение: Найдено {len(reals)} действ. корня. Остальные являются комплексными."
    return steps, reals


# Окно графика

class GraphWindow(QDialog):
    def __init__(self, coeffs, reals=None, parent=None):
        super().__init__(parent)
        self.setWindowTitle("График функции")
        self.setMinimumSize(600, 650)
        self.setStyleSheet("background-color: #d3d3d3;")

        layout = QVBoxLayout()
        top = QHBoxLayout()
        top.addStretch()
        btn = QPushButton("Выход")
        btn.setFixedSize(80, 30)
        btn.setStyleSheet("""
            QPushButton { background-color: white; border: 1px solid black; color: black; font-weight: bold; }
            QPushButton:hover { background-color: #cfe2ff; }
        """)
        btn.clicked.connect(self.close)
        top.addWidget(btn)
        layout.addLayout(top)

        self.figure = Figure(facecolor='#d3d3d3')
        self.canvas = FigureCanvas(self.figure)
        layout.addWidget(self.canvas)

        ax = self.figure.add_subplot(111)
        ax.set_facecolor('#d3d3d3')

        ax.spines['left'].set_position('zero')
        ax.spines['bottom'].set_position('zero')
        ax.spines['right'].set_color('none')
        ax.spines['top'].set_color('none')

        # Математический расчет экстремумов
        deriv_coeffs = np.polyder(coeffs)
        deriv_roots = np.roots(deriv_coeffs)
        extrema_x = sorted([r.real for r in deriv_roots if abs(r.imag) < 1e-7])

        # Автоматический расчет масштаба с учетом корней и экстремумов
        all_important_points = (reals if reals else []) + extrema_x
        if all_important_points:
            min_pt = min(all_important_points)
            max_pt = max(all_important_points)
            padding = max(2.0, (max_pt - min_pt) * 0.5)
            x_start = min_pt - padding
            x_end = max_pt + padding
        else:
            x_start, x_end = -10, 10

        x_vals = np.linspace(x_start, x_end, 1000)
        y_vals = np.polyval(coeffs, x_vals)

        # График функции
        ax.plot(x_vals, y_vals, color='black', linewidth=1.5, zorder=2)

        if reals:
            for root in reals:
                ax.plot(root, 0, marker='o', color='red', markersize=8, zorder=3,
                        label='Корень' if 'Корень' not in ax.get_legend_handles_labels()[1] else "")

        for ext_x in extrema_x:
            ext_y = np.polyval(coeffs, ext_x)
            ax.plot(ext_x, ext_y, marker='^', color='green', markersize=8, zorder=3,
                    label='Экстремум' if 'Экстремум' not in ax.get_legend_handles_labels()[1] else "")

        if reals or extrema_x:
            ax.legend(loc="upper left")

        ax.grid(True, linestyle=':', alpha=0.6, zorder=1)

        ax.set_xlim(x_start, x_end)
        self.canvas.draw()

        y_start, y_end = ax.get_ylim()

        ax.text(x_end, 0, " X", fontsize=12, fontweight='bold', ha='left', va='center')
        ax.text(0, y_end, " Y", fontsize=12, fontweight='bold', ha='center', va='bottom')

        self.setLayout(layout)


# Главное окно приложения

class EquationApp(QWidget):
    def __init__(self):
        super().__init__()
        self.degree = None
        self.current_coeffs = []
        self.current_reals = []
        self.init_ui()

    def init_ui(self):
        self.setWindowTitle("Решение уравнений 1-4 степеней")
        self.setMinimumSize(500, 750)
        self.setStyleSheet("""
            QWidget { background-color: #d3d3d3; color: black; font-family: Arial; }
            QLineEdit, QTextEdit, QComboBox { background-color: white; border: 1px solid black; padding: 5px; }
            QPushButton { background-color: white; border: 1px solid black; font-weight: bold; }
            QPushButton:hover { background-color: #cfe2ff; }
            QStatusBar { background-color: #bebebe; border-top: 1px solid black; color: black; }
        """)

        main_layout = QVBoxLayout()
        main_layout.setSpacing(15)
        main_layout.setContentsMargins(20, 20, 20, 10)

        main_layout.addWidget(QLabel("Выберите степень уравнения", alignment=Qt.AlignmentFlag.AlignCenter))
        deg_layout = QHBoxLayout()
        self.btns = []
        for i in range(1, 5):
            btn = QPushButton(str(i))
            btn.setFixedSize(50, 50)
            btn.setCheckable(True)
            btn.setStyleSheet("""
                QPushButton { border-radius: 25px; border: 2px solid black; background-color: white; }
                QPushButton:checked { background-color: #a0a0a0; }
                QPushButton:hover { background-color: #cfe2ff; }
            """)
            btn.clicked.connect(lambda _, d=i: self.select_degree(d))
            deg_layout.addWidget(btn)
            self.btns.append(btn)
        main_layout.addLayout(deg_layout)

        # Панель истории вычислений
        hist_layout = QHBoxLayout()
        hist_layout.addWidget(QLabel("История расчетов:"))
        self.history_combo = QComboBox()
        self.history_combo.addItem("Выбрать из сохраненных...")
        self.history_combo.currentIndexChanged.connect(self.load_history)
        hist_layout.addWidget(self.history_combo)
        main_layout.addLayout(hist_layout)

        self.fmt_label = QLabel("", alignment=Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.fmt_label)

        main_layout.addWidget(QLabel("Введите коэффициенты через пробел", alignment=Qt.AlignmentFlag.AlignCenter))

        self.input_field = QLineEdit()
        self.input_field.setMinimumHeight(40)
        self.input_field.returnPressed.connect(self.process)

        regex = QRegularExpression(r"^[0-9\s,\-]*$")
        validator = QRegularExpressionValidator(regex, self)
        self.input_field.setValidator(validator)
        main_layout.addWidget(self.input_field)

        calc_layout = QHBoxLayout()
        calc_layout.addStretch()
        btn_calc = QPushButton("Рассчитать")
        btn_calc.setFixedSize(110, 35)
        btn_calc.clicked.connect(self.process)
        calc_layout.addWidget(btn_calc)
        main_layout.addLayout(calc_layout)

        main_layout.addWidget(QLabel("Шаги решения", alignment=Qt.AlignmentFlag.AlignCenter))
        self.results_area = QTextEdit()
        self.results_area.setReadOnly(True)
        main_layout.addWidget(self.results_area)

        # Нижняя панель
        bot_layout = QHBoxLayout()

        # Кнопка Выход
        btn_exit = QPushButton("Выход")
        btn_exit.setFixedSize(80, 35)
        btn_exit.clicked.connect(self.close)
        bot_layout.addWidget(btn_exit)

        bot_layout.addStretch()

        # Кнопка График
        btn_graph = QPushButton("График")
        btn_graph.setFixedSize(100, 35)
        btn_graph.clicked.connect(self.open_graph)
        bot_layout.addWidget(btn_graph)

        main_layout.addLayout(bot_layout)

        # Статус-бар
        self.status_bar = QStatusBar()
        main_layout.addWidget(self.status_bar)
        self.status_bar.showMessage("Программа готова к работе")

        self.setLayout(main_layout)

    def select_degree(self, d):
        self.degree = d
        for b in self.btns: b.setChecked(int(b.text()) == d)
        formats = {1: "ax + b = 0", 2: "ax² + bx + c = 0", 3: "ax³ + bx² + cx + d = 0",
                   4: "ax⁴ + bx³ + cx² + dx + e = 0"}
        self.fmt_label.setText(f"Текущий формат: {formats[d]}")
        self.clear_all()
        self.status_bar.showMessage(f"Выбрана {d}-я степень уравнения")

    def clear_all(self):
        self.input_field.clear()
        self.results_area.clear()
        self.current_coeffs = []
        self.current_reals = []

    def process(self):
        if not self.degree:
            QMessageBox.warning(self, "Ошибка", "Выберите степень!")
            self.status_bar.showMessage("Ошибка: Не выбрана степень уравнения")
            return
        try:
            vals = [float(x.replace(',', '.')) for x in self.input_field.text().split()]

            expected_count = self.degree + 1
            if len(vals) != expected_count:
                QMessageBox.warning(self, "Ошибка валидации",
                                    f"Для уравнения {self.degree} степени должно быть введено строго {expected_count} коэффициентов!\nВы ввели: {len(vals)}.")
                self.status_bar.showMessage("Ошибка: Неверное количество коэффициентов")
                return

            if vals[0] == 0:
                QMessageBox.warning(self, "Ошибка валидации", "Старший коэффициент 'a' не может быть равен нулю!")
                self.status_bar.showMessage("Ошибка: Старший коэффициент равен нулю")
                return

            self.current_coeffs = vals

            if self.degree == 1:
                res, reals = solve_linear(*vals)
            elif self.degree == 2:
                res, reals = solve_quadratic(*vals)
            elif self.degree == 3:
                res, reals = solve_cubic(*vals)
            elif self.degree == 4:
                res, reals = solve_quartic(*vals)
            else:
                res, reals = "Степень уравнения выше 4-й.", []

            self.current_reals = reals
            res_ru = res.replace('.', ',')
            self.results_area.setText(res_ru)

            input_text = self.input_field.text()
            hist_str = f"Степень {self.degree}: [{input_text}]"
            if self.history_combo.findText(hist_str) == -1:
                self.history_combo.addItem(hist_str, (self.degree, input_text))

            self.status_bar.showMessage("Расчет успешно завершен")

        except Exception as e:
            QMessageBox.warning(self, "Ошибка", "Произошла ошибка при обработке данных. Проверьте корректность ввода.")
            self.status_bar.showMessage("Ошибка в структуре введенных данных")

    def load_history(self, index):
        if index <= 0: return
        data = self.history_combo.itemData(index)
        if data:
            deg, coeffs_str = data
            self.history_combo.blockSignals(True)
            self.select_degree(deg)
            self.input_field.setText(coeffs_str)
            self.history_combo.blockSignals(False)
            self.process()
            self.status_bar.showMessage("Уравнение успешно загружено из истории")

    def open_graph(self):
        if not self.current_coeffs:
            QMessageBox.information(self, "Информация", "Сначала введите коэффициенты и нажмите 'Рассчитать'.")
            self.status_bar.showMessage("Невозможно построить график: расчеты отсутствуют")
            return
        try:
            self.g_win = GraphWindow(self.current_coeffs, self.current_reals)
            self.g_win.show()
            self.status_bar.showMessage("Окно графика успешно открыто")
        except Exception as e:
            print(f"Ошибка открытия графика: {e}")
            self.status_bar.showMessage("Критическая ошибка при генерации графика")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = EquationApp()
    window.show()
    sys.exit(app.exec())
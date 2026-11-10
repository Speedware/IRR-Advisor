from dataclasses import dataclass
import math
import os

RESET='\033[0m'; CYAN='\033[96m'; GREEN='\033[92m'; GOLD='\033[93m'; RED='\033[91m'; DIM='\033[2m'; BOLD='\033[1m'


def paint(text, color):
    return f'{color}{text}{RESET}' if os.environ.get('NO_COLOR') is None else str(text)


def npv(rate, flows):
    """NPV = сумма CF_t / (1+r)^t; CF_0 — начальная инвестиция."""
    if rate <= -1 or not math.isfinite(rate):
        raise ValueError('Ставка должна быть конечной и больше -100%.')
    return sum(cf / (1 + rate) ** t for t, cf in enumerate(flows))


def irr(flows, tolerance=1e-12, max_iter=300):
    """IRR методом бисекции для потоков с единственной сменой знака (от минуса к плюсу).
    Возвращает None, если IRR не существует в диапазоне (-100%, +∞).
    """
    if len(flows) < 2 or flows[0] >= 0:
        raise ValueError('Начальная инвестиция должна быть отрицательной.')
    seen_positive = False
    for x in flows[1:]:
        if x > 0:
            seen_positive = True
        elif x < 0 and seen_positive:
            raise ValueError('После первого положительного потока отрицательные потоки недопустимы.')
    if not any(x > 0 for x in flows[1:]):
        return None
    low = -1 + 1e-10
    high = 1.0
    while npv(high, flows) > 0 and high < 1e12:
        high = 2 * high + 1
    if npv(high, flows) > 0:
        return None
    for _ in range(max_iter):
        mid = (low + high) / 2
        value = npv(mid, flows)
        if abs(value) < tolerance or high - low < tolerance:
            return mid
        if value > 0:
            low = mid
        else:
            high = mid
    return (low + high) / 2


@dataclass
class Project:
    name: str
    investment: float
    cashflows: list[float]

    @property
    def flows(self):
        return [-self.investment] + self.cashflows

    def evaluate(self, discount_rate):
        return {'irr': irr(self.flows), 'npv': npv(discount_rate, self.flows)}


def recommend(projects, discount_rate):
    """Экспертные правила: отбор NPV>0 и IRR>r, выбор max NPV.
    При равенстве NPV с точностью до 0.01 выбирается больший IRR.
    """
    results = [(p, p.evaluate(discount_rate)) for p in projects]
    eligible = [(p, m) for p, m in results if m['irr'] is not None and m['irr'] > discount_rate and m['npv'] > 0]
    if not eligible:
        return None, results, 'Все проекты не проходят критерии: IRR > ставка дисконтирования и NPV > 0.'
    best_p, best_m = eligible[0]
    for p, m in eligible[1:]:
        if m['npv'] > best_m['npv'] + 0.01 or (abs(m['npv'] - best_m['npv']) <= 0.01 and m['irr'] > best_m['irr']):
            best_p, best_m = p, m
    reason = (f'Проект «{best_p.name}» создаёт наибольшую чистую приведённую стоимость '
              f'(NPV = {best_m["npv"]:,.2f} у.е.) среди приемлемых проектов. '
              f'Его IRR = {best_m["irr"] * 100:.2f}% превышает требуемую доходность {discount_rate * 100:.2f}%. '
              'При взаимоисключающих проектах основной критерий выбора — максимальный NPV.')
    return best_p, results, reason


def ask_number(prompt, minimum=None, maximum=None, integer=False):
    while True:
        try:
            raw = input(paint('  › ', CYAN) + prompt + ' ').strip().replace(',', '.')
            value = int(raw) if integer else float(raw)
            if not math.isfinite(value) or (minimum is not None and value < minimum) or (maximum is not None and value > maximum):
                raise ValueError
            return value
        except (ValueError, OverflowError):
            bounds = f'от {minimum} до {maximum}' if minimum is not None and maximum is not None else 'в допустимом диапазоне'
            print(paint(f'  ✗ Введите корректное число {bounds}.', RED))
        except EOFError:
            raise SystemExit('\nВвод завершён.')


WIDTH = 73

FONT = {
    'I': ['█████', '  █  ', '  █  ', '  █  ', '█████'],
    'R': ['████ ', '█   █', '████ ', '█  █ ', '█   █'],
    'A': [' ███ ', '█   █', '█████', '█   █', '█   █'],
    'D': ['████ ', '█   █', '█   █', '█   █', '████ '],
    'V': ['█   █', '█   █', ' █ █ ', ' █ █ ', '  █  '],
    'S': [' ████', '█    ', ' ███ ', '    █', '████ '],
    'O': [' ███ ', '█   █', '█   █', '█   █', ' ███ '],
    ' ': ['  ', '  ', '  ', '  ', '  '],
}


def banner_lines(text):
    glyphs = [FONT[ch] for ch in text]
    return [' '.join(glyph[row] for glyph in glyphs) for row in range(5)]


def line():
    print(paint('  ' + '─' * WIDTH, DIM))


def box_line(text, border_color=CYAN, text_color=None):
    print(paint('  │', border_color) + paint(f' {text}'.ljust(WIDTH), text_color or border_color) + paint('│', border_color))


def box_line_centered(text, border_color=CYAN, text_color=None):
    pad = WIDTH - len(text)
    left, right = pad // 2, pad - pad // 2
    print(paint('  │', border_color) + paint(' ' * left + text + ' ' * right, text_color or border_color) + paint('│', border_color))


def section(title, color=BOLD):
    print('\n' + paint(f'  {title}', color))
    line()


def main():
    print('\n' + paint('  ╭' + '─' * WIDTH + '╮', CYAN))
    for row in banner_lines('IRR ADVISOR'):
        box_line_centered(row, border_color=CYAN, text_color=CYAN + BOLD)
    box_line_centered('', border_color=CYAN)
    box_line_centered('Мини-экспертная система выбора инвестиционного проекта', border_color=CYAN, text_color=DIM)
    print(paint('  ╰' + '─' * WIDTH + '╯', CYAN))
    print('  Введите 2–3 проекта. Для каждого инвестиция в момент t=0 и 5–8')
    print('  последующих годовых потоков. Допускаются ранние отрицательные потоки до первого положительного.\n')
    rate = ask_number('Ставка дисконтирования, % [например 10]:', minimum=0, maximum=100000) / 100
    count = ask_number('Количество проектов (2 или 3):', minimum=2, maximum=3, integer=True)
    projects = []
    for index in range(1, count + 1):
        line()
        print(paint(f'  Проект {index} из {count}', BOLD))
        try:
            name = input(paint('  › ', CYAN) + 'Название: ').strip() or f'Проект {index}'
        except EOFError:
            raise SystemExit('\nВвод завершён.')
        investment = ask_number('Начальная инвестиция (> 0), у.е.:', minimum=0.000000001)
        n = ask_number('Количество годовых потоков (5–8):', minimum=5, maximum=8, integer=True)
        flows = []
        seen_positive = False
        for year in range(1, n + 1):
            while True:
                value = ask_number(f'Поток за год {year}, у.е.:')
                if seen_positive and value < 0:
                    print(paint('  ✗ После положительного потока отрицательный недопустим.', RED))
                    continue
                flows.append(value)
                if value > 0:
                    seen_positive = True
                break
        projects.append(Project(name, investment, flows))
    winner, results, reason = recommend(projects, rate)
    section('РЕЗУЛЬТАТЫ АНАЛИЗА')
    print(paint(f'  {"Проект":<24} {"IRR":>11} {"NPV, у.е.":>17} {"Статус":>16}', BOLD))
    line()
    for p, m in results:
        acceptable = m['irr'] is not None and m['irr'] > rate and m['npv'] > 0
        rate_text = f'{m["irr"] * 100:.2f}%' if m['irr'] is not None else 'нет'
        status_color = GREEN if acceptable else RED
        status = 'ПОДХОДИТ' if acceptable else 'ОТКЛОНЁН'
        row = f'  {p.name[:24]:<24} {rate_text:>11} {m["npv"]:>17,.2f} '
        print(row + paint(f'{status:>16}', status_color))
    line()
    section('РЕКОМЕНДАЦИЯ', color=GREEN if winner else GOLD)
    print('  ' + paint(f'Выбрать: {winner.name}' if winner else 'Не выбирать ни один проект.', BOLD))
    print('  ' + reason + '\n')


if __name__ == '__main__':
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print('\n  Работа завершена.')

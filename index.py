import os
import sys
import time

# Настройка ввода с клавиатуры (без нажатия Enter)
if os.name == "nt":
  import msvcrt

  def get_key():
    key = ""
    while msvcrt.kbhit():
      ch = msvcrt.getch()
      if ch in (b"\x00", b"\xe0"):  # Стрелки на Windows
        ch2 = msvcrt.getch()
        key = {b"K": "a", b"M": "d", b"H": "w"}.get(ch2, "")
      else:
        key = ch.decode("utf-8", errors="ignore").lower()
    return key

else:
  import select
  import termios
  import tty

  def get_key():
    dr, _, _ = select.select([sys.stdin], [], [], 0)
    if dr:
      ch = sys.stdin.read(1)
      if ch == "\x1b":  # Стрелки на Linux/macOS
        seq = sys.stdin.read(2)
        return {"[D": "a", "[C": "d", "[A": "w"}.get(seq, "")
      return ch.lower()
    return ""


# Карта уровня (10 строк x 42 символа)
LEVEL = [
    "..........................................",
    ".........................*................",
    "......................#######.............",
    "...............*..........................",
    "............#######.......................",
    ".....*...........................*........",
    "..#######..........^..........#######.....",
    "................#######................F..",
    ".........*............................####",
    "##########################################",
]


def clear_screen():
  os.system("cls" if os.name == "nt" else "clear")


def main():
  grid = [list(row) for row in LEVEL]
  height = len(grid)
  width = len(grid[0])  # Полная ширина первой строки (42 клетки)

  # Координаты игрока
  px, py = 2, 8
  vy = 0
  hang_time = 0
  lives = 3
  score = 0
  total_coins = sum(row.count("*") for row in grid)

  # Координаты медленного врага
  ex, ey = 28, 8
  edir = -1
  tick = 0

  old_settings = None
  if os.name != "nt":
    old_settings = termios.tcgetattr(sys.stdin)
    tty.setcbreak(sys.stdin.fileno())

  try:
    while True:
      key = get_key()
      if key == "q":
        break

      # Проверка опоры под ногами
      on_ground = py + 1 < height and grid[py + 1][px] == "#"

      # Движение игрока влево / вправо (в воздухе шаг шире на 2 клетки)
      step = 1 if on_ground else 2
      if key == "a":
        for _ in range(step):
          if px - 1 >= 0 and grid[py][px - 1] != "#":
            px -= 1
      elif key == "d":
        for _ in range(step):
          if px + 1 < width and grid[py][px + 1] != "#":
            px += 1

      # Обновляем опору после сдвига
      on_ground = py + 1 < height and grid[py + 1][px] == "#"

      # Прыжок (W или Пробел)
      if key in ("w", " ") and on_ground:
        vy = -3
        hang_time = 2

      # Плавная физика прыжка и падения
      if vy < 0:
        if py - 1 >= 0 and grid[py - 1][px] != "#":
          py -= 1
        vy += 1
      elif hang_time > 0 and not on_ground:
        hang_time -= 1
      else:
        if not on_ground and py + 1 < height:
          py += 1

      # Движение врага (раз в 6 кадров)
      tick += 1
      if tick % 6 == 0:
        next_ex = ex + edir
        if next_ex <= 24 or next_ex >= 36 or grid[ey][next_ex] == "#":
          edir *= -1
        else:
          ex = next_ex

      # Столкновение с врагом
      if px == ex and py == ey:
        if not on_ground:
          ex, ey = -1, -1
          vy = -2
        else:
          lives -= 1
          if lives <= 0:
            clear_screen()
            print("💀 ЗАКОНЧИЛИСЬ ЖИЗНИ! ИГРА ОКОНЧЕНА.")
            print(f"Собрано монет: {score}/{total_coins}")
            break
          px, py = 2, 8

      # Взаимодействие с объектами
      cell = grid[py][px]
      if cell == "*":
        score += 1
        grid[py][px] = "."
      elif cell == "^":
        lives -= 1
        if lives <= 0:
          clear_screen()
          print("💀 ВЫ НАСТУПИЛИ НА ШИПЫ И ПОТЕРЯЛИ ВСЕ ЖИЗНИ!")
          print(f"Собрано монет: {score}/{total_coins}")
          break
        px, py = 2, 8
      elif cell == "F":
        if score == total_coins:
          clear_screen()
          print("🏆 ПОБЕДА! ВЫ ПРОШЛИ УРОВЕНЬ!")
          print(f"Осталось жизней: {lives} | Собрано монет: {score}/{total_coins}")
          break

      # Отрисовка экрана
      clear_screen()
      hearts = "♥ " * lives
      print("=== ЦИФРОВОЙ МАРИО (ЛЁГКИЙ РЕЖИМ) ===")
      print("Управление: A/D (стрелки) — идти | W/Пробел — прыжок | Q — выход")
      print(f"Жизни: {hearts} | Монеты: {score}/{total_coins}")
      if score == total_coins:
        print("-> Все монеты собраны! Идите к флагу (F)!")
      else:
        print("-> Соберите все звёздочки (*) и дойдите до флага (F)")
      print("-" * width)

      for y in range(height):
        line = ""
        for x in range(width):
          if x == px and y == py:
            line += "M"
          elif x == ex and y == ey:
            line += "E"
          else:
            line += grid[y][x]
        print(line)

      time.sleep(0.11)

  finally:
    if old_settings is not None:
      termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_settings)


if __name__ == "__main__":
  main()

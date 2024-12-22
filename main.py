# Gui Snake Game using PyQt5

# import sys
from contextlib import contextmanager
import random
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QObject
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import (QApplication, QWidget, QGridLayout,
                             QLabel, QPushButton, QMainWindow,
                             QMessageBox, QFrame, QHBoxLayout)


class ViewController(QMainWindow):
    def __init__(self) -> None:
        super().__init__()


class Engine(QObject):
    # Signals
    def __init__(self, board_height: int, board_width: int) -> None:
        super().__init__()
        self.board_width: int = board_width
        self.board_height: int = board_height
        self.snake: list[tuple[int, int]] | None = None
        self.current_dir: tuple[int, int] | None = None
        self.food: tuple[int, int] | None = None
        self._directions: list[tuple[int, int]] = [(1, 0), (0, 1), (-1, 0), (0, -1)]

        self.generate_start()

    def generate_start(self) -> None:
        # random.seed(None)
        self.current_dir = random.choice(self._directions)
        self.snake = [(random.choice(range(1, self.board_height - 1)), random.choice(range(1, self.board_width - 1)))]
        self.food = self.generate_food()

    def generate_food(self) -> tuple[int, int]:
        all_positions: set[tuple[int, int]] = {(x, y) for x in range(self.board_height)
                                               for y in range(self.board_width)}
        available_positions: set[tuple[int, int]] = all_positions - set(self.snake)
        if not available_positions:
            return -1, -1

        return random.choice(list(available_positions))

    def print_game_board(self) -> None:
        # Create an empty board
        board = [['.' for _ in range(self.board_height)] for _ in range(self.board_width)]

        # Place the food on the board
        food_x, food_y = self.food
        board[food_x][food_y] = 'F'

        # Place the snake on the board
        for i, (x, y) in enumerate(self.snake):
            board[x][y] = 'H' if i == 0 else 'S'  # Head is 'H', body is 'S'

        # Print the board
        for row in board:
            print(' '.join(row))
        print()  # Extra newline for spacing


def print_random() -> None:
    number = int(input("Enter a number: "))
    for _ in range(number):
        print(random.choice(range(number)))


if __name__ == '__main__':
    # print_random()
    engine = Engine(20, 20)
    for _ in range(5):
        engine.print_game_board()
        print(engine.current_dir)
        engine.generate_start()

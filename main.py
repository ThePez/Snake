# Gui Snake Game using PyQt5

# import sys
from contextlib import contextmanager
import random
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QObject
from PyQt5.QtGui import QFont, QIcon
from PyQt5.QtWidgets import (QApplication, QWidget, QGridLayout,
                             QLabel, QPushButton, QMainWindow,
                             QMessageBox, QFrame, QHBoxLayout)

ROWS: int = 20
COLUMNS: int = 40


class ViewController(QMainWindow):
    def __init__(self) -> None:
        super().__init__()


class Engine(QObject):
    # Signals
    def __init__(self, board_rows: int, board_columns: int) -> None:
        super().__init__()
        self.board_columns: int = board_columns
        self.board_rows: int = board_rows
        self.snake: list[tuple[int, int]] | None = None
        self.current_dir: tuple[int, int] | None = None
        self.food: tuple[int, int] | None = None
        self._directions: list[tuple[int, int]] = [(1, 0), (0, 1), (-1, 0), (0, -1)]

        self.generate_start()

    def generate_start(self) -> None:
        # random.seed(None)
        self.current_dir = random.choice(self._directions)
        # Snake starts 3 long
        self.snake = [(random.choice(range(1, self.board_rows - 2)), random.choice(range(1, self.board_columns - 2)))]
        self.snake.append((self.snake[0][0] + self.current_dir[0] * -1, self.snake[0][1] + self.current_dir[1] * -1))
        self.snake.append((self.snake[1][0] + self.current_dir[0] * -1, self.snake[1][1] + self.current_dir[1] * -1))
        self.food = self.generate_food()

    def generate_food(self) -> tuple[int, int]:
        all_positions: set[tuple[int, int]] = {(x, y) for x in range(self.board_rows)
                                               for y in range(self.board_columns)}
        available_positions: set[tuple[int, int]] = all_positions - set(self.snake)
        if not available_positions:
            return -1, -1

        return random.choice(list(available_positions))

    def change_direction(self, direction: tuple[int, int]) -> bool:
        if direction not in self._directions:
            return False

        self.current_dir = direction
        return True

    def move_snake(self) -> None:
        new_head: tuple[int, int] = (self.snake[0][0] + self.current_dir[0], self.snake[0][1] + self.current_dir[1])
        self.snake.insert(0, new_head)
        if new_head != self.food:
            self.snake.pop()
            return

        # Food has been eaten -> generate new food
        self.food = self.generate_food()

    def check_collision(self) -> bool:
        destination: tuple[int, int] = self.snake[0][0] + self.current_dir[0], self.snake[0][1] + self.current_dir[1]
        for position in self.snake:
            if position == destination:
                return True

        row, col = destination
        if 0 > row or row >= ROWS or 0 > col or col >= COLUMNS:
            return True

        return False

    def is_game_over(self) -> bool:
        return self.food == (-1, -1)

    def print_game_board(self) -> None:
        # Create an empty board
        board = [['.' for _ in range(self.board_columns)] for _ in range(self.board_rows)]

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


def play_game() -> None:
    engine = Engine(ROWS, COLUMNS)
    engine.print_game_board()
    engine.move_snake()
    engine.print_game_board()
    while True:
        move = input("Move snake: up/down/left/right: ").lower()
        if move == 'up':
            direction = (-1, 0)
        elif move == 'down':
            direction = (1, 0)
        elif move == 'left':
            direction = (0, -1)
        elif move == 'right':
            direction = (0, 1)
        else:
            print('Invalid move')
            continue

        engine.change_direction(direction)
        if engine.check_collision() or engine.is_game_over():
            print("Game over!")
            response = input("Would you like to play again? (y/n): ").lower()
            if response == 'y':
                play_game()
            else:
                print("Bye")
                return

        engine.move_snake()
        engine.print_game_board()


if __name__ == '__main__':
    play_game()


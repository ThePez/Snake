# Gui Snake Game using PyQt5
import sys
import random
from typing import Callable
from PyQt5.QtCore import Qt, QObject, QTimer
from PyQt5.QtGui import QBrush, QColor, QPen
from PyQt5.QtWidgets import (QApplication, QMainWindow, QMessageBox, QGraphicsRectItem, QGraphicsScene,
                             QGraphicsView, QDialog, QLineEdit, QPushButton, QLabel, QGridLayout)

CELL_SIZE = 20
BORDER_MARGIN = 10


class SnakeSegment(QGraphicsRectItem):
    def __init__(self, x, y) -> None:
        super().__init__(x * CELL_SIZE + BORDER_MARGIN, y * CELL_SIZE + BORDER_MARGIN, CELL_SIZE, CELL_SIZE)
        self.setBrush(QBrush(QColor("green")))


class SnakeHeadSegment(QGraphicsRectItem):
    def __init__(self, x, y) -> None:
        super().__init__(x * CELL_SIZE + BORDER_MARGIN, y * CELL_SIZE + BORDER_MARGIN, CELL_SIZE, CELL_SIZE)
        self.setBrush(QBrush(QColor("grey")))


class SnakeTailSegment(QGraphicsRectItem):
    def __init__(self, x, y) -> None:
        super().__init__(x * CELL_SIZE + BORDER_MARGIN, y * CELL_SIZE + BORDER_MARGIN, CELL_SIZE, CELL_SIZE)
        self.setBrush(QBrush(QColor("light green")))


class Food(QGraphicsRectItem):
    def __init__(self, x, y) -> None:
        super().__init__(x * CELL_SIZE + BORDER_MARGIN, y * CELL_SIZE + BORDER_MARGIN, CELL_SIZE, CELL_SIZE)
        self.setBrush(QBrush(QColor("red")))


class GameView(QGraphicsView):
    def __init__(self, scene: QGraphicsScene, engine: 'Engine', pause_game: Callable, parent: QMainWindow):
        super().__init__(scene, parent)
        self.engine = engine
        self.pause_game = pause_game

    def keyPressEvent(self, event):
        # print(f"Key pressed: {event.key()}")
        if event.key() == Qt.Key_Up or event.key() == Qt.Key_W:
            self.engine.change_direction((-1, 0))  # Move up (decrease y)
        elif event.key() == Qt.Key_Down or event.key() == Qt.Key_S:
            self.engine.change_direction((1, 0))  # Move down (increase y)
        elif event.key() == Qt.Key_Left or event.key() == Qt.Key_A:
            self.engine.change_direction((0, -1))  # Move left (decrease x)
        elif event.key() == Qt.Key_Right or event.key() == Qt.Key_D:
            self.engine.change_direction((0, 1))  # Move right (increase x)
        elif event.key() == Qt.Key_Escape or event.key() == Qt.Key_Space:
            self.pause_game()  # Pause the game
        else:
            super().keyPressEvent(event)  # Pass unhandled keys to the parent


class BoardSizeDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Board Size")
        self.setModal(True)

        # Layout and widgets
        layout = QGridLayout(self)
        self.rows_input = QLineEdit(self)
        self.rows_input.setPlaceholderText("5")
        self.columns_input = QLineEdit(self)
        self.columns_input.setPlaceholderText("7")

        self.ok_button = QPushButton("OK", self)
        self.ok_button.clicked.connect(self.accept)  # type: ignore

        layout.addWidget(QLabel("Set the size of your game board\n(must be bigger or equal to a 5x5 grid)"), 0, 0, 1, 2)
        layout.addWidget(QLabel("Rows:"), 1, 0)
        layout.addWidget(self.rows_input, 1, 1)
        layout.addWidget(QLabel("Columns:"), 2, 0)
        layout.addWidget(self.columns_input, 2, 1)
        layout.addWidget(self.ok_button, 3, 0, 1, 2)

    def get_board_size(self):
        try:
            rows = int(self.rows_input.text())
            columns = int(self.columns_input.text())
            if rows > 4 and columns > 4:
                return rows, columns
            else:
                raise ValueError("Invalid dimensions")
        except ValueError:
            return None, None


class ViewController(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.rows, self.columns = self.get_board_size_from_user()
        self.engine = Engine(self.rows, self.columns)
        # Graphics scene and view
        scene_height = self.engine.board_rows * CELL_SIZE + 2 * BORDER_MARGIN
        scene_width = self.engine.board_columns * CELL_SIZE + 2 * BORDER_MARGIN
        self.scene = QGraphicsScene(0, 0, scene_width, scene_height)
        self.view = GameView(self.scene, self.engine, self.pause_game, self)
        self.setCentralWidget(self.view)
        self.setWindowTitle("Snake Game")

        # Timer for game updates
        self.default_timer_interval: int = 500
        self.remaining_timer_interval: int = self.default_timer_interval
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.update_game)  # type: ignore

        # Keep track of snake graphics
        self.snake_graphics = None
        self.food_graphic = None

        # Start the game
        self.init_game()

    def get_board_size_from_user(self):
        while True:
            dialog = BoardSizeDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                rows, columns = dialog.get_board_size()
                if rows and columns:
                    return rows, columns
                QMessageBox.warning(self, "Invalid Input", "Please enter valid positive integers for rows and columns.")
            else:
                sys.exit()

    def add_border(self):
        pen = QPen(QColor("black"))
        pen.setWidth(20)
        self.scene.addRect(
            0, 0,
            self.engine.board_columns * CELL_SIZE + 2 * BORDER_MARGIN,
            self.engine.board_rows * CELL_SIZE + 2 * BORDER_MARGIN,
            pen
        )

    def add_grid_lines(self) -> None:
        grid_color = QColor("gray")
        grid_color.setAlpha(50)  # Make the grid lines faint
        rows = self.engine.board_rows
        columns = self.engine.board_columns
        for row in range(1, rows):  # Horizontal lines
            y_start = row * CELL_SIZE + BORDER_MARGIN
            y_end = y_start
            x_start = BORDER_MARGIN
            x_end = columns * CELL_SIZE + BORDER_MARGIN
            self.scene.addLine(x_start, y_start, x_end, y_end, QColor(grid_color))

        for col in range(1, columns):  # Vertical lines
            x_start = col * CELL_SIZE + BORDER_MARGIN
            x_end = x_start
            y_start = BORDER_MARGIN
            y_end = rows * CELL_SIZE + BORDER_MARGIN
            self.scene.addLine(x_start, y_start, x_end, y_end, QColor(grid_color))

    def init_game(self):
        self.engine.generate_start()  # Reset the engine state
        self.scene.clear()  # Clear the scene
        self.add_grid_lines()  # Add grid lines to the scene
        self.add_border()  # Add border to the scene
        self.snake_graphics = []  # Clear the list of references to the snake
        self.food_graphic = None  # Clear the reference to the food
        self.render_snake()
        self.render_food()
        self.timer.start(500)  # Update every 100 ms
        self.view.setFocus()  # Ensure the view has focus to capture keyboard events

    def pause_game(self) -> None:
        # print("Game paused")
        if self.timer.isActive():
            self.remaining_timer_interval = self.timer.remainingTime()  # Capture remaining time
            self.timer.stop()
            print(f"Remaining time: {self.remaining_timer_interval}")

            pause_dialog = QMessageBox(self)
            pause_dialog.setWindowTitle("Game Paused")
            pause_dialog.setText("Snake is resting...")
            resume_button = pause_dialog.addButton("Keep Eating", QMessageBox.AcceptRole)
            quit_button = pause_dialog.addButton("Give Up", QMessageBox.RejectRole)
            pause_dialog.exec_()

            if pause_dialog.clickedButton() == resume_button:
                self.timer.start(self.remaining_timer_interval)  # Resume with the remaining time
            elif pause_dialog.clickedButton() == quit_button:
                self.close()

    def render_snake(self):
        # X and Y co-ordinate are swapped here. Engine rows will be the Y co-ordinate in view and cols will be X
        for segment in self.snake_graphics:
            self.scene.removeItem(segment)
        self.snake_graphics.clear()

        for index, pos in enumerate(self.engine.snake):
            x, y = pos
            if index == 0:
                segment = SnakeHeadSegment(y, x)
            elif index == len(self.engine.snake) - 1:
                segment = SnakeTailSegment(y, x)
            else:
                segment = SnakeSegment(y, x)

            self.scene.addItem(segment)
            self.snake_graphics.append(segment)

    def render_food(self):
        # X and Y co-ordinate are swapped here. Engine rows will be the Y co-ordinate in view and cols will be X
        if self.food_graphic:
            self.scene.removeItem(self.food_graphic)

        if self.engine.food:
            fx, fy = self.engine.food
            self.food_graphic = Food(fy, fx)
            self.scene.addItem(self.food_graphic)

    def update_game(self) -> None:
        if self.engine.is_game_over():
            self.timer.stop()
            self.show_game_over_dialog("Snake is full")
            return

        if self.engine.check_collision():
            self.timer.stop()
            self.show_game_over_dialog("Snake has died")
            return

        if self.engine.move_snake():
            self.shorten_timer()

        self.render_snake()
        self.render_food()
        if self.remaining_timer_interval < self.default_timer_interval:
            self.timer.start(self.default_timer_interval)
            self.remaining_timer_interval = self.default_timer_interval

    def shorten_timer(self) -> None:
        timer: int = max(100, 500 - ((len(self.engine.snake) - 3) * 5))
        self.default_timer_interval = timer
        print(f"Timer: {timer}")

    def show_game_over_dialog(self, message: str) -> None:
        # Display a popup dialog when the game is over
        msg_box = QMessageBox(self)
        msg_box.setIcon(QMessageBox.Question)
        msg_box.setWindowTitle("Game Over")
        msg_box.setText(f"Game Over!\n{message}\nDo you want to play again?")
        msg_box.setStandardButtons(QMessageBox.Yes | QMessageBox.No)
        result = msg_box.exec_()

        if result == QMessageBox.Yes:
            self.init_game()  # Restart the game
        else:
            self.close()  # Close the application


class Engine(QObject):
    # Signals
    def __init__(self, board_rows: int, board_columns: int) -> None:
        super().__init__()
        self.board_columns: int = board_columns
        self.board_rows: int = board_rows
        self._directions: list[tuple[int, int]] = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        self.snake: list[tuple[int, int]] = [(0, 0)]
        self.current_dir: tuple[int, int] = 1, 0
        self.last_dir: tuple[int, int] = self.current_dir
        self.food: tuple[int, int] = 0, 1

    def generate_start(self) -> None:
        self.current_dir = random.choice(self._directions)
        self.last_dir = self.current_dir
        # Snake starts 3 long
        self.snake = [(random.choice(range(2, self.board_rows - 2 )), random.choice(range(2, self.board_columns - 2)))]
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
        # print(f"Attempting to change direction to: {direction}")  # Debugging
        if direction not in self._directions:
            # print("Invalid direction")  # Debugging
            return False

        # Prevent reversing directly into the snake
        if direction[0] == -self.last_dir[0] and direction[1] == -self.last_dir[1]:
            # print("Cannot reverse direction!")  # Debugging
            return False

        self.current_dir = direction
        # print(f"Direction changed to: {self.current_dir}")  # Debugging
        return True

    def move_snake(self) -> int:
        new_head: tuple[int, int] = (self.snake[0][0] + self.current_dir[0], self.snake[0][1] + self.current_dir[1])
        self.snake.insert(0, new_head)
        # Save last move direction
        self.last_dir = self.current_dir
        if new_head != self.food:
            self.snake.pop()
            return 0

        # Food has been eaten -> generate new food
        self.food = self.generate_food()
        return 1

    def check_collision(self) -> bool:
        destination: tuple[int, int] = self.snake[0][0] + self.current_dir[0], self.snake[0][1] + self.current_dir[1]
        for position in self.snake:
            if position == destination:
                return True

        row, col = destination
        if 0 > row or row >= self.board_rows or 0 > col or col >= self.board_columns:
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


# def play_game() -> None:
#     engine = Engine(ROWS, COLUMNS)
#     engine.print_game_board()
#     engine.move_snake()
#     engine.print_game_board()
#     while True:
#         move = input("Move snake: up/down/left/right: ").lower()
#         if move == 'up':
#             direction = (-1, 0)
#         elif move == 'down':
#             direction = (1, 0)
#         elif move == 'left':
#             direction = (0, -1)
#         elif move == 'right':
#             direction = (0, 1)
#         else:
#             print('Invalid move')
#             continue
#
#         engine.change_direction(direction)
#         if engine.check_collision() or engine.is_game_over():
#             print("Game over!")
#             response = input("Would you like to play again? (y/n): ").lower()
#             if response == 'y':
#                 play_game()
#             else:
#                 print("Bye")
#                 return
#
#         engine.move_snake()
#         engine.print_game_board()


if __name__ == '__main__':
    # play_game()
    app = QApplication(sys.argv)
    controller = ViewController()
    controller.show()
    sys.exit(app.exec_())

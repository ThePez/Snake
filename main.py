# Gui Snake Game using PyQt5
import sys
import random
from typing import Callable
from PyQt5.QtCore import Qt, QObject, QTimer
from PyQt5.QtGui import QBrush, QColor, QPen
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QMessageBox, QGraphicsRectItem,
    QGraphicsScene, QGraphicsView, QDialog, QLineEdit,
    QPushButton, QLabel, QGridLayout, QGraphicsEllipseItem,
    QAction, QWidget, QVBoxLayout, QHBoxLayout)

CELL_SIZE = 20
BORDER_MARGIN = 10


class SnakeSegment(QGraphicsRectItem):
    def __init__(self, x, y, cell_size, head=False, tail=False) -> None:
        super().__init__(x * cell_size + BORDER_MARGIN, y * cell_size + BORDER_MARGIN, cell_size, cell_size)
        if not head and not tail:
            self.setBrush(QBrush(QColor("green")))
        elif head and not tail:
            self.setBrush(QBrush(QColor("grey")))
        elif tail and not head:
            self.setBrush(QBrush(QColor("light green")))


class Food(QGraphicsEllipseItem):
    def __init__(self, x, y, cell_size) -> None:
        super().__init__(x * cell_size + BORDER_MARGIN, y * cell_size + BORDER_MARGIN, cell_size, cell_size)
        self.setBrush(QBrush(QColor("red")))


class GameView(QGraphicsView):
    def __init__(self,
                 scene: QGraphicsScene,
                 engine: 'Engine',
                 pause_game: Callable,
                 boost_speed: Callable,
                 parent: QMainWindow) -> None:
        super().__init__(scene, parent)
        self.engine = engine
        self.pause_game = pause_game
        self.boost_speed = boost_speed

    def keyPressEvent(self, event) -> None:
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
        elif event.key() == Qt.Key_Shift:
            self.boost_speed(True)  # Speed Boost Activate
        else:
            super().keyPressEvent(event)  # Pass unhandled keys to the parent

    def keyReleaseEvent(self, event) -> None:
        if event.key() == Qt.Key_Shift:
            self.boost_speed(False)  # Speed Boost De-Activate


class BoardSizeDialog(QDialog):
    def __init__(self, parent=None) -> None:
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

    def get_board_size(self) -> tuple[int, int] | tuple[None, None]:
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
        # Main window setup
        self.setWindowTitle("Snake Game")
        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)
        central_layout = QVBoxLayout()
        central_widget.setLayout(central_layout)

        # Engine Setup
        self.rows, self.columns = self.get_board_size_from_user()
        self.engine = Engine(self.rows, self.columns)

        # Score label
        self.score_label = QLabel("Score: 0")
        font = self.score_label.font()
        font.setBold(True)
        font.setPointSize(16)
        self.score_label.setFont(font)
        self.score_label.setAlignment(Qt.AlignCenter)
        score_layout = QHBoxLayout()
        score_layout.addWidget(self.score_label)
        central_layout.addLayout(score_layout)

        # Graphics scene and view
        self.cell_size: int = 20
        scene_height = self.engine.board_rows * self.cell_size + 2 * BORDER_MARGIN
        scene_width = self.engine.board_columns * self.cell_size + 2 * BORDER_MARGIN
        self.scene = QGraphicsScene(0, 0, scene_width, scene_height)
        self.view = GameView(self.scene, self.engine, self.pause_game, self.boost_speed, self)
        central_layout.addWidget(self.view)

        # Setup window menus
        self.add_menus()

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

    def get_board_size_from_user(self) -> tuple[int, int]:
        while True:
            dialog = BoardSizeDialog(self)
            if dialog.exec_() == QDialog.Accepted:
                rows, columns = dialog.get_board_size()
                if rows and columns:
                    return rows, columns
                QMessageBox.warning(self, "Invalid Input", "Please enter valid positive integers for rows and columns.")
            else:
                sys.exit()

    def add_menus(self) -> None:
        menu_bar = self.menuBar()
        # Game menu
        game_menu = menu_bar.addMenu("Game")
        game_menu.aboutToShow.connect(self.menu_pause_game)  # type: ignore
        game_menu.aboutToHide.connect(self.menu_un_pause_game)  # type: ignore
        # Add actions to the "Game" menu
        restart_action = QAction("Restart", self)
        restart_action.triggered.connect(self.init_game)  # type: ignore
        game_menu.addAction(restart_action)
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)  # type: ignore
        game_menu.addAction(exit_action)

    def add_border(self) -> None:
        pen = QPen(QColor("black"))
        pen.setWidth(20)
        height = self.engine.board_rows * self.cell_size + 2 * BORDER_MARGIN
        width = self.engine.board_columns * self.cell_size + 2 * BORDER_MARGIN
        self.scene.addRect(0, 0, width, height, pen)

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

    def boost_speed(self, is_boosting: bool) -> None:
        if is_boosting:
            interval: int = self.timer.interval() / 2
            self.timer.setInterval(interval)
        else:
            self.timer.setInterval(self.default_timer_interval)

    def init_game(self) -> None:
        self.engine.generate_start()  # Reset the engine state
        self.score_label.setText("Score: 0")
        self.scene.clear()  # Clear the scene
        self.add_grid_lines()  # Add grid lines to the scene
        self.add_border()  # Add border to the scene
        self.snake_graphics = []  # Clear the list of references to the snake
        self.food_graphic = None  # Clear the reference to the food
        self.render_snake()
        self.render_food()
        self.timer.start(500)  # Update every 100 ms
        self.view.setFocus()  # Ensure the view has focus to capture keyboard events

    def menu_pause_game(self) -> None:
        self.remaining_timer_interval = self.timer.remainingTime()
        self.timer.stop()

    def menu_un_pause_game(self) -> None:
        self.timer.start(self.remaining_timer_interval)

    def pause_game(self) -> None:
        if self.timer.isActive():
            self.remaining_timer_interval = self.timer.remainingTime()  # Capture remaining time
            self.timer.stop()
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

    def render_snake(self) -> None:
        # X and Y co-ordinate are swapped here. Engine rows will be the Y co-ordinate in view and cols will be X
        for segment in self.snake_graphics:
            self.scene.removeItem(segment)
        self.snake_graphics.clear()

        for index, pos in enumerate(self.engine.snake):
            x, y = pos
            if index == 0:
                segment = SnakeSegment(y, x, self.cell_size, head=True)
            elif index == len(self.engine.snake) - 1:
                segment = SnakeSegment(y, x, self.cell_size, tail=True)
            else:
                segment = SnakeSegment(y, x, self.cell_size)

            self.scene.addItem(segment)
            self.snake_graphics.append(segment)

    def render_food(self) -> None:
        # X and Y co-ordinate are swapped here. Engine rows will be the Y co-ordinate in view and cols will be X
        if self.food_graphic:
            self.scene.removeItem(self.food_graphic)

        if self.engine.food:
            fx, fy = self.engine.food
            self.food_graphic = Food(fy, fx, self.cell_size)
            self.scene.addItem(self.food_graphic)

    def update_game(self) -> None:
        if self.engine.check_collision():
            self.timer.stop()
            self.show_game_over_dialog("Snake has died")
            return

        if self.engine.move_snake():
            # Food was eaten
            self.shorten_timer()
            self.score_label.setText(f"Score: {self.engine.score}")

        self.render_snake()
        if self.engine.is_game_over():
            self.timer.stop()
            self.show_game_over_dialog("Snake is full")
            return

        self.render_food()
        # Reset any pause timer intervals
        if self.remaining_timer_interval < self.default_timer_interval:
            self.timer.start(self.default_timer_interval)
            self.remaining_timer_interval = self.default_timer_interval

    def shorten_timer(self) -> None:
        # Timer between moves is shorten by 5ms after each food is consumed. Capped at 100ms as the fastest speed
        timer: int = max(100, 500 - (self.engine.score * 5))
        self.default_timer_interval = timer
        # print(f"Timer: {timer}")

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
    def __init__(self, board_rows: int, board_columns: int) -> None:
        super().__init__()
        self.board_columns: int = board_columns
        self.board_rows: int = board_rows
        self._directions: list[tuple[int, int]] = [(1, 0), (0, 1), (-1, 0), (0, -1)]
        self.snake: list[tuple[int, int]] = [(0, 0)]
        self.current_dir: tuple[int, int] = 1, 0
        self.last_dir: tuple[int, int] = self.current_dir
        self.food: tuple[int, int] = 0, 1
        self.score: int = 0

    def generate_start(self) -> None:
        self.current_dir = random.choice(self._directions)
        self.last_dir = self.current_dir
        # Snake starts 3 long
        self.snake = [(random.choice(range(2, self.board_rows - 2 )), random.choice(range(2, self.board_columns - 2)))]
        self.snake.append((self.snake[0][0] + self.current_dir[0] * -1, self.snake[0][1] + self.current_dir[1] * -1))
        self.snake.append((self.snake[1][0] + self.current_dir[0] * -1, self.snake[1][1] + self.current_dir[1] * -1))
        self.food = self.generate_food()
        self.score = 0

    def update_board_size(self, rows: int, columns: int) -> None:
        self.board_rows = rows
        self.board_columns = columns

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
        self.score += 1
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
        # No longer used, as the UI now renders the game
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
    # Old function used before UI was made
    engine = Engine(10, 10)
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
    app = QApplication(sys.argv)
    controller = ViewController()
    controller.show()
    sys.exit(app.exec_())

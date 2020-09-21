import collections
import copy
import curses
import random
import time


class MainScreen:
    def __init__(self, field_rows, field_cols, screen):
        self.screen = screen

        curses.init_pair(1, curses.COLOR_WHITE, curses.COLOR_BLACK)

        self.border = self.screen.derwin(field_rows+2, field_cols+2, 2, 0)
        self.border.box()

        self.field = self.border.derwin(field_rows, field_cols, 1, 1)
        self.score_board = self.screen.derwin(2, field_cols+2, 0, 0)

    def show_die_message(self):
        self.field.addstr(0, 0, f"You died!", curses.color_pair(1))
        self.field.refresh()
        self.screen.refresh()

    def draw(self, snake, game_field, game_state):
        """Calls draw methods of all objects in game.
        """
        self.field.erase()
        self.score_board.erase()

        #game_state.draw()
        snake.draw(self.field)

        game_field.draw(self.field)

        self.score_board.addstr(0, 0, f"Score: {0}", curses.color_pair(1))
        self.score_board.addstr(0, 10, f"Lives: {3}", curses.color_pair(1))

        self.field.refresh()
        self.border.refresh()
        self.score_board.refresh()
        self.screen.refresh()


class GameField:
    def __init__(self, rows, cols, snake, num_flowers=2):
        self.rows = rows
        self.cols = cols

        self.num_flowers = num_flowers
        self.flowers = set()
        while len(self.flowers) < num_flowers:
            pos = (random.randint(0, rows-1), random.randint(0, cols-1))
            if pos not in snake.blocks:
                self.flowers.add(pos)

        curses.init_pair(3, curses.COLOR_GREEN, curses.COLOR_GREEN)

    def update(self, snake):
        """Updates the playing field.

        Adds flowers if not enough exist on the field.
        """
        while len(self.flowers) < self.num_flowers:
            pos = (random.randint(0, self.rows-1), random.randint(0, self.cols-1))
            if pos not in snake.blocks:
                self.flowers.add(pos)

    def draw(self, screen):
        for f in self.flowers:
            screen.addstr(f[0], f[1], ' ', curses.color_pair(3))

    def eat_flower(self, flower):
        self.flowers.remove(flower)


class Snake:
    def __init__(self, rows, cols, length=3):
        """Initialize snake at center of the screeen facing right.
        """
        self.rows = rows
        self.cols = cols

        self.pos = (rows // 2, cols // 2)
        self.dir = (0, 1)
        self.blocks = collections.deque() # queue of blocks
        for i in range(-length+1, 1):
            new_pos = [self.pos[0] + i * self.dir[0] ,self.pos[1] + i * self.dir[1]]
            if new_pos[0] < 0:
                new_pos[0] = rows + new_pos[0]
            if new_pos[1] < 0:
                new_pos[1] = cols + new_pos[1]
            self.blocks.append(tuple(new_pos))

        curses.init_pair(2, curses.COLOR_YELLOW, curses.COLOR_YELLOW)

    def grow(self):
        """Grows snake in the direction of its tail.

        We ignore the case where the tail grows into the snake itself. Since the growth only
        happens one element at a time, this should be negligible.
        """
        if len(self.blocks) < 2: # grow in current direction
            tail_dir = self.dir
        else:
            tail_dir = (self.blocks[0][0] - self.blocks[1][0], self.blocks[0][1] - self.blocks[1][1])

        new_block = [self.blocks[0][0] + tail_dir[0], self.blocks[0][1] + tail_dir[1]]
        if new_block[0] < 0:
            new_block[0] = self.rows + new_block[0]
        elif new_block[0] >= self.rows:
            new_block[0] -= self.rows

        if new_block[1] < 0:
            new_block[1] = self.cols + new_block[1]
        elif new_block[1] >= self.cols:
            new_block[1] -= self.cols
        new_block = tuple(new_block)
        self.blocks.appendleft(new_block)


    def update(self, field):
        """Updates snake based on current field.

        Args:
            field: Playing field to update if snake ate some flowers.

        Returns:
            A tuple (is_living, ate_flower), indicating if the game is over (you collided with yourself) or you ate a flower.
        """
        self.blocks.popleft()
        new_block = [self.blocks[-1][0] + self.dir[0], self.blocks[-1][1] + self.dir[1]]
        if new_block[0] < 0:
            new_block[0] = self.rows + new_block[0]
        elif new_block[0] >= self.rows:
            new_block[0] -= self.rows

        if new_block[1] < 0:
            new_block[1] = self.cols + new_block[1]
        elif new_block[1] >= self.cols:
            new_block[1] -= self.cols
        new_block = tuple(new_block)

        # check if we collided with ourselves
        if new_block in self.blocks:
            return False, False

        # if we ate a flower, remove flower from field and grow
        ate_flower = False
        if new_block in field.flowers:
            field.eat_flower(new_block)
            self.grow()
            ate_flower = True

        self.blocks.append(new_block)
        return True, ate_flower

    def draw(self, screen):
        for block in self.blocks:
            screen.addstr(block[0], block[1], ' ', curses.color_pair(2))

    def key_callback(self, key):
        if key == curses.KEY_UP:
            self.dir = (-1, 0)
        elif key == curses.KEY_DOWN:
            self.dir = (1, 0)
        elif key == curses.KEY_LEFT:
            self.dir = (0, -1)
        elif key == curses.KEY_RIGHT:
            self.dir = (0, 1)


def main(screen):
    rows = 30
    cols = 40

    # The `screen` is a window that acts as the master window
    # that takes up the whole screen. Other windows created
    # later will get painted on to the `screen` window.
    curses.curs_set(0)
    screen.nodelay(True)

    max_rows, max_cols = screen.getmaxyx()
    if rows > max_rows or cols > max_cols:
        curses.nocbreak()
        screen.keypad(False)
        curses.echo()
        curses.endwin()
        print(f'Screen not large enough to initialize game: required rows: {rows}, available rows: {max_rows}, required cols: {cols}, available cols: {max_cols}')
        quit()

    score = 0
    lives = 3

    main_screen = MainScreen(rows, cols, screen)

    snake = Snake(rows, cols)
    game_field = GameField(rows, cols, snake)

    while True:
        c = screen.getch()
        if c == curses.KEY_UP or c == curses.KEY_DOWN or c == curses.KEY_LEFT or c == curses.KEY_RIGHT:
            snake.key_callback(c)
        elif c == ord('q'):
            break

        is_living, ate_flower = snake.update(game_field)
        if not is_living:
            lives -= 1
            main_screen.show_die_message()
            curses.napms(1000)
            break
        
        if ate_flower:
            score += 1

        game_field.update(snake)

        main_screen.draw(snake, game_field, None)
        time.sleep(0.1)

if __name__=='__main__':
    curses.wrapper(main)
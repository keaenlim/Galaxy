import random

from kivy.config import Config
from kivy.core.audio import SoundLoader
from kivy.lang import Builder
from kivy.uix.relativelayout import RelativeLayout

Config.set('graphics', 'width', '900')
Config.set('graphics', 'height', '400')

from kivy import platform
from kivy.core.window import Window
from kivy.app import App
from kivy.graphics.vertex_instructions import Line, Quad, Triangle
from kivy.properties import NumericProperty, Clock, ObjectProperty, StringProperty
from kivy.uix.widget import Widget
from kivy.graphics.context_instructions import Color

Builder.load_file("menu.kv")        # this is to import the kv file

class MainWidget(RelativeLayout):
    from transforms import transform, transform2D, transform_perspective        # importing must be done inside the class
    from user_actions import keyboard_closed, on_keyboard_up, on_keyboard_down, on_touch_down, on_touch_up

    menu_widget = ObjectProperty()
    perspective_point_x = NumericProperty(0)
    perspective_point_y = NumericProperty(0)

    number_of_vlines = 8        # for this to work, should use an odd number because there would be an uneven number
    # of lines on both sides of the screen if the number of lines are even
    vlines_spacing = .4         # percentage on-screen vertical width, this is to allow the spacing to adapt relative
    # to the size of the screen instead of being a fixed spacing, so that there is a constant number of lines on screen
    vertical_lines = []

    number_of_hlines = 15
    hlines_spacing = .1         # percentage space of on-screen height
    horizontal_lines = []

    speed_y = .8
    current_offset_y = 0
    current_y_loop = 0

    speed_x = 3.0
    current_offset_x = 0
    current_speed_x = 0

    number_of_tiles = 16
    tiles = []       # to list all the tiles
    tiles_coordinates = []          # coordinates of all the tiles

    ship_width = .1
    ship_height = .035
    ship_base_y = .02          # this is basically the distance from the bottom of the tile to the base of the ship
    ship = None
    ship_coordinates = [(0,0),(0,0),(0,0)]

    state_game_over = False
    state_game_has_started = False

    menu_title = StringProperty("G   A   L   A   X   Y")
    menu_button_title = StringProperty("START")
    score_txt = StringProperty("SCORE: 0")

    sound_begin = None
    sound_galaxy = None
    sound_gameover_impact = None
    sound_gameover_voice = None
    sound_music1 = None
    sound_restart = None

    def __init__(self, **kwargs):
        super(MainWidget, self).__init__(**kwargs)          # the super() function makes it easy to call the Widget parent class's attributes and methods instead of saying Widget in this case
        # **kwargs allows us to pass a variable number of keyword arguments to a python function, think of it as a dictionary
        # print("INIT W: " + str(self.width) + " H: " + str(self.height))
        line = None
        # only these functions here are the ones that need to be initialised
        self.init_audio()
        self.init_vertical_lines()
        self.init_horizontal_lines()
        self.init_tiles()
        self.init_ship()        # need to call this function after the tiles are initialised if not the ship will be below the tiles
        # self.pre_fill_tiles_coordinates()       # must call before the other tiles begin generating
        # self.generate_tiles_coordinates()
        self.reset_game()

        if self.is_desktop():
            self._keyboard = Window.request_keyboard(self.keyboard_closed, self)
            self._keyboard.bind(on_key_down=self.on_keyboard_down)
            self._keyboard.bind(on_key_up=self.on_keyboard_up)

        Clock.schedule_interval(self.update, 1 / 60)  # your own machine may be slower/faster than the 60fps, so it may not accurately call the function 60 times every second so it differs from one device to another
        self.sound_galaxy.play()

    def init_audio(self):
        self.sound_begin = SoundLoader.load("audio/begin.wav")           # the SoundLoader function helps to initialise sound folders
        self.sound_galaxy = SoundLoader.load("audio/galaxy.wav")
        self.sound_gameover_impact = SoundLoader.load("audio/gameover_impact.wav")
        self.sound_gameover_voice = SoundLoader.load("audio/gameover_voice.wav")
        self.sound_music1 = SoundLoader.load("audio/music1.wav")
        self.sound_restart = SoundLoader.load("audio/restart.wav")

        self.sound_music1.volume = .1
        self.sound_begin.volume = .02
        self.sound_galaxy.volume = .02
        self.sound_gameover_voice.volume = .02
        self.sound_gameover_impact.volume = .02
        self.sound_restart.volume = .02


    def reset_game(self):           # this function is called when the game ends and you want to restart
        self.current_offset_y = 0
        self.current_y_loop = 0
        self.current_speed_x = 0
        self.current_offset_x = 0

        # have to pre fill the first 10 tiles and generate random tiles gain
        self.tiles_coordinates = []
        self.score_txt = "SCORE: 0"          # this is to reset the score to 0 each time before the game starts
        self.pre_fill_tiles_coordinates()
        self.generate_tiles_coordinates()

        self.state_game_over = False

    def is_desktop(self):       # determine if it is mobile or pc user/platform of user
        if platform in ('linux', 'win', 'macosx'):
            return True
        return False

    def init_ship(self):
        with self.canvas:
            Color(0,0,0)        # because we want the ship to be black in colour
            self.ship = Triangle()

    def update_ship(self):
        center_x = self.width/2     # cant give pixel width because it will not adjust according to screen size, so need to give a percentage of the screen instead
        base_y = self.ship_base_y * self.height
        ship_width_x = self.ship_width * self.width
        center_y = self.ship_height * self.height + base_y
        left_x = center_x - ship_width_x/2
        right_x = center_x + ship_width_x/2

        self.ship_coordinates[0] = (left_x, base_y)
        self.ship_coordinates[1] = (center_x, center_y)
        self.ship_coordinates[2] = (right_x, base_y)

        x1, y1 = self.transform(left_x, base_y)
        x2, y2 = self.transform(center_x, center_y)
        x3, y3 = self.transform(right_x, base_y)

        self.ship.points = [x1, y1, x2, y2, x3, y3]

    def check_ship_collision(self):
        for i in range(0, len(self.tiles_coordinates)):
            ti_x, ti_y = self.tiles_coordinates[i]
            if ti_y > self.current_y_loop + 1:      # if the current tile is 2 ranks above the current position of the ship, there is no need to check it
                return False
            if self.check_collision(ti_x, ti_y):
                return True
        return False

    def check_collision(self, ti_x, ti_y):
        xmin, ymin = self.get_tile_coordinates(ti_x, ti_y)
        xmax, ymax = self.get_tile_coordinates(ti_x+1, ti_y+1)
        for i in range(0,3):
            px, py = self.ship_coordinates[i]
            if xmin <= px <= xmax and ymin <= py <= ymax:       # to check that the point in the ship is within the bottom tile
                return True
        return False


    def init_tiles(self):
        with self.canvas:
            Color(1, 1, 1)
            for i in range(0, self.number_of_tiles):
                self.tiles.append(Quad())       # can add the appropriate number of Quads into the list

    def pre_fill_tiles_coordinates(self):
        for i in range(0, 10):
            self.tiles_coordinates.append((0,i))            # this works because there are already more tiles than the supposed number of tiles in the generate tiles portion, so no additional tiles will be created

    def generate_tiles_coordinates(self):
        last_y = 0
        last_x = 0
        # remove coordinates/tiles that are out of the screen
        for i in range(len(self.tiles_coordinates)-1, -1, -1):
            if self.tiles_coordinates[i][1] < self.current_y_loop:      # checking that the tile is out of the screen
                del self.tiles_coordinates[i]

        if len(self.tiles_coordinates) > 0:
            last_coordinates = self.tiles_coordinates[-1]               # getting the largest coordinate values
            last_y = last_coordinates[1] + 1
            last_x = last_coordinates[0]

        for i in range(len(self.tiles_coordinates), self.number_of_tiles):
            r = random.randint(0, 2)               # generate a random x coordinate
            start_index = -int(self.number_of_vlines / 2) + 1
            end_index = start_index + self.number_of_vlines - 1
            # 0 -> straight, 1 -> right, 2 -> left
            if last_x >= end_index - 1:     # if the tile is all the way to the end of the right side of the grid, force it left
                r = 2
            if last_x <= start_index:   # if the tile is all the way to the end of the left side of the grid, force it right
                r = 1

            self.tiles_coordinates.append((last_x, last_y))       # appending the tile coordinates into the tiles_coordinates list
            # shape of tiles is either   #                               #
            #                           ##              OR               ##
            if r == 1:
                last_x += 1
                self.tiles_coordinates.append((last_x, last_y))
                last_y += 1
                self.tiles_coordinates.append((last_x, last_y))
            if r == 2:
                last_x -= 1
                self.tiles_coordinates.append((last_x, last_y))
                last_y += 1
                self.tiles_coordinates.append((last_x, last_y))
            last_y += 1

    def init_vertical_lines(self):
        with self.canvas:
            Color(1, 1, 1)
            # self.line = Line(points=[100, 0, 100, 100, 100, self.height])
            # cannot just take the self.width/2 to get the line to be created in the middle because the width of the screen is initialised
            # as 100 at the start so it will not change according to the screen size
            for i in range(0, self.number_of_vlines):       # the vertical lines are appendable and mutable in a list
                self.vertical_lines.append(Line())      # this is to add the allocated number of vertical lines into the screen by creating the line object

    def get_line_x_from_index(self, index):
        center_line_x = self.perspective_point_x
        spacing = self.vlines_spacing * self.width
        offset = index - 0.5
        line_x = center_line_x + offset*spacing + self.current_offset_x
        return line_x

    def get_line_y_from_index(self, index):
        spacing_y = self.hlines_spacing * self.height
        line_y = index * spacing_y - self.current_offset_y      # deduct by the offset to create the illusion that you are moving forward in the game
        return line_y

    def get_tile_coordinates(self, ti_x, ti_y):
        ti_y = ti_y - self.current_y_loop       # this is to ensure that the tiles are evolving/moving forward without the previous white tiles
        x = self.get_line_x_from_index(ti_x)
        y = self.get_line_y_from_index(ti_y)
        return x, y

    def update_tiles(self):
        for i in range(0, self.number_of_tiles):
            tile = self.tiles[i]
            tile_coordinates = self.tiles_coordinates[i]
            xmin, ymin = self.get_tile_coordinates(tile_coordinates[0], tile_coordinates[1])
            xmax, ymax = self.get_tile_coordinates(tile_coordinates[0] + 1, tile_coordinates[1] + 1)

            x1, y1 = self.transform(xmin, ymin)
            x2, y2 = self.transform(xmin, ymax)
            x3, y3 = self.transform(xmax, ymax)
            x4, y4 = self.transform(xmax, ymin)

            tile.points = [x1, y1, x2, y2, x3, y3, x4, y4]     # 1st coordinates are bottom left, then top left, then top right, then bottom right, need to go in an order

    def update_vertical_lines(self):
        # center_line_x = int(self.width/2)
        # spacing = self.vlines_spacing * self.width
        # self.line.points = [center_x, 0, center_x, 100, center_x, self.height]
        # offset = -int(self.number_of_vlines/2) + 0.5      # creating a variable for the 2 sides of the screen that are split up by the middle line, forming the spacing between them
                                                          # the .5 is added so that there is a space for the ship to move in the space in the middle
        start_index = -int(self.number_of_vlines/2) + 1
        for i in range(start_index, start_index+self.number_of_vlines):
            line_x = self.get_line_x_from_index(i)

            x1, y1 = self.transform(line_x, 0)
            x2, y2 = self.transform(line_x, self.height)
            self.vertical_lines[i].points = [x1, y1, x2, y2]      # the lines will inherit properties from the Line class

    def init_horizontal_lines(self):
        with self.canvas:
            Color(1, 1, 1)
            # self.line = Line(points=[100, 0, 100, 100, 100, self.height])
            # cannot just take the self.width/2 to get the line to be created in the middle because the width of the screen is initialised
            # as 100 at the start so it will not change according to the screen size
            for i in range(0, self.number_of_hlines):       # the vertical lines are appendable and mutable in a list
                self.horizontal_lines.append(Line())      # this is to add the allocated number of vertical lines into the screen by creating the line object

    def update_horizontal_lines(self):
        start_index = -int(self.number_of_vlines / 2) + 1
        end_index =  start_index + self.number_of_vlines - 1

        xmin = self.get_line_x_from_index(start_index)       # the xmin and xmax value is to make sure that the lines follow a grid structure and the horizontal lines stop at the right position
        xmax = self.get_line_x_from_index(end_index)     # the offset value is negative that is why the signs are inversed for xmin and xmax
        spacing_y = self.hlines_spacing*self.height

        for i in range(0, self.number_of_hlines):
            line_y = self.get_line_y_from_index(i)

            x1, y1 = self.transform(xmin, line_y)
            x2, y2 = self.transform(xmax, line_y)
            self.horizontal_lines[i].points = [x1, y1, x2, y2]      # the lines will inherit properties from the Line class

    def update(self, dt):       # the update function calls all the functions that need to be updated in the file, for each frame of the game
        # delta time describes the difference in time between the previous frame drawn and the current frame
        # print("dt: "+ str(dt*60))     # this is just to show that the code is updating at 60fps
        # updating both the horizontal and vertical lines in this update function at the rate of delta time
        time_factor = dt*60     # if we spend more/less time between 2 update calls, we need to update the speed of the program because the time is proportional to the speed.
        # so if we spend more than 1 second for each call of the function, we should increase the speed of movement of the horizontal lines to make up for the "lost" time and vice versa.
        # this allows us to make the same progression regardless of device
        self.update_vertical_lines()
        self.update_horizontal_lines()
        self.update_tiles()
        self.update_ship()

        # to prevent the ship from moving when the game is over
        if not self.state_game_over and self.state_game_has_started:
            speed = self.speed_y * self.height / 100              # this is to make sure that the vertical speed changes proportionally to the size of the screen
            self.current_offset_y += speed*time_factor      # adding to the offset creates the illusion that the horizontal lines are moving downwards, so it is moving upwards (vertically)
                                                                   # we increment our vertical speed for each frame

            spacing_y = self.hlines_spacing * self.height
            while self.current_offset_y >= spacing_y:      # always doing all the calculations in 2D
                self.current_offset_y -= spacing_y
                self.current_y_loop += 1
                self.generate_tiles_coordinates()       # need to call this function because it changes after each update
                self.score_txt = "SCORE: " + str(self.current_y_loop)
                # this will create the illusion of looping because everytime the offset is greater than the spacing, the offset is will just be deducted

            SPEED_x = self.current_speed_x * self.width/100       # this is to make sure that the horizontal speed changes proportionally to the size of the screen
            self.current_offset_x += SPEED_x * time_factor  # horizontal speed (left to right), only changes when the button is pressed

        if not self.check_ship_collision() and not self.state_game_over:        # check if the game is already over and the ship has not collided
            self.state_game_over = True
            self.menu_title = "G  A  M  E   O  V  E  R"
            self.menu_button_title = "RESTART"
            self.menu_widget.opacity = 1
            self.sound_music1.stop()
            self.sound_gameover_impact.play()
            # this is to create a delay between the impact and the sound saying game over
            Clock.schedule_once(self.play_game_over_voice_sound, 2)

    def play_game_over_voice_sound(self, dt):
        # this ensures that if the game has restarted the game over voiceover will not be played
        if self.state_game_over:
            self.sound_gameover_voice.play()

    def on_menu_button_pressed(self):
        print("BUTTON")
        if self.state_game_over:
            self.sound_restart.play()
        else:
            self.sound_begin.play()
        # need to do this before the state of the game is resetted
        self.reset_game()
        self.sound_music1.play()
        self.state_game_has_started = True
        self.menu_widget.opacity = 0

class GalaxyApp(App):
    pass

GalaxyApp().run()
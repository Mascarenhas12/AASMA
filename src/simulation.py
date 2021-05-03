from drone import *
from map2 import *
from weather import *
from sector import *
from button import *
import time


class Simulation:
    def __init__(self):
        pygame.init()
        self.running, self.playing = True, True
        self.UP_KEY, self.DOWN_KEY, self.START_KEY, self.BACK_KEY = False, False, False, False
        self.screen = pygame.display.set_mode((DISPLAY_W, DISPLAY_H))
        # use to draw and do update to tiles
        self.tile_group = pygame.sprite.Group()
        # use to draw and do update to drones
        self.drone_group = pygame.sprite.Group()
        # to put created tiles dont know/can do the same with the Group above
        self.tile_dict = {}
        # to put created tiles dont know/can do the same with the Group above
        self.drone_list = []
        self.wind = Wind(
            random.choice([Direction.North, Direction.South, Direction.East, Direction.West]),
            random.randint(1, 10))  # Static for testing
        self.wind_dysplay = button(WHITE, 40, 120, 180, 30, "Wind direction: " + str(self.wind.direction))
        self.wildfire_list: List[Wildfire] = []

        self.sector_list: List[Sector] = []

        # button and variable that indicates if sim is in step or continuose mode
        self.step_button = None
        self.step = False

        # button and variable that make sim do one step in step mode
        self.step_next_button = None
        self.step_pause = False

        # button and var that inidcates to create reactive drones
        self.reactive_drone_button = None
        self.create_reactive_drone = False

        # button and var that indicates to create hybrid drones
        self.hydrid_drone_button = None
        self.create_hybrid_drone = False

        # button and var that inidcates to create hybrid coop drones
        self.coop_drone_button = None
        self.create_hybrid_coop_drone = False

        self.drone_not_chosen = True

    def simulation_loop(self):
        self.initial_draw()
        while self.drone_not_chosen and self.playing and self.running:
            self.check_events()
        self.init_and_draw_drones()
        while self.playing:
            self.check_events()
            for agent in self.drone_list:
                agent.agent_decision()
            for wild in self.wildfire_list:
                update_wildfire(wild)
                expand_wildfire(wild, self.tile_dict, self.wind)

            for sector in self.sector_list:
                if sector.calculate_fire_alert(self.wildfire_list):
                    print("FIRE! in sector " + str(sector.sectorID))
            self.update()
            self.draw()
            self.reset_keys()
            time.sleep(1)
            while self.step and self.step_pause and self.playing and self.running:
                self.check_events()
            self.step_pause = True

    def check_events(self):
        for event in pygame.event.get():
            mouse_position = pygame.mouse.get_pos()
            if event.type == pygame.QUIT:
                self.running, self.playing = False, False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self.START_KEY = True
                if event.key == pygame.K_BACKSPACE:
                    self.BACK_KEY = True
                if event.key == pygame.K_DOWN:
                    self.DOWN_KEY = True
                if event.key == pygame.K_UP:
                    self.UP_KEY = True
            if event.type == pygame.MOUSEBUTTONDOWN:
                if self.step_button.is_over(mouse_position):
                    self.step = not self.step
                    self.step_button.text = 'step:' + str(self.step)
                if self.step_next_button.is_over(mouse_position):
                    self.step_pause = False
                if self.reactive_drone_button.is_over(mouse_position):
                    self.create_reactive_drone = True
                    self.create_hybrid_drone = False
                    self.create_hybrid_coop_drone = False
                    self.drone_not_chosen = False
                if self.hydrid_drone_button.is_over(mouse_position):
                    self.create_hybrid_drone = True
                    self.create_reactive_drone = False
                    self.create_hybrid_coop_drone = False
                    self.drone_not_chosen = False
                if self.coop_drone_button.is_over(mouse_position):
                    self.create_hybrid_coop_drone = True
                    self.create_reactive_drone = False
                    self.create_hybrid_drone = False
                    self.drone_not_chosen = False

    def reset_keys(self):
        self.UP_KEY, self.DOWN_KEY, self.START_KEY, self.BACK_KEY = False, False, False, False

    # update things

    def update(self):
        self.tile_group.update()
        self.drone_group.update()

    def update_tiles(self):
        for tile in self.tile_dict.values():
            if tile.on_fire:
                color = ORANGE
            elif tile.integrity == 0:
                color = BLACK
            elif tile.__class__ == Population:
                color = RED
            elif tile.__class__ == Forest:
                color = GREEN
            elif tile.__class__ == Road:
                color = LIGHTGREY
            else:
                color = BLUE
            tile.image.fill(color)

    # draw things

    def draw(self):
        self.update_tiles()
        self.draw_tiles()
        self.draw_grid()
        self.draw_drones()
        self.draw_buttons()
        pygame.display.flip()

    def initial_draw(self):
        self.update_tiles()
        self.draw_tiles()
        self.draw_grid()
        self.draw_buttons()
        pygame.display.flip()

    def draw_grid(self):
        for x in range(0, GRID_W + 1, TILESIZE):
            pygame.draw.line(self.screen, WHITE, (x + GRID_MARGIN_X, GRID_MARGIN_Y),
                             (x + GRID_MARGIN_X, GRID_H + GRID_MARGIN_Y))
        for y in range(0, GRID_H + 1, TILESIZE):
            pygame.draw.line(self.screen, WHITE, (GRID_MARGIN_X, y + GRID_MARGIN_Y),
                             (GRID_W + GRID_MARGIN_X, y + GRID_MARGIN_Y))

    def draw_tiles(self):
        self.tile_group.draw(self.screen)

    def draw_drones(self):
        self.drone_group.draw(self.screen)

    def draw_buttons(self):
        self.step_button.draw(self.screen)
        self.step_next_button.draw(self.screen)
        self.reactive_drone_button.draw(self.screen)
        self.hydrid_drone_button.draw(self.screen)
        self.coop_drone_button.draw(self.screen)
        self.wind_dysplay.draw(self.screen)

    # initiate and create things

    def initiate(self):
        self.create_tiles()
        self.expand_priority()
        self.create_sectors()
        self.create_wildfires()
        self.create_buttons()

    def create_tiles(self):
        for y in range(0, 32, 1):
            for x in range(0, 32, 1):
                if sim_map2[y][x][0] == "population":
                    tile = Population(self, x, y)
                elif sim_map2[y][x][0] == "road":
                    tile = Road(self, x, y)
                elif sim_map2[y][x][0] == "forest":
                    tile = Forest(self, x, y)
                else:  # Water
                    tile = Water(self, x, y)
                self.tile_group.add(tile)
                self.tile_dict[tile.point] = tile

    def expand_priority(self):
        q = []

        for tile in self.tile_dict.values():
            if tile.priority == 10:
                q.append(tile)

        while len(q) != 0:
            tile = q.pop()
            priority = tile.priority - 1
            for n in get_neighbours(tile, self.tile_dict):
                if n.priority >= priority or n in q:
                    continue
                n.priority = priority
                q.append(n)

        """for tile in self.tile_dict.values():
            print(tile)"""

    def create_reactive_drones(self):
        drone = DroneReactive(self, 16, 16)
        self.drone_group.add(drone)
        self.drone_list.append(drone)

    def create_hybrid_drones(self):
        drone = DroneHybrid(self, 16, 16)
        self.drone_group.add(drone)
        self.drone_list.append(drone)

    def create_coop_hybrid_drones(self):
        drone = DroneHybridCoop(self, 16, 16)
        self.drone_group.add(drone)
        self.drone_list.append(drone)

    def create_sectors(self):
        sector_id = 1
        sector_size = 8
        for y in range(0, 32 // sector_size, 1):
            for x in range(0, 32 // sector_size, 1):
                # id, probability per fire, size
                sector = Sector(sector_id, 16 / 64, sector_size)
                sector_id = sector_id + 1
                sector.create_sector(x * sector_size, y * sector_size)
                self.sector_list.append(sector)

    def create_wildfires(self):
        point = Point(16, 16)
        fire = self.tile_dict[Point(16, 16)]
        fire.on_fire = True
        fire.image.fill(ORANGE)
        fire.fire_intensity = random.randint(1, 10)
        wild = Wildfire(1, point, 1)
        wild.add_fire(fire)
        self.wildfire_list.append(wild)

    def create_buttons(self):
        self.step_button = button(WHITE, 40, 40, 180, 30, 'step:' + str(self.step))
        self.step_next_button = button(WHITE, 40, 80, 180, 30, 'next step')
        self.reactive_drone_button = button(WHITE, 250, 40, 160, 30, 'Start with reative drones')
        self.hydrid_drone_button = button(WHITE, 425, 40, 160, 30, 'Start with hybrid drones')
        self.coop_drone_button = button(WHITE, 600, 40, 160, 30, 'Start with hybrid coop drones')

    def init_and_draw_drones(self):
        if self.create_reactive_drone:
            self.create_reactive_drones()

        if self.create_hybrid_drone:
            self.create_hybrid_drones()

        if self.create_hybrid_coop_drone:
            self.create_coop_hybrid_drones()

        self.draw_drones()

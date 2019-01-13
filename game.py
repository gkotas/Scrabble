import pygame
import os

from spritesheet import Spritesheet
from constants import *


class SceneBase:
    def __init__(self):
        self.next = self

    def process_input(self, events, pressed_keys):
        print("uh-oh, you didn't override this in the child class")

    def update(self):
        print("uh-oh, you didn't override this in the child class")

    def render(self, screen):
        print("uh-oh, you didn't override this in the child class")

    def SwitchToScene(self, next_scene):
        self.next = next_scene

    def Terminate(self):
        self.SwitchToScene(None)


def run_game(width, height, fps, starting_scene):
    pygame.init()
    screen = pygame.display.set_mode((width, height))
    clock = pygame.time.Clock()

    active_scene = starting_scene

    while active_scene:
        pressed_keys = pygame.key.get_pressed()

        # Event filtering
        filtered_events = []
        for event in pygame.event.get():
            quit_attempt = False
            if event.type == pygame.QUIT:
                quit_attempt = True
            elif event.type == pygame.KEYDOWN:
                alt_pressed = pressed_keys[pygame.K_LALT] or \
                              pressed_keys[pygame.K_RALT]
                if event.key == pygame.K_ESCAPE:
                    quit_attempt = True
                elif event.key == pygame.K_F4 and alt_pressed:
                    quit_attempt = True

            if quit_attempt:
                active_scene.Terminate()
            else:
                filtered_events.append(event)

        active_scene.process_input(filtered_events, pressed_keys)
        needs_update = active_scene.update()
        active_scene.render(screen)

        active_scene = active_scene.next

        # if needs_update:
        pygame.display.flip()
        clock.tick(fps)


# The rest is code where you implement your game using the Scenes model
def tile_to_pixel(x, y):
    """
    Takes an x, y coordinate of the board and translates into the
    corresponding pixel coordinate.

    Note: 0, 0 is top left of board.
    """
    pixel_x = 2 + 40*x
    pixel_y = 2 + 40*y
    return pixel_x, pixel_y

def pixel_to_tile(x, y):
    """
    Takes an x, y coordinate of the cursor and translates into the
    corresponding tile coordinate.
    """
    tile_x = (x - 2)//40
    tile_y = (y - 2)//40
    return tile_x, tile_y


class TitleScene(SceneBase):
    def __init__(self):
        SceneBase.__init__(self)
        self.needs_update = False

    def process_input(self, events, pressed_keys):
        self.needs_update = False
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                # Move to the next scene when the user pressed Enter
                self.SwitchToScene(GameScene())
                self.needs_update = True

    def update(self):
        return self.needs_update

    def render(self, screen):
        # For the sake of brevity, the title scene is a blank red screen
        screen.fill((255, 0, 0))


class Board(pygame.sprite.Sprite):
    def __init__(self, image_file, location):
        pygame.sprite.Sprite.__init__(self)  # call Sprite initializer
        self.image = pygame.image.load(image_file)
        self.rect = self.image.get_rect()
        self.rect.left, self.rect.top = location


class Tile(pygame.sprite.Sprite):
    def __init__(self, image, location):
        pygame.sprite.Sprite.__init__(self)  # call Sprite initializer
        self.image = image
        self.rect = self.image.get_rect()
        self.rect.left, self.rect.top = location
        self.tray_position = location

    def move_to_tile(self, tile_x, tile_y):
        """Sets the position to the tile coordinates."""
        self.rect.left, self.rect.top = tile_to_pixel(tile_x, tile_y)

    def return_to_tray(self):
        """Sets the position back to its tray location."""
        self.rect.left, self.rect.top = self.tray_position


class GameScene(SceneBase):
    def __init__(self):
        SceneBase.__init__(self)
        self.board = Board('imgs/board.jpg', [0, 0])
        self.letter_ss = Spritesheet('imgs/letters.jpg')
        self.game_tiles = []
        self.player_tiles = []
        self.selected_tile = None
        self.offset_x = 0
        self.offset_y = 0
        self.needs_update = False

        for i in range(7):
            self.player_tiles.append(Tile(self.letter_ss.image_at(LETTERS[chr(ord('a') + i)]), PLAYER_TILE_POSITIONS[i]))

        self.letter = ord('a')
        self.x = 0
        self.y = 0
        self.tile = Tile(self.letter_ss.image_at(LETTERS['a']), [2, 2])
        self.tile2 = Tile(self.letter_ss.image_at(LETTERS['b']), [41, 2])

    def process_input(self, events, pressed_keys):
        self.needs_update = False

        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.letter += 1
                    if self.letter > ord('z'):
                        self.letter = ord('a')

                elif event.key == pygame.K_UP:
                    self.y = (self.y - 1) % 15
                elif event.key == pygame.K_DOWN:
                    self.y = (self.y + 1) % 15
                elif event.key == pygame.K_LEFT:
                    self.x = (self.x - 1) % 15
                elif event.key == pygame.K_RIGHT:
                    self.x = (self.x + 1) % 15

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:
                    for tile in self.player_tiles:
                        if tile.rect.collidepoint(event.pos):
                            self.selected_tile = tile
                            mouse_x, mouse_y = event.pos
                            self.offset_x = tile.rect.left - mouse_x
                            self.offset_y = tile.rect.top - mouse_y

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    if self.selected_tile:
                        self.needs_update = True
                        tile_x, tile_y = pixel_to_tile(*event.pos)

                        # Move to valid tile otherwise return to tray
                        if 0 <= tile_x < 15 and 0 <= tile_y < 15:
                            self.selected_tile.move_to_tile(tile_x, tile_y)
                        else:
                            self.selected_tile.return_to_tray()

                        # Not selected anymore
                        self.selected_tile = None

            elif event.type == pygame.MOUSEMOTION:
                if self.selected_tile:
                    self.needs_update = True

                    mouse_x, mouse_y = event.pos
                    self.selected_tile.rect.left = mouse_x + self.offset_x
                    self.selected_tile.rect.top = mouse_y + self.offset_y


    def update(self):
        self.tile.image = self.letter_ss.image_at(LETTERS[chr(self.letter)])
        self.tile.rect.left, self.tile.rect.top = tile_to_pixel(self.x, self.y)

        return self.needs_update

    def render(self, screen):
        # The game scene is just a blank blue screen
        screen.fill((0, 0, 255))
        screen.blit(self.board.image, self.board.rect)
        screen.blit(self.tile.image, self.tile.rect)
        screen.blit(self.tile2.image, self.tile2.rect)

        for tile in self.player_tiles:
            screen.blit(tile.image, tile.rect)


if __name__ == '__main__':
    run_game(800, 800, 30, TitleScene())

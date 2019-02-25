import pygame
import os
from random import shuffle

from constants import *
from scrabble import Scrabble
from spritesheet import Spritesheet


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
        active_scene.update()
        active_scene.render(screen)

        active_scene = active_scene.next

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

    def process_input(self, events, pressed_keys):
        self.needs_update = False
        for event in events:
            if event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN:
                # Move to the next scene when the user pressed Enter
                self.SwitchToScene(GameScene())
                self.needs_update = True

    def update(self):
        pass

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
    def __init__(self, letter, spritesheet, location):
        pygame.sprite.Sprite.__init__(self)  # call Sprite initializer
        self.image = spritesheet.image_at(LETTERS[letter])
        self.letter = letter
        self.rect = self.image.get_rect()
        self.rect.left, self.rect.top = location
        self.tray_position = location
        self.on_board = False
        self.board_x = 0
        self.board_y = 0

    def move(self, pos):
        """Moves the tile to either the board or back to the tray."""
        tile_x, tile_y = pixel_to_tile(*pos)

        # Move to valid tile otherwise return to tray
        if 0 <= tile_x < 15 and 0 <= tile_y < 15:
            self.rect.topleft = tile_to_pixel(tile_x, tile_y)
            self.on_board = True
            self.board_x = tile_x
            self.board_y = tile_y
        else:
            self.rect.topleft = self.tray_position
            self.on_board = False

    def tile(self):
        """Returns the tuple (board_x, board_y, letter)."""
        return self.board_x, self.board_y, self.letter

    def rerack(self):
        """Moves the tile back to the rack."""
        self.rect.topleft = self.tray_position


class GameScene(SceneBase):
    def __init__(self):
        SceneBase.__init__(self)
        self.scrabble = Scrabble(True)
        self.board = Board('imgs/board.jpg', [0, 0])
        self.letter_ss = Spritesheet('imgs/letters.jpg')
        self.player_tiles = []
        self.game_tiles = []
        self.selected_tile = None
        self.offset_x = 0
        self.offset_y = 0

        for i, letter in enumerate(self.scrabble.get_rack()):
            self.player_tiles.append(Tile(letter, self.letter_ss, PLAYER_TILE_POSITIONS[i]))

    def process_input(self, events, pressed_keys):
        for event in events:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    self._submit_turn()

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
                        if self._hits_tile(event.pos, self.selected_tile):
                            self.selected_tile.rerack()
                        else:
                            self.selected_tile.move(event.pos)

                        # Not selected anymore
                        self.selected_tile = None

            elif event.type == pygame.MOUSEMOTION:
                if self.selected_tile:
                    mouse_x, mouse_y = event.pos
                    self.selected_tile.rect.left = mouse_x + self.offset_x
                    self.selected_tile.rect.top = mouse_y + self.offset_y


    def update(self):
        pass

    def render(self, screen):
        # The game scene is just a blank blue screen
        screen.fill((0, 0, 255))
        screen.blit(self.board.image, self.board.rect)

        for tile in self.player_tiles:
            screen.blit(tile.image, tile.rect)

        for tile in self.game_tiles:
            screen.blit(tile.image, tile.rect)

        # Make selected tile on top
        if self.selected_tile:
            screen.blit(self.selected_tile.image, self.selected_tile.rect)

    def _hits_tile(self, pos, ignore=None):
        """Returns true if the position hits a tile."""
        for tile in self.player_tiles + self.game_tiles:
            if tile == ignore:
                continue
            if tile.rect.collidepoint(pos):
                return True
        return False

    def _submit_turn(self):
        """
        Submits the turn to the scrabble backend. Moves the player tiles to
        game tiles and updates the player tiles.
        """
        # Get a list of tiles that will be sumbit
        tiles = []
        for tile in self.player_tiles:
            if tile.on_board:
                tiles.append(tile.tile())

        if self.scrabble.submit_turn(tiles):
            # Valid turn, move all played tiles to game.
            for tile in self.player_tiles:
                if tile.on_board:
                    self.game_tiles.append(tile)

            # Update the player tiles
            self.player_tiles = []
            for i, letter in enumerate(self.scrabble.get_rack()):
                self.player_tiles.append(Tile(letter, self.letter_ss, PLAYER_TILE_POSITIONS[i]))

        else:
            # Invalid turn, return all tiles to rack
            for tile in self.player_tiles:
                tile.rerack()


if __name__ == '__main__':
    run_game(800, 800, 30, TitleScene())

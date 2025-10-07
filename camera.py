from constants import SCREEN_WIDTH, LEVEL_WIDTH


class Camera:
    def __init__(self):
        self.x = 0
        self.y = 0

    def update(self, target):
        self.x = target.rect.centerx - SCREEN_WIDTH // 2
        if self.x < 0:
            self.x = 0
        if self.x > LEVEL_WIDTH - SCREEN_WIDTH:
            self.x = LEVEL_WIDTH - SCREEN_WIDTH



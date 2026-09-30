import random
import pygame

GRID_SIZE = 8
TILE_SIZE = 60
GEM_COLORS = [
    (220, 50, 50),   # Red
    (50, 200, 50),   # Green
    (50, 100, 240),  # Blue
    (240, 200, 40),  # Yellow
    (180, 50, 220),  # Purple
    (240, 130, 40),  # Orange
]


class Gem:
   
    def __init__(self, color, target_row, col, is_bomb=False):
        self.color = color
        self.target_row = target_row
        self.col = col
        self.is_bomb= is_bomb # flag to identify bomb gems
        self.current_y = (target_row - 2) * TILE_SIZE
        self.target_y = target_row * TILE_SIZE
        self.fall_speed = 12.0

    def update(self):
        if self.current_y < self.target_y:
            self.current_y += self.fall_speed
            if self.current_y > self.target_y:
                self.current_y = self.target_y

    def is_animating(self):
        return self.current_y < self.target_y


class Board:
    """Manages animated gem grid, gravity drops, score, and game limits."""

    def __init__(self, offset_x, offset_y, target_score=500, max_moves=20):
        self.offset_x = offset_x
        self.offset_y = offset_y
        self.target_score = target_score
        self.max_moves = max_moves
        self.grid = [[None for _ in range(GRID_SIZE)] for _ in range(GRID_SIZE)]
        self.selected = None
        self.score = 0
        self.moves_remaining = max_moves
        self.reset()

    def reset(self):
        """Reset board grid, score, and move limits."""
        self.score = 0
        self.moves_remaining = self.max_moves
        self.selected = None
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                color = random.choice(GEM_COLORS)
                gem = Gem(color, r, c)
                gem.current_y = gem.target_y  # Snap instantly on initial start
                self.grid[r][c] = gem

        self.resolve_matches()

    def is_animating(self):
        """Returns True if any gem is currently dropping down."""
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.grid[r][c] and self.grid[r][c].is_animating():
                    return True
        return False

    def swap_gems(self, pos1, pos2):
        """Swap positions and target render coordinates of two gems."""
        r1, c1 = pos1
        r2, c2 = pos2

        g1, g2 = self.grid[r1][c1], self.grid[r2][c2]
        self.grid[r1][c1], self.grid[r2][c2] = g2, g1

        if self.grid[r1][c1]:
            self.grid[r1][c1].target_row = r1
            self.grid[r1][c1].target_y = r1 * TILE_SIZE
            self.grid[r1][c1].current_y = r1 * TILE_SIZE

        if self.grid[r2][c2]:
            self.grid[r2][c2].target_row = r2
            self.grid[r2][c2].target_y = r2 * TILE_SIZE
            self.grid[r2][c2].current_y = r2 * TILE_SIZE

    def is_adjacent(self, pos1, pos2):
        r1, c1 = pos1
        r2, c2 = pos2
        return abs(r1 - r2) + abs(c1 - c2) == 1

    def find_matches(self):
        """Scan grid for horizontal and vertical 3-in-a-row color matches."""
        matched = set()
        to_spawn_bombs=set()

        # Horizontal matches
        for r in range(GRID_SIZE):
            c = 0
            while c < GRID_SIZE:
                color = self.grid[r][c].color if self.grid[r][c] else None
                if color is None:
                    c += 1
                    continue
                match_len = 1
                while c + match_len < GRID_SIZE and self.grid[r][c + match_len] and self.grid[r][c + match_len].color == color:
                    match_len += 1
                
                if match_len >= 3:
                    for i in range(match_len):
                        matched.add((r, c + i))
                    if match_len >= 4:
                        to_spawn_bombs.add((r, c)) # Mark bomb spawn location
                c += match_len

        # Vertical matches
        for c in range(GRID_SIZE):
            r = 0
            while r < GRID_SIZE:
                color = self.grid[r][c].color if self.grid[r][c] else None
                if color is None:
                    r += 1
                    continue
                match_len = 1
                while r + match_len < GRID_SIZE and self.grid[r + match_len][c] and self.grid[r + match_len][c].color == color:
                    match_len += 1
                
                if match_len >= 3:
                    for i in range(match_len):
                        matched.add((r + i, c))
                    if match_len >= 4:
                        to_spawn_bombs.add((r, c)) # Mark bomb spawn location
                r += match_len

        return matched, to_spawn_bombs

    def drop_and_refill(self):
        for c in range(GRID_SIZE):
            empty_slots = 0
            for r in range(GRID_SIZE - 1, -1, -1):
                if self.grid[r][c] is None:
                    empty_slots += 1
                elif empty_slots > 0:
                    gem = self.grid[r][c]
                    gem.target_row = r + empty_slots
                    gem.target_y = (r + empty_slots) * TILE_SIZE
                    self.grid[r + empty_slots][c] = gem
                    self.grid[r][c] = None

            for r in range(empty_slots):
                color = random.choice(GEM_COLORS)
                gem = Gem(color, r, c)
                gem.current_y = -((empty_slots - r) * TILE_SIZE)
                self.grid[r][c] = gem
    def resolve_matches(self):
        total_cleared = 0
        multiplier=1 # 1x for initial match, 2x for secondary drop, 3x for tertiary
        while True:
            matches, bombs_to_spawn = self.find_matches()
            if not matches:
                break
            #Award points for this cascade later multiplied by the current chain level
            expanded_clears = set(matches)
            for r, c in matches:
                if self.grid[r][c] and self.grid[r][c].is_bomb:
                    # Detonate entire row and column!
                    for i in range(GRID_SIZE):
                        expanded_clears.add((r, i))
                        expanded_clears.add((i, c))
            
            total_cleared += len(matches) * 10 * multiplier
            multiplier += 1
            for r, c in matches:
                self.grid[r][c] = None
            self.drop_and_refill()
            for r, c in bombs_to_spawn:
                if self.grid[r][c]:
                    self.grid[r][c].is_bomb = True
        return total_cleared

    def process_swap(self, pos1, pos2):
        if not self.is_adjacent(pos1, pos2) or self.is_game_over() or self.is_animating():
            return False

        self.swap_gems(pos1, pos2)
        matches = self.find_matches()

        # BUG SYMPTOM:
        # Move count decrements on EVERY swap attempt even invalid ones.
        if not matches:
            self.swap_gems(pos1, pos2)  # Revert invalid swap
            return False

        self.moves_remaining -= 1


        points_earned=self.resolve_matches()
        self.score += points_earned
        return True

    def is_game_over(self):
        return self.score >= self.target_score or self.moves_remaining <= 0

    def check_result(self):
        if self.score >= self.target_score:
            return "WIN"
        if self.moves_remaining <= 0:
            return "LOSS"
        return None
    def find_hint(self):
        """Finds the first valid swap pair that produces a match."""
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                for dr, dc in [(0, 1), (1, 0)]:
                    r2, c2 = r + dr, c + dc
                    if 0 <= r2 < GRID_SIZE and 0 <= c2 < GRID_SIZE:
                        # Swap temporarily
                        self.grid[r][c], self.grid[r2][c2] = self.grid[r2][c2], self.grid[r][c]
                        matches, _ = self.find_matches()
                        # Swap back
                        self.grid[r][c], self.grid[r2][c2] = self.grid[r2][c2], self.grid[r][c]

                        if matches:
                            return (r, c), (r2, c2)
        return None

    def update(self):
        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                if self.grid[r][c]:
                    self.grid[r][c].update()

    def render(self, surface, hint_pair=None):
        board_rect = pygame.Rect(
            self.offset_x, self.offset_y, GRID_SIZE * TILE_SIZE, GRID_SIZE * TILE_SIZE
        )
        pygame.draw.rect(surface, (20, 22, 28), board_rect, border_radius=8)
        pygame.draw.rect(surface, (60, 65, 75), board_rect, width=3, border_radius=8)

        for r in range(GRID_SIZE):
            for c in range(GRID_SIZE):
                gem = self.grid[r][c]
                if gem:
                    x = self.offset_x + c * TILE_SIZE
                    y = self.offset_y + gem.current_y
                    tile_rect = pygame.Rect(x + 2, y + 2, TILE_SIZE - 4, TILE_SIZE - 4)

                    pygame.draw.rect(surface, gem.color, tile_rect, border_radius=10)
                    pygame.draw.rect(
                        surface, (255, 255, 255), tile_rect, width=1, border_radius=10
                    )

                if self.selected == (r, c):
                    sel_x = self.offset_x + c * TILE_SIZE
                    sel_y = self.offset_y + r * TILE_SIZE
                    sel_rect = pygame.Rect(sel_x + 2, sel_y + 2, TILE_SIZE - 4, TILE_SIZE - 4)
                    pygame.draw.rect(
                        surface, (255, 255, 255), sel_rect, width=4, border_radius=10
                    )
                    
                if gem.is_bomb:
                    # Draw a white pulsing ring or dark center core for Bomb Gems
                    center_x = x + TILE_SIZE // 2
                    center_y = int(self.offset_y + gem.current_y + TILE_SIZE // 2)
                    pygame.draw.circle(surface, (255, 255, 255), (center_x, center_y), TILE_SIZE // 4)
                    pygame.draw.circle(surface, (0, 0, 0), (center_x, center_y), TILE_SIZE // 6)
                
                #Render hint indicator if active
                if hint_pair:
                    pulse = int((pygame.time.get_ticks() // 200) % 2) * 2  # Simple pulsing width
                    for r, c in hint_pair:
                        hx = self.offset_x + c * TILE_SIZE
                        hy = self.offset_y + r * TILE_SIZE
                        hint_rect = pygame.Rect(hx + 2, hy + 2, TILE_SIZE - 4, TILE_SIZE - 4)
                        pygame.draw.rect(surface, (255, 255, 0), hint_rect, width=3 + pulse, border_radius=10)
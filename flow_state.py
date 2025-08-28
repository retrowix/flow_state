import sys
import random
from dataclasses import dataclass
from typing import List, Tuple

import pygame

# -------------------------
# Config / constants
# -------------------------
SCREEN_W, SCREEN_H = 720, 720
GRID_N = 5
BG = (0, 0, 0)
WHITE = (255, 255, 255)

# Distinct, bright-ish colors for pairs
PALETTE = [
    (244, 67, 54),    # red
    (76, 175, 80),    # green
    (33, 150, 243),   # blue
    (255, 193, 7),    # amber
    (156, 39, 176),   # purple
    (255, 87, 34),    # deep orange (spare)
    (0, 188, 212),    # cyan (spare)
]

# Fonts initialized after pygame.init()
FONT = None
FONT_BIG = None

@dataclass
class AppState:
    screen: pygame.Surface
    clock: pygame.time.Clock
    running: bool = True
    scene: str = "menu"    # "menu" | "config" | "run"
    num_pairs: int = 3     # 3, 4, or 5
    endpoints: List[Tuple[Tuple[int,int], Tuple[int,int]]] = None

# -------------------------
# Utility
# -------------------------
def grid_to_px(cell: Tuple[int, int], margin: int, cell_size: int) -> Tuple[int, int]:
    r, c = cell
    x = margin + c * cell_size + cell_size // 2
    y = margin + r * cell_size + cell_size // 2
    return x, y

def draw_text_center(surf, text, y, color=WHITE, big=False):
    font = FONT_BIG if big else FONT
    img = font.render(text, True, color)
    rect = img.get_rect(center=(SCREEN_W//2, y))
    surf.blit(img, rect)

def draw_button(surf, rect: pygame.Rect, label: str, hover: bool):
    pygame.draw.rect(surf, (32,32,32) if not hover else (64,64,64), rect, border_radius=10)
    pygame.draw.rect(surf, (96,96,96), rect, width=2, border_radius=10)
    img = FONT.render(label, True, WHITE)
    img_rect = img.get_rect(center=rect.center)
    surf.blit(img, img_rect)

def distinct_random_cells(k: int, n: int) -> List[Tuple[int,int]]:
    """Pick k distinct grid cells uniformly."""
    all_cells = [(r,c) for r in range(n) for c in range(n)]
    random.shuffle(all_cells)
    return all_cells[:k]

def generate_endpoints(num_pairs: int, n: int) -> List[Tuple[Tuple[int,int], Tuple[int,int]]]:
    """Simple random placement of endpoints (does not guarantee solvable; fine for MVP)."""
    # Heuristic: bias endpoints to be not too close to each other
    tries = 1000
    best = None
    best_score = -1
    for _ in range(tries):
        cells = distinct_random_cells(2*num_pairs, n)
        pairs = [(cells[2*i], cells[2*i+1]) for i in range(num_pairs)]
        # Score by sum of Manhattan distances (encourage spread)
        score = sum(abs(a[0]-b[0]) + abs(a[1]-b[1]) for a,b in pairs)
        if score > best_score:
            best_score = score
            best = pairs
    return best

# -------------------------
# Scenes
# -------------------------
def scene_menu(app: AppState):
    screen = app.screen
    mx, my = pygame.mouse.get_pos()

    screen.fill(BG)
    draw_text_center(screen, "Flow (prototype)", 130, big=True)
    draw_text_center(screen, "Use ↑/↓ or mouse; Enter/Click to select", 180)
    draw_text_center(screen, f"Pairs: {app.num_pairs} (change in Config)", 215, color=(180,180,180))

    button_w, button_h = 260, 60
    spacing = 20
    start_y = 280
    rects = [
        pygame.Rect((SCREEN_W - button_w)//2, start_y + i*(button_h+spacing), button_w, button_h)
        for i in range(3)
    ]
    labels = ["Run", "Config", "Quit"]

    hover_idx = -1
    for i, r in enumerate(rects):
        if r.collidepoint(mx, my):
            hover_idx = i
        draw_button(screen, r, labels[i], hover=r.collidepoint(mx, my))

    pygame.display.flip()

    # Input
    sel = None
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            app.running = False
        elif event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                # Pick by hover, else default to top
                if hover_idx == -1:
                    sel = 0
                else:
                    sel = hover_idx
            elif event.key in (pygame.K_q, pygame.K_ESCAPE):
                app.running = False
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, r in enumerate(rects):
                if r.collidepoint(mx, my):
                    sel = i
                    break

    if sel == 0:
        app.endpoints = generate_endpoints(app.num_pairs, GRID_N)
        app.scene = "run"
    elif sel == 1:
        app.scene = "config"
    elif sel == 2:
        app.running = False

def scene_config(app: AppState):
    screen = app.screen
    screen.fill(BG)

    draw_text_center(screen, "Config", 120, big=True)
    draw_text_center(screen, "Choose number of color pairs for 5x5:", 170)
    draw_text_center(screen, "[3]  [4]  [5]", 215)
    draw_text_center(screen, "Press 3/4/5, or click buttons. ESC to return.", 255, color=(180,180,180))

    mx, my = pygame.mouse.get_pos()
    button_w, button_h = 90, 60
    spacing = 20
    total_w = 3*button_w + 2*spacing
    x0 = (SCREEN_W - total_w)//2
    y0 = 320

    choices = [3,4,5]
    rects = [pygame.Rect(x0 + i*(button_w+spacing), y0, button_w, button_h) for i in range(3)]

    for i, r in enumerate(rects):
        hover = r.collidepoint(mx, my)
        val = choices[i]
        lbl = f"{val} pairs"
        draw_button(screen, r, lbl, hover)
        if val == app.num_pairs:
            pygame.draw.rect(screen, (200,200,200), r, width=3, border_radius=10)

    pygame.display.flip()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            app.running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                app.scene = "menu"
            elif event.key == pygame.K_3:
                app.num_pairs = 3
            elif event.key == pygame.K_4:
                app.num_pairs = 4
            elif event.key == pygame.K_5:
                app.num_pairs = 5
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i, r in enumerate(rects):
                if r.collidepoint(mx, my):
                    app.num_pairs = choices[i]

def draw_grid_and_endpoints(surface, endpoints, n=GRID_N):
    margin = 60
    grid_size = SCREEN_W - 2*margin
    cell = grid_size // n
    grid_w = cell * n
    x0 = (SCREEN_W - grid_w)//2
    y0 = (SCREEN_H - grid_w)//2

    # Grid background (optional subtle)
    pygame.draw.rect(surface, BG, (x0, y0, grid_w, grid_w))

    # Grid lines
    for i in range(n+1):
        x = x0 + i*cell
        y = y0 + i*cell
        pygame.draw.line(surface, WHITE, (x0, y), (x0 + grid_w, y), 2)
        pygame.draw.line(surface, WHITE, (x, y0), (x, y0 + grid_w), 2)

    # Endpoints as filled circles
    for idx, (a, b) in enumerate(endpoints):
        color = PALETTE[idx % len(PALETTE)]
        ax, ay = x0 + a[1]*cell + cell//2, y0 + a[0]*cell + cell//2
        bx, by = x0 + b[1]*cell + cell//2, y0 + b[0]*cell + cell//2
        radius = int(cell*0.32)
        pygame.draw.circle(surface, color, (ax, ay), radius)
        pygame.draw.circle(surface, color, (bx, by), radius)

def scene_run(app: AppState):
    screen = app.screen
    screen.fill(BG)

    draw_text_center(screen, f"5x5 • {app.num_pairs} pairs  —  ESC to menu", 28, color=(180,180,180))
    draw_grid_and_endpoints(screen, app.endpoints, GRID_N)

    pygame.display.flip()

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            app.running = False
        elif event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            app.scene = "menu"

# -------------------------
# Main
# -------------------------
def main():
    global FONT, FONT_BIG
    pygame.init()
    pygame.display.set_caption("Flow (prototype)")
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    clock = pygame.time.Clock()
    FONT = pygame.font.SysFont("arial", 24)
    FONT_BIG = pygame.font.SysFont("arial", 40, bold=True)

    app = AppState(screen=screen, clock=clock)

    while app.running:
        if app.scene == "menu":
            scene_menu(app)
        elif app.scene == "config":
            scene_config(app)
        elif app.scene == "run":
            scene_run(app)
        else:
            app.scene = "menu"

        app.clock.tick(60)

    pygame.quit()
    sys.exit(0)

if __name__ == "__main__":
    main()

import matplotlib.pyplot as plt
import pygame 
import numpy as np

from src.nasch_core import run_simulation, init_road, step
from src.config import L, LANES

# --- WIZUALIZACJA (PYGAME) ---
CELL_SIZE = 10                    # Rozmiar pojedynczej komórki (piksele)
ROAD_WIDTH = L * CELL_SIZE        # Szerokość wizualizowanej drogi
ROAD_HEIGHT = CELL_SIZE * 2       # Wysokość pasa ruchu
SCREEN_HEIGHT = ROAD_HEIGHT * 2 + 150   # Wysokość całego okna
SCREEN_WIDTH = ROAD_WIDTH + 50    # Szerokość całego okna

# Kolory (RGB)
CAR_COLOR = (255, 255, 255)       
BG_COLOR = (0, 0, 0)              
ROAD_COLOR = (50, 50, 50)   


def get_car_color(v, v_max):
    """Zwraca kolor samochodu w zależności od prędkości.
    
    Od czerwonego (v=0) do zielonego (v=v_max).
    
    Args:
        v (int): Prędkość pojazdu.
        v_max (int): Maksymalna prędkość.
    
    Returns:
        tuple: Kolor RGB.
    """
    if v <= 0:
        return (255, 0, 0)
    ratio = v / v_max
    red = int(255 * (1 - ratio))
    green = int(255 * ratio)
    return (red, green, 0)


def run_pygame_simulation(initial_density, v_max, p, steps_per_second=10):
    """Uruchamia dynamiczną symulację NaSch w oknie Pygame.
    
    Args:
        initial_density (float): Początkowa gęstość pojazdów.
        v_max (int): Maksymalna prędkość.
        p (float): Prawdopodobieństwo losowego spowolnienia.
        steps_per_second (int): Szybkość symulacji w FPS.
    """
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("NaSch: Symulacja Swobodnego Przepływu (Calibrated)")
    clock = pygame.time.Clock()
    
    road = init_road(L, initial_density, n_lanes=LANES)
    font = pygame.font.Font(None, 24)
    
    running = True
    paused = False
    total_steps = 0

    center_x = SCREEN_WIDTH // 2

    buttons = {
        "slower": pygame.Rect(center_x - 50, SCREEN_HEIGHT - 30, 20, 20),
        "faster": pygame.Rect(center_x + 50, SCREEN_HEIGHT - 30, 20, 20),
        "pause": pygame.Rect(center_x + 100, SCREEN_HEIGHT - 30, 20, 20),        
    }

    def draw_icon(name, rect):
        cx, cy = rect.center
        if name == "slower":
            pygame.draw.polygon(screen, (255, 255, 255), [
                (cx + 6, cy - 10), (cx - 8, cy), (cx + 6, cy + 10)                
            ])
        elif name == "faster":
            pygame.draw.polygon(screen, (255, 255, 255), [
                (cx - 6, cy - 10), (cx + 8, cy), (cx - 6, cy + 10)
            ])
        elif name == "pause":
            pygame.draw.rect(screen, (255, 255, 255), (cx - 8, cy - 10, 5, 20))
            pygame.draw.rect(screen, (255, 255, 255), (cx + 3, cy - 10, 5, 20))

    def draw_buttons():
        for name, rect in buttons.items():
            pygame.draw.rect(screen, (80, 80, 80), rect, border_radius=8)
            draw_icon(name, rect)

        text_surface = font.render(f"{steps_per_second}", True, (255, 255, 255)) 
        screen.blit(text_surface, (center_x, SCREEN_HEIGHT - 30))
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            # zmiana prędkości animacji za pomocą przycisków na ekranie
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if buttons["slower"].collidepoint(mx, my):
                    steps_per_second = max(steps_per_second - 2, 1)
                elif buttons["faster"].collidepoint(mx, my):
                    steps_per_second = min(steps_per_second + 2, 120)
                elif buttons["pause"].collidepoint(mx, my):
                    paused = not paused

            # zmiana prędkości animacji za pomocą strzałek góra, dół i spacja    
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    steps_per_second = min(steps_per_second + 2, 120)
                elif event.key == pygame.K_DOWN:
                    steps_per_second = max(steps_per_second - 2, 1)
                elif event.key == pygame.K_SPACE:
                    paused = not paused

        if not paused:
            road, flow_count = step(road, v_max, p)
            total_steps += 1
        else:
            flow_count = 0
        
        screen.fill(BG_COLOR)
        pygame.draw.rect(screen, ROAD_COLOR, (25, 50, ROAD_WIDTH, ROAD_HEIGHT))

        pygame.draw.rect(screen, ROAD_COLOR, (25, 50 + (ROAD_HEIGHT + 5), ROAD_WIDTH, ROAD_HEIGHT))
        
        text_info = (
            f"Krok: {total_steps} | Gęstość K: {initial_density:.3f} | "
            f"V_max: {v_max} | P: {p:.2f} | Przepływ Q: {flow_count * steps_per_second:.1f} Veh/s"
        )
        text_render = font.render(text_info, True, CAR_COLOR)
        screen.blit(text_render, (25, 10))

        for lane_idx, lane in enumerate(road):
            y_pos = 50 + lane_idx * (ROAD_HEIGHT + 5)
            for i, v in enumerate(lane):
                if v is not None:   
                    x_pos = 25 + i * CELL_SIZE
                    color = get_car_color(v, v_max)
                    pygame.draw.rect(
                        screen, color, (x_pos + 1, y_pos + 1, CELL_SIZE - 2, ROAD_HEIGHT - 2))
                
        draw_buttons()

        pygame.display.flip()
        clock.tick(steps_per_second)
    pygame.quit()


def plot_heatmap(arr, v_max, p):
    """Tworzy heatmapę zmian prędkości w czasie.
    
    Args:
        arr (list[list[int]]): Macierz stanów drogi.
        v_max (int): Maksymalna prędkość.
        p (float): Prawdopodobieństwo spowolnienia.
    """
    plt.imshow(arr, aspect='auto')
    plt.xlabel('Pozycja na drodze')
    plt.ylabel('Czas (kroki)')
    plt.title(f'Heatmapa prędkości w modelu NaSch (V_max={v_max}, P={p})')
    plt.show()


def history_to_array(history):
    """Konwertuje historię stanów dwupasmowej drogi do macierzy numerycznej.

    Args:
        history (list[list[list]]): Historia stanów [czas][pas][pozycja].
    
    Returns:
        np.ndarray: Tablica 2D do heatmapy, gdzie -1 = pusto.
                    Osie: (czas * liczba pasów, pozycja).
    """
    all_rows = []
    for timestep in history:
        for lane in timestep:
            row = [cell if cell is not None else -1 for cell in lane]
            all_rows.append(row)
    return np.array(all_rows, dtype=int)


def run_full_visualization(v_max, p, density):
    print("Uruchamianie wizualizacji...")
    run_pygame_simulation(initial_density=density, v_max=v_max, p=p, steps_per_second=10)
    history, _ = run_simulation(steps=300, length=133, density=density, v_max=v_max, p=p)
    arr = history_to_array(history)
    plot_heatmap(arr, v_max, p)

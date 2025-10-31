import random 
import matplotlib.pyplot as plt
import numpy as np
import pygame 

# --- STAŁE ---
CELL_LENGTH = 7.5                 # Długość jednej komórki w metrach
SIM_LENGTH_M = 1000               # Długość drogi w metrach
L = int(SIM_LENGTH_M / CELL_LENGTH)  # Długość drogi w komórkach (~133)

# --- WIZUALIZACJA (PYGAME) ---
CELL_SIZE = 10                    # Rozmiar pojedynczej komórki (piksele)
ROAD_WIDTH = L * CELL_SIZE        # Szerokość wizualizowanej drogi
ROAD_HEIGHT = CELL_SIZE * 2       # Wysokość pasa ruchu
SCREEN_HEIGHT = ROAD_HEIGHT + 100 # Wysokość całego okna
SCREEN_WIDTH = ROAD_WIDTH + 50    # Szerokość całego okna

# Kolory (RGB)
CAR_COLOR = (255, 255, 255)       
BG_COLOR = (0, 0, 0)              
ROAD_COLOR = (50, 50, 50)         


def init_road(length, density):
    """Inicjalizuje drogę o zadanej długości i gęstości.
    
    Args:
        length (int): Długość drogi w komórkach.
        density (float): Prawdopodobieństwo zajęcia komórki przez samochód.
    
    Returns:
        list: Lista reprezentująca stan drogi (v=0 lub None).
    """
    road = []
    for _ in range(length):
        if random.random() < density:
            road.append(0)
        else:
            road.append(None)
    return road


def distance_to_next(road, position):
    """Oblicza odległość do najbliższego samochodu z przodu.
    
    Args:
        road (list): Lista reprezentująca stan drogi.
        position (int): Indeks pozycji pojazdu.
    
    Returns:
        int: Liczba wolnych komórek do następnego pojazdu.
    """
    length = len(road)
    distance = 1
    while distance < length:
        next_pos = (position + distance) % length
        if road[next_pos] is not None:
            return distance
        distance += 1
    return length


def update_speeds(road, v_max, p):
    """Aktualizuje prędkości wszystkich pojazdów według reguł NaSch.
    
    Reguły:
        1. Przyspieszenie do v_max.
        2. Hamowanie, by uniknąć kolizji.
        3. Losowe spowolnienie z prawdopodobieństwem p.
    
    Args:
        road (list): Lista prędkości (lub None).
        v_max (int): Maksymalna prędkość (w komórkach/krok).
        p (float): Prawdopodobieństwo losowego spowolnienia.
    
    Returns:
        list: Zaktualizowany stan drogi (z nowymi prędkościami).
    """
    new_road = road.copy()
    length = len(road)
    for i in range(length):
        if road[i] is not None:
            v = road[i]
            if v < v_max:
                v += 1
            gap = distance_to_next(road, i)
            v = min(v, gap - 1)
            if v > 0 and random.random() < p:
                v -= 1
            new_road[i] = v
    return new_road


def move_cars(road):
    """Przesuwa samochody o ich prędkości, zliczając pojazdy przekraczające granicę drogi.
    
    Args:
        road (list): Lista prędkości pojazdów (lub None).
    
    Returns:
        tuple: (nowy stan drogi, liczba samochodów, które przekroczyły koniec drogi)
    """
    length = len(road)
    new_road = [None] * length
    flow_count = 0
    for i in range(length - 1, -1, -1):
        if road[i] is not None:
            v = road[i]
            new_pos = i + v
            if new_pos >= length:
                flow_count += 1
                new_pos %= length
            new_road[new_pos] = v
    return new_road, flow_count


def step(road, v_max, p):
    """Wykonuje jeden krok czasowy symulacji NaSch.
    
    Args:
        road (list): Stan drogi.
        v_max (int): Maksymalna prędkość.
        p (float): Prawdopodobieństwo spowolnienia.
    
    Returns:
        tuple: (nowy stan drogi, liczba pojazdów, które opuściły drogę)
    """
    updated_speeds = update_speeds(road=road, v_max=v_max, p=p)
    new_road, flow_count = move_cars(updated_speeds)
    return new_road, flow_count


def run_simulation(steps, length, density, v_max, p):
    """Uruchamia pełną symulację NaSch na określoną liczbę kroków.
    
    Args:
        steps (int): Liczba kroków symulacji.
        length (int): Długość drogi.
        density (float): Początkowa gęstość pojazdów.
        v_max (int): Maksymalna prędkość.
        p (float): Prawdopodobieństwo spowolnienia.
    
    Returns:
        tuple: (historia stanów drogi, lista przepływów w kolejnych krokach)
    """
    road = init_road(length, density)
    history = []
    point_flows = []
    for _ in range(steps):
        history.append(road.copy())
        road, flow_count = step(road, v_max, p)
        point_flows.append(flow_count)
    return history, point_flows


def history_to_array(history):
    """Konwertuje historię stanów drogi do postaci macierzy numerycznej.
    
    Args:
        history (list[list]): Historia stanów (lista list).
    
    Returns:
        list[list[int]]: Macierz, gdzie -1 oznacza puste komórki.
    """
    arr = []
    for row in history:
        arr.append([cell if cell is not None else -1 for cell in row])
    return arr


# --- WIZUALIZACJA ---

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
    
    road = init_road(L, initial_density)
    font = pygame.font.Font(None, 24)
    
    running = True
    total_steps = 0
    
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
        
        road, flow_count = step(road, v_max, p)
        total_steps += 1
        
        screen.fill(BG_COLOR)
        pygame.draw.rect(screen, ROAD_COLOR, (25, 50, ROAD_WIDTH, ROAD_HEIGHT))
        
        text_info = (
            f"Krok: {total_steps} | Gęstość K: {initial_density:.3f} | "
            f"V_max: {v_max} | P: {p:.2f} | Przepływ Q: {flow_count * steps_per_second:.1f} Veh/s"
        )
        text_render = font.render(text_info, True, CAR_COLOR)
        screen.blit(text_render, (25, 10))

        for i, v in enumerate(road):
            if v is not None:
                x_pos = 25 + i * CELL_SIZE
                y_pos = 50 
                color = get_car_color(v, v_max)
                pygame.draw.rect(screen, color, (x_pos + 1, y_pos + 1, CELL_SIZE - 2, ROAD_HEIGHT - 2))
                
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

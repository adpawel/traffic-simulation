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
SCREEN_HEIGHT = ROAD_HEIGHT * 2 + 150   # Wysokość całego okna
SCREEN_WIDTH = ROAD_WIDTH + 50    # Szerokość całego okna

# Kolory (RGB)
CAR_COLOR = (255, 255, 255)       
BG_COLOR = (0, 0, 0)              
ROAD_COLOR = (50, 50, 50)         


def init_road(length, density, n_lanes=2):
    """Inicjalizuje wielopasmową drogę.
    
    Args:
        length (int): Długość drogi w komórkach.
        density (float): Prawdopodobieństwo zajęcia komórki przez samochód.
        n_lanes (int): Liczba pasów (domyślnie 2).
    
    Returns:
        list[list]: Lista pasów, z których każdy to lista komórek (v=0 lub None).
    """
    road = []
    for _ in range(n_lanes):
        lane = []
        for _ in range(length):
            if random.random() < density:
                lane.append(0)
            else:
                lane.append(None)
        road.append(lane)
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
    new_road = road[:]
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

def change_lane(road, lane, pos, v_max, p_change, v_strat_nasch, gap_rear_nasch):
    """
    Decyzja kierowcy o zmianie pasa ruchu zgodnie z rozszerzonym modelem NaSch-CL.
    
    Uwzględnia zarówno motywację (V_strat), jak i warunek bezpieczeństwa z tyłu (Gap_rear).

    Args:
        road (list[list]): Aktualny stan drogi (lista pasów).
        lane (int): Indeks pasa, na którym znajduje się pojazd.
        pos (int): Pozycja pojazdu na pasie.
        v_max (int): Maksymalna prędkość pojazdu w modelu NaSch.
        p_change (float): Prawdopodobieństwo podjęcia decyzji o zmianie pasa.
        v_strat_nasch (float): Próg motywacji do zmiany pasa [komórki/krok].
        gap_rear_nasch (int): Minimalny bezpieczny dystans z tyłu [komórki].

    Returns:
        bool: True jeśli kierowca zmienia pas, False w przeciwnym wypadku.
    """
    other_lane = 1 - lane
    length = len(road[lane])

    # --- 1 MOTYWACJA DO ZMIANY PASA ---
    gap_front = distance_to_next(road[lane], pos)       # Dystans do najbliższego pojazdu z przodu
    max_v_possible = gap_front - 1                      # maksymalna prędkość możliwa na aktualnym pasie

    # Kierowca jest sfrustrowany jeśli nie może jechać z prędkością bliską v_max
    if v_max - max_v_possible < v_strat_nasch:
        return False  # Brak wystarczającej motywacji do zmiany pasa

    # Potencjalny zysk na drugim pasie
    gap_front_other = distance_to_next(road[other_lane], pos)
    if gap_front_other - 1 <= max_v_possible + v_strat_nasch:
        return False  # Brak realnego zysku prędkości po zmianie pasa

    # --- 2 WARUNEK DOSTĘPNOŚCI (miejsce na drugim pasie) ---
    if road[other_lane][pos] is not None:
        return False  # Komórka bezpośrednio naprzeciwko jest zajęta

    # --- 3 WARUNEK BEZPIECZEŃSTWA Z TYŁU ---
    distance_to_rear = 1
    while distance_to_rear < length:
        behind_pos = (pos - distance_to_rear) % length
        v_rear = road[other_lane][behind_pos]

        if v_rear is not None:
            required_gap = v_rear + gap_rear_nasch  # minimalny bezpieczny dystans
            if distance_to_rear < required_gap:
                return False  # Zbyt blisko pojazdu z tyłu → niebezpieczna zmiana pasa
            break
        distance_to_rear += 1

    # --- 4 PROBABILISTYCZNA DECYZJA KIEROWCY ---
    return random.random() < p_change


def step(road, v_max, p):
    """Wykonuje jeden krok czasowy symulacji NaSch dla wielu pasów (np. 2).
    
    Args:
        road (list[list]): Stan drogi [pas][pozycja].
        v_max (int): Maksymalna prędkość.
        p (float): Prawdopodobieństwo spowolnienia.
    
    Returns:
        tuple: (nowy stan drogi, łączny przepływ z wszystkich pasów)
    """
    n_lanes = len(road)
    length = len(road[0])
    
    new_road = []
    total_flow = 0

    # zmiana pasa
    lane_changes = []
    for lane in range(n_lanes):
        for pos in range(length):
            if road[lane][pos] is not None:
                if change_lane(road, lane, pos, v_max, p_change=0.3, v_strat_nasch=0.9, gap_rear_nasch=2):
                    lane_changes.append((lane, pos))

    for lane, pos in lane_changes:
        other = 1 - lane
        if road[other][pos] is None:  # sprawdź czy nadal wolne
            road[other][pos] = road[lane][pos]
            road[lane][pos] = None

    # aktualizacja prędkości
    for lane in range(n_lanes):
        updated_lane = update_speeds(road[lane], v_max, p)
        new_road.append(updated_lane)

    # przesunięcie samochodów
    moved_road = []
    for lane in range(n_lanes):
        moved_lane, flow_count = move_cars(new_road[lane])
        moved_road.append(moved_lane)
        total_flow += flow_count

    return moved_road, total_flow



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
    road = init_road(length, density, n_lanes=2)
    history = []
    point_flows = []
    for _ in range(steps):
        history.append([lane.copy() for lane in road])
        road, flow_count = step(road, v_max, p)
        point_flows.append(flow_count)
    return history, point_flows


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
    
    road = init_road(L, initial_density, n_lanes=2)
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

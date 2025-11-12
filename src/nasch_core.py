import random 
import numpy as np

from src.config import P_CHANGE, V_STRAT, GAP_REAR, LANES

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

    if v_max - max_v_possible < v_strat_nasch:
        return False  # Brak wystarczającej motywacji do zmiany pasa

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
                return False  # Zbyt blisko pojazdu z tyłu - niebezpieczna zmiana pasa
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
    if n_lanes > 1:
        lane_changes = []
        for lane in range(n_lanes):
            for pos in range(length):
                if road[lane][pos] is not None:
                    if change_lane(road, lane, pos, v_max, p_change=P_CHANGE, v_strat_nasch=V_STRAT, gap_rear_nasch=GAP_REAR):
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
    road = init_road(length, density, n_lanes=LANES)
    history = []
    point_flows = []
    for _ in range(steps):
        history.append([lane.copy() for lane in road])
        road, flow_count = step(road, v_max, p)
        point_flows.append(flow_count)
    return history, point_flows

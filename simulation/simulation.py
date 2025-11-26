from __future__ import annotations

import random
from dataclasses import dataclass
from typing import List, Optional, Dict, Tuple

from src.config import (
    P_CHANGE,
    GAP_REAR,
    P_SLOW,
    L,
    LANES,
    DENSITY,
)
from .road import Road
from .vehicle import Vehicle, LaneDecision
from .localview import LocalView
from .speedLimits import Position


Grid = List[List[Optional[Vehicle]]]  # grid[lane][x] = Vehicle lub None


@dataclass
class SimulationStats:
    """Proste statystyki symulacji, przydatne do HUD-a w pygame_view."""
    step_count: int = 0
    last_flow: int = 0
    cumulative_flow: int = 0

    @property
    def avg_flow(self) -> float:
        if self.step_count == 0:
            return 0.0
        return self.cumulative_flow / self.step_count


class Simulation:
    """
    Główna klasa odpowiedzialna za symulację modelu NaSch (+zmiana pasa).

    Trzyma:
      - obiekt Road (geometria + ograniczenia prędkości),
      - siatkę pojazdów (grid[lane][x]),
      - listę pojazdów (Vehicle),
      - parametry modelu (p_slow, p_change, gap_rear, density),
      - statystyki przepływu.
    """

    def __init__(
        self,
        length: int = L,
        lanes: int = LANES,
        density: float = DENSITY,
        p_slow: float = P_SLOW,
        p_change: float = P_CHANGE,
        gap_rear: int = GAP_REAR,
        record_history: bool = False,
        speed_limits: Optional[List] = None,
    ) -> None:
        """
        Args:
            length: długość drogi (liczba komórek).
            lanes: liczba pasów.
            density: początkowa gęstość pojazdów (0–1).
            p_slow: prawdopodobieństwo losowego zwolnienia (NaSch).
            p_change: prawdopodobieństwo próby zmiany pasa.
            gap_rear: minimalny odstęp z tyłu przy zmianie pasa.
            record_history: jeśli True, zapisuje historię gridów.
            speed_limits: lista obiektów SpeedLimit (światła, przeszkody, ograniczenia).
        """
        self.length = length
        self.lanes = lanes

        from .speedLimits import SpeedLimits
        speed_limits_list = speed_limits if speed_limits is not None else []
        speed_limits_obj = SpeedLimits(speedLimits=speed_limits_list, maxSpeed=5)
        self.road = Road(lanesCount=lanes, length=length, speedLimits=speed_limits_obj)
        self.grid: Grid = [[None for _ in range(length)] for _ in range(lanes)]
        self.vehicles: List[Vehicle] = []

        self.p_slow = p_slow
        self.p_change = p_change
        self.gap_rear = gap_rear
        self.density = density

        self.stats = SimulationStats()
        self.record_history = record_history
        self.history: Optional[List[Grid]] = [] if record_history else None

        self._init_random_vehicles()

    # -------------------------------------------------------------------------
    # Inicjalizacja
    # -------------------------------------------------------------------------

    def _init_random_vehicles(self) -> None:
        """
        Losowo rozstawia pojazdy na drodze zgodnie z gęstością density.
        Przyjmuje prosty model: każdy cell jest zajęty z prawdopodobieństwem density.
        """
        for lane in range(self.lanes):
            for x in range(self.length):
                if random.random() < self.density and self.grid[lane][x] is None:
                    pos = Position(x=x, lane=lane)
                    v = Vehicle(pos=pos)  # v_max i inne rzeczy może brać z configu w samej klasie Vehicle
                    self.grid[lane][x] = v
                    self.vehicles.append(v)

    # -------------------------------------------------------------------------
    # Główny krok symulacji
    # -------------------------------------------------------------------------

    def step(self) -> None:
        """
        Wykonuje jeden krok czasowy modelu:
          1. budowa widoków lokalnych,
          2. decyzje o zmianie pasa,
          3. zastosowanie zmian pasa,
          4. aktualizacja prędkości (NaSch) i przesunięcie pojazdów,
          5. aktualizacja statystyk (przepływ).
        """
        # Zawsze zwiększamy licznik kroków, nawet dla pustej drogi
        self.stats.step_count += 1
        
        # Aktualizuj światła i inne dynamiczne ograniczenia
        self.road.speedLimits.update()
        
        if not self.vehicles:
            self.stats.last_flow = 0
            return

        # 1. Lokalne widoki dla każdego pojazdu (na podstawie obecnego gridu)
        # Używamy listy zamiast dict, bo Vehicle nie jest hashable
        views: List[LocalView] = [
            self._build_local_view(v) for v in self.vehicles
        ]

        # 2. Decyzje o zmianie pasa
        lane_change_targets: List[Position] = (
            self._compute_lane_change_targets(views)
        )

        # 3. Zastosowanie zmian pasa (aktualizacja tylko pasa, bez ruchu do przodu)
        self._apply_lane_changes(lane_change_targets)

        # Po zmianach pasa – nowe widoki (bo sąsiedzi się zmienili)
        views = [self._build_local_view(v) for v in self.vehicles]

        # 4. Aktualizacja prędkości wg NaSch + ruch do przodu
        flow_this_step = self._update_speeds_and_positions(views)

        # 5. Statystyki
        self.stats.last_flow = flow_this_step
        self.stats.cumulative_flow += flow_this_step

        # 6. Historia (opcjonalnie)
        if self.record_history and self.history is not None:
            snapshot: Grid = [
                lane_row.copy() for lane_row in self.grid
            ]
            self.history.append(snapshot)

    def run(self, steps: int) -> None:
        """Uruchamia symulację na zadaną liczbę kroków."""
        for _ in range(steps):
            self.step()

    # -------------------------------------------------------------------------
    # Budowa LocalView
    # -------------------------------------------------------------------------

    def _build_local_view(self, v: Vehicle) -> LocalView:
        """
        Buduje LocalView dla pojazdu:
          - odległości do najbliższego auta z przodu (ten sam pas / góra / dół),
          - odległości z tyłu na sąsiednich pasach,
          - ograniczenie prędkości w danej pozycji,
          - flagi: czy można zmienić pas w górę / w dół.
        """
        lane = v.pos.lane
        x = v.pos.x

        speed_limit = self.road.getLimit(v.pos)

        dist_front_same = self._distance_to_next_car(lane, x)
        dist_front_up = self._distance_to_next_car(lane - 1, x) if lane > 0 else 0
        dist_front_down = (
            self._distance_to_next_car(lane + 1, x)
            if lane < self.lanes - 1
            else 0
        )

        dist_back_up = self._distance_to_prev_car(lane - 1, x) if lane > 0 else 0
        dist_back_down = (
            self._distance_to_prev_car(lane + 1, x)
            if lane < self.lanes - 1
            else 0
        )

        can_change_up = False
        can_change_down = False

        if lane > 0:
            can_change_up = (
                dist_front_up >= v.velocity and dist_back_up >= self.gap_rear
            )
        if lane < self.lanes - 1:
            can_change_down = (
                dist_front_down >= v.velocity and dist_back_down >= self.gap_rear
            )

        return LocalView(
            pos=v.pos,
            speed_limit=speed_limit,
            dist_front_same=dist_front_same,
            dist_front_up=dist_front_up,
            dist_front_down=dist_front_down,
            dist_back_up=dist_back_up,
            dist_back_down=dist_back_down,
            can_change_up=can_change_up,
            can_change_down=can_change_down,
        )

    def _distance_to_next_car(self, lane: int, x: int) -> int:
        """
        Zwraca liczbę wolnych komórek do najbliższego auta z przodu na danym pasie.
        Jeśli pas nie istnieje -> 0.
        """
        if not (0 <= lane < self.lanes):
            return 0

        d = 1
        while d < self.length:
            nx = (x + d) % self.length
            if self.grid[lane][nx] is not None:
                return d - 1
            d += 1
        return self.length - 1

    def _distance_to_prev_car(self, lane: int, x: int) -> int:
        """
        Zwraca liczbę wolnych komórek do najbliższego auta z tyłu na danym pasie.
        Jeśli pas nie istnieje -> 0.
        """
        if not (0 <= lane < self.lanes):
            return 0

        d = 1
        while d < self.length:
            px = (x - d) % self.length
            if self.grid[lane][px] is not None:
                return d - 1
            d += 1
        return self.length - 1

    # -------------------------------------------------------------------------
    # Zmiany pasa
    # -------------------------------------------------------------------------

    def _compute_lane_change_targets(
        self,
        views: List[LocalView],
    ) -> List[Position]:
        """
        Na podstawie LocalView + decyzji pojazdów (Vehicle.decideLaneChange)
        wyznacza docelowe pozycje (bez ruchu do przodu).
        """
        targets: List[Position] = []

        for i, view in enumerate(views):
            v = self.vehicles[i]
            
            # z jakimś prawdopodobieństwem w ogóle rozważamy zmianę pasa
            if random.random() > self.p_change:
                targets.append(v.pos)
                continue

            decision = v.decideLaneChange(view)

            if decision == LaneDecision.UP and view.can_change_up:
                new_lane = v.pos.lane - 1
                targets.append(Position(x=v.pos.x, lane=new_lane))
            elif decision == LaneDecision.DOWN and view.can_change_down:
                new_lane = v.pos.lane + 1
                targets.append(Position(x=v.pos.x, lane=new_lane))
            else:
                targets.append(v.pos)

        return targets

    def _apply_lane_changes(self, targets: List[Position]) -> None:
        """
        Zastosowanie zmian pasa w sposób równoległy:
          - budujemy nowy grid,
          - jeśli kilka aut chce na tę samą komórkę, blokujemy konflikt
            (wszyscy zostają na starych pasach).
        """
        new_grid: Grid = [[None for _ in range(self.length)] for _ in range(self.lanes)]

        # mapa docelowych pozycji -> lista indeksów pojazdów, które tam chcą
        pos_to_vehicle_indices: Dict[Tuple[int, int], List[int]] = {}
        for i, pos in enumerate(targets):
            key = (pos.lane, pos.x)
            pos_to_vehicle_indices.setdefault(key, []).append(i)

        for i, v in enumerate(self.vehicles):
            old_pos = v.pos
            target_pos = targets[i]

            key = (target_pos.lane, target_pos.x)
            cand_list = pos_to_vehicle_indices.get(key, [])

            if len(cand_list) == 1:
                # tylko jedno auto chce tę komórkę -> zmiana pasa dozwolona
                v.pos = Position(x=target_pos.x, lane=target_pos.lane)
            else:
                # konflikt -> zostaje na starym pasie
                v.pos = Position(x=old_pos.x, lane=old_pos.lane)

        # po aktualizacji lane'ów, przepisujemy grid (bez ruchu do przodu)
        for lane in range(self.lanes):
            for x in range(self.length):
                self.grid[lane][x] = None

        for v in self.vehicles:
            self.grid[v.pos.lane][v.pos.x] = v

    # -------------------------------------------------------------------------
    # NaSch: prędkość i ruch
    # -------------------------------------------------------------------------

    def _update_speeds_and_positions(
        self,
        views: List[LocalView],
    ) -> int:
        """
        Zasady NaSch na zaktualizowanych pasach:
          1. Przyspieszanie (do min(v_max pojazdu, speed_limit, dystans do przodu)),
          2. Hamowanie (uwzględnione przez dystans),
          3. Losowe zwolnienie z prawdopodobieństwem p_slow,
          4. Ruch o v komórek.

        Zwraca:
            flow_count – liczba pojazdów, które minęły x=0 w tym kroku (przepływ).
        """
        flow_count = 0

        # nowa siatka po przemieszczeniu
        new_grid: Grid = [[None for _ in range(self.length)] for _ in range(self.lanes)]

        # Tworzymy mapę pojazd -> view dla szybkiego dostępu
        vehicle_to_view = {id(self.vehicles[i]): views[i] for i in range(len(self.vehicles))}

        # kolejność aktualizacji: z tyłu do przodu po każdym pasie,
        # żeby nie nadpisać sobie informacji potrzebnej do NaSch
        # (chociaż używamy new_grid, więc i tak jest równoległe).
        vehicles_sorted = sorted(
            self.vehicles,
            key=lambda v: v.pos.x,
            reverse=True,
        )

        for v in vehicles_sorted:
            view = vehicle_to_view[id(v)]

            # 1. Przyspieszanie
            # maksymalna prędkość z ograniczeń: v_max pojazdu & ograniczenie drogi
            v_max_allowed = min(v.v_max, view.speed_limit)
            v.velocity = min(v.velocity + 1, v_max_allowed)

            # 2. Hamowanie na podstawie wolnego dystansu z przodu
            gap = view.dist_front_same
            if gap < v.velocity:
                v.velocity = gap

            # 3. Losowe zwolnienie
            if v.velocity > 0 and random.random() < self.p_slow:
                v.velocity -= 1

            # 4. Ruch o v komórek
            old_x = v.pos.x
            new_x = (old_x + v.velocity) % self.length
            lane = v.pos.lane

            # przepływ: pojazd mija x=0, jeśli "przeskoczył" za 0
            if new_x < old_x:
                flow_count += 1

            v.pos = Position(x=new_x, lane=lane)
            new_grid[lane][new_x] = v

        # podmieniamy grid
        self.grid = new_grid

        return flow_count

    # -------------------------------------------------------------------------
    # API pomocnicze
    # -------------------------------------------------------------------------

    def get_grid(self) -> Grid:
        """Zwraca aktualną siatkę (do pygame_view)."""
        return self.grid

    def reset(
        self,
        density: Optional[float] = None,
        p_slow: Optional[float] = None,
        p_change: Optional[float] = None,
    ) -> None:
        """
        Resetuje symulację z nową losową konfiguracją (i opcjonalnie nowymi parametrami).
        """
        if density is not None:
            self.density = density
        if p_slow is not None:
            self.p_slow = p_slow
        if p_change is not None:
            self.p_change = p_change

        self.grid = [[None for _ in range(self.length)] for _ in range(self.lanes)]
        self.vehicles = []

        self.stats = SimulationStats()
        if self.record_history:
            self.history = []
        else:
            self.history = None

        self._init_random_vehicles()

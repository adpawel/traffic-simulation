"""
Wizualizacja symulacji ruchu drogowego w pygame.

Wyświetla:
  - siatkę komórek reprezentującą drogi (pasy ruchu),
  - pojazdy jako kolorowe prostokąty,
  - prędkość każdego pojazdu,
  - statystyki (krok, przepływ, średni przepływ),
  - limity prędkości na poszczególnych odcinkach drogi.
"""

import pygame
from typing import Optional, Tuple
import sys

from .simulation import Simulation
from .vehicle import Vehicle
from .speedLimits import Position


# Kolory
COLOR_BG = (40, 40, 40)           # tło
COLOR_ROAD = (60, 60, 60)          # komórka drogi (pusta)
COLOR_LINE = (100, 100, 100)       # linie między pasami
COLOR_VEHICLE_BASE = (50, 150, 255)  # kolor bazowy pojazdu
COLOR_TEXT = (255, 255, 255)       # tekst
COLOR_SPEED_LIMIT = (255, 200, 50)  # ograniczenie prędkości


class PygameView:
    """
    Wizualizacja symulacji w pygame.
    
    - Obsługuje klawisze:
        SPACE: pauza/wznowienie
        R: reset symulacji
        +/-: zmiana prędkości symulacji
        ESC/Q: wyjście
    """

    def __init__(
        self,
        simulation: Simulation,
        cell_size: int = 12,
        fps: int = 10,
        window_width: int = 1200,
    ) -> None:
        """
        Args:
            simulation: Obiekt symulacji do wizualizacji.
            cell_size: Wysokość jednej komórki w pikselach (szerokość auto).
            fps: Docelowa liczba klatek na sekundę.
            window_width: Szerokość okna (długość drogi skalowana).
        """
        self.sim = simulation
        self.cell_size = cell_size
        self.fps = fps
        self.window_width = window_width
        
        # Oblicz szerokość jednej komórki (x)
        self.cell_width = window_width // simulation.length
        
        # Wysokość okna zależy od liczby pasów + margines na statystyki
        self.stats_height = 120
        self.road_height = simulation.lanes * cell_size
        self.window_height = self.road_height + self.stats_height
        
        # Stan wizualizacji
        self.paused = False
        self.running = True
        
        # Inicjalizacja pygame
        pygame.init()
        self.screen = pygame.display.set_mode((self.window_width, self.window_height))
        pygame.display.set_caption("Traffic Simulation - NaSch Model")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 14)
        self.font_small = pygame.font.SysFont("monospace", 10)
        self.font_legend = pygame.font.SysFont("monospace", 16)
        
        # Losowe kolory dla każdego lokalnego ograniczenia prędkości
        self.speed_limit_colors = {}
        self._assign_speed_limit_colors()

    def run(self) -> None:
        """Główna pętla wizualizacji."""
        while self.running:
            self._handle_events()
            
            if not self.paused:
                self.sim.step()
            
            self._draw()
            self.clock.tick(self.fps)
        
        pygame.quit()
        sys.exit()

    def _assign_speed_limit_colors(self) -> None:
        """Przypisuje losowe kolory do lokalnych ograniczeń prędkości."""
        import random
        random.seed(42)  # Dla powtarzalności
        
        for limit in self.sim.road.speedLimits.speedLimits:
            if limit.speedLimit > 0:  # Tylko dla lokalnych ograniczeń
                # Losowy odcień w zakresie żółto-pomarańczowo-różowym
                hue_range = [(30, 60), (200, 230), (280, 320)]  # żółty, niebieski, różowy
                hue_choice = random.choice(hue_range)
                hue = random.randint(hue_choice[0], hue_choice[1])
                
                # Konwersja HSV -> RGB (uproszczona)
                if hue <= 60:  # żółty-pomarańczowy
                    r = random.randint(200, 255)
                    g = random.randint(150, 220)
                    b = random.randint(0, 100)
                elif hue <= 230:  # niebieski-cyjan
                    r = random.randint(50, 150)
                    g = random.randint(150, 220)
                    b = random.randint(200, 255)
                else:  # różowy-fioletowy
                    r = random.randint(200, 255)
                    g = random.randint(100, 180)
                    b = random.randint(200, 255)
                
                self.speed_limit_colors[id(limit)] = (r, g, b)

    def _handle_events(self) -> None:
        """Obsługa zdarzeń klawiatury i zamknięcia okna."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                
                elif event.key == pygame.K_r:
                    self.sim.reset()
                
                elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                    self.fps = min(self.fps + 5, 60)
                
                elif event.key == pygame.K_MINUS:
                    self.fps = max(self.fps - 5, 1)
                
                elif event.key == pygame.K_ESCAPE or event.key == pygame.K_q:
                    self.running = False

    def _draw(self) -> None:
        """Rysuje całą scenę: droga + pojazdy + statystyki."""
        self.screen.fill(COLOR_BG)
        
        self._draw_road()
        self._draw_vehicles()
        self._draw_traffic_lights_and_obstacles()  # Rysujemy NA WIERZCHU pojazdów
        self._draw_stats()
        
        pygame.display.flip()

    def _draw_road(self) -> None:
        """Rysuje siatkę komórek drogi i linie między pasami."""
        for lane in range(self.sim.lanes):
            y = lane * self.cell_size
            
            # Tło pasa
            rect = pygame.Rect(0, y, self.window_width, self.cell_size)
            pygame.draw.rect(self.screen, COLOR_ROAD, rect)
            
            # Linia oddzielająca pasy
            if lane > 0:
                pygame.draw.line(
                    self.screen,
                    COLOR_LINE,
                    (0, y),
                    (self.window_width, y),
                    1
                )

    def _draw_traffic_lights_and_obstacles(self) -> None:
        """Rysuje światła, przeszkody i ograniczenia prędkości."""
        
        for speed_limit in self.sim.road.speedLimits.speedLimits:
            # Przeszkody (v_max=0, ticks=0) rysujemy zawsze
            # Światła (v_max=0, ticks>0) tylko gdy aktywne
            # Lokalne ograniczenia prędkości (v_max>0, ticks=0) rysujemy zawsze
            if speed_limit.speedLimit == 0 and speed_limit.ticks == 0:
                # Stała przeszkoda - zawsze widoczna
                draw_it = True
                color = (180, 0, 0)  # ciemnoczerwone
                alpha = 220
            elif speed_limit.speedLimit == 0 and speed_limit.ticks > 0:
                # Światło
                if speed_limit.active:
                    draw_it = True
                    color = (255, 50, 50)  # jasnoczerwone
                    alpha = 160
                else:
                    draw_it = False
            elif speed_limit.speedLimit > 0:
                # Lokalne ograniczenie prędkości
                draw_it = True
                color = self.speed_limit_colors.get(id(speed_limit), (255, 200, 50))
                alpha = 180
            else:
                # Światło zielone (nieaktywne) - nie rysujemy
                draw_it = False
                
            if not draw_it:
                continue
                
            lane_min, lane_max = speed_limit.lanesRange
            x_min, x_max = speed_limit.xRange
            
            # Rysuj prostokąt dla każdego pasa w zakresie
            for lane in range(lane_min, lane_max + 1):
                for x in range(x_min, x_max + 1):
                    screen_x = x * self.cell_width
                    screen_y = lane * self.cell_size
                    
                    # Wypełnienie (z przezroczystością dla lokalnych ograniczeń)
                    rect = pygame.Rect(screen_x, screen_y, self.cell_width, self.cell_size)
                    if speed_limit.speedLimit > 0:
                        # Lokalne ograniczenie - lekko przezroczyste
                        surf = pygame.Surface((self.cell_width, self.cell_size))
                        surf.set_alpha(100)
                        surf.fill(color)
                        self.screen.blit(surf, (screen_x, screen_y))
                    else:
                        # Przeszkoda/światło - pełne
                        pygame.draw.rect(self.screen, color, rect)
                    
                    # Mocniejsze obramowanie
                    pygame.draw.rect(self.screen, (255, 255, 255), rect, 2)
                    
                    # Dodaj krzyżyk dla przeszkód (lepsze rozpoznanie)
                    if speed_limit.speedLimit == 0 and speed_limit.ticks == 0:
                        pygame.draw.line(
                            self.screen, 
                            (255, 255, 255),
                            (screen_x + 2, screen_y + 2),
                            (screen_x + self.cell_width - 2, screen_y + self.cell_size - 2),
                            2
                        )
                        pygame.draw.line(
                            self.screen,
                            (255, 255, 255),
                            (screen_x + self.cell_width - 2, screen_y + 2),
                            (screen_x + 2, screen_y + self.cell_size - 2),
                            2
                        )

    def _draw_vehicles(self) -> None:
        """Rysuje pojazdy na drodze."""
        grid = self.sim.get_grid()
        
        for lane in range(self.sim.lanes):
            for x in range(self.sim.length):
                vehicle = grid[lane][x]
                if vehicle is not None:
                    self._draw_vehicle(vehicle)

    def _draw_vehicle(self, vehicle: Vehicle) -> None:
        """
        Rysuje pojedynczy pojazd.
        Kolor: 0 = czerwony, środek = pomarańcz/żółty, max = zielony.
        """
        x = vehicle.pos.x
        lane = vehicle.pos.lane
        screen_x = x * self.cell_width
        screen_y = lane * self.cell_size

        # Normalizacja prędkości
        v = vehicle.velocity
        vmax = max(vehicle.v_max, 1)
        speed_ratio = v / vmax

        # Kolor: 0 = czerwony (255,0,0), 0.5 = żółty (255,255,0), 1 = zielony (0,255,0)
        if speed_ratio <= 0.5:
            # Od czerwonego (255,0,0) do żółtego (255,255,0)
            r = 255
            g = int(2 * 255 * speed_ratio)
            b = 0
        else:
            # Od żółtego (255,255,0) do zielonego (0,255,0)
            r = int(2 * 255 * (1 - speed_ratio))
            g = 255
            b = 0
        color = (max(0, min(r, 255)), max(0, min(g, 255)), b)

        rect = pygame.Rect(screen_x, screen_y + 1, self.cell_width - 1, self.cell_size - 2)
        pygame.draw.rect(self.screen, color, rect)
        pygame.draw.rect(self.screen, (255, 255, 255), rect, 1)

        # Prędkość pojazdu (małym fontem)
        if self.cell_width > 8:
            v_text = self.font_small.render(str(vehicle.velocity), True, (0, 0, 0))
            text_rect = v_text.get_rect(center=(screen_x + self.cell_width // 2, screen_y + self.cell_size // 2))
            self.screen.blit(v_text, text_rect)

    def _draw_stats(self) -> None:
        """Rysuje statystyki symulacji u dołu ekrana."""
        y_offset = self.road_height + 10
        
        stats = self.sim.stats
        
        lines = [
            f"Krok: {stats.step_count}",
            f"Przepływ (ostatni krok): {stats.last_flow}",
            f"Średni przepływ: {stats.avg_flow:.2f}",
            f"Pojazdy: {len(self.sim.vehicles)}",
            "",
            f"FPS: {self.fps} | [+/-] zmiana prędkości",
            f"[SPACE] pauza | [R] reset | [ESC/Q] wyjście",
        ]
        
        if self.paused:
            lines.insert(0, "=== PAUZA ===")
        
        for i, line in enumerate(lines):
            text = self.font.render(line, True, COLOR_TEXT)
            self.screen.blit(text, (10, y_offset + i * 18))
        
        # Legenda ograniczeń prędkości
        self._draw_speed_limits_legend(y_offset)
    
    def _draw_speed_limits_legend(self, y_offset: int) -> None:
        """Rysuje legendę z aktywnymi ograniczeniami prędkości."""
        legend_x = self.window_width - 320
        legend_y = y_offset
        
        # Nagłówek
        header = self.font_legend.render("Ograniczenia prędkości:", True, COLOR_TEXT)
        self.screen.blit(header, (legend_x, legend_y))
        legend_y += 24
        
        speed_limits = self.sim.road.speedLimits.speedLimits
        if not speed_limits:
            no_limits = self.font_small.render("Brak", True, (150, 150, 150))
            self.screen.blit(no_limits, (legend_x, legend_y))
            return
        
        # Grupuj ograniczenia według typu
        for i, limit in enumerate(speed_limits):
            if i >= 5:  # Maksymalnie 5 ograniczeń na legendzie
                more_text = self.font_small.render(f"... i {len(speed_limits) - 5} więcej", True, (150, 150, 150))
                self.screen.blit(more_text, (legend_x, legend_y))
                break
            
            # Określ typ i kolor
            if limit.speedLimit == 0 and limit.ticks == 0:
                label = "Przeszkoda"
                color = (180, 0, 0)
            elif limit.speedLimit == 0 and limit.ticks > 0:
                status = "CZERWONE" if limit.active else "ZIELONE"
                label = f"Światła ({status})"
                color = (255, 50, 50) if limit.active else (50, 255, 50)
            else:
                label = f"v_max = {limit.speedLimit}"
                color = self.speed_limit_colors.get(id(limit), (255, 200, 50))
            
            # Pozycja
            x_min, x_max = limit.xRange
            lane_min, lane_max = limit.lanesRange
            if lane_min == lane_max:
                pos_str = f"x:{x_min}-{x_max}, pas:{lane_min}"
            else:
                pos_str = f"x:{x_min}-{x_max}, pasy:{lane_min}-{lane_max}"
            
            # Rysuj kolorowy kwadracik
            box_size = 12
            pygame.draw.rect(self.screen, color, (legend_x, legend_y + 2, box_size, box_size))
            pygame.draw.rect(self.screen, (255, 255, 255), (legend_x, legend_y + 2, box_size, box_size), 1)
            
            # Rysuj tekst
            text = self.font.render(f"{label}: {pos_str}", True, COLOR_TEXT)
            self.screen.blit(text, (legend_x + box_size + 5, legend_y))
            legend_y += 20


def main() -> None:
    """Funkcja pomocnicza do szybkiego uruchomienia wizualizacji."""
    from simulation.config import L, LANES, DENSITY, P_SLOW, P_CHANGE, GAP_REAR
    
    sim = Simulation(
        length=L,
        lanes=LANES,
        density=DENSITY,
        p_slow=P_SLOW,
        p_change=P_CHANGE,
        gap_rear=GAP_REAR,
    )
    
    view = PygameView(simulation=sim, cell_size=20, fps=2, window_width=1700)
    view.run()


if __name__ == "__main__":
    main()

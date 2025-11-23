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
            # Przeszkody (ticks=0) rysujemy zawsze, światła tylko gdy aktywne
            if speed_limit.ticks == 0:
                # Stała przeszkoda - zawsze widoczna
                draw_it = True
                color = (180, 0, 0)  # ciemnoczerwone
                alpha = 220
            elif speed_limit.active:
                # Światło czerwone (aktywne)
                draw_it = True
                color = (255, 50, 50)  # jasnoczerwone
                alpha = 160
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
                    
                    # Wypełnienie
                    rect = pygame.Rect(screen_x, screen_y, self.cell_width, self.cell_size)
                    pygame.draw.rect(self.screen, color, rect)
                    
                    # Mocniejsze obramowanie
                    pygame.draw.rect(self.screen, (255, 255, 255), rect, 2)
                    
                    # Dodaj krzyżyk dla przeszkód (lepsze rozpoznanie)
                    if speed_limit.ticks == 0:
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


def main() -> None:
    """Funkcja pomocnicza do szybkiego uruchomienia wizualizacji."""
    from src.config import L, LANES, DENSITY, P_SLOW, P_CHANGE, GAP_REAR
    
    sim = Simulation(
        length=L,
        lanes=LANES,
        density=DENSITY,
        p_slow=P_SLOW,
        p_change=P_CHANGE,
        gap_rear=GAP_REAR,
    )
    
    view = PygameView(simulation=sim, cell_size=20, fps=10, window_width=1400)
    view.run()


if __name__ == "__main__":
    main()

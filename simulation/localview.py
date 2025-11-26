from dataclasses import dataclass
from typing import Optional
from .speedLimits import Position


@dataclass
class LocalView:
    """
    Lokalny widok kierowcy w danym kroku symulacji.
    Zawiera tylko to, co samochód musi wiedzieć o otoczeniu.
    """

    pos: Position              # aktualna pozycja auta

    speed_limit: int           # limit prędkości w tej pozycji

    dist_front_same: int       # wolna odległość z przodu na tym samym pasie

    dist_front_up: Optional[int]   # wolna odległość z przodu na pasie wyżej (None jeśli brak pasa)
    dist_front_down: Optional[int] # wolna odległość z przodu na pasie niżej (None jeśli brak pasa)

    dist_back_up: Optional[int]    # odległość do auta z tyłu na pasie wyżej (None jeśli brak auta/pasa)
    dist_back_down: Optional[int]  # odległość do auta z tyłu na pasie niżej (None jeśli brak auta/pasa)

    can_change_up: bool        # czy w ogóle można rozważać zmianę pasa w górę
    can_change_down: bool      # czy w ogóle można rozważać zmianę pasa w dół

CELL_LENGTH_M = 7.5      # Długość jednej komórki [m]
TIME_STEP_S = 1.6        # Krok czasowy symulacji [s]
SIM_LENGTH_M = 1000      # Długość drogi, dla której prowadzona jest symulacja [m]
L = int(SIM_LENGTH_M / CELL_LENGTH_M) # Długość drogi wyrażona w liczbie komórek
LANES = 1                # Liczba pasów ruchu w symulacji
DENSITY = 0.15           # Początkowa gęstość zaludnienia drogi (prawdopodobieństwo, że komórka będzie zajęta) [0.0 - 1.0]

P_CHANGE = 0.6           # Prawdopodobieństwo, że kierowca podejmie decyzję o zmianie pasa, gdy warunki są sprzyjające [0.0 - 1.0]
V_STRAT = 1.0            # Wymagana motywacja do zmiany pasa (minimalna strata prędkości) [komórki/krok]
GAP_REAR = 2             # Minimalny bezpieczny odstęp (bufor) za pojazdem zmieniającym pas [komórki]
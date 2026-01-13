# Symulacja Ruchu Drogowego - Model NaSch

Projekt implementuje model automatów komórkowych Nagela-Schreckenberga (NaSch) z wieloma pasami ruchu, dynamiczną zmianą pasa, światłami i przeszkodami. Zawiera kalibrację na danych rzeczywistych z detektorów pętlowych (Darmstadt) oraz scenariusze demonstracyjne.

## Struktura Projektu

```
traffic-simulation/
├── main.py                      # Punkt wejścia - wizualizacja pygame
├── calibrate_darmstadt.py       # Kalibracja na danych rzeczywistych
├── scenarios.py                 # Scenariusze demonstracyjne
├── simulation/
│   ├── simulation.py            # Logika symulacji NaSch
│   ├── vehicle.py               # Klasa pojazdu
│   ├── road.py                  # Klasa drogi
│   ├── localview.py             # Widok lokalny pojazdu
│   ├── speedLimits.py           # Limity prędkości, światła, przeszkody
│   └── pygame_view.py           # Wizualizacja pygame
├── src/
│   └── config.py                # Parametry domyślne
├── tests/                       # 70 testów jednostkowych
├── data/
│   └── A001/                    # Dane z detektorów (Darmstadt)
└── pyproject.toml
```

## Instalacja

```bash
git clone <repo-url>
cd traffic-simulation

# Z uv (zalecane)
uv venv && source .venv/bin/activate
uv pip install -e .

# Lub standardowy pip
python3 -m venv venv && source venv/bin/activate
pip install -e .
```

### Dodatkowe zależności (kalibracja, wykresy)

```bash
uv pip install pandas numpy matplotlib scipy
# lub: pip install pandas numpy matplotlib scipy
```

## Uruchomienie

### Wizualizacja pygame

```bash
python main.py
python main.py --lanes 3 --density 0.25
python main.py --lanes 3 --traffic-lights "50,0,52,2,10"
```

Sterowanie: SPACE (pauza), R (reset), +/- (prędkość), ESC (wyjście)

### Kalibracja modelu

Kalibracja dopasowuje parametry NaSch do rzeczywistych danych z detektorów pętlowych na autostradzie A001 w Darmstadt (Niemcy). Dane zawierają:
- **Przepływ** (Belegungen): liczba pojazdów na interwał (1 minuta)
- **Zajętość** (Verweilzeit): czas obecności pojazdów w ms
- **4 grupy detektorów** (D1-D4), każda dla 4 pasów ruchu
- **Okres**: styczeń 2025, ~37 000 pomiarów dla D4

#### Diagram fundamentalny

Kalibracja bazuje na **diagramie fundamentalnym** - zależności między gęstością ruchu a przepływem. To podstawowa charakterystyka ruchu drogowego:
- **Niska gęstość**: mało pojazdów → niski przepływ (brak zatłoczenia)
- **Średnia gęstość**: optymalny przepływ (maksimum krzywej)
- **Wysoka gęstość**: korki → niski przepływ (mimo wielu pojazdów)

#### Metoda optymalizacji

1. **Grid Search** dla parametrów dyskretnych:
   - `gap_rear` ∈ {2}
   - `reaction_delay` ∈ {0, 1}

2. **Nelder-Mead** dla parametrów ciągłych:
   - `p_slow` ∈ [0.05, 0.45]
   - `p_change` ∈ [0.1, 0.9]

3. **Funkcja celu**: RMSE (Root Mean Squared Error) między diagramami fundamentalnymi:
   - Model NaSch: symulacja dla różnych gęstości (0.01-0.80)
   - Dane rzeczywiste: agregacja pomiarów w przedziały zajętości
   - Minimalizacja różnicy przepływów

#### Uruchomienie

```bash
# Detektor D4 (domyślnie, najlepsze dane)
python calibrate_darmstadt.py

# Inny detektor
python calibrate_darmstadt.py --detector D1

# Bez wykresu (tylko JSON)
python calibrate_darmstadt.py --no-plot
```

#### Wyniki

**Skalibrowane parametry (detektor D4, 4 pasy):**
- `p_slow = 0.25` - prawdopodobieństwo losowego hamowania
- `p_change = 0.525` - prawdopodobieństwo próby zmiany pasa
- `gap_rear = 2` - minimalny odstęp z tyłu przy zmianie pasa
- `reaction_delay = 1` - opóźnienie reakcji (~1.6s)
- **RMSE = 88.53** poj/min
- **MAE = 66.96** poj/min

Pliki wyjściowe:
- `calibration_result.png` - porównanie diagramów fundamentalnych
- `calibration_result.json` - pełne wyniki kalibracji

#### Interpretacja

Model NaSch z skalibrowanymi parametrami:
- ✅ Dobrze odwzorowuje kształt krzywej przepływu
- ✅ Maksimum przepływu w podobnym miejscu jak dane rzeczywiste
- ✅ Poprawnie symuluje przejście swobodny ruch → korek
- ⚠️ Flow scaling 0.5× (korekta na warunki brzegowe cykliczne)

### Scenariusze demonstracyjne

```bash
# Wszystkie scenariusze (generuje 5 wykresów PNG)
python scenarios.py all

# Pojedynczy scenariusz
python scenarios.py shockwave      # Fala uderzeniowa
python scenarios.py lanes          # 1 vs 2 vs 3 pasy
python scenarios.py accident       # Wypadek - blokada pasa
python scenarios.py drivers        # Agresywni vs spokojni kierowcy
python scenarios.py speedlimit     # Strefa ograniczenia prędkości

# Animacja pygame
python scenarios.py shockwave --pygame
python scenarios.py accident --pygame
python scenarios.py lights --pygame    # Światła drogowe
```

## Scenariusze

### 1. Fala uderzeniowa (Shockwave)
Demonstracja jak jedno hamowanie propaguje się wstecz jako korek, nawet po usunięciu przyczyny.

### 2. Porównanie pasów
Pokazuje że 3 pasy ≠ 3× przepływ - efekt zmiany pasów i interakcji.

### 3. Wypadek
Blokada środkowego pasa na 3-pasmowej drodze. Spadek przepływu ~30-50%, nie 33%.

### 4. Zachowanie kierowców
Porównanie agresywnych (p_slow=0.10), normalnych (0.25) i spokojnych (0.40) kierowców.

### 5. Ograniczenie prędkości
Paradoks: przy wysokiej gęstości ograniczenie może POPRAWIĆ przepływ.

## Model NaSch

Reguły dla każdego pojazdu w każdym kroku:

1. **Przyspieszanie**: v → min(v + 1, v_max)
2. **Hamowanie**: v → min(v, gap_front)
3. **Losowe zwolnienie**: v → v - 1 z prawdopodobieństwem p_slow
4. **Ruch**: x → (x + v) mod L

### Zmiana pasa
- Motywacja: pas docelowy oferuje więcej przestrzeni
- Bezpieczeństwo: odstęp z przodu i tyłu
- Losowość: próba z prawdopodobieństwem p_change

### Opóźnienie reakcji
`reaction_delay = 1` symuluje czas reakcji kierowcy (~1.6s). Przy wysokiej gęstości stabilizuje ruch.

## Parametry

```bash
python main.py --help

# Podstawowe
--length 133        # Długość drogi [komórki]
--lanes 3           # Liczba pasów
--density 0.25      # Gęstość pojazdów [0-1]

# Model
--p-slow 0.25       # Losowe hamowanie
--p-change 0.525    # Zmiana pasa
--gap-rear 2        # Min. odstęp z tyłu
--reaction-delay 1  # Opóźnienie reakcji

# Przeszkody i światła
--traffic-lights "50,0,52,2,10"   # x1,lane1,x2,lane2,ticks
--obstacles "30,1,32,1"           # x1,lane1,x2,lane2
--speed-limits "20,0,40,2,3"      # x1,lane1,x2,lane2,vmax
```

## Dane

Projekt używa danych z detektorów pętlowych A001 (Darmstadt):
- `data/A001/A001_20250101_000000_-_20250201_000000_1min.csv`
- Interwał: 1 minuta
- Kolumny: przepływ (Belegungen), zajętość (Verweilzeit)
- Detektory: D1-D4, po 4 pasy każdy

## Testy

```bash
uv run pytest tests/ -v
```

70 testów pokrywających mechanikę NaSch, zmianę pasa, światła, przeszkody.

## Pliki wyjściowe

Po uruchomieniu skryptów:
- `calibration_result.png` - diagram fundamentalny (model vs dane)
- `calibration_result.json` - skalibrowane parametry
- `scenario_*.png` - wykresy ze scenariuszy

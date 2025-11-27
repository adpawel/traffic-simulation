# Symulacja Ruchu Drogowego - Model NaSch

Projekt implementuje obiektowy model automatów komórkowych Nagela-Schreckenberga (NaSch) z wieloma pasami ruchu, dynamiczną zmianą pasa, światłami sygnalizacyjnymi i przeszkodami. Wizualizacja w **Pygame**.

## Struktura Projektu

```
traffic-simulation/
├── main.py                     # Punkt wejścia aplikacji
├── simulation/                 # Główny pakiet symulacji
│   ├── __init__.py
│   ├── simulation.py          # Logika symulacji NaSch
│   ├── vehicle.py             # Klasa pojazdu
│   ├── road.py                # Klasa drogi
│   ├── localview.py           # Widok lokalny pojazdu
│   ├── speedLimits.py         # Limity prędkości, światła, przeszkody
│   └── pygame_view.py         # Wizualizacja pygame
├── src/
│   └── config.py              # Parametry domyślne
├── tests/                      # 70 testów jednostkowych
├── notebooks/                  # Jupyter notebooks (kalibracja)
├── data/                       # Dane ExiD (pobierz samodzielnie)
└── pyproject.toml             # Konfiguracja projektu
```

## Wymagania

- Python 3.11+
- pygame 2.6+ (jedyna wymagana zależność)

## Instalacja

### Opcja 1: Z użyciem uv (zalecane - szybsze)

1. Zainstaluj [uv](https://docs.astral.sh/uv/):
```bash
# Linux/Mac
curl -LsSf https://astral.sh/uv/install.sh | sh

# Windows (PowerShell)
powershell -c "irm https://astral.sh/uv/install.ps1 | iex"
```

2. Sklonuj repozytorium i zainstaluj:
```bash
git clone <repo-url>
cd traffic-simulation

# Utwórz środowisko i zainstaluj podstawowe zależności (pygame)
uv venv
source .venv/bin/activate  # Linux/Mac (.venv\Scripts\activate na Windows)
uv pip install -e .

# Zainstaluj narzędzia testowe (opcjonalnie)
uv pip install pytest pytest-cov
```

### Opcja 2: Standardowy pip

```bash
git clone <repo-url>
cd traffic-simulation

# Utwórz środowisko wirtualne
python3.13 -m venv venv lub py -3.13 -m venv venv # wersja musi być >=3.11
source venv/bin/activate  # Linux/Mac (venv\Scripts\activate na Windows)

# Zainstaluj podstawowe zależności
pip install -e .

# Zainstaluj narzędzia testowe (opcjonalnie)
pip install pytest pytest-cov
```

### Opcjonalne zależności

**Dla pracy z danymi ExiD i notebookami:**
```bash
# Z uv:
uv pip install pandas numpy matplotlib seaborn scikit-learn ipykernel

# Lub z pip:
pip install pandas numpy matplotlib seaborn scikit-learn ipykernel
```


## Uruchomienie

### Wizualizacja pygame (domyślnie)

```bash
python main.py
```

### Parametry z linii poleceń

```bash
# Zmień liczbę pasów i gęstość
python main.py --lanes 3 --density 0.3

# Dostosuj parametry modelu
python main.py --p-slow 0.2 --p-change 0.5

# Dostosuj wizualizację
python main.py --fps 20 --cell-size 15 --window-width 1600

# Dodaj światła sygnalizacyjne (x=50-52, pasy 0-1, cykl 10 kroków)
python main.py --lanes 3 --traffic-lights "50,0,52,2,10"

# Dodaj przeszkodę (x=30-32, pas 1)
python main.py --lanes 3 --obstacles "30,1,32,1"

# Dodaj lokalne ograniczenie prędkości (x=30-32, v_max = 3 komórki na krok)
python main.py --lanes 3 --speed-limits "30,0,32,2,3"

# Kombinacja świateł i przeszkód
python main.py --lanes 3 --traffic-lights "40,0,42,1,8;80,1,82,2,12" --obstacles "60,0,62,0"

# Reakcja kierowcy (opóźnienie 1 krok = ~1.6s)
python main.py --lanes 1 --density 0.6 --reaction-delay 1

# Powtarzalne testy z seedem
python main.py --lanes 1 --density 0.6 --seed 42 --no-gui --steps 2000

# Pełna demonstracja wszystkich opcji
python main.py --lanes 3 --density 0.2 --seed 42 --reaction-delay 1 \
  --speed-limits "20,0,40,2,3;60,1,80,2,2" \
  --obstacles "50,0,55,1" \
  --traffic-lights "45,0,45,2,5" \
  --length 100
```

### Tryb konsolowy (bez GUI)

```bash
python main.py --no-gui --steps 1000 --lanes 2 --density 0.25
```

### Pełna lista parametrów

```bash
python main.py --help
```

**Parametry symulacji:**
- `--length` - długość drogi w komórkach (domyślnie: 133)
- `--lanes` - liczba pasów ruchu (domyślnie: 1)
- `--density` - początkowa gęstość pojazdów 0.0-1.0 (domyślnie: 0.15)
- `--p-slow` - prawdopodobieństwo losowego zwolnienia (domyślnie: 0.3)
- `--p-change` - prawdopodobieństwo próby zmiany pasa (domyślnie: 0.6)
- `--gap-rear` - minimalny odstęp z tyłu przy zmianie pasa (domyślnie: 2)
- `--reaction-delay` - opóźnienie reakcji kierowcy w krokach (domyślnie: 0)
- `--seed` - seed dla generatora losowego (domyślnie: losowy)

**Światła, przeszkody i lokalne ograniczenia:**
- `--traffic-lights` - światła sygnalizacyjne: `"x1,lane1,x2,lane2,ticks;..."` (np. `"50,0,52,1,10"`)
- `--obstacles` - przeszkody stałe: `"x1,lane1,x2,lane2;..."` (np. `"30,1,32,1"`)
- `--speed-limits` - lokalne ograniczenia prędkości: `"x1,lane1,x2,lane2,vmax;..."` (np. `"20,0,40,2,3"`)

**Parametry wizualizacji:**
- `--cell-size` - wysokość komórki w pikselach (domyślnie: 20)
- `--fps` - liczba klatek na sekundę (domyślnie: 10)
- `--window-width` - szerokość okna w pikselach (domyślnie: 1400)

**Tryb konsolowy:**
- `--no-gui` - uruchom bez wizualizacji
- `--steps` - liczba kroków w trybie --no-gui (domyślnie: 1000)

## Sterowanie (pygame)

- **SPACE** - pauza/wznowienie symulacji
- **R** - reset symulacji
- **+/-** - zmiana prędkości symulacji (FPS)
- **ESC/Q** - wyjście

## Testy

Uruchom wszystkie testy (70 testów):
```bash
# Z uv:
uv run pytest tests/ -v

# Lub ze standardowym pytest:
pytest tests/ -v
```

Uruchom konkretny plik testowy:
```bash
uv run pytest tests/test_simulation.py -v
pytest tests/test_vehicle.py -v
```

Wszystkie testy pokrywają:
- ✅ Mechanikę NaSch (acceleration, braking, randomization, movement)
- ✅ Zmianę pasa (motivation, safety, gaps)
- ✅ Światła sygnalizacyjne (cykliczne przełączanie)
- ✅ Przeszkody (statyczne blokowanie)
- ✅ Widoki lokalne (LocalView)
- ✅ Liczenie przepływu (flow counting)

## Konfiguracja

Domyślne parametry można edytować w `src/config.py`:

```python
L = 133              # Długość drogi w komórkach
LANES = 1            # Liczba pasów
DENSITY = 0.15       # Gęstość początkowa
P_SLOW = 0.3         # Prawdopodobieństwo losowego zwolnienia (NaSch)
P_CHANGE = 0.6       # Prawdopodobieństwo próby zmiany pasa
GAP_REAR = 2         # Minimalny odstęp z tyłu przy zmianie pasa
MAX_SPEED = 5        # Maksymalna prędkość pojazdu (komórki/krok)
REACTION_DELAY = 0   # Opóźnienie reakcji kierowcy (kroki)
TIME_STEP_S = 1.6    # Czas jednego kroku symulacji w sekundach
```

## Model NaSch

Model Nagela-Schreckenberga implementuje następujące reguły (dla każdego pojazdu w każdym kroku):

1. **Przyspieszanie**: v → min(v + 1, v_max, speed_limit)
2. **Hamowanie**: v → min(v, gap_front)
3. **Losowe zwolnienie**: v → max(v - 1, 0) z prawdopodobieństwem p_slow
4. **Sprawdzenie przeszkód**: v → 0 jeśli przeszkoda na drodze
5. **Retardacja (opcjonalna)**: opóźnienie reakcji kierowcy przez bufor FIFO
6. **Ruch**: x → (x + v) mod L

### Opóźnienie reakcji (Reaction Delay)

Parametr `--reaction-delay N` symuluje biologiczny czas reakcji kierowcy:
- Kierowca podejmuje decyzję o zmianie prędkości (przyspieszenie/hamowanie)
- Faktyczna zmiana następuje dopiero po N krokach (~1.6s na krok)
- Implementacja: bufor FIFO przechowujący historię N+1 wartości prędkości

**Efekty przy różnych gęstościach:**
- **Niska gęstość (0.2-0.3)**: Delay zmniejsza przepływ (~5-8%), bo pojazdy wolniej reagują na wolną przestrzeń
- **Wysoka gęstość (0.6-0.8)**: Delay zwiększa przepływ (+7-14%!), stabilizując ruch i redukując fale uderzeniowe

Przykład porównania (seed 48, density 0.6, 2000 kroków):
- Bez delay: 0.269 pojazdów/krok (stop-and-go, korki)
- Z delay=1: 0.406 pojazdów/krok (płynniejszy ruch)

### Zmiana pasa

Pojazdy mogą zmieniać pasy jeśli:
- Motywacja: pas docelowy oferuje więcej wolnej przestrzeni
- Bezpieczeństwo: wystarczający odstęp z przodu i z tyłu
- Losowość: próba zmiany z prawdopodobieństwem p_change

## Światła, przeszkody i lokalne ograniczenia prędkości

System obsługuje:
- **Światła sygnalizacyjne** - dynamiczne, cykliczne (czerwone↔zielone)
- **Przeszkody** - statyczne blokady (v_max=0)
- **Lokalne ograniczenia prędkości** - strefy ze zmniejszonym v_max

### Format parametrów

**Światła sygnalizacyjne:**
```
--traffic-lights "x1,lane1,x2,lane2,ticks;x3,lane3,x4,lane4,ticks;..."
```
- `x1,x2` - zakres pozycji x (komórki)
- `lane1,lane2` - zakres pasów (0-indexed)
- `ticks` - liczba kroków cyklu (czerwone↔zielone)

**Przeszkody:**
```
--obstacles "x1,lane1,x2,lane2;x3,lane3,x4,lane4;..."
```
- Przeszkody są stałe (nie zmieniają stanu)
- Blokują całkowicie ruch (v_max=0)

**Lokalne ograniczenia prędkości:**
```
--speed-limits "x1,lane1,x2,lane2,vmax;x3,lane3,x4,lane4,vmax;..."
```
- `x1,x2` - zakres pozycji x
- `lane1,lane2` - zakres pasów
- `vmax` - maksymalna prędkość w tej strefie (komórki/krok)

### Przykłady

```bash
# Światło na pozycji x=50-52, wszystkie pasy, cykl 10 kroków
python main.py --lanes 3 --traffic-lights "50,0,52,2,10"

# Dwa światła z różnymi cyklami
python main.py --lanes 3 --traffic-lights "30,0,32,2,8;70,0,72,2,12"

# Przeszkoda na środkowym pasie
python main.py --lanes 3 --obstacles "40,1,42,1"

# Kombinacja świateł i przeszkód
python main.py --lanes 3 --traffic-lights "30,0,32,1,10" --obstacles "70,2,72,2"

# Lokalne ograniczenie prędkości (strefa 30 → v_max=2)
python main.py --lanes 2 --speed-limits "20,0,50,1,2"

# Kompleksowy scenariusz
python main.py --lanes 3 --density 0.2 --seed 42 --reaction-delay 1 \
  --speed-limits "20,0,40,2,3;60,1,80,2,2" \
  --obstacles "50,0,55,1" \
  --traffic-lights "45,0,45,2,5"
```

### Wizualizacja w pygame

**Limity prędkości:**
- 🔴 **Ciemnoczerwony** - przeszkoda stała (v_max=0)
- 🔴 **Jasnoczerwony** - światło czerwone aktywne (v_max=0)
- 🟦 **Losowe kolory** - lokalne ograniczenia prędkości (v_max > 0)
- ⬜ **Brak koloru** - światło zielone (przejezdne)

**Legenda** :
- Pokazuje wszystkie aktywne strefy z ich zakresami, pasami i limitami prędkości
- Każde lokalne ograniczenie ma przypisany losowy kolor dla łatwego rozróżnienia

**Pojazdy (gradient prędkości):**
- 🔴 **Czerwony** - stojący (v=0)
- 🟡 **Żółty** - średnia prędkość (~50% v_max)
- 🟢 **Zielony** - maksymalna prędkość (v=v_max)

## Dane ExiD (opcjonalnie)

Projekt może używać danych z [ExiD Dataset](https://www.exid-dataset.com/) do kalibracji parametrów.

⚠️ **Dane NIE są w repozytorium** (ważą ~6GB). Aby z nich korzystać:

1. Pobierz ExiD dataset z oficjalnej strony
2. Rozpakuj do `data/data/` i `data/exiD-dataset-v2.1/`
3. Uruchom notebook kalibracyjny: `notebooks/calibration.ipynb`

Bez danych ExiD możesz korzystać z domyślnych parametrów lub przykładowych wyników kalibracji (`data/nasch_calibration_summary.csv`).

***

Koniec i bomba a kto czytał ten trąba.

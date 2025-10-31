# Predykcja Ruchu Samochodów (Data-Driven NaSch Model) 

Projekt implementuje model automatów komórkowych Nagela-Schreckenberga (NaSch), kalibrowany na danych z drona **ExiD**, z dynamiczną wizualizacją w **Pygame** / **SUMO**.

## 1. Wymagania i Struktura Projektu

### A. Wymagania Wstępne

-   Zainstalowana dystrybucja **Conda** (lub Miniconda).
    
-   Pliki danych **ExiD** (w formacie `XX_tracks.csv`, `XX_tracksMeta.csv`, etc.).
    

### B. Struktura Katalogów

Umieść wypakowany zbiór ExiD w katalogu /data, aby umożliwić pomyślne ładowanie danych:

```
/katalog_projektu
|-- environment.yml
|-- main.py
|-- data.py
|-- /data
    |-- /data
    |-- /maps
    |-- ...   

```

----------

## 2. Instrukcja Uruchomienia

Postępuj zgodnie z poniższymi krokami, aby skonfigurować środowisko i uruchomić symulację.

### Krok 2.1: Konfiguracja Środowiska Conda

1.  Otwórz terminal w katalogu głównym projektu.
    
2.  Utwórz i aktywuj środowisko korzystając z pliku `environment.yml`:
    
`conda env create -f environment.yml`
`conda activate nasch`

### Krok 2.2: Uruchomienie Symulacji

Uruchom plik główny `main.py`. Program automatycznie załaduje i zagreguje dane ExiD w celu kalibracji, a następnie uruchomi dynamiczną wizualizację.
`python main.py`

### Oczekiwane Działanie

1.  **Konsola:** Zobaczysz komunikaty o pomyślnej **kalibracji** (wartości **VMAX​** i **P** wyciągnięte z ExiD).
    
2.  **Pygame:** Otworzy się okno z dynamiczną symulacją. Samochody będą poruszać się w trybie **Swobodnego Przepływu**, zwalniając zgodnie z empirycznie ustalonym prawdopodobieństwem **P**.
    

----------

## 3. Parametry Kontrolne

Kluczowe parametry symulacji można kontrolować w pliku `main.py`:
| Parametr | Opis | Lokalizacja w main.py |
|------------|------------|------------|
| EXID_REC_IDS | Lista ID nagrań ExiD użytych do **kalibracji** VMAX​ i P. | if __name__ == "__main__": |
| K_FREE_FLOW | **Gęstość początkowa** w symulacji Pygame. (np. `0.10`) | if __name__ == "__main__": |
| steps_per_second | Kontroluje **prędkość wizualizacji** w Pygame (np. `10` kroków/sekundę). | Funkcja `run_pygame_simulation` |

**Wskazówka:** Aby zaobserwować tworzenie się **spontanicznych korków** (tylko z powodu losowości P), ustaw **`K_FREE_FLOW`** na wyższą wartość, np. **`0.30`**

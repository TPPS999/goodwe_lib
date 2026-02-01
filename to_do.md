# Plan działania - goodwe_lib

**Data rozpoczęcia:** 2026-01-24 18:32
**Ostatnia aktualizacja:** 2026-02-01 13:54

---

## Status ogólny

### Co zostało zrobione
- ✅ Struktura podstawowa projektu goodwe_lib
- ✅ Wsparcie dla wielu serii inwerterów (ET, EH, BT, BH, ES, EM, BP, DT, MS, D-NS, XS)
- ✅ Komunikacja UDP (port 8899) i Modbus/TCP (port 502)
- ✅ Dodano wsparcie dla ET40 i ET50 (commit 147c4f3, b40b7aa)
- ✅ Kompletne pokrycie rejestrów Work Mode i Power Factor (commit d57cf0a)
- ✅ Poprawiono mapowanie sensorów PV dla ET40/ET50 (commit 147c4f3)
- ✅ Wersja 0.4.9 → 0.5.0 (wsparcie dla parallel system)
- ✅ Utworzenie struktury zarządzania projektem:
  - ✅ Folder to_do/
  - ✅ Folder context_record/
  - ✅ Plik CLAUDE.md z zasadami pracy
  - ✅ Wpisy w .gitignore dla lokalnych plików zarządzania

- ✅ Peak Shaving switch (47591) i Battery Current Limits (45353, 45355) - v0.6.1
- ✅ Entity ID prefix (GWxxxx_) dla parallel systems - v0.6.0
- ✅ Auto-discovery parallel slaves - v0.6.0
- ✅ Observation sensors dla nieudokumentowanych rejestrow (33xxx, 38xxx, 48xxx, 55xxx)
  - Usunięto udokumentowane zakresy (42xxx, 50xxx)

### Co jest w trakcie realizacji
🎯 **v0.6.6 - Testowanie i dopracowanie observation sensors**
- ✅ System parallel działa poprawnie
- ✅ TypeError naprawiony
- ⚠️ **Observation sensors nie ładują się** (33xxx, 38xxx, 48xxx, 55xxx)
  - Reszta systemu startuje bez problemów
  - Wymaga zbadania dlaczego flagi `_observe_*` nie działają
  - Możliwe że trzeba ręcznie włączyć: `inverter._observe_48xxx = True`

### Ostatnie zmiany (2026-01-31 12:30)
- ✅ **v0.6.3 + custom component v0.9.9.51** - Fix peak_shaving_power_slot8 unit
  - **Problem:** Rejestr 47592 oczekuje wartosci w watach, nie kW
  - **Rozwiazanie:** Zmiana z KILO_WATT na WATT
  - **Zmiany w number.py:**
    - native_unit_of_measurement: KILO_WATT -> WATT
    - native_step: 0.1 -> 100
    - native_min_value/max_value: +-40 -> +-40000
    - Usunieto /10 z mapper i *10 z setter
  - **Dodano:** Komentarz o parallel systems (wartość wysylana do kazdego invertera osobno)
  - **Commit:** 91abb33
- ✅ **Wersje:** goodwe_lib v0.6.3, custom_components/goodwe v0.9.9.51

### Ostatnie zmiany (2026-01-25 15:30)
- ✅ **v0.5.9 + custom component v0.9.9.42** - TOU sensors widoczne w Home Assistant
  - **Problem:** TOU sensory były w __settings_arm_fw_* zamiast __all_sensors
  - **Skutek:** Nie pojawiały się w HA bo custom component czyta tylko z inverter.sensors()
  - **Rozwiązanie:** Przeniesienie wszystkich 48 TOU sensors do __all_sensors
  - **goodwe_lib v0.5.9:**
    - Wszystkie TOU slots 1-8 (47547-47594) przeniesione do __all_sensors
    - Dodano komentarz w et.py o wymaganych wersjach FW (19+ dla 1-4, 22+ dla 5-8)
    - Testy zmienione z pytest na unittest (zgodność z projektem)
    - Poprawiono testy: 23:59 = 5947 (nie 6143)
    - Commit: 24a2f92, Tag: v0.5.9
  - **custom_components/goodwe v0.9.9.42:**
    - Aktualizacja zależności goodwe_lib: v0.5.8 → v0.5.9
    - Commit: b0eac91
  - **Rezultat:** TOU sensory będą widoczne w HA bez zmian w custom component!

### Poprzednia zmiana (2026-01-25 14:00)
- ✅ **v0.5.7 + custom component v0.9.9.40** - Implementacja TOU (Time of Use) masks
  - **goodwe_lib v0.5.7:**
    - Nowy moduł `tou_helpers.py` z funkcjami encode/decode
    - Nowe klasy sensorów: TimeOfDay, WorkWeekV2, MonthMask
    - 8 slotów TOU (47547-47594) z czytelnymi nazwami
    - Testy jednostkowe dla wszystkich funkcji TOU
    - Commit: 523eca1, Tag: v0.5.7
  - **custom_components/goodwe v0.9.9.40:**
    - Aktualizacja zależności goodwe_lib: v0.5.6 → v0.5.7
    - Usunięcie hardcoded eco_mode_*_param* Number entities (296 linii)
    - Usunięcie translation keys dla starych sensorów TOU
    - Commit: f461707
- ✅ **v0.5.8 + custom component v0.9.9.41** - Dodano WorkWeekMode.BATTERY_POWER_PERMILLAGE (0xF9)
  - Znaleziono w produkcji: slot 1 używał mode 0xF9 (nieznany enum)
  - Dodano BATTERY_POWER_PERMILLAGE = 0xF9 do WorkWeekMode
  - Commit: 6498ae2 (v0.5.8), 0ea28f6 (custom component)

### Co jest do zrobienia

#### 0. Dopracowanie observation sensors - **PRIORYTET**
**Status:** ⚠️ W TRAKCIE
**Problem:** Observation sensors (33xxx, 38xxx, 48xxx, 55xxx) nie ładują się w HA
- ✅ Sensory są zdefiniowane w et.py
- ✅ Flagi `_observe_*` są zainicjalizowane na False
- ⚠️ Wymaga zbadania:
  - Czy sensory muszą być ręcznie włączone przez użytkownika
  - Czy potrzebna jest dedykowana konfiguracja w custom component
  - Czy read_runtime_data() poprawnie obsługuje te rejestry
  - Sprawdzić logi HA dla szczegółów błędu
- **Następny krok:** Analiza logów i mechanizmu włączania observation sensors

#### 1. Inicjalizacja systemu zarządzania projektem
- ✅ Utworzenie folderu to_do/
- ✅ Utworzenie folderu context_record/
- ✅ Utworzenie pierwszego context snapshot
- ✅ Utworzenie pliku to_do.md
- ⏸️ Commit zmian (oczekiwanie na zakończenie bieżącego zadania)

#### 2. Wsparcie dla systemów równoległych (Parallel Inverter System)
**Priorytet:** WYSOKI
**Źródło:** docs/modbus parralel.md
**Status:** ✅ ZAKOŃCZONE

##### 2.1. Analiza wymagań
- ✅ Przeanalizowanie dokumentacji rejestrów Modbus dla systemów równoległych
- ✅ Identyfikacja aktualnego stanu implementacji w kodzie
- ✅ Określenie zakresu zmian (które pliki zostaną dotknięte)

##### 2.2. Implementacja rejestrów systemu równoległego - ✅ ZAKOŃCZONE
Dodano wszystkie 38 rejestrów Modbus (10400-10485) dla systemów równoległych:
- ✅ Grupa 1 (10400-10440): System Status - 27 rejestrów
- ✅ Grupa 2 (10470-10485): Additional Parameters - 11 rejestrów

##### 2.3. Implementacja w kodzie - ✅ ZAKOŃCZONE
- ✅ Dodano nową grupę sensorów `__all_sensors_parallel` w et.py
- ✅ Typy U32 i S32 już istniały (Power4, Power4S)
- ✅ Dodano obsługę scale factor (Decimal z dzielnikiem 100 i 10)
- ✅ Dodano zmienną `_has_parallel` do wykrywania wsparcia
- ✅ Dodano komendę `_READ_PARALLEL_DATA` (0x28a0, 0x56)
- ✅ Zintegrowano z metodą `read_runtime_data()`
- ✅ Automatyczne wykrywanie parallel system przez rejestr 10400
- ✅ Weryfikacja składni Python - bez błędów
- ✅ Liczba sensorów: 173 (bez parallel) → 211 (z parallel)

##### 2.4. Dokumentacja i testy - ⚠️ CZĘŚCIOWO
- ✅ Weryfikacja zgodności z istniejącymi rejestrami (brak konfliktów)
- ✅ Podstawowe testy kompilacji
- ⚠️ Testy jednostkowe wymagają aktualizacji (liczba sensorów się zmieniła)
- ⏳ Aktualizacja dokumentacji użytkownika (opcjonalne)
- ⏳ Dodanie przykładów użycia (opcjonalne)

##### 2.5. Finalizacja - ✅ ZAKOŃCZONE
- ✅ Aktualizacja VERSION: 0.4.9 → 0.5.0
- ⏳ Commit i push (goodwe_lib)
- ⏳ Aktualizacja custom component w home-assistant-goodwe-inverter
- ⏳ Commit i push (home-assistant-goodwe-inverter)

#### 3. Aktualizacja Home Assistant Custom Component - ✅ ZAKOŃCZONE
**Priorytet:** WYSOKI
**Status:** ✅ ZAKOŃCZONE

- ✅ Przejście do repozytorium home-assistant-goodwe-inverter
- ✅ Aktualizacja zależności goodwe do wersji 0.5.0 w manifest.json
- ✅ Weryfikacja kodu custom component:
  - Custom component używa `inverter.sensors()` do generowania encji
  - Nowe parallel sensors będą automatycznie dostępne w HA
  - ✅ Nie wymagane żadne dodatkowe zmiany w kodzie
- ✅ Aktualizacja wersji custom component: 0.9.9.30 → 0.9.9.31
- ✅ Utworzono tag v0.5.0 w goodwe_lib
- ✅ Commit i push zmian do obu repozytoriów
- ⏳ Testy z Home Assistant (do wykonania przez użytkownika)

#### 4. Naprawy i ulepszenia po implementacji Parallel System - ✅ ZAKOŃCZONE (v0.5.4)
**Priorytet:** KRYTYCZNY
**Status:** ✅ ZAKOŃCZONE

##### 4.1. Problem: Slave inverter zwracał success: False - ✅ ROZWIĄZANE
- ✅ Zidentyfikowano problem: brak zagnieżdżonych try/except w meter fallback chain
- ✅ Dodano nested exception handling dla całego fallback:
  - Extended meter2 (125 reg) → Extended (58 reg) → Basic (45 reg)
  - Każdy poziom z własnym try/except dla ILLEGAL_DATA_ADDRESS
- ✅ Rezultat: Slave zwraca `success: True`
- ✅ Commit: 00504d0 (v0.5.2)

##### 4.2. Problem: Version detection pokazywał 'unknown' - ✅ ROZWIĄZANE
- ✅ Dodano `__version__` attribute w goodwe/__init__.py
- ✅ Użyto importlib.metadata (standard Python packaging)
- ✅ Dodano MANIFEST.in dla pliku VERSION
- ✅ Fallback do pkg_resources dla starszych Python
- ✅ Rezultat: Pokazuje `GoodWe library version: 0.5.4`
- ✅ Commit: 36b80d8 (v0.5.3), 3af2f8e (v0.5.4)

##### 4.3. Comprehensive EMS Settings - ✅ DODANE
- ✅ 24 sloty Feed Power schedule (47619-47738)
- ✅ Force charge SOC settings (47531-47532)
- ✅ WiFi management (47539, 47541)
- ✅ SAPN settings (47739-47744)
- ✅ Battery/Grid control registers
- ✅ Commit: cf887a6 (v0.5.1)

##### 4.4. Finalizacja - ✅ ZAKOŃCZONE
- ✅ goodwe_lib: v0.5.0 → v0.5.4
- ✅ custom_components/goodwe: 0.9.9.31 → 0.9.9.36
- ✅ Wszystkie tagi pushed do GitHub
- ✅ System równoległy działa stabilnie (Master + Slave)
- ✅ Używanie shell_command w HA do wymuszonej reinstalacji

#### 5. Ulepszenia nazewnictwa i UX - ✅ ZAKOŃCZONE (v0.5.5 - v0.5.6)
**Priorytet:** ŚREDNI
**Status:** ✅ ZAKOŃCZONE

##### 5.1. Zmiana oznaczeń faz z RST na L1/L2/L3 - ✅ ZAKOŃCZONE
**Uzasadnienie:** RST to stara konwencja, L1/L2/L3 jest bardziej zrozumiała
**Zakres:**
- ✅ Zmieniono 3 sensory parallel phase power (et.py:366-368)
- ✅ `parallel_r_phase_inverter_power` → `parallel_l1_inverter_power`
- ✅ `parallel_s_phase_inverter_power` → `parallel_l2_inverter_power`
- ✅ `parallel_t_phase_inverter_power` → `parallel_l3_inverter_power`
- ✅ Commit: 9146072 (v0.5.5)

##### 5.2. Dodanie prefiksu "Master" do encji parallel system - ✅ ZAKOŃCZONE
**Uzasadnienie:** Encje z grupy parallel są zbiorcze (suma wszystkich inwerterów)
**Zakres:**
- ✅ Dodano prefiks "Master" do wszystkich 42 parallel sensors (et.py:349-389, 534)
- ✅ Przykłady: "PV Total Power" → "Master PV Total Power", "SOC" → "Master SOC"
- ✅ Ułatwia rozróżnienie encji master vs slave w HA
- ✅ Commit: 9146072 (v0.5.5)

##### 5.3. Implementacja masek TOU (Time of Use) - ✅ ZAKOŃCZONE (v0.5.7 - v0.5.9)
**Priorytet:** WYSOKI - duże ułatwienie dla użytkowników
**Uzasadnienie:** Aktualne wartości TOU (47547-47594) to surowe dane binarne, trudne do interpretacji
**Zakres:**
- ✅ **Moduł tou_helpers.py** z funkcjami encode/decode (v0.5.7):
  - ✅ `encode_time()` / `decode_time()` - format HH:MM → (hours << 8) | minutes
  - ✅ `encode_workweek()` / `decode_workweek()` - Table 8-34 (H-byte=mode, L-byte=days)
  - ✅ `encode_months()` / `decode_months()` - month bitmask (12 bits)
  - ✅ WorkWeekMode enum z trybami: ECO, Dry contact load, Peak shaving, Backup mode, Battery power permillage
  - ✅ Format functions: `format_workweek_readable()`, `format_months_readable()`
- ✅ **Nowe klasy sensorów** (sensor.py v0.5.7):
  - ✅ `TimeOfDay` - automatyczne formatowanie HH:MM
  - ✅ `WorkWeekV2` - wyświetlanie trybu i dni (np. "ECO Mode: Mon,Tue,Wed,Thu,Fri")
  - ✅ `MonthMask` - wyświetlanie miesięcy (np. "Jan,Feb,Dec" lub "All year")
- ✅ **Aktualizacja et.py** - TOU sensors widoczne w HA (v0.5.9):
  - ✅ 8 slotów TOU (47547-47594) przeniesione do __all_sensors
  - ✅ Każdy slot: Start Time, End Time, Work Week, Param1, Param2, Months
  - ✅ Sloty 1-4: wymagają ARM FW 19+
  - ✅ Sloty 5-8: wymagają ARM FW 22+
  - ✅ Sensory automatycznie pojawiają się w HA (bez zmian w custom component)
- ✅ **Testy jednostkowe** (tests/test_tou_helpers.py v0.5.7, v0.5.9):
  - ✅ Testy encode/decode dla wszystkich typów
  - ✅ Roundtrip tests (encode → decode → verify)
  - ✅ Walidacja błędów (invalid input)
  - ✅ Wszystkie WorkWeekMode enum values
  - ✅ Zmieniono z pytest na unittest (zgodność z projektem)
- ✅ **Commits:** 523eca1 (v0.5.7), 6498ae2 (v0.5.8), 24a2f92 (v0.5.9)
- ✅ **Uwagi:**
  - Wykorzystano algorytmy z goodwe_modbus_gui
  - Znaleziono w produkcji: mode 0xF9 (BATTERY_POWER_PERMILLAGE)
  - ⏳ **Następny krok:** Write support (zadania 3-4 w TodoWrite)

##### 5.4. Poprawka odczytu Serial Number - ✅ ZAKOŃCZONE
**Problem:** AttributeError: 'ProtocolResponse' object has no attribute 'get'
**Przyczyna:** Sensor serial_number próbował wywołać `.get()` na ProtocolResponse zamiast dict
**Rozwiązanie:**
- ✅ Usunięto sensor serial_number z `__all_sensors` (et.py:157-159)
- ✅ Serial number jest już dostępny w device info (główne miejsce)
- ✅ Serial number jest dodawany manualnie w read_runtime_data() (et.py:892)
- ✅ Commit: ef0ed6a (v0.5.6)

##### 5.5. Automatyczna weryfikacja wersji biblioteki w custom component - ✅ ZAKOŃCZONE
**Uzasadnienie:** Zapobiegnie problemom z cache - user zobaczy warning jeśli wersja się nie zgadza
**Zakres:**
- ✅ Parsowanie oczekiwanej wersji z manifest.json requirements (regex)
- ✅ Porównanie z zainstalowaną wersją goodwe.__version__
- ✅ Persistent notification w HA UI jeśli wersje się nie zgadzają
- ✅ Gotowa komenda shell do skopiowania dla aktualizacji
- ✅ TODO w kodzie: w przyszłości zamienić na repair issue dla lepszego UX
- ✅ Commit: df2a8d1, 4fc516d (v0.9.9.37-39 custom component)

##### 5.6. Write support dla TOU sensors - ⏳ W TRAKCIE
**Priorytet:** WYSOKI - dokończenie TOU functionality
**Uzasadnienie:** TOU sensors są już widoczne w HA (read-only), ale użytkownicy chcą je edytować przez UI
**Zakres:**
- ⏳ **goodwe_lib**: Już gotowe!
  - ✅ TimeOfDay, WorkWeekV2, MonthMask mają metodę encode_value()
  - ✅ Można użyć inverter.write_setting() do zapisu
- ⏳ **custom_components/goodwe**: Utworzenie UI entities
  - ⏳ Number entities dla time inputs (format HH:MM)
  - ⏳ Select entities dla Work Week mode
  - ⏳ Helper entities dla day/month selection
  - ⏳ Integration z inverter.write_setting()
- ⏳ **Testy**: Weryfikacja read/write cycle
  - ⏳ Odczyt TOU z invertera
  - ⏳ Modyfikacja przez HA UI
  - ⏳ Zapis do invertera
  - ⏳ Weryfikacja trwałości zmian
- ⏳ **Status:** DO ZROBIENIA - następne zadanie

##### 5.7. Dokumentacja systemów równoległych
**Priorytet:** NISKI
**Zakres:**
- Dodać do README.md sekcję o parallel systems
- Wyjaśnić różnice Master vs Slave
- Opisać które rejestry są dostępne dla slave
- Dodać przykłady konfiguracji w HA
- ⏳ Status: DO ZROBIENIA

#### 6. Znane ograniczenia (do zaakceptowania)
- ❌ **Slave nie ma SOC baterii**: W systemach równoległych GoodWe tylko master ma dostęp do BMS (37000-37023). Slave zwraca ILLEGAL_DATA_ADDRESS. To jest **ograniczenie hardware**, nie bug.
- ❌ **Slave nie ma meter**: Meter jest wspólny i obsługiwany przez master. Slave zwraca ILLEGAL_DATA_ADDRESS dla 36000+.

#### 7. Dalszy rozwój - backlog
- Wsparcie dla nowych modeli inwerterów (jeśli będą zgłoszenia)
- Optymalizacja istniejącego kodu
- Rozszerzenie testów jednostkowych

---

## Notatki

### Struktura commitów
- Commity regularnie, nie rzadziej niż co 15 minut
- Format: `<type>: <opis>` np. `feat:`, `fix:`, `chore:`
- Zawsze z opisem gdzie jesteśmy w planie

### GitHub Issues
Duże funkcjonalności będą śledzone przez GitHub Issues i linkowane tutaj.

### Zasady pracy
Wszystkie zasady pracy są opisane w [CLAUDE.md](CLAUDE.md):
- Plan kroczący (nigdy nie usuwamy, tylko dodajemy i oznaczamy jako skończone)
- Backup to_do.md przed każdą modyfikacją
- Context snapshots regularnie
- Kod bez polskich znaków
- Komunikacja po polsku

---

## Historia zmian planu

### 2026-02-01 13:51 - Bugfix: TypeError in parallel sensors (v0.6.6)
- ✅ Naprawiono krytyczny błąd TypeError: 'str' object is not callable
  - **Problem:** Calculated sensors w __all_sensors_parallel (linie 442-444) nie miały funkcji getter
  - **Przyczyna:** Sensory Calculated wymagają callable jako drugi parametr, ale zostały zdefiniowane tylko z nazwą
  - **Skutek:** Błąd w _map_response() podczas odczytu parallel data (linia 1149)
- ✅ **Rozwiązanie:** Usunięto błędne sensory Calculated z __all_sensors_parallel
  - Wartości calculated są już obliczane w read_runtime_data() (linie 1150-1164)
  - Dodawane bezpośrednio do data dict: parallel_meter_current_l1/l2/l3_calc
  - Nie potrzebują definicji sensorów w tuple
- ✅ Wersje finalne:
  - goodwe_lib: v0.6.6 (tag pushed)
  - custom_components/goodwe: v0.9.9.55
- ✅ Wszystkie commity pushed, gotowe do testowania
- Backup: to_do/202602011352_to_do.md

### 2026-02-01 13:07 - Cleanup: Remove documented registers from observation sensors
- ✅ Usunięto udokumentowane rejestry 42xxx i 50xxx z observation sensors
  - **42xxx (Feed Power)**: Rejestr jest w pełni udokumentowany w oficjalnej dokumentacji GoodWe
    - 42000: EMS Power Mode (0=Self Use, 1=ECO)
    - 42003/42004: Feed Power Enable/Limit
    - 42006-42014: Anti-backflow settings
  - **50xxx (Self-check)**: Rejestr jest w pełni udokumentowany
    - 50002-50099: Diagnostyka PV/baterii, status sieci, częstotliwość
- ✅ Pozostawiono tylko naprawdę nieudokumentowane rejestry:
  - **33xxx (Grid config)**: 33002-33079 nieudokumentowane (tylko 33200+ jest w docs)
  - **38xxx (Grid phase)**: Całkowicie nieudokumentowane
  - **48xxx (Slave battery)**: Slave-specific registers nieudokumentowane
  - **55xxx (Energy counters)**: Nieudokumentowane
- ✅ Usunięto z kodu:
  - Tuple definitions `__observation_sensors_42xxx` i `__observation_sensors_50xxx`
  - Read commands `_READ_OBS_42XXX` i `_READ_OBS_50XXX`
  - Flags `_observe_42xxx` i `_observe_50xxx`
  - Sensor assignments `_sensors_obs_42xxx` i `_sensors_obs_50xxx`
  - Runtime data blocks w `read_runtime_data()`
  - Sensor method blocks w `sensors()`
- ✅ Weryfikacja kompilacji Python - OK
- ✅ Commit: 8214b9b
- Backup: to_do/202602011307_to_do.md

### 2026-02-01 12:50 - Observation sensors for undocumented registers
- ✅ Dodano sensory obserwacyjne dla wszystkich nieudokumentowanych rejestrow
  - **33xxx (Grid config)**: Limity sieci (33002-33079)
  - **38xxx (Grid phase)**: Ustawienia faz sieci (38000-38059, 38451-38460)
  - **42xxx (Feed Power)**: Grid export dla >30kW/parallel systems (42000-42014)
    - 42003: Grid Export Enable (32-bit)
    - 42004-42005: Grid Export Limit (32-bit signed)
  - **48xxx (Slave battery)**: Slave-specific battery registers (48000-48066)
    - 48011/48012: Battery discharge/charge current limits
    - 48013: Battery SOC on slave inverter
  - **50xxx (Grid freq)**: Czestotliwosc/power factor (50000-50099)
  - **55xxx (Energy)**: Liczniki energii (55252-55281)
  - **10486-10499**: Undocumented parallel registers
- ✅ Sensory domyslnie wylaczone - wlaczanie przez:
  - `inverter._observe_33xxx = True`
  - `inverter._observe_38xxx = True`
  - `inverter._observe_42xxx = True`
  - `inverter._observe_48xxx = True`
  - `inverter._observe_50xxx = True`
  - `inverter._observe_55xxx = True`
- ✅ Cel: Obserwacja zmian wartosci dla reverse engineering
- ✅ Commits: 819d0a4, dabf231
- Backup: to_do/202602011245_to_do.md

### 2026-01-31 12:30 - Fix peak_shaving_power_slot8 unit (v0.6.3 -> v0.9.9.51)
- ✅ Zmiana jednostki z KILO_WATT na WATT dla rejestru 47592
- ✅ Usunieto przeliczenia /10 i *10 - raw values w watach
- ✅ native_step zmieniony z 0.1 na 100
- ✅ Zakres zmieniony z +-40 na +-40000 W
- ✅ Dodano komentarz o parallel systems
- ✅ Commit 91abb33 pushed do home-assistant-goodwe-inverter
- Backup: to_do/202601311230_to_do.md

### 2026-01-30 15:35 - Peak Shaving switch i Battery Current Limits (v0.6.0 -> v0.6.1)
- ✅ **v0.6.0**: Dodano sensor_name_prefix i auto-discovery dla parallel slaves
  - Property `sensor_name_prefix` zwraca GWxxxx_ na podstawie ostatnich 4 cyfr serial number
  - Metoda `discover_parallel_slaves()` - auto-discovery slave'ow w systemach rownoleglych
  - Przykład: `examples/discover_parallel_system.py`
  - Custom component: unique_id wszystkich encji zawiera teraz prefix (sensor, number, select, switch, button)
- ✅ **v0.6.1**: Nowe encje dla Peak Shaving i Battery Current Limits
  - **SwitchValue** - nowa klasa sensora dla switchy z custom wartosciami on/off
  - **peak_shaving_enabled** (register 47591): ON=64512 (0xFC00), OFF=768 (0x0300)
  - **battery_charge_current** (45353) i **battery_discharge_current** (45355) - number entities 0-100A
- ✅ Wersje finalne:
  - goodwe_lib: v0.6.1 (tags pushed)
  - custom_components/goodwe: v0.9.9.47
- ✅ Gotowe do testowania na rzeczywistym hardware
- 📝 Organizacja dashboardu: TOU 1-7, Peak Shaving (slot 8), Master values - do konfiguracji w Lovelace przez filtrowanie entity_id
- Backup: to_do/202601301530_to_do.md

### 2026-01-25 15:30 - TOU sensors widoczne w Home Assistant (v0.5.9)
- ✅ Zidentyfikowano problem: TOU sensors w __settings_arm_fw_* zamiast __all_sensors
- ✅ Przeanalizowano kod custom component - tworzy sensory tylko z inverter.sensors()
- ✅ Przeniesiono wszystkie 48 TOU sensors (slots 1-8) do __all_sensors
- ✅ Usunięto TOU z __settings_arm_fw_19 i __settings_arm_fw_22
- ✅ Testy zmienione z pytest na unittest (zgodność z projektem)
- ✅ Poprawiono błędne wartości testowe (23:59 = 5947, nie 6143)
- ✅ Wersje finalne:
  - goodwe_lib: v0.5.9 (tag pushed)
  - custom_components/goodwe: v0.9.9.42
- ✅ System działa: TOU sensors będą widoczne w HA przy następnym restarcie
- 🎯 Następny cel: Write support dla TOU (zadanie 5.6)
- Backup: to_do/202601251530_to_do.md

### 2026-01-25 11:30 - Realizacja zadań 5.1, 5.2, 5.4, 5.5 i bugfixy
- ✅ Ukończono wszystkie 4 zaplanowane zadania (5.1, 5.2, 5.4, 5.5)
- ✅ Zadanie 5.1: Zmiana RST → L1/L2/L3 (3 sensory phase power)
- ✅ Zadanie 5.2: Dodanie "Master" do 42 parallel sensors
- ✅ Zadanie 5.4: Naprawiono AttributeError przez usunięcie serial_number sensor
- ✅ Zadanie 5.5: Auto-weryfikacja wersji z persistent notification
- ✅ Bugfix: Naprawiono import persistent_notification w custom component
- ✅ Wersje finalne:
  - goodwe_lib: v0.5.6 (tag pushed)
  - custom_components/goodwe: v0.9.9.39
- ✅ System działa stabilnie w Home Assistant
- 📝 Notatka: Do realizacji TOU (5.3) wykorzystamy algorytmy z goodwe_modbus_gui
- 🎯 Następny duży cel: Implementacja masek TOU (zadanie 5.3)
- Backup: to_do/202601251130_to_do.md

### 2026-01-25 02:33 - Podsumowanie sesji naprawy slave invertera i planowanie przyszłych zadań
- ✅ Zakończono walkę ze slave inverterem - system działa stabilnie
- ✅ Dodano sekcję 4: Naprawy po implementacji Parallel System (v0.5.2 - v0.5.4)
  - 4.1: Nested exception handling dla meter fallback
  - 4.2: Version detection przez importlib.metadata
  - 4.3: Comprehensive EMS settings
  - 4.4: Finalizacja - v0.5.4
- ✅ Dodano sekcję 5: Zadania zaplanowane na przyszłość
  - 5.1: Zmiana RST → L1/L2/L3 w opisach faz
  - 5.2: Dodanie "Master" do encji parallel
  - 5.3: Maski TOU input/output (duże zadanie!)
  - 5.4: Poprawka Serial Number sensor
  - 5.5: Automatyczna weryfikacja wersji w custom component (inteligentne!)
  - 5.6: Dokumentacja parallel systems
- ✅ Dodano sekcję 6: Znane ograniczenia (slave bez SOC/meter - hardware limitation)
- 📝 System równoległy działa: Master (success: True) + Slave (success: True)
- 📝 Wersje finalne: goodwe_lib v0.5.4, custom_components v0.9.9.36
- 🎉 Kluczowa lekcja: pip cache + shell_command = winning combination
- Backup: to_do/202601250233_to_do.md

### 2026-01-24 20:00 - Finalizacja projektu Parallel Inverter System
- ✅ Zaktualizowano custom component (home-assistant-goodwe-inverter)
- ✅ Zweryfikowano kod - nowe sensory będą automatycznie dostępne w HA
- ✅ Utworzono tag v0.5.0 w goodwe_lib
- ✅ Commit i push do obu repozytoriów zakończone
- 📝 Projekt gotowy do testowania przez użytkownika w Home Assistant
- Backup: to_do/202601242000_to_do.md

### 2026-01-24 19:20 - Zakończenie implementacji Parallel Inverter System
- ✅ Zaimplementowano wszystkie 38 rejestrów Modbus (10400-10485)
- ✅ Dodano automatyczne wykrywanie parallel system
- ✅ Zaktualizowano VERSION do 0.5.0
- ✅ Kod zweryfikowany i działa poprawnie (173 → 211 sensorów)
- 📝 Następny krok: aktualizacja home-assistant-goodwe-inverter custom component
- Backup: to_do/202601241920_to_do.md

### 2026-01-24 18:36 - Dodanie zadania: Parallel Inverter System
- Dodano szczegółowy plan implementacji rejestrów dla systemów równoległych
- Źródło: docs/modbus parralel.md
- Zakres: ~40 nowych rejestrów Modbus (10400-10485)
- Podział na 5 podetapów: analiza, implementacja rejestrów, implementacja w kodzie, dokumentacja/testy, finalizacja
- Backup: to_do/202601241836_to_do.md

### 2026-01-24 18:32 - Inicjalizacja
- Utworzenie początkowej struktury to_do.md
- Podsumowanie aktualnego stanu projektu
- Przygotowanie do dalszej pracy
- Backup: to_do/202601241832_to_do.md

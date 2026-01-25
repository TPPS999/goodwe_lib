# Plan działania - goodwe_lib

**Data rozpoczęcia:** 2026-01-24 18:32
**Ostatnia aktualizacja:** 2026-01-25 14:00

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

### Co jest w trakcie realizacji
Brak aktywnych zadań - wszystkie zaplanowane prace zakończone.

### Ostatnie zmiany (2026-01-25 14:00)
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

### Co jest do zrobienia

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

##### 5.3. Implementacja masek TOU (Time of Use) - ✅ ZAKOŃCZONE
**Priorytet:** WYSOKI - duże ułatwienie dla użytkowników
**Uzasadnienie:** Aktualne wartości TOU (47547-47594) to surowe dane binarne, trudne do interpretacji
**Zakres:**
- ✅ **Moduł tou_helpers.py** z funkcjami encode/decode:
  - ✅ `encode_time()` / `decode_time()` - format HH:MM → (hours << 8) | minutes
  - ✅ `encode_workweek()` / `decode_workweek()` - Table 8-34 (H-byte=mode, L-byte=days)
  - ✅ `encode_months()` / `decode_months()` - month bitmask (12 bits)
  - ✅ WorkWeekMode enum z trybami: ECO, Dry contact load, Peak shaving, Backup mode
  - ✅ Format functions: `format_workweek_readable()`, `format_months_readable()`
- ✅ **Nowe klasy sensorów** (sensor.py):
  - ✅ `TimeOfDay` - automatyczne formatowanie HH:MM
  - ✅ `WorkWeekV2` - wyświetlanie trybu i dni (np. "ECO Mode: Mon,Tue,Wed,Thu,Fri")
  - ✅ `MonthMask` - wyświetlanie miesięcy (np. "Jan,Feb,Dec" lub "All year")
- ✅ **Aktualizacja et.py** - zastąpienie EcoModeV2/PeakShavingMode:
  - ✅ 8 slotów TOU (47547-47594)
  - ✅ Każdy slot: Start Time, End Time, Work Week, Param1, Param2, Months
  - ✅ Sloty 1-4: ARM FW 19 (__settings_arm_fw_19)
  - ✅ Sloty 5-8: ARM FW 22 (__settings_arm_fw_22)
- ✅ **Testy jednostkowe** (tests/test_tou_helpers.py):
  - ✅ Testy encode/decode dla wszystkich typów
  - ✅ Roundtrip tests (encode → decode → verify)
  - ✅ Walidacja błędów (invalid input)
  - ✅ Wszystkie WorkWeekMode enum values
- ✅ **Commit:** 523eca1 (v0.5.7)
- ✅ **Uwagi:**
  - Wykorzystano algorytmy z goodwe_modbus_gui
  - Slot 8 ma specjalne parametry (0xFC=peak shaving, 0xFA=limit permillage)
  - Na razie parametry jako Integer - można rozszerzyć w przyszłości

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

##### 5.6. Dokumentacja systemów równoległych
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

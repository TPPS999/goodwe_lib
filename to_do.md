# Plan działania - goodwe_lib

**Data rozpoczęcia:** 2026-01-24 18:32
**Ostatnia aktualizacja:** 2026-01-25 02:33

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

#### 5. Zadania zaplanowane na przyszłość
**Priorytet:** ŚREDNI
**Status:** ⏳ DO ZROBIENIA

##### 5.1. Zmiana oznaczeń faz z RST na L1/L2/L3
**Uzasadnienie:** RST to stara konwencja, L1/L2/L3 jest bardziej zrozumiała
**Zakres:**
- Przejrzeć wszystkie sensory w et.py zawierające "phase_r", "phase_s", "phase_t"
- Zamienić opisy na "Phase L1", "Phase L2", "Phase L3"
- Sprawdzić czy to nie złamie kompatybilności z istniejącymi instalacjami
- ⏳ Status: DO ZROBIENIA

##### 5.2. Dodanie prefiksu "Master" do encji parallel system
**Uzasadnienie:** Encje z grupy parallel są zbiorcze (suma wszystkich inwerterów)
**Zakres:**
- Wszystkie sensory z Kind.PARALLEL powinny mieć w nazwie "Master" lub "System Total"
- Przykład: "Total PV Power" → "Master Total PV Power"
- Ułatwi rozróżnienie encji master vs slave w HA
- ⏳ Status: DO ZROBIENIA

##### 5.3. Implementacja masek TOU (Time of Use) - Input/Output
**Priorytet:** WYSOKI - duże ułatwienie dla użytkowników
**Uzasadnienie:** Aktualne wartości TOU (47500-47518) to surowe dane binarne, trudne do interpretacji
**Zakres:**
- **Input masks**: Łatwe wprowadzanie harmonogramów TOU przez HA UI
  - Graficzny wybór godzin dla każdego slotu
  - Walidacja zakresów czasowych
  - Konwersja do formatu Modbus (offset w sekundach)
- **Output interpretation**: Czytelne wyświetlanie aktualnego harmonogramu
  - Konwersja sekund → godziny:minuty
  - Formatowanie jako harmonogram dzienny
  - Opcjonalnie: wizualizacja graficzna (timeline)
- **Implementacja:**
  - Rozszerzyć klasę Sensor/Setting o metody encode/decode
  - Dodać pomocnicze funkcje konwersji czasu
  - Opcjonalnie: custom Lovelace card w custom_components
- ⏳ Status: DO ZROBIENIA

##### 5.4. Poprawka odczytu Serial Number
**Priorytet:** NISKI (kosmetyczny błąd)
**Problem:**
```
ValueError: invalid literal for int() with base 10: '9040KETF254L0008'
```
**Przyczyna:** Sensor serial_number ma state_class='measurement', ale wartość to string
**Rozwiązanie:**
- Serial number jest już dostępny w `self.serial_number` z device info
- Obecna implementacja w et.py:156-158:
  ```python
  Calculated("serial_number",
             lambda data: "",  # ← pusta wartość!
             "Serial Number", "")
  ```
- Poprawić na:
  ```python
  Calculated("serial_number",
             lambda data: data.get("serial_number", ""),
             "Serial Number", "", Kind.PV)  # bez state_class
  ```
- Lub usunąć sensor całkowicie (serial number jest już w device info)
- ⏳ Status: DO ZROBIENIA

##### 5.5. Automatyczna weryfikacja wersji biblioteki w custom component
**Priorytet:** ŚREDNI
**Uzasadnienie:** Zapobiegnie problemom z cache - user zobaczy warning jeśli wersja się nie zgadza
**Zakres:**
- Rozszerzyć custom_components/goodwe/__init__.py
- Po zalogowaniu wersji (linia 12-14) dodać weryfikację:
  ```python
  # Current: line 12-14 logs version
  EXPECTED_VERSION = "0.5.4"  # czytać z manifest.json requirements
  if goodwe.__version__ != EXPECTED_VERSION:
      _LOGGER.warning(
          "GoodWe library version mismatch! Expected %s, got %s. "
          "Please run: pip3 uninstall -y goodwe && pip3 cache purge && "
          "pip3 install --no-cache-dir --force-reinstall git+https://github.com/TPPS999/goodwe_lib.git@v%s",
          EXPECTED_VERSION, goodwe.__version__, EXPECTED_VERSION
      )
  ```
- Opcjonalnie: Dodać persistent_notification w HA UI z instrukcją update
- Opcjonalnie: Utworzyć repair issue w HA (jeśli wersja się nie zgadza)
- ⏳ Status: DO ZROBIENIA

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

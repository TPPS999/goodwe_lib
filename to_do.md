# Plan działania - goodwe_lib

**Data rozpoczęcia:** 2026-01-24 18:32
**Ostatnia aktualizacja:** 2026-10-06 23:21

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
🎯 **v0.6.9 / v0.9.9.61 - Observation sensors z pełną persystencją** ✅ ZAKOŃCZONE
- ✅ System parallel działa poprawnie
- ✅ TypeError naprawiony
- ✅ **Observation sensors switche z persystencją** (33xxx, 38xxx, 48xxx, 55xxx)
  - ✅ Switche zapisują swój stan do ConfigEntry.options
  - ✅ Po restarcie HA inverter przywraca flagi _observe_*xxx z zapisanych opcji
  - ✅ Sensory pojawiają się po restarcie jeśli switche były włączone
  - ✅ **Auto-disable logic usunięta** - błędy Modbus nie nadpisują zapisanego stanu
  - ⚠️ **Wymaga restartu HA** po włączeniu/wyłączeniu switcha (to jest OK)

### Ostatnie zmiany (2026-02-20 00:57)
- ✅ **v0.9.9.78** - REFACTOR: Modułowa architektura price plans (BREAKING CHANGE)
  - **Motywacja:** User feedback - "integracja sie rozrasta, moze lepiej zrobic maske wprowadzania decyzji cenowej z innych integracji"
  - **Problem:** goodwe integration mieszała Modbus communication + price logic (PSE API, entity extraction, scheduling)
  - **Rozwiązanie:** Clean separation of concerns - każda integracja robi JEDNĄ rzecz

  - **USUNIĘTO** (~280 linii):
    - PSE API integration (_fetch_pse_prices, constants)
    - Entity price extraction (_extract_prices)
    - configure_neg_price_plan service
    - update_neg_price_plans service
    - Auto-update scheduling dla PSE
    - source_type logic (entity/rce_warsaw)
    - Cache w runtime_data

  - **ZOSTAŁO** (~300 linii):
    - build_mask() helper function (może być skopiowane przez external integrations)
    - set_neg_price_plan service (low-level: przyjmuje maski lub prices+threshold)
    - _midnight_rollover() - uproszczona wersja czytająca sensory
    - encode_rtc_date() helper
    - neg_price_enable switch

  - **DODANO:**
    - 4 sensory pokazujące aktualne maski (JSON arrays):
      * sensor.goodwe_neg_price_sell_today_mask
      * sensor.goodwe_neg_price_sell_tomorrow_mask
      * sensor.goodwe_neg_price_buy_today_mask
      * sensor.goodwe_neg_price_buy_tomorrow_mask
    - NegPriceMaskSensor class w sensor.py (czyta 6 rejestrów → JSON)
    - PRICE_OPTIMIZER_GUIDE.md - pełny guide dla external integrations (+550 linii)

  - **Nowa architektura:**
    - **GoodWe integration**: Modbus communication + low-level service + midnight rollover
    - **Price Optimizer integration** (external, przyszła): price logic + scheduling + wywołuje goodwe service
    - Przykłady: pse_price_optimizer, nordpool_price_optimizer, ml_price_optimizer

  - **Midnight rollover (zmienione):**
    - Nie czyta z cache (cache removed)
    - Czyta sensory tomorrow_mask (JSON parse)
    - Zapisuje jako today_mask (Modbus write)
    - Clearuje tomorrow_mask → [0,0,0,0,0,0]

  - **Pliki zmienione:**
    - price_plan.py: -280 +65 = -215 net lines
    - sensor.py: +60 lines (4 mask sensors)
    - const.py: -2 lines (removed unused service constants)
    - services.yaml: -135 lines (removed configure/update definitions)
    - manifest.json: v0.9.9.77 → v0.9.9.78
    - PRICE_OPTIMIZER_GUIDE.md: NEW +550 lines

  - **Commit:** 21c78e1
  - **Breaking change:** configure_neg_price_plan i update_neg_price_plans usunięte
  - **Migration:** Użytkownicy PSE API muszą poczekać na external pse_price_optimizer integration
  - **Korzyści:** Scalable, maintainable, clean separation, łatwo dodać nowe źródła cen

### Poprzednie zmiany (2026-02-20 00:39)
- ✅ **v0.9.9.77** - Midnight rollover dla price plans
  - **Problem:** O północy "jutro" staje się "dzisiaj", ale rejestry się nie przesuwają automatycznie
  - **User feedback:** "o polnocy musimy przepisac je na dzis, bo to sie robi nasze jutro"
  - **Rozwiązanie:**
    - Dodano `_midnight_rollover()` handler (trigger 00:00:30 daily)
    - Cache prices w runtime_data: `last_price_today`, `last_price_tomorrow`
    - O północy: cached yesterday's tomorrow → build today masks → write to inverter
    - Tomorrow zostaje puste do 14:30 (PSE auto-update)
  - **Przepływ dzienny:**
    1. 00:00:30 - Midnight rollover (yesterday's tomorrow → today)
    2. 14:30+ - PSE auto-update (fetch today + tomorrow, cache both)
    3. Retry co 30 min do 23:30 jeśli tomorrow brak
  - **Zmiany w price_plan.py:**
    - New: `_midnight_rollover()` - async handler
    - Updated: `_update_from_config()` - dodano `runtime_data` param + caching
    - Updated: `_setup_auto_update_schedule()` - dodano midnight trigger
    - Updated: wszystkie wywołania _update_from_config() przekazują runtime_data
  - **Commit:** 4c9f2e3
  - **Działa dla:** RCE Warsaw i Entity source types
  - **Uwaga:** Separate buy/sell thresholds już były od v0.9.9.76 (user miał wątpliwości, ale to już działało)

### Poprzednie zmiany (2026-01-31 12:30)
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

### Audyt prac (2026-10-06 23:21)

**Było:** to_do.md zatrzymane na 2026-02-20 (v0.6.x / komponent 0.9.9.78).
**Jest:** lib v0.8.7 (e645e5b, 2026-04-01), komponent v0.9.9.87 (145b34d). Oba repo == origin.
**Uzupełnienie brakującej historii (z git log):**
- ✅ v0.7.0 - usunięte observation sensors (0f53a4f) - sekcja 0 poniżej jest historyczna
- ✅ v0.7.1-0.7.2 - poprawione rejestry 32-bit power, reactive energy
- ✅ v0.7.3 - rejestry FW 2025, v0.7.4 - negative price plan, v0.7.5 - filtr reactive + fix peak shaving switch
- ✅ v0.7.6 - nie usuwamy settings przy przejściowych błędach odczytu
- ✅ v0.8.0-0.8.7 - ładowarka HCA (EV charger): G2 rejestry, FaultBitmaskSensor, PackedTimeSensor, hca_clock sync
- ✅ komponent 0.9.9.79-0.9.9.87 - limity baterii 200A, encje HCA, tłumaczenia, clock sync

**Ustalenia audytu (do zrobienia):**
- ⏳ A1. Na HA Radzyny działa komponent 567e72a (0.9.9.80 / lib v0.7.6) - HCA i v0.8.x niewdrożone (decyzja usera)
- ⏳ A2. Testy: 8 FAIL w test_et.py - tylko nieaktualne liczniki sensorów (np. 168 != 201); brak testów HCA
- ⏳ A3. Tag v0.8.0 ma VERSION=0.7.6 (od v0.8.1 zgodne) - nie używać @v0.8.0
- ⏳ A4. 5 nieśledzonych extract_regs*.py w root (2026-02-19) - przenieść do docs/scripts albo usunąć
- ⏳ A5. Komponent __init__.py: `_version_mismatch` niezdefiniowane gdy requirement bez `@vX.Y.Z` -> NameError (naprawić w Z-002)
- ⏳ A6. Sekcje X i 5.6 wiszą jako "W TRAKCIE" od lutego - zweryfikować czy aktualne
- ℹ️ A7. to_do.md w .gitignore jako "local only", ale śledzony i pushowany na GitHub

**Zalecenia z haos_radzyny (zalecenia.md):**
- ⏳ **Z-002** [goodwe fork][goodwe_lib] - wersja komponentu + lib + commit/data w API - status `nowe`
  - lib: `__version__` (importlib.metadata + setup.cfg `version: file: VERSION`) działa - bez zmian
  - fork: `sensor.goodwe_integration_version` (diagnostic, 1 na instancję) + atrybuty lib_version/lib_expected/lib_match
  - fork: GitHub release przy każdym podbiciu manifestu -> HACS pokaże vX.Y.Z zamiast hasha
- Context: context_record/202610062321_context.md

### Bieżące działania (2026-02-19)

🎯 **Fix: Numbers TOU nie aktualizują wartości + skalowanie peak shaving power** 🚧 W TRAKCIE

**Problem 1: Numbers nie odświeżają wartości z falownika**
- Numbers wysyłają wartości poprawnie (write działa)
- Ale nie odczytują aktualnej wartości z falownika (brak read-back)
- Pokazują wartość którą użytkownik wpisał, nie rzeczywistą z falownika
- Cel: każdy Number powinien po zapisie i periodycznie odczytywać swój rejestr

**Problem 2: Peak Shaving Power - błędne skalowanie**
- Falownik przechowuje w jednostkach 10W (3800 = 38000W = 38kW)
- Trzeba dostosować skalowanie w number entity

**Plan:**
1. Zbadać number.py i switch.py - jak działa periodic read / response
2. Sprawdzić czy Numbers mają async_update / coordinator refresh
3. Naprawić skalowanie peak_shaving_power

---

### Poprzednie działania (2026-02-03)
🎯 **Reverse engineering rejestrów Modbus dla ustawień master i slave** - ZAWIESZONE

**Cel:** Znalezienie rejestrów Modbus odpowiadających za ustawienia invertera dla master i slave

**Metoda:**
- Porównanie scan logów przed i po zmianach ustawień
- Analiza delt z multiplikatorami (x1, x10, x100, x1000)
- Sprawdzanie wartości odwróconych (100-value encoding)
- Wykluczenie pomiarów (47443, 47447, 47451)

**Porównywane skany:**
- Master OLD: scan_log_20260202_131128.txt (13:11) - 5217 rejestrów
- Master NEW: scan_log_20260203_083328.txt (08:33) - 5219 rejestrów
- Slave OLD: scan_log_20260202_160831.txt (16:08) - 579 rejestrów
- Slave NEW: scan_log_20260202_190411.txt (19:04) - 579 rejestrów

**Status MASTER (5 z 6 znalezionych):**
- ✅ Peak Shaving SOC: **47593** (87 → 88, bezpośrednia %)
- ✅ On Grid DOD: **45356** (34 → 32, encoding: 100-value, 66%→68%)
- ✅ Charging Current: **45353** (490 → 480, encoding: value × 0.1A, 49.0A→48.0A)
- ✅ Discharging Current: **45355** (520 → 510, encoding: value × 0.1A, 52.0A→51.0A)
- ✅ SOC Upper Limit: **47760** (90 → 91, bezpośrednia %)
- ❌ Peak Shaving Power: NIE ZNALEZIONY (delta +5.9kW)

**Status SLAVE (kandydaci do weryfikacji):**
- 🟡 Peak Shaving SOC: **48200** lub **48271** (oba +2, wymaga weryfikacji)
- 🟡 On Grid DOD: **10435**, **10478**, lub **48199** (wszystkie -1, niejasne kodowanie)
- 🟡 Charging Current: **45229** (1933 → 1953, +20, niejasne kodowanie)
- 🟡 Discharging Current: **20009**, **10411**, lub **10472** (niejasne kodowanie)
- 🟡 SOC Upper Limit: **48269** (23 → 28, +5, niejasne kodowanie)
- ❌ Peak Shaving Power: NIE ZNALEZIONY (delta +4.9kW)

**Kluczowe odkrycia:**
1. Potwierdzono: ustawienia slave są przechowywane w pamięci mastera (slave ma tylko 0xxx i 55xxx)
2. Rejestry slave prawdopodobnie w zakresach: 10xxx (parallel system) i 48xxx (slave battery)
3. Master używa różnych enkodingów: bezpośrednie wartości, 0.1A multiplier, 100-value inversion
4. Slave prawdopodobnie używa offsetów lub kombinowanych wartości

**Pliki wygenerowane:**
- docs/scripts/FOUND_REGISTERS_SUMMARY.md - szczegółowe podsumowanie wszystkich znalezisk
- docs/scripts/search_slave_settings.py - skrypt wyszukiwania rejestrów slave
- docs/scripts/compare_master_slave_deltas.py - porównanie delt master vs slave

**Następne kroki:**
1. Weryfikacja kandydatów slave przez małe testowe zmiany i reskan
2. Znalezienie Peak Shaving Power dla master i slave
3. Dekodowanie enkodingu absolutnych wartości dla rejestrów slave
4. Testy zapisu do znalezionych rejestrów

---

### Co jest do zrobienia

#### X. Fix Numbers TOU + peak shaving scaling 🚧 W TRAKCIE
- 🚧 Analiza number.py i switch.py
- 🚧 Fix: Numbers nie aktualizują wartości z falownika (brak read-back)
- 🚧 Fix: peak_shaving_power skalowanie (x10, jednostki 10W)
- Context: 202602191909_context.md

#### 0. Dopracowanie observation sensors - **ZAKOŃCZONE** ✅
**Status:** ✅ ZAKOŃCZONE
**Problem:** Observation sensors (33xxx, 38xxx, 48xxx, 55xxx) wymagają persystencji stanu
- ✅ Sensory są zdefiniowane w et.py
- ✅ Flagi `_observe_*` są zainicjalizowane na False
- ✅ **Implementacja switchy z persystencją stanu (v0.9.9.58):**
  - ✅ 4 switche w custom component do włączania/wyłączania observation sensors
  - ✅ Switche zapisują swój stan do ConfigEntry.options
  - ✅ Po restarcie HA inverter przywraca flagi z zapisanych opcji
  - ✅ Sensory pojawiają się po restarcie jeśli switche były włączone
  - ℹ️ Wymaga restartu HA po zmianie stanu switcha (to jest OK - standardowe dla HA)
- **Rezultat:** User może włączyć observation sensors, zrestartować HA i sensory się pojawią

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

### 2026-10-06 23:21 - Audyt prac + przegląd zalecenia.md (haos_radzyny)
- ✅ Uzupełniona historia v0.7.0-v0.8.7 / komponent 0.9.9.79-0.9.9.87 (z git log)
- ✅ Ustalenia audytu A1-A7 (sekcja "Audyt prac")
- ✅ Przegląd zalecenia.md: dla nas tylko Z-002 (status `nowe`), reszta to battery_balancer
- Backup: to_do/202610062321_to_do.md

### 2026-02-03 11:39 - Reverse engineering: Znalezienie rejestrów Modbus dla master i slave
- 🚧 **W TRAKCIE:** Analiza scan logów w celu znalezienia rejestrów odpowiadających za ustawienia
- ✅ **Metoda:**
  - Porównanie 4 scan logów (2 master, 2 slave) przed i po zmianach ustawień
  - Analiza delt z multiplikatorami (x1, x10, x100, x1000)
  - Sprawdzanie wartości odwróconych (100-value encoding)
  - Wykluczenie rejestrów pomiarowych (47443, 47447, 47451)
- ✅ **Master: Znaleziono 5 z 6 rejestrów:**
  - 47593: Peak Shaving SOC (87 → 88)
  - 45356: On Grid DOD (34 → 32, inverted: 66% → 68%)
  - 45353: Charging Current (490 → 480, 0.1A: 49.0A → 48.0A)
  - 45355: Discharging Current (520 → 510, 0.1A: 52.0A → 51.0A)
  - 47760: SOC Upper Limit (90 → 91)
  - ❌ Peak Shaving Power: nie znaleziony
- 🟡 **Slave: Znaleziono kandydatów do weryfikacji:**
  - Peak Shaving SOC: 48200 lub 48271 (oba +2)
  - On Grid DOD: 10435, 10478, lub 48199 (wszystkie -1)
  - Charging Current: 45229 (1933 → 1953, +20)
  - Discharging Current: 20009, 10411, lub 10472
  - SOC Upper Limit: 48269 (23 → 28, +5)
  - ❌ Peak Shaving Power: nie znaleziony
- 📝 **Kluczowe odkrycia:**
  - Potwierdzono: ustawienia slave w pamięci mastera (zakresy 10xxx, 48xxx)
  - Slave prawdopodobnie używa offsetów lub kombinowanych wartości
  - Wymaga weryfikacji przez testowe zmiany i reskan
- 📄 **Dokumentacja:** docs/scripts/FOUND_REGISTERS_SUMMARY.md
- Backup: to_do/202602031139_to_do.md

### 2026-02-02 14:15 - Fix: Remove auto-disable logic (v0.6.9 / v0.9.9.61)
- ✅ **Problem:** Observation switches nadal traciły stan po niektórych błędach
  - Auto-disable logic w et.py nadpisywała zapisane opcje ConfigEntry.options
  - Przy błędzie ILLEGAL_DATA_ADDRESS kod ustawiał `self._observe_*xxx = False`
  - To nadpisywało preferencje użytkownika zapisane w ConfigEntry.options
- ✅ **Rozwiązanie:** Usunięcie auto-disable logic ze wszystkich observation ranges
  - **et.py (v0.6.9):**
    - Usunięto linię `self._observe_48xxx = False` z exception handlera
    - Usunięto linię `self._observe_33xxx = False` z exception handlera
    - Usunięto linię `self._observe_38xxx = False` z exception handlera
    - Usunięto linię `self._observe_55xxx = False` z exception handlera
    - Zmieniono logi z INFO na DEBUG poziom
    - Dodano informację "will retry on next update" zamiast "disabling"
  - **manifest.json (v0.9.9.61):**
    - Aktualizacja wymagań: goodwe @ ...@v0.6.8 → v0.6.9
- ✅ **Rezultat:** Observation switches teraz w pełni persistentne
  - User preferences w ConfigEntry.options są zachowywane
  - Błędy Modbus nie nadpisują zapisanego stanu
  - Switch pozostaje włączony nawet przy błędach odczytu
- ✅ Wersje:
  - goodwe_lib: v0.6.9 (tag pushed)
  - custom_components/goodwe: v0.9.9.61
- ✅ Commit: 3f19fa7, acc7a5a
- Backup: to_do/202602021415_to_do.md

### 2026-02-01 14:15 - Fix: Persistent state for observation switches (v0.9.9.58)
- ✅ **Problem:** Switche observation sensors traciły swój stan po restarcie HA
  - Flagi `_observe_*xxx` w inverterze były inicjalizowane jako False przy każdym starcie
  - User włączał switch, ale po restarcie HA wracał do stanu wyłączonego
- ✅ **Rozwiązanie:** Persystencja stanu przez ConfigEntry.options
  - **switch.py:**
    - async_turn_on/off zapisuje stan do `entry.options[OBSERVATION_*XXX]`
    - Dodano `config_entry` parameter do ObservationSwitchEntity.__init__
    - Informacja w logu że wymaga restartu HA
  - **__init__.py:**
    - Po utworzeniu invertera odczytuje opcje i ustawia flagi:
      ```python
      inverter._observe_33xxx = entry.options.get(OBSERVATION_33XXX, False)
      inverter._observe_38xxx = entry.options.get(OBSERVATION_38XXX, False)
      inverter._observe_48xxx = entry.options.get(OBSERVATION_48XXX, False)
      inverter._observe_55xxx = entry.options.get(OBSERVATION_55XXX, False)
      ```
- ✅ **Rezultat:** Switche zachowują stan po restarcie HA
  - User może włączyć switche, zrestartować HA i observation sensors się pojawią
  - Po wyłączeniu i restarcie sensory znikną
- ✅ Wersja: custom_components/goodwe v0.9.9.58
- Backup: to_do/202602011415_to_do.md

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

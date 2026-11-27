# Misja Programista

**Autor:** Bartosz Szerszon (2026)

**Przeznaczenie:** projekt przygotowany na prezentację dla klasy 1D Szkoły Podstawowej nr 84.

## Wymagania

Python 3.10 lub nowszy z dostępnym Tkinterem. Uruchom polecenia z katalogu
projektu. Gra korzysta ze standardowej biblioteki Pythona i nie wymaga
instalowania pakietów zewnętrznych.

### Na iPhonie bez TestFlight

[Otwórz Misja Programista](https://ba-sz.github.io/mr_robot/) w Safari, stuknij
**Udostępnij → Dodaj do ekranu początkowego** i uruchamiaj ją jak aplikację.
Nie potrzeba Apple ID, TestFlight ani instalacji z App Store. Gra robota działa
offline po pierwszym otwarciu; projekty Scratch w playerze wymagają internetu.

### Gotowa paczka dla macOS

[Pobierz aplikację macOS Intel](https://github.com/ba-sz/mr_robot/releases/download/v1.0.0/Misja-Programista-macOS-x86_64.zip).
Paczka nie wymaga instalacji Pythona. Została przetestowana na macOS 12.7.6
z procesorem Intel; na Apple Silicon wymaga Rosetta 2. Przy pierwszym
uruchomieniu macOS może poprosić o potwierdzenie otwarcia aplikacji pobranej
z internetu — instrukcja znajduje się w archiwum.

## Gra w Pythonie

```bash
python robot_game.py --fullscreen
```

Większy labirynt i dłuższy program:

```bash
python robot_game.py --turbo --fullscreen
```

Dzieci mogą dyktować strzałki lub układać program z klawiatury:
**↑ ↓ ← →** dodają krok; **S** uruchamia program; **N** przechodzi do
następnej rundy po zwycięstwie; **U** cofa ostatnią strzałkę; **R** czyści
program; **T** włącza turbo, **L** ultra, a **P** wraca do trybu standardowego.
**E** uruchamia „Popraw strzałki” po nieudanej próbie.
Klawisze **F11** i **Esc** zmieniają tryb okna. Wszystkie te
czynności są też dostępne jako przyciski.

Zwykła rozgrywka ma też widoczny przycisk **„Turbo teraz (T)”**:
można natychmiast zacząć długi labirynt, bez zaliczania standardowych
rund. Dziecko może zamiast tego nacisnąć **T**. Przycisk zaczyna nową
przygodę turbo i zeruje bieżący wynik gry. Jeśli turbo ma uruchomić się
od razu przy starcie programu, użyj `--turbo`.

Jedna strzałka przesuwa robota o jedno pole w kierunku na ekranie. **START**
wykonuje program powoli, podświetlając aktualną instrukcję. Kamień lub brzeg
zatrzymuje robota i wskazuje błędny krok.
Skarb jest zdobyty, gdy robot stoi na nim **po ostatniej instrukcji**.
Każde uruchomienie programu w danej rundzie zaczyna się od jej pola START.

**Po zdobyciu skarbu odblokowuje się „Kolejna runda”.** Dopiero kliknięcie
tego przycisku losuje nową planszę i usuwa poprzedni program.

Wynik widać też **na dużej karcie na planszy**: po sukcesie gwiazdki
i przycisk „Kolejna runda (N)”; po błędzie wskazane miejsce zatrzymania
i akcja „Popraw strzałki”. Program pozostaje edytowalny.
„Popraw strzałki” od razu przenosi robota na START i usuwa ślad próby,
zachowując ułożone strzałki do poprawienia.
Znacznik START pozostaje na mapie, a legenda odróżnia drogę, ściany i skarb.
Skarb to otwarta skrzynia ze sztabkami złota i diamentem.
Powtórzenie programu w wygranej rundzie nie nalicza drugiego skarbu.
Nieudana próba nie zwiększa trudności i nie zabiera skarbów.
Licznik u góry pokazuje rundę, poziom i zdobyte skarby.

### Poziomy trybu Przygoda

| Poziom | Najkrótsza droga | Kamienie | Minimalna liczba zmian kierunku w wygenerowanym rozwiązaniu |
| --- | --- | --- | --- |
| 1 | 3 kroki | 0 | 1 |
| 2 | 4 kroki | 1 | 1 |
| 3 | 5 kroków | 2 | 2 |
| 4 | 6 kroków | 3 | 2 |
| 5 | 7 kroków | 4 | 3 |
| 6 | 8 kroków | 5 | 3 |

Wszystkie trzy tryby generują plansze z osiągalnym skarbem i rozwiązaniem
opartym na najkrótszej trasie. W trybie standardowym plansza ma 5 × 4 pola,
żeby były duże na projektorze. Po poziomie 6 można nadal zdobywać skarby na
nowych mapach, ale trudność pozostaje na poziomie maksymalnym. Gra nie ma
limitu rund, a wynik jest przechowywany tylko do zamknięcia okna.

„Cofnij strzałkę” usuwa ostatni krok, „Wyczyść program” usuwa wszystkie.
Podpowiedź pokazuje początek rozwiązania **aktualnej** planszy.
Zamknięcie okna kończy grę.
Opcja `--demo` układa poprawny program, ale nie uruchamia go automatycznie.
`--seed 42` pozwala odtworzyć tę samą sekwencję plansz przy tym samym trybie
i tej samej wersji generatora. Plansza i reguły gry znajdują się w
`robot_model.py`.

### Tryby turbo i ultra

Turbo jest otwartą planszą pośrednią z rozrzuconymi kamieniami.
Każda mapa oferuje co najmniej dwie różne najkrótsze trasy do skarbu,
a wszystkie wolne pola są połączone. Kamieni przybywa od 10 do 20
na poziomach 1–6; nie zamykają robota w jednym korytarzu.
Ultra to prawdziwy labirynt 21 × 17 ze ścianami i jedną najkrótszą trasą
do skarbu.
Na drodze od startu do skarbu są co najmniej trzy rozgałęzienia:
można wybrać kierunek, ale błędne odnogi prowadzą do ślepych zaułków.
Długość najkrótszej trasy rośnie mocniej niż w turbo.

| Tryb | Plansza | Najkrótsze trasy na poziomach 1–6 | Limit programu |
| --- | --- | --- | --- |
| Przygoda | 5 × 4 | 3, 4, 5, 6, 7, 8 | 12 |
| Turbo | 11 × 9 | 8, 10, 12, 14, 16, 18 | 24 |
| Ultra | 21 × 17 | 20, 25, 30, 35, 40, 45 | 48 |

```bash
python robot_game.py --turbo --fullscreen
python robot_game.py --ultra --fullscreen
```

Dwa przyciski trybów zawsze pokazują pozostałe tryby: w standardzie
**Turbo (T)** i **Ultra (L)**, w turbo **Standard (P)** i **Ultra (L)**,
a w ultra **Turbo (T)** i **Standard (P)**.
Przełączanie między turbo i ultra zaczyna nową kampanię od poziomu 1,
zeruje skarby i czyści program. Nie zmienia trybu podczas animacji;
ponowny wybór aktualnego trybu nie resetuje przygody.
Opcje `--turbo` i `--ultra` wzajemnie się wykluczają.

W standardzie i turbo robot omija kamienie na otwartej planszy.
Tylko w ultra porusza się po korytarzach między ścianami.
Trudność rośnie **po wygranej i wybraniu kolejnej rundy**; błędy jej nie
zwiększają. Po poziomie 6 losujemy nowe mapy o tej samej maksymalnej
długości trasy. Podpowiedź pokazuje pierwsze dwa kroki.
Robot wykonuje krok co 750 ms w standardzie, 500 ms w turbo i 250 ms w ultra,
żeby dłuższe programy nie trwały zbyt długo.

### Moduły gry

Punkt wejścia **`robot_game.py`** jest celowo krótki: odczytuje ustawienia,
wybiera tryb, uruchamia okno i zaczyna grę. Można pokazać klasie `main()`
bez czytania całego projektu.

| Plik | Za co odpowiada |
| --- | --- |
| `robot_game.py` | Plan: wybranie trybu i uruchomienie gry |
| `robot_controls.py` | Połączenie strzałek i klawiszy z poleceniami |
| `robot_window.py` | Okno, przyciski, rysowanie planszy i animowanie robota |
| `robot_model.py` | Zasady ruchu, losowanie dróg, poziomy i skarby |

## Sprawdzenie projektu

```bash
python -m unittest discover -s tests -v
```

Testy sprawdzają zasady ruchu, losowanie i powtarzalność plansz, postęp
kampanii, limity programu, skróty klawiaturowe oraz działanie interfejsu
w trybach standardowym, turbo i ultra. Testy interfejsu otwierają okna
Tkintera, dlatego wymagają sesji graficznej. GitHub Actions uruchamia je
na Ubuntu z wirtualnym ekranem.

## Projekty Scratch

Nie trzeba instalować Scratch Desktop. Darmowy edytor działa w przeglądarce i
wymaga połączenia z internetem. [Pobierz projekty, karty pracy i prezentację](https://github.com/ba-sz/mr_robot/releases/download/v1.1.0/Misja-Scratch-1.1.0.zip),
otwórz [edytor Scratch](https://scratch.mit.edu/projects/editor/), a następnie
wybierz **Plik → Wczytaj z komputera** i wskaż plik `.sb3`. Do wczytania i
uruchomienia projektu nie trzeba konta. Zmiany można zapisać przez
**Plik → Zapisz na swoim komputerze**; publikacja projektu na Scratch wymaga
konta.

Pliki są zapisane w formacie Scratch 3.0.

| Plik | Zawartość |
| --- | --- |
| [01_Urodzinowa_misja.sb3](Scratch_Urodzinowa_Misja/projekty/01_Urodzinowa_misja.sb3) | Główna gra urodzinowa: wybór ekipy, łapanie balonów, obrazkowy szyfr i własny finał. |
| [02_Zepsuty_balon.sb3](Scratch_Urodzinowa_Misja/projekty/02_Zepsuty_balon.sb3) | Wersja z celowym błędem w ruchu balonu do ćwiczenia diagnozowania i poprawiania kodu. |
| [03_Studio_przyjecia.sb3](Scratch_Urodzinowa_Misja/projekty/03_Studio_przyjecia.sb3) | Studio do dalszej zabawy: zmiana finałowego tańca i reguł gry. |
| [04_Slonce_start.sb3](Scratch_Urodzinowa_Misja/projekty/04_Slonce_start.sb3) | Projekt startowy do zbudowania animacji wschodu i zachodu Słońca. |
| [05_Slonce_gotowe.sb3](Scratch_Urodzinowa_Misja/projekty/05_Slonce_gotowe.sb3) | Gotowy przykład animacji Słońca do obejrzenia lub porównania z projektem startowym. |

Pierwsze trzy pliki dotyczą głównej tajnej misji urodzinowej; dwa ostatnie
stanowią osobny, opcjonalny warsztat „Misja Słońce”. Wersja `02_Zepsuty_balon`
jest celowo uszkodzona i służy do ćwiczenia naprawy, nie jako gotowa gra.

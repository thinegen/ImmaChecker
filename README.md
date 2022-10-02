# ImmaChecker
How to make Immatrikulationschecking easy!

## Die Basics

Um dieses Programm sinvoll auszuführen braucht es ein paar Basics.
Wir haben die Vergabe über eine AirTable gelöst (Hierfür ist das Script ausgelegt, Google-Forms funktionieren unter bestimmten Vorraussetzungen auch, macht euch das Leben aber etwas schwieriger)

## How-To
1. Erstellt euch einen kostenlosen AirTable-Account auf www.airtable.com
2. Erstellt euer Formular und baut ein Upload-Feld ein! (P.S. betont mehrfach, dass es nur originale PDF-Dateien sein sollen, das spart euch unfassbar viel Arbeit im Nachhinein!
3. Verteilt den Link und lasst eure Studis sich eintragen.
4. Nach Ablauf der Fristen ladet euch die AirTable als Tabelle (.csv) runter.
5. stellt sicher, dass ihr Python3 auf eurem PC installiert habt.
   - Falls ihr das nicht habt findet ihr eine gute Anleitung hier: 
     - Windows: https://docs.python-guide.org/starting/install3/win/
     - Apple: https://docs.python-guide.org/starting/install3/osx/
6. Install pip
   - Anleitung findet ihr in den oben genannten Anleitungen!
7. ladet euch die beiden Dateien (Imma_Checking.py & Setup.py) in einen neuen Ordner herunter!
8. öffnet eure Commandline und führt Setup.py aus
   - Windows: 
     - a) in der Suche (rechts vom Windows Buton in der Task-Leiste 'cmd' eingeben
     - b) zu eurem Ordner (dort wo ihr die csv-Tabelle gespeichert habt) navigieren. Beispiel: `cd c:\Users\chris\Medis\Tickets\2022\Runde1`
     - c) startet die Python-Datei: `python Setup.py`
     - d) Python installiert alle nötigen Packages für euch

    - Apple:
      - tba
9. Öffnet die Imma_Checking.py Datei in eurer Programmiersoftware der Wahl - oder auch einfach im Editor
   - Passt eure Parameter in der Datei an - haltet hier gerne nochmal Rücksprache mit mir!
10. Wenn alles eingestellt ist startet ihr das Programm mit folgendem Befehl: `python Imma_Checking.py`
11. Ihr erhaltet im besten Fall einen neuen Ordner mit den runtergeladenen PDF-Dateien und einen Output-Ordner. Hier findet ihr 2 Excel-Listen, eine mit den fehlerhaften-PDFs -> dei müsstet ihr noch per Hand checken und eine Liste mit allen Einträgen die die Prüfung erfolgreich bestanden haben. 
12. Je nach eurem Vorgehen müsst ihr jetzt nur noch die Tickets verteilen


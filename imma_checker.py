try:
    import config
    import fitz
    import pandas
    import os
    import requests
    import re
    from fuzzywuzzy import fuzz
except ImportError as e:
    print("[!] Pythonmodule konnten nicht importiert werden. Wurde 'pip install -r requirements.txt' ausgeführt?\n\tFehler: " + str(e))
    quit()

# Zuerst ändern wir den aktuellen Ausführungspfad in den Ordner,
# in dem die Python-Datei gespeichert ist. Das sollte zwar der Fall
# sein, aber besser Vorsicht als Nachsicht
main_abspath = os.path.abspath(__file__)
main_dir_name = os.path.dirname(main_abspath)
os.chdir(main_dir_name)

# Regex compilation. Das ist ein Fehler der früh abgefangen werden sollte.
try:
    namen_regex_compiled = re.compile(config.namen_regex)
except Exception as e:
    print("[!] in namen_regex stimmt etwas nicht:\n\t" + str(e))
    quit()

# Pfade überprüfen. Existiert das CSV?
# Existiert der Ordner in dem die Immatrikulationsbescheinigungen
# gespeichert werden?
if not os.path.isdir(config.imma_path):
    os.makedirs(config.imma_path)
    print(f"[i] Ordner {config.imma_path} erstellt.")

if not os.path.isdir(config.output_pfad):
    os.makedirs(config.output_pfad)
    print(f"[i] Ordner {config.output_pfad} erstellt.")

try:
    csv = pandas.read_csv(config.csv)
except Exception as e:
    print("[!] Beim Lesen der CSV-Datei ist ein Fehler aufgetreten:\n\t" + str(e))
    quit()

# Wir testen einmal ob sämtliche Spalten die wir brauchen vorhanden sind
try:
    csv[config.vorname_spalte]
    csv[config.nachname_spalte]
    csv[config.email_spalte]
    csv[config.imma_bescheinigung_spalte]
except Exception as e:
    print("[!] Eine Spalte in der Tabelle scheint in config.py falsch zu sein:\n\t" + str(e))
    quit()

# Das Feld für den PDF-Upload hat das Format "YYY-MM-DD <filename> (<downloadurl>)".
# Wir teilen das Feld in die einzelnen Bestandteile und
# schreiben die Daten in unser CSV
split = csv[config.imma_bescheinigung_spalte].str.split(
    config.uploaded_imma_regex, regex=True, expand=True)
csv["imma_upload_date"], csv["imma_filename"], csv["imma_download_url"] = split[1], split[2], split[3]

# Jetzt speichern wir alle Immas
downloaded_imma_paths = [None] * len(csv["imma_download_url"])
for index, download_url in enumerate(csv["imma_download_url"]):
    try:
        # Der Pfad, in dem die Imma gespeichert wird ist effektiv nur der angegebene Ordner und der Zeilenindex im CSV
        imma_file_path = config.imma_path + "/" + str(index) + ".pdf"

        # Alles runterladen
        r = requests.get(download_url)
        with open(imma_file_path, 'wb') as f:
            f.write(r.content)
            downloaded_imma_paths[index] = imma_file_path

    except Exception as e:
        # Bei Fehlern wird der Name und der Fehler noch einmal gesondert ausgegeben
        print(
            f"[!] Beim Herunterladen einer Immatrikulationsbescheinigung ist ein Fehler aufgetreten:\n\tName: {csv.iloc[index][config.vorname_spalte]} {csv.iloc[index][config.nachname_spalte]}\n\tURL: {download_url}\n" + str(e))

# Die Liste der runtergeladenen Immas wird gespeichert
csv["immatrikulations_pdf_location"] = downloaded_imma_paths

# Jetzt validieren wir alle PDFs
validierungsergebnisse = []
for csv_zeile in csv.iloc:
    ist_gueltig = True
    ablehnungsgrund = []

    name = f"{csv_zeile[config.vorname_spalte]} {csv_zeile[config.nachname_spalte]}"
    email = csv_zeile[config.email_spalte]
    pdf_location = csv_zeile["immatrikulations_pdf_location"]

    if pdf_location is None:
        # Wir haben kein PDF für diesen Eintrag
        ist_gueltig = False
        ablehnungsgrund.append("Das PDF konnte nicht heruntergeladen werden.")
        validierungsergebnisse.append((ist_gueltig, ablehnungsgrund, "", 0))
        continue

    # Wir öffnen das PDF und holen uns den Inhalt
    pdf_inhalt = []
    try:
        with fitz.open(pdf_location) as imma_pdf:
            for seite in imma_pdf:
                seiten_inhalt = seite.get_text().split("\n")
                pdf_inhalt.extend(seiten_inhalt)
    except Exception as e:
        print(
            f"[!] Beim Öffnen und Verarbeiten eines PDFs gab es einen Fehler:\n\tName: {name}\n\tDatei: {pdf_location}\n\t" + str(e))
        ist_gueltig = False
        ablehnungsgrund.append("Das PDF konnte nicht geöffnet werden")
        validierungsergebnisse.append((ist_gueltig, ablehnungsgrund, "", 0))
        continue

    # Jetzt überprüfen wir, ob alles im PDF steht:
    # Zuerst prüfen wir, ob das PDF Inhalt hat
    if len(pdf_inhalt) == 0:
        print(
            f"[!] Das PDF ist leer:\n\tName: {name}\n\tDatei: {pdf_location}\n\t" + str(e))

    # Danach das Semester
    if not any([string in config.semester for string in pdf_inhalt]):
        ist_gueltig = False
        ablehnungsgrund.append("Falsches Semester")

    # Den Studiengang
    if not any([string in config.studiengaenge for string in pdf_inhalt]):
        ist_gueltig = False
        ablehnungsgrund.append("Falscher Studiengang")

    # Den Namen
    namens_kandidaten = []
    for s in pdf_inhalt:
        match_result = namen_regex_compiled.match(s)
        if match_result is not None:
            namens_kandidaten.append(match_result.group(1))

    # Für den Namen berechnen wir die Levenstheindistanz, einen Wert zur Bestimmung des Abstandes
    # zweier Zeichenketten
    levenshtein_ratios = []
    for kandidat in namens_kandidaten:
        levenshtein_ratios.append((kandidat, fuzz.token_sort_ratio(name, kandidat)))
    if all([lr < config.levensthein_cutoff for (k, lr) in levenshtein_ratios]):
        ist_gueltig = False
        ablehnungsgrund.append("Name nicht gefunden")
    
    # bester Namenskandidat
    bester_name = sorted(levenshtein_ratios,key=lambda item: item[1], reverse=True)[0]

    # Das Ergebnis wird in eine Liste geschrieben, die später mit den anderen
    # Daten zusammengeführt wird
    validierungsergebnisse.append((ist_gueltig, ablehnungsgrund, bester_name[0], bester_name[1]))

# Hier wird die Validierung zusammengeführt
csv["Gültig"] = [ist_gueltig for (
    ist_gueltig, ablehnungsgrund, namenskandidat, levensthein_distance) in validierungsergebnisse]
csv["Ablehnungsgrund"] = ["/".join(ablehnungsgrund)
                          for (ist_gueltig, ablehnungsgrund, namenskandidat, levensthein_distance) in validierungsergebnisse]
csv["bester Namenskandidat"] = [namenskandidat
                          for (ist_gueltig, ablehnungsgrund, namenskandidat, levensthein_distance) in validierungsergebnisse]
csv["Levenshteindistanz"] = [levensthein_distance
                          for (ist_gueltig, ablehnungsgrund, namenskandidat, levensthein_distance) in validierungsergebnisse]

# Neuordnung der Spalten:
csv.insert(0, config.vorname_spalte, csv.pop(config.vorname_spalte))
csv.insert(1, config.nachname_spalte, csv.pop(config.nachname_spalte))
csv.insert(2, config.email_spalte, csv.pop(config.email_spalte))
csv.insert(3, "immatrikulations_pdf_location",
           csv.pop("immatrikulations_pdf_location"))
csv.insert(4, "Gültig", csv.pop("Gültig"))
csv.insert(5, "Ablehnungsgrund", csv.pop("Ablehnungsgrund"))
csv.insert(4, "bester Namenskandidat", csv.pop("bester Namenskandidat"))
csv.insert(5, "Levenshteindistanz", csv.pop("Levenshteindistanz"))

# Filtern der Ergebnisse
duplicates = csv[csv.duplicated(subset=config.email_spalte, keep="first")]
erfolg = csv[csv["Gültig"]]
fehler = csv[csv["Gültig"] != True]

# Zum Schluss schreiben wir die Ergebnisse in den output-Pfad
erfolg.to_excel(config.output_pfad + "/erfolg.xlsx", index=False)
fehler.to_excel(config.output_pfad + "/fehler.xlsx", index=False)
duplicates.to_excel(config.output_pfad + "/duplikate.xlsx", index=False)

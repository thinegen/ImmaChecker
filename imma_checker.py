try:
    import config
    import fitz
    import pandas
    import os
    import requests
    import re
    from fuzzywuzzy import fuzz
    from datetime import datetime
    from dateutil import relativedelta
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

volljaehrigkeit_pruefen = True
# Können wir das Medidatum parsen?
if len(config.medis_erster_tag) == 0 or len(config.geburtsdatum_spalte) == 0:
    volljaehrigkeit_pruefen = False
else:
    try:
        parsed_medis_erster_tag = datetime.strptime(config.medis_erster_tag, '%d.%m.%Y')
        mindestgeburtstag_medis_volljaehrigkeit = parsed_medis_erster_tag - relativedelta.relativedelta(years=18)
        print(f"[i] Der erste Tag der Medis ist der {parsed_medis_erster_tag.strftime('%d.%m.%Y')}")
        print(f"[i] Wer mit auf die Medis will muss spätestens am {mindestgeburtstag_medis_volljaehrigkeit.strftime('%d.%m.%Y')} geboren sein")
    except Exception as e:
        print(f"[!] Der erste Tag der Medis (config.py: medis_erster_tag) konnte nicht bestimmt werden. Das Datum sollte wie 08.06.2023 aussehen.\n\tFehler: "+str(e))
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
    csv[config.geburtsdatum_spalte]
    csv[config.imma_bescheinigung_spalte]
except Exception as e:
    print("[!] Eine Spalte in der Tabelle scheint in config.py falsch zu sein:\n\t" + str(e))
    quit()

# Das Feld für den PDF-Upload hat das Format "YYY-MM-DD <filename> (<downloadurl>)".
# Wir teilen das Feld in die einzelnen Bestandteile und
# schreiben die Daten in unser CSV
split = csv[config.imma_bescheinigung_spalte].str.split(
    config.uploaded_imma_regex, regex=True, expand=True)
csv["imma_upload_date"], csv["imma_filename"], csv["imma_file_ending"], csv["imma_download_url"] = split[1], split[2], split[3], split[4]

print("[i] Es werden alle Immatrikulationsbescheinigungen heruntergeladen. Das dauert etwas.")

# Jetzt speichern wir alle Immas
zaehler = 0
anzahl_zeilen = len(csv["imma_download_url"])
downloaded_imma_paths = [None] * anzahl_zeilen
for index, csv_zeile in enumerate(csv.iloc):
    zaehler += 1
    if zaehler % 50 == 0:
        print(f"[i] {zaehler} von {anzahl_zeilen} Dateien heruntergeladen")

    try:
        download_url = csv_zeile["imma_download_url"]
        # Der Pfad, in dem die Imma gespeichert wird ist effektiv nur der angegebene Ordner und der Zeilenindex im CSV
        imma_file_path = config.imma_path + "/" + str(index)  + "." + csv_zeile["imma_file_ending"]

        # Alles runterladen
        if download_url is None:
            print(
            f"[!] Es konnte kein Downloadlink gefunden werden:\n\tName: {csv.iloc[index][config.vorname_spalte]} {csv.iloc[index][config.nachname_spalte]}")
            continue
        r = requests.get(download_url)
        with open(imma_file_path, 'wb') as f:
            f.write(r.content)
            downloaded_imma_paths[index] = imma_file_path

    except Exception as e:
        # Bei Fehlern wird der Name und der Fehler noch einmal gesondert ausgegeben
        print(
            f"[!] Beim Herunterladen einer Immatrikulationsbescheinigung ist ein Fehler aufgetreten:\n\tName: {csv.iloc[index][config.vorname_spalte]} {csv.iloc[index][config.nachname_spalte]}\n\tURL: {download_url}\n\t" + str(e))

# Die Liste der runtergeladenen Immas wird gespeichert
csv["immatrikulations_pdf_location"] = downloaded_imma_paths

print("[i] Die Immatrikulationsbescheinigungen werden geprüft.")

# Jetzt validieren wir alle PDFs
validierungsergebnisse = []
for csv_zeile in csv.iloc:
    ist_gueltig = True
    ablehnungsgrund = []

    vorname = csv_zeile[config.vorname_spalte]
    nachname = csv_zeile[config.nachname_spalte]
    name = f"{vorname} {nachname}"
    email = csv_zeile[config.email_spalte]
    geburtsdatum_parsen_ok = False
    pdf_location = csv_zeile["immatrikulations_pdf_location"]

    geburtsdaten_formatiert = []
    try:
        parsed_geburtsdatum = datetime.strptime(csv_zeile[config.geburtsdatum_spalte], config.airtable_geburtstagsdatum_format)
        for datumsformat in config.geburtsdatum_formate:
            geburtsdaten_formatiert.append(parsed_geburtsdatum.strftime(datumsformat))
    except Exception as e:
        print(
            f"[!] Das Geburtsdatum konnte nicht geprüft werden. Wahrscheinlich steht im CSV kein Datum oder es ist im falschen Format:\n\tName: {name}\n\tDatei: {pdf_location}")
        ist_gueltig = False
        ablehnungsgrund.append("Beim Geburtsdatum im CSV stimmt etwas nicht")

    if pdf_location is None:
        # Wir haben kein PDF für diesen Eintrag
        ist_gueltig = False
        ablehnungsgrund.append("Das PDF konnte nicht heruntergeladen werden")
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
    if len(pdf_inhalt) == 0 or (len(pdf_inhalt) == 1 and pdf_inhalt[0] == ''):
        print(
            f"[!] Das PDF ist leer, ein Scan oder die Datei ist kein PDF:\n\tName: {name}\n\tDatei: {pdf_location}")
        ist_gueltig = False
        ablehnungsgrund.append("Das PDF ist leer, ein Scan oder die Datei ist kein PDF")
        validierungsergebnisse.append((ist_gueltig, ablehnungsgrund, "", 0))
        continue

    # Danach das Semester
    im_richtigen_semester = any([
        semester in string
        for semester in config.semester
        for string in pdf_inhalt
    ])
    if not im_richtigen_semester:
        ist_gueltig = False
        ablehnungsgrund.append("Falsches Semester")

    # Die Maildomain
    if len(config.erlaubte_email_domains) > 0:
        email_teile = email.split("@")
        if len(email_teile) != 2 or (len(email_teile) == 2 and email_teile[1] not in config.erlaubte_email_domains):
            ist_gueltig = False
            ablehnungsgrund.append("Falsche Emaildomain")

    # Den Studiengang
    im_richtigen_studiengang = any([
        studiengang in string
        for studiengang in config.studiengaenge
        for string in pdf_inhalt
    ])
    if not im_richtigen_studiengang:
        ist_gueltig = False
        ablehnungsgrund.append("Falscher Studiengang")

    # Die Volljährigkeit
    if volljaehrigkeit_pruefen and geburtsdatum_parsen_ok:
        hat_richtiges_geburtsdatum = any([
            geburtsdatums_str in string
            for string in pdf_inhalt
            for geburtsdatums_str in geburtsdaten_formatiert
        ])
        if hat_richtiges_geburtsdatum:
            if mindestgeburtstag_medis_volljaehrigkeit < parsed_geburtsdatum:
                ist_gueltig = False
                ablehnungsgrund.append("Minderjährig")
        else:
            ist_gueltig = False
            ablehnungsgrund.append("Geburtsdatum nicht in der Immatrikulationsbescheinigung")

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

    name_mit_regex_nicht_gefunden = all([lr < config.levensthein_cutoff for (k, lr) in levenshtein_ratios])

    # Falls wir den Namen nicht finden, prüfen wir ob sich Vor- und Nachname einzeln finden lässt    
    if name_mit_regex_nicht_gefunden:
        vorname_in_pdf = any([
            vorname in string
            for string in pdf_inhalt
        ])
        nachname_in_pdf = any([
            nachname in string
            for string in pdf_inhalt
        ])
    
    # default: Name nicht gefunden
    bester_name = ("", 0)

    # Wenn das alles nicht funktioniert gibt es den Namen wohl tatsächlich nicht
    if name_mit_regex_nicht_gefunden and not vorname_in_pdf and not nachname_in_pdf:
        ist_gueltig = False
        ablehnungsgrund.append("Name nicht gefunden")
    else:
        # Es wurde ein Name gefunden
        bester_name = (name, 100)
    
    # Falls mit Levensthein gefunden ist das der beste Namenskandidat
    if not name_mit_regex_nicht_gefunden and len(levenshtein_ratios) > 0:
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
duplicates_mask = csv.duplicated(subset=config.email_spalte, keep=False)
duplicates = csv[duplicates_mask]

# Es werden nur deduplizierte Zeilen angenommen
csv = csv[~duplicates_mask]

erfolg = csv[csv["Gültig"]]
fehler = csv[~csv["Gültig"]]

# Zum Schluss schreiben wir die Ergebnisse in den output-Pfad
erfolg.to_excel(config.output_pfad + "/erfolg.xlsx", index=False)
fehler.to_excel(config.output_pfad + "/fehler.xlsx", index=False)
duplicates.to_excel(config.output_pfad + "/duplikate.xlsx", index=False)

print("[i] Fertig!")
print("[i] Alle Personen in output/fehler.xlsx und output/duplikate.xlsx sollten überprüft werden.")
print("[i] Viel Spaß auf den Medis!")
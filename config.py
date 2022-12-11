# Das exportierte Airtable CSV
csv = "export.csv"

# Der Ordner, in dem die Immatrikulationsbescheinigungen gespeichert werden sollen
imma_path = "immatrikulationsbescheinigungen"

# Der Ordner, in dem die Ergebnisse gespeichert werden sollen
output_pfad = "output"

# Die Studiengänge, die mit auf die Medis dürfen, genau so wie sie in der Immatrikulationsbescheinigung stehen
studiengaenge = ["Zahnmedizin", "Humanmedizin", "Medizin"]

# Das aktuelle Semester wie in der Immatrikulationsbescheinigung.
# Falls es hier mehrere Möglichkeiten gibt, könnt ihr wie bei den Studiengängen
# eine Liste erstellen (also z. B. ["semester1", "semester2"]).
semester = ["Wintersemester 2022"]

# Die Spaltennamen, die ihr für das Airtable verwendet habt
vorname_spalte = "Vorname"
nachname_spalte = "Nachname"
email_spalte = "Email"
imma_bescheinigung_spalte = "Immatrikulationsbescheinigung"

# Die Regular Expression, die den Namen herausfiltert.
# Wendet euch bei Fragen an mich oder an den Informatiker eures Vertrauens
namen_regex = r"(?:Herr|Frau)\s+([A-zÀ-ú@0-9- üÜ]*),\s+(?:geboren|Matrikel-Nr.:)"

# Ab hier kommen Sachen die nur verändert werden sollten,
# wenn ihr wisst was ihr macht (oder neugierig seid)
# Das Regex für den Airtable Imma Upload
uploaded_imma_regex = "([0-9]{4}-[0-9]{2}-[0-9]{2})?\ ?([A-z0-9\.]*) \((http[s]:\/\/[A-z0-9_\-\.\/]*)\)"

# Der maximale Levensthein Wert zum Namensvergleich
levensthein_cutoff = 66

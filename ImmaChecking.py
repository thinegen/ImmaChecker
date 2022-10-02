#!/usr/bin/env python
# coding: utf-8



import os
import pandas as pd
from tika import parser  
import numpy as np
import re
import random
import requests
from fuzzywuzzy import fuzz



# Wo ist die AirTable CSV-Datei gespeichert? Gib sie hier bitte an!
csv= 'Codevergabe-Grid view.csv'

#Bitte gib hier deinen Pfad an wo die Immas gespeichert werden sollen
path= './Immatrikulationsbescheinigung/Abgaben'

# Welche Studiengänge sind erlaubt? Bitte schreibe sie genauso wie in den Immabescheinigungen(WICHTIG!)
studiengaenge_LMU= ['Zahnmedizin','Medizin', 'Tiermedizin']
studiengaenge_TUM= ['Medizin',]

#Aus welchem Semester dürfen die Immabescheinigungen sein?? 
#Bitte genauso schreiben wie in den Immabescheinigungen (Copy-Paste ist euer Freund)
semester_LMU= ['SoSe@2022@an@der@Universität@München', 'WS@2021/2022@']
semester_TUM= ['Sommersemester@2022', 'Wintersemester@2021/22']

# Wie heisst die Spalte mit dem Downloadlink im Airtable? Bitte in den Anführungszeichen Copy-Pasten
PDF_ROWNAME= 'Nachweis Mediziner:in'

# Wie heisst die Spalte mit dem Vornamen in eurer AirTable?
AIRTABLE_VORNAME = 'Name copy'

# Wie heisst die Spalte mit dem Nachnamen in eurer AirTable?
AIRTABLE_NACHNAME = 'Name'

#Wollt ihr nach Uni-Mail checken?
CHECK_FOR_MAIL = True
#CHECK_FOR_MAIL = False


# Wie heisst die Spalte mit der E-Mail in eurer AirTable?
AIRTABLE_Mail = 'MAIL'

#Das hier ist die Schwelle der Übereinstimmung, je näher an 1.0 desto mehr fliegen raus (Cave bei Doppelnamen etc.)
#0.669 hat sich hier bis jetzt gut bewährt
levensthein_cutoff = .66

#Hier sind die regulären Ausdrücke formuliert die die Namen aus dem ganzen Text herausfiltern.
#Ihr dürft hier gerne rumspielen, sont meldet euch bei Christopher für genauere Erklärungen!
regex_TUM= "(Herr@|Frau@)([A-zÀ-ú@0-9- üÜ]*)@geboren"
regex_TUM2= '@{1}(.*)@geboren'
regex_LMU="(Herr@|Frau@)([A-zÀ-ú@0-9- üÜ]*)@Matrikel"
regex_LMU2= '@{1}(.*)@Matrikel'


 


#Erstelle alle notwendigen Ordnerstrukturen

if os.path.isdir(path) == False:
    os.path.makedir(path)
    print(f'Die Immatrikulationsbescheinigungen werden unter folgendem Ordner gespeichert: {path})

if os.path.isfile(csv) == False:
    print(f"Die angegebene CSV-Datei gibt es nicht - bitte kontrolliere den Namen und versuche es erneut! \n Du hast folgenden DAteiort angeben: {csv}")
    
if os.path.isdir('./output') == False:
    os.path.makedir('./output')
    print(f'Die fertigen Listen werden in diesem Ordner gespeichert: {os.getcwd}/output')
    



# Hier werden nur ganz viele Funktionen definiert, die wir später brauchen!
def levenshtein_ratio_and_distance(s, t, ratio_calc = True):
    """ levenshtein_ratio_and_distance:
        Calculates levenshtein distance between two strings.
        If ratio_calc = True, the function computes the
        levenshtein distance ratio of similarity between two strings
        For all i and j, distance[i,j] will contain the Levenshtein
        distance between the first i characters of s and the
        first j characters of t
    """
    # Initialize matrix of zeros
    rows = len(s)+1
    cols = len(t)+1
    distance = np.zeros((rows,cols),dtype = int)

    # Populate matrix of zeros with the indeces of each character of both strings
    for i in range(1, rows):
        for k in range(1,cols):
            distance[i][0] = i
            distance[0][k] = k

    # Iterate over the matrix to compute the cost of deletions,insertions and/or substitutions    
    for col in range(1, cols):
        for row in range(1, rows):
            if s[row-1] == t[col-1]:
                cost = 0 # If the characters are the same in the two strings in a given position [i,j] then the cost is 0
            else:
                # In order to align the results with those of the Python Levenshtein package, if we choose to calculate the ratio
                # the cost of a substitution is 2. If we calculate just distance, then the cost of a substitution is 1.
                if ratio_calc == True:
                    cost = 2
                else:
                    cost = 1
            distance[row][col] = min(distance[row-1][col] + 1,      # Cost of deletions
                                 distance[row][col-1] + 1,          # Cost of insertions
                                 distance[row-1][col-1] + cost)     # Cost of substitutions
    if ratio_calc == True:
        # Computation of the Levenshtein Distance Ratio
        Ratio = ((len(s)+len(t)) - distance[row][col]) / (len(s)+len(t))
        return Ratio
    
def list_check(list, text):
    data= []
    for i in list:
        x= string_check(i,text)
        data.append(x)
    if True in data:
        return True
    else:
        return False
        
def string_check(str, text):
    if str in text:
        return True
    else:
        return False



def lev_check(lev_distance, cutoff):
    if lev_distance>= cutoff:
        return True
    else:
        return False



def bool_check(list):
    if False in list:
        return 'Name Check error'
    else:
        return False





#Einlesen der AirTable-Tabelle

df1= pd.read_csv(csv)
all= df1





#Aufspalten der Downloadlink-Zeile in  filename, downloadlink, filetype
d= df1[PDF_ROWNAME].str.split("([.]*[\w]*) \((https[^\(\)]*)", regex=True ,expand= True)

df1['filename'], df1['filetype'], df1['download']= d[0], d[1], d[2]



 


#Lade Dateien herunter und speichere unter dem Index-Namen (Zeilennummer)
def download_pdf(url, filename):
    filepath= './downloads/' + str(filename)   
    if os.path.exists(os.path.join('./downloads/')) == False:
        os.mkdir('./downloads')

    r = requests.get(url)
    with open(filepath, 'wb') as f:
        f.write(r.content) 

df1.apply(lambda x : download_pdf(x['download'], str(x.name)+str(x['filetype'])), axis=1)


 


# Erstelle Spalte mit dem lokalen Dateipfad um die Dateien aufrufen zu können
df1['filepath_local']= df1.apply(lambda x: os.path.join(('./downloads/' + str(x.name) +'.pdf')), axis=1)


 


#Funktion um die PDF-Dateien einzulesen
def parsing_pdf(filename):
    try:
        # opening pdf file
        parsed_pdf = parser.from_file(filename)
        data = parsed_pdf['content'] 
        
        if data == None:
            return False
        
        data= data.replace('\n', '@')
        data= data.replace(' ', '@')
        data= re.sub(r'@{2,}', '@', data)
        #print(data)
        return data
    except:
        return False


 


#Parsen (Einlesen) der PDF-Dateien, sollten hier fehlerhafte PDFs entahlten sein, werden die markiert! Die müsst ihr dann per Hand Checken
df1['content']= df1.apply(lambda x: parsing_pdf(x['filepath_local']), axis=1)
f= df1[df1['content']==False]
f['error'] = "Invalid PDF"
no_pdf= pd.DataFrame(f)
df1= df1[df1['content']!=False]


 


#Funktion um zu schauen ob die Studiengänge, Semester und Namen mit den angegeben übereinstimmen!
def checking(filelist, studiengaenge, semester, lev_cutoff, regex):
    
    filelist['name_ok']= filelist.apply(lambda row : lev_check(str( row['Vorname']) + ' ' + str(row['Nachname']), r_name(row['content']), lev_cutoff, regex), axis=1)
    filelist['Semester_ok']= filelist.apply(lambda row : list_check(semester, str(row['content'])), axis=1)
    filelist['Fach_ok']= filelist.apply(lambda row : list_check(studiengaenge, row['content']),axis=1)
    return filelist


 


#Funktion zum Auslesen der Namen

def r_name(data, regex1, regex2):
    try:
        d= re.search(regex1, str(data))
        d= d.group()
        print(d)
        d= re.search (regex2, str(d))
        d= d.group()
        d= d.strip()
        
        return d
    except:
        return False



 


#Auslesen der Namen aus allen PDF-Dateien mittels der Regulären Ausdrücke von oben
#Hier müssen wir ggf einmal über die entsprechenden Namen schauen - das ist je nachdem etwas anstrengend manchmal

df1['parsed_name']= df1.apply(lambda x: r_name(x['content'], regex_1, regex_2), axis=1)
no_pdf= no_pdf.append(df1[df1['parsed_name']==False])
df1= df1[df1['parsed_name']!=False]
df1['parsed_name'] = df1.apply(lambda row:row['parsed_name'].strip(), axis=1)
df1['parsed_name'] = df1.apply(lambda row:row['parsed_name'].replace('@', ' ').strip(), axis=1)
print(f'So sehen die Namen aus, schaut einmal drüber ob das passt: \n {df1['parsed_name'][1:8]}')





 


#Auslesen der Semester in der PDF
df1['semester_ok']= df1.apply(lambda row : list_check(semester, str(row['content'])), axis=1)




 


#Check ob das Semester von euch validiert ist
df1['Fach_ok']= df1.apply(lambda row : list_check(studiengaenge, row['content']),axis=1)
          


 


#ganz viele Berechnungen zum Abgleich der Namen und Check ob alle Parameter die ihr vorgegeben habt (Semester, Studiengang, etc.) stimmen
df1['lev_ratio']= df1.apply(lambda row: fuzz.token_sort_ratio((str(row[VORNAME_AIRTABLE]) + ' ' + str(row[NACHNAME_AIRTABLE])), str(row['parsed_name'])), axis=1)

df1['name_ok']= df1.apply(lambda row: lev_check(row['lev_ratio'], levensthein_cutoff*100), axis=1)

df1['error']=df1.apply(lambda row: bool_check([row['semester_ok'], row['name_ok'], row['Fach_ok']]), axis=1)

if CHECK_FOR_MAIL:
          df1['mail_error']= df1.apply(lambda row: string_check(AIRTABLE_MAIL_SUFFIX, row[AIRTABLE_MAIL]), axis=1)
          no_pdf = no_pdf.append(df1[df1['mail_error']== False])
          df1= df1= df1[df1['error']== True]

no_pdf= no_pdf.append(df1[df1['error']!= False])

df1= df1[df1['error']== False]

          

 





 


#Entferne alle Doppeleinreichungen, behalte nur die erste Zeile

unique_values= df1.drop_duplicates(subset= ['content', 'Uni',] )


 


# Filtere alle fehlerhaften PDF-Dateien raus und schreibe sie in eine Excel-Tabelle
no_pdf.to_excel('./output/Fehlerhafte.xlsx', encoding='UTF-8', engine='xlsxwriter')

#Schreibe alle erfolgreich gecheckten in eine Tabelle
unique_values.to_excel('./output/Erfolgreich_gecheckt.csv', encoding='utf-8', engine='xlsxwriter')


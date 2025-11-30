EXPORT SUMMARY DIALOG - Jedan Finalni Dijalog
==============================================

DATUM: 2025-11-28
AŽURIRANO: 2025-11-28 (dodato no_data handling)

FUNKCIONALNOST:
---------------

Plugin sada prikazuje JEDAN finalni dijalog sa spiskom svih exportovanih slojeva
umesto pojedinačnih poruka za svaki sloj.

Plugin proverava da li postoje feature-i sa datim job_id PRE exporta i prikazuje
informaciju o slojevima koji nemaju digitalizovane podatke.

IZMENE:
-------

1. Export metode vraćaju rezultat (dictionary) umesto prikazivanja poruka:
   - export_punkt_layer() → vraća dict ili None
   - export_rohrmuffe_layer() → vraća dict ili None

2. Nova metoda: show_export_summary(export_results, job_id)
   - Prikazuje jedan finalni dijalog
   - Grupiše uspešne i neuspešne exportove
   - Prikazuje broj feature-a i naziv fajla za svaki sloj

STRUKTURA REZULTATA:
--------------------

Uspešan export:
{
    'layer': 'PUNKT',
    'count': 150,
    'file': '/path/to/PUNKT_job_12345.shp',
    'success': True
}

Nema podataka (no_data):
{
    'layer': 'PUNKT',
    'success': False,
    'no_data': True,
    'error': 'No features found with job_id = 12345'
}

Neuspešan export (greška):
{
    'layer': 'PUNKT',
    'success': False,
    'error': 'Error message'
}

None - ako sloj nije pronađen u projektu

FINALNI DIJALOG:
----------------

Prikazuje:
✓ Broj uspešno exportovanih slojeva
✓ Spisak slojeva sa brojem feature-a i nazivom fajla
✓ Spisak neuspešnih exporta (ako ih ima)

Format poruke (primer 1 - svi slojevi uspešni):
==================================================
Successfully exported 2 layer(s) for Job ID: 12345

✓ PUNKT: 150 features → PUNKT_job_12345.shp
✓ ROHRMUFFE: 85 features → ROHRMUFFE_job_12345.shp
==================================================

Format poruke (primer 2 - neki slojevi bez podataka):
==================================================
Successfully exported 1 layer(s) for Job ID: 12345

✓ PUNKT: 150 features → PUNKT_job_12345.shp

==================================================

Layers with no data for Job ID 12345 (1):

○ ROHRMUFFE: No features digitized
==================================================

Format poruke (primer 3 - svi slojevi bez podataka):
==================================================
Layers with no data for Job ID 12345 (2):

○ PUNKT: No features digitized
○ ROHRMUFFE: No features digitized
==================================================

TIP DIJALOGA:
-------------

- Information (zelena) - svi exporti uspešni ILI samo slojevi bez podataka
- Warning (žuta) - neki exporti uspešni, neki neuspešni
- Critical (crvena) - svi exporti neuspešni (greške, ne no_data)

PREDNOSTI:
----------

✓ Jedan dijalog umesto više
✓ Pregled svih exportovanih slojeva odjednom
✓ Jasna indikacija uspešnih (✓) i neuspešnih (✗) exporta
✓ Prikazuje broj feature-a za svaki sloj
✓ Skalabilno - lako dodati nove slojeve

DODAVANJE NOVIH SLOJEVA:
-------------------------

1. Kreirajte novu export metodu (npr. export_haltung_layer)
2. Vratite dictionary sa rezultatom
3. Dodajte poziv u run() metodi:
   
   result = self.export_haltung_layer(job_id, output_folder)
   if result:
       export_results.append(result)

4. show_export_summary() će automatski prikazati novi sloj

TESTIRANJE:
-----------

Scenario 1: Oba sloja uspešno exportovana
- Prikazuje se Information dialog
- Lista sa oba sloja i brojem feature-a

Scenario 2: Jedan sloj uspešan, drugi ne postoji
- Prikazuje se Information dialog
- Samo uspešan sloj u listi

Scenario 3: Oba sloja ne postoje ili nemaju feature-a
- Prikazuje se Warning dialog
- "No layers were exported"

Scenario 4: Greška pri exportu
- Prikazuje se Warning/Critical dialog
- Lista neuspešnih exporta sa error porukama

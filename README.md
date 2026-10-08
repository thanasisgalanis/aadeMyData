# ΑΑΔΕ myData Rest API to JSON

Δεδομένα myData σε μορφή **json** για προγραμματιστές, σχετικά με την πλατφόρμα [myData](https://www.aade.gr/mydata) της ΑΑΔΕ.

> Όλα τα αρχεία είναι ενημερωμένα σύμφωνα με την **έκδοση 2.0.2 (Σεπτέμβριος 2026)** των
> [τεχνικών προδιαγραφών myDATA](https://www.aade.gr/mydata/tehnikes-prodiagrafes-ekdoseis-mydata).
> Κάθε κατάλογος ελέγχεται μηχανικά απέναντι στα επίσημα XSD της ίδιας έκδοσης (`tools/verify.py`).

## Πηγές (v2.0.2)

| Πηγή | Τι δίνει |
|---|---|
| [Τεχνική περιγραφή διεπαφών REST API για χρήστες ERP v2.0.2](https://www.aade.gr/sites/default/files/2026-09/myDATA%20API%20Documentation%20v2.0.2_official_erp_1.pdf) | Οι περιγραφές των πινάκων του Παραρτήματος (8.x) και τα επιχειρησιακά σφάλματα (7.2) |
| [Τεχνική περιγραφή για Παρόχους v2.0.2](https://www.aade.gr/sites/default/files/2026-09/myDATA%20API%20Documentation_Providers_v2%200%202_official_0.pdf) | Ποια είδη παραστατικών διαβιβάζονται από πάροχο |
| [Τεχνική περιγραφή Ψηφιακής Διακίνησης Αγαθών v2.0.2](https://www.aade.gr/sites/default/files/2026-09/myDATA%20API%20Documentation_DeliveryNote_v2.0.2_official_0.pdf) | Οι πίνακες 7.1–7.4 του Ψηφιακού Δελτίου Αποστολής |
| [XSDs v2.0.2](https://www.aade.gr/sites/default/files/2026-09/v2.0.2XSDs_0.zip) → [`sources/v2.0.2/xsd/`](/sources/v2.0.2/xsd) | Οι τιμές που δέχεται το σχήμα — το μέτρο ελέγχου κάθε καταλόγου |
| [Συνδυασμοί χαρακτηρισμών v2.0.2](https://www.aade.gr/sites/default/files/2026-09/syndiasmoi_xaraktirismwn_v2.0.2_0.xlsx) → [`sources/v2.0.2/`](/sources/v2.0.2) | Το [`combinations.json`](/combinations.json), παραγόμενο αυτούσιο |

Τα αρχεία XSD και xlsx φυλάσσονται στο `sources/` όπως δημοσιεύτηκαν, ώστε κάθε
κατάλογος να ελέγχεται απέναντι στην πηγή του χωρίς πρόσβαση στο δίκτυο.

## Εργαλεία

```bash
pip install -r tools/requirements.txt       # openpyxl, μόνο για το build
python3 tools/build_combinations.py          # sources/…/syndiasmoi_*.xlsx → combinations.json
python3 tools/verify.py                      # κάθε κατάλογος απέναντι στα XSD (μόνο standard library)
```

Νέα έκδοση της ΑΑΔΕ: τα νέα αρχεία στο `sources/v<έκδοση>/`, ενημέρωση των καταλόγων,
`build_combinations.py`, και `verify.py <έκδοση>` μέχρι να περάσει.

## Γνωστές ασυμφωνίες της ίδιας της προδιαγραφής (v2.0.2)

Η προδιαγραφή διαφωνεί με τον εαυτό της στα παρακάτω. Οι κατάλογοι ακολουθούν τον
**πίνακα** της τεκμηρίωσης και το `verify.py` δηλώνει ρητά τη διαφορά:

| Κατάλογος | Κωδικός | Ασυμφωνία |
|---|---|---|
| `classificationTypes.json` | `E3_585_017` | Υπάρχει στον πίνακα 8.11 και στους συνδυασμούς (17.5), όχι στο XSD (`ExpensesClassificationValueType`) |
| `receivingNotePurposes.json` | `7` | Το XSD δέχεται 1–7, ο πίνακας 8.24 ορίζει 1–6 |
| `invoiceDeliveryStatuses.json` | `6` | Το XSD δέχεται 1–9, ο πίνακας 7.1 δεν ορίζει το 6 |

## Είδη παραστατικών
Παράρτημα myDATA REST API - Πίνακας 8.1

[documentTypes.json](/documentTypes.json) — `metadata.availableForERP`, `availableForProvider`, `requiresCounterparty` όπου η τεκμηρίωση το ορίζει.
Τα 9.1, 9.2, 10.1, 10.2 (v2.0.0) δεν περιλαμβάνονται στον πίνακα 8.1 των Παρόχων. Τα 4 και 12 είναι «Για Μελλοντική Χρήση».

## Συνδυασμοί χαρακτηρισμών E3
[Συνδυασμοί χαρακτηρισμών (xls)](https://www.aade.gr/sites/default/files/2026-09/syndiasmoi_xaraktirismwn_v2.0.2_0.xlsx)

[combinations.json](/combinations.json) — ανά είδος παραστατικού, οι επιτρεπτοί τύποι E3 ανά κατηγορία χαρακτηρισμού, για έσοδα και έξοδα:

```json
"1.1": {
    "description": "ΤΙΜΟΛΟΓΙΟ ΠΩΛΗΣΗΣ",
    "sections": [{
        "title": null,
        "income": {
            "categories": {
                "category1_1": { "types": ["E3_561_001", "E3_561_002", "E3_561_007"] },
                "category1_8": { "types": [], "rule": "sameTypesAsOtherCategories", "note": "…" },
                "category1_95": { "types": ["E3_596", "E3_597"], "allowsEmptyType": true }
            }
        },
        "expenses": { "categories": { … } }
    }]
}
```

- `types: []` — η πηγή δεν δίνει επιτρεπτό τύπο E3· ο λόγος είναι στο `note` (π.χ. «Δεν ενημερώνει E3»).
- `rule: "sameTypesAsOtherCategories"` — `category1_8`/`1_9`/`2_10`/`2_11`: «είναι επιτρεπτοί οι παραπάνω χαρακτηρισμοί ανά τιμή ΣΤ.9», με μεταφορά χρήσης.
- `allowsEmptyType` — «ή κενό».
- `rule: "sameAsCorrelatedInvoiceType"` (σε επίπεδο πλευράς) — 1.6, 2.4, 5.1: ισχύουν οι συνδυασμοί του είδους του συσχετιζόμενου παραστατικού (`correlatedInvoiceTypes`).
- `markers` — σημάνσεις του αρχείου δίπλα σε κωδικό (π.χ. «νέο»).
- `sections` — ένα φύλλο μπορεί να έχει περισσότερες ενότητες (1.5). Ο τίτλος αποδίδεται αυτούσιος· το αρχείο δεν ορίζει σε ποιο `invoiceDetailType` αντιστοιχεί κάθε ενότητα.

Κάθε κείμενο του αρχείου διατηρείται αυτούσιο στο αντίστοιχο `note`· ό,τι δεν αναγνωρίζει ο builder σταματά την παραγωγή.

## Κατηγορίες Χαρακτηρισμού Εσόδων/Εξόδων
Παράρτημα myDATA REST API - Πίνακας 8.8 & 8.10

[classificationCategories.json](/classificationCategories.json)

## Τύποι Χαρακτηρισμού Εσόδων/Εξόδων
Παράρτημα myDATA REST API - Πίνακας 8.9 & 8.11

[classificationTypes.json](/classificationTypes.json) — ένας κωδικός που ισχύει και για έσοδα και για έξοδα εμφανίζεται δύο φορές, με `metadata.class` `income` και `expenses`.

## Τύποι Χαρακτηρισμού Φ.Π.Α.
Παράρτημα myDATA REST API - Πίνακας 8.11

[vatTypes.json](/vatTypes.json)

## Κατηγορίες ΦΠΑ
Παράρτημα myDATA REST API - Πίνακας 8.2

[vatCategories.json](/vatCategories.json)

## Κατηγορίες Αιτίας Εξαίρεσης ΦΠΑ
Παράρτημα myDATA REST API - Πίνακας 8.3

[vatExceptionReasons.json](/vatExceptionReasons.json) — `description` σύμφωνα με τον ισχύοντα Κώδικα ΦΠΑ (ν. 5144/2024). Η αρίθμηση άρθρων του ν. 2859/2000 διατηρείται στο `metadata.previousLawDescription` (νέα κωδικοποίηση από την έκδοση 1.0.11· οι κωδικοί δεν άλλαξαν).

## Κατηγορίες παρακρατούμενων φόρων
Παράρτημα myDATA REST API - Πίνακας 8.4

[withholdingTaxes.json](/withholdingTaxes.json)

## Κατηγορίες λοιπών φόρων
Παράρτημα myDATA REST API - Πίνακας 8.5

[otherTaxes.json](/otherTaxes.json)

## Κατηγορίες Συντελεστή Ψηφιακού Τέλους συναλλαγής
Παράρτημα myDATA REST API - Πίνακας 8.6 (το Χαρτόσημο μετονομάστηκε σε Ψηφιακό Τέλος συναλλαγής στην έκδοση 1.0.11)

[stampRates.json](/stampRates.json)

## Κατηγορίες Τελών
Παράρτημα myDATA REST API - Πίνακας 8.7

[feeCategories.json](/feeCategories.json)

## Τρόποι Πληρωμής
Παράρτημα myDATA REST API - Πίνακας 8.12

[paymentMethods.json](/paymentMethods.json)

## Είδη Ποσότητας
Παράρτημα myDATA REST API - Πίνακας 8.13

[quantityTypes.json](/quantityTypes.json)

## Σκοποί Διακίνησης
Παράρτημα myDATA REST API - Πίνακας 8.14

[transactionPurposes.json](/transactionPurposes.json) — οι κωδικοί που δεν επιτρέπεται πλέον να αποστέλλονται (6, 15, 16, 17, 18) φέρουν `metadata.deprecated: true`.

## Επισημάνσεις
Παράρτημα myDATA REST API - Πίνακας 8.15

[highlightings.json](/highlightings.json)

## Είδος Γραμμής
Παράρτημα myDATA REST API - Πίνακας 8.16

[lineTypes.json](/lineTypes.json)

## Κωδικοί Καυσίμων
Παράρτημα myDATA REST API - Πίνακας 8.17

[fuelCodes.json](/fuelCodes.json)

## Τύποι Απόκλισης Παραστατικού
Παράρτημα myDATA REST API - Πίνακας 8.18

[documentVariationTypes.json](/documentVariationTypes.json)

## Ειδικές Κατηγορίες Παραστατικού
Παράρτημα myDATA REST API - Πίνακας 8.19

[documentSpecialCategories.json](/documentSpecialCategories.json)

## Κατηγορίες Οντότητας (EntityType)
Παράρτημα myDATA REST API - Πίνακας 8.20

[entityTypes.json](/entityTypes.json)

## Αιτία Έκδοσης Αντίστροφης Διακίνησης
Παράρτημα myDATA REST API - Πίνακας 8.21

[reverseDeliveryNotePurposes.json](/reverseDeliveryNotePurposes.json)

## Αιτία Έκδοσης Δελτίου Ποσοτικής Παραλαβής
Παράρτημα myDATA REST API - Πίνακας 8.24

[receivingNotePurposes.json](/receivingNotePurposes.json) — `metadata.allowedInvoiceTypes` από τη στήλη Παρατηρήσεις.

## Ψηφιακό Δελτίο Αποστολής
Τεχνική περιγραφή Ψηφιακής Διακίνησης Αγαθών — Παράρτημα 7 (οι πίνακες 8.22 και 8.23 της τεκμηρίωσης ERP παραπέμπουν εδώ)

- [invoiceDeliveryStatuses.json](/invoiceDeliveryStatuses.json) — Πίνακας 7.1, Καταστάσεις Δελτίου Αποστολής
- [deliveryEventTypes.json](/deliveryEventTypes.json) — Πίνακας 7.2, Τύποι Γεγονότων
- [packagingTypes.json](/packagingTypes.json) — Πίνακας 7.3, Τύποι Συσκευασίας
- [transportTypes.json](/transportTypes.json) — Πίνακας 7.4, Είδος Μεταφορικού Μέσου

## Επιχειρησιακά Σφάλματα
Τεχνική περιγραφή ERP - Παράγραφος 7.2

[operationalErrors.json](/operationalErrors.json) — `code`, `statusCode`, `element`, `message` (ελληνικά), `messageEn`. Τα κείμενα αποδίδονται όπως στην πηγή, μαζί με τα τυπογραφικά της. Η τελευταία γραμμή του πίνακα δεν έχει κωδικό (`code: null`, «Μη αναμενόμενο σφάλμα συνθήκης»).

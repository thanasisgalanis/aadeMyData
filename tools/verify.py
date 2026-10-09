#!/usr/bin/env python3
"""Verify every JSON list against the official AADE XSDs it mirrors.

Usage:
    python3 tools/verify.py [version]

For each list, the set of codes must equal the set the XSD accepts — an
enumeration, or a minInclusive..maxInclusive range. combinations.json is then
checked against the lists themselves. Standard library only.

The specification disagrees with itself in a few places. Those are declared in
KNOWN_DISCREPANCIES with the reason; every other difference fails the run, and
so does a declared discrepancy that is no longer there (the next version may
have fixed it, and the declaration must not outlive the fact).
"""

from __future__ import annotations

import json
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
X = "{http://www.w3.org/2001/XMLSchema}"

# list file -> where the XSD declares its codes:
#   ("simple", SimpleTypes name) | ("element", file stem, complexType, element)
SOURCES = {
    "documentTypes.json": ("simple", "InvoiceType"),
    "classificationCategories.json": ("simple", "IncomeClassificationCategoryType", "ExpensesClassificationCategoryType"),
    "classificationTypes.json": ("e3", None),
    "vatTypes.json": ("vat", None),
    "vatCategories.json": ("simple", "VatType"),
    "vatExceptionReasons.json": ("simple", "VatExemptionType"),
    "withholdingTaxes.json": ("simple", "WithheldType"),
    "stampRates.json": ("simple", "StampDutyType"),
    "feeCategories.json": ("simple", "FeesType"),
    "otherTaxes.json": ("simple", "OtherTaxesType"),
    "quantityTypes.json": ("simple", "QuantityType"),
    "fuelCodes.json": ("simple", "FuelCodes"),
    "documentSpecialCategories.json": ("simple", "SpecialInvoiceCategoryType"),
    "documentVariationTypes.json": ("simple", "InvoiceVariationType"),
    "reverseDeliveryNotePurposes.json": ("simple", "ReverseDeliveryNotePurposeType"),
    "receivingNotePurposes.json": ("simple", "ReceivingNotePurposeType"),
    "transactionPurposes.json": ("element", "InvoicesDoc", "InvoiceHeaderType", "movePurpose"),
    "lineTypes.json": ("element", "InvoicesDoc", "InvoiceRowType", "recType"),
    "paymentMethods.json": ("element", "InvoicesDoc", "PaymentMethodDetailType", "type"),
    "entityTypes.json": ("element", "InvoicesDoc", "EntityType", "type"),
    "invoiceDeliveryStatuses.json": ("element", "InvoicesDoc", "AadeBookInvoiceType", "invoiceDeliveryStatus"),
    "packagingTypes.json": ("element", "TransportTypes", "PackagingDetailType", "packagingType"),
    "transportTypes.json": ("element", "TransportTypes", "TransportDetailType", "transportType"),
}

# Lists the XSDs say nothing about; their source is the PDF alone.
PDF_ONLY = {"highlightings.json", "deliveryEventTypes.json", "operationalErrors.json"}

# (file, code, "only_in_list" | "only_in_xsd") -> why the difference is the specification's own.
KNOWN_DISCREPANCIES = {
    ("classificationTypes.json", "E3_585_017", "only_in_list"):
        "Πίνακας 8.11 και συνδυασμοί χαρακτηρισμών v2.0.2 — απουσιάζει από το ExpensesClassificationValueType του XSD v2.0.2.",
    ("receivingNotePurposes.json", "7", "only_in_xsd"):
        "Το ReceivingNotePurposeType δέχεται 1..7, ο πίνακας 8.24 ορίζει μόνο 1..6.",
    ("invoiceDeliveryStatuses.json", "6", "only_in_xsd"):
        "Το invoiceDeliveryStatus δέχεται 1..9, ο πίνακας 7.1 (Ψηφιακό Δελτίο Αποστολής) δεν ορίζει τον κωδικό 6.",
}


def xsd_dir(version: str) -> Path:
    return ROOT / "sources" / f"v{version}" / "xsd"


def restriction_codes(restriction) -> set[str]:
    enums = {e.get("value") for e in restriction.findall(X + "enumeration")}
    if enums:
        return enums
    low, high = restriction.find(X + "minInclusive"), restriction.find(X + "maxInclusive")
    if low is None or high is None:
        raise SystemExit("restriction without an enumeration or a closed range")
    return {str(n) for n in range(int(low.get("value")), int(high.get("value")) + 1)}


def simple_types(directory: Path, version: str) -> dict[str, set[str]]:
    root = ET.parse(directory / f"SimpleTypes-v{version}.xsd").getroot()
    out = {}
    for st in root.findall(X + "simpleType"):
        restriction = st.find(X + "restriction")
        try:
            out[st.get("name")] = restriction_codes(restriction)
        except SystemExit:
            continue  # amounts and the like: not code lists
    return out


def element_codes(directory: Path, version: str, stem: str, complex_type: str, element: str) -> set[str]:
    root = ET.parse(directory / f"{stem}-v{version}.xsd").getroot()
    for ct in root.iter(X + "complexType"):
        if ct.get("name") != complex_type:
            continue
        for el in ct.iter(X + "element"):
            restriction = el.find(f"{X}simpleType/{X}restriction")
            if el.get("name") == element and restriction is not None:
                return restriction_codes(restriction)
    raise SystemExit(f"{stem}: {complex_type}/{element} not found")


def codes(name: str) -> set[str]:
    return {str(x["code"]) for x in json.loads((ROOT / name).read_text(encoding="utf-8"))}


def main() -> None:
    version = sys.argv[1] if len(sys.argv) > 1 else "2.0.2"
    directory = xsd_dir(version)
    simple = simple_types(directory, version)
    e3_all = simple["IncomeClassificationValueType"] | simple["ExpensesClassificationValueType"]
    vat = {c for c in e3_all if c.startswith(("VAT_", "NOT_VAT_"))}

    unexpected: list[str] = []
    seen: set[tuple[str, str, str]] = set()

    for name, source in SOURCES.items():
        kind = source[0]
        if kind == "simple":
            expected = set().union(*(simple[n] for n in source[1:]))
        elif kind == "element":
            expected = element_codes(directory, version, *source[1:])
        elif kind == "e3":
            expected = e3_all - vat
        else:
            expected = vat
        have = codes(name)
        for code in sorted(have - expected):
            key = (name, code, "only_in_list")
            seen.add(key)
            if key not in KNOWN_DISCREPANCIES:
                unexpected.append(f"{name}: {code} is not accepted by the XSD")
        for code in sorted(expected - have):
            key = (name, code, "only_in_xsd")
            seen.add(key)
            if key not in KNOWN_DISCREPANCIES:
                unexpected.append(f"{name}: {code} is accepted by the XSD but missing from the list")
        print(f"{name:36} {len(have):4} codes")

    for name in sorted(PDF_ONLY):
        print(f"{name:36} {len(codes(name)):4} codes (no XSD source — PDF only)")

    for key, reason in KNOWN_DISCREPANCIES.items():
        if key not in seen:
            unexpected.append(f"declared discrepancy no longer present, remove it: {key}")
        else:
            print(f"known: {key[0]} {key[1]} — {reason}")

    # combinations.json may only name codes the lists carry.
    combinations = json.loads((ROOT / "combinations.json").read_text(encoding="utf-8"))
    types = codes("documentTypes.json")
    categories = codes("classificationCategories.json")
    e3 = codes("classificationTypes.json") | codes("vatTypes.json")
    for invoice_type, sheet in combinations["invoiceTypes"].items():
        if invoice_type not in types:
            unexpected.append(f"combinations.json: invoice type {invoice_type} is not in documentTypes.json")
        for section in sheet["sections"]:
            for side in ("income", "expenses"):
                block = section.get(side) or {}
                for correlated in block.get("correlatedInvoiceTypes", []):
                    if correlated not in types:
                        unexpected.append(f"combinations.json: {invoice_type} names unknown correlated type {correlated}")
                for category, entry in block.get("categories", {}).items():
                    if category not in categories:
                        unexpected.append(f"combinations.json: {invoice_type} {side} unknown category {category}")
                    for code in entry["types"]:
                        if code not in e3:
                            unexpected.append(f"combinations.json: {invoice_type} {side} {category} unknown type {code}")

    if unexpected:
        print("\nFAILED:")
        for line in unexpected:
            print(f"  - {line}")
        sys.exit(1)
    print(f"\nOK — every list matches the v{version} XSDs, and combinations.json names only listed codes.")


if __name__ == "__main__":
    main()

"""Builds wave-1 asset #6, "In case something happens", as two PDFs.

The File-of-Life pattern done properly (DECISIONS 198): EMS agencies across
US municipalities actively promote fridge-posted information sheets, which is
the design precedent — page 1 is written for whoever comes to help and lives
on the refrigerator; page 2 is for the adult child, and mirrors article
topic 8's "have this ready before you call" list.

No hotline or agency phone number is printed anywhere on this sheet: every
number on it is one the family writes in themselves, which keeps the asset
clear of the researcher's outstanding phone-number verifications and of the
dated-footer requirement (198, wave-2 crosswalk).

Regenerate with:

    python3 tools/printables/asset6_emergency_info.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sheetlib import BaseSheet, emit  # noqa: E402


class EmergencySheet(BaseSheet):
    title = "In case something happens"
    subject = "One page for whoever comes to help. Keep it where they'll see it."

    # Page 1 must be exactly one page: it is the artifact. Rows run a shade
    # tighter than the library default to hold the line; type size is
    # untouched, so the 198 spec is intact.
    def r(self, cells, h=26.0):
        self.row(cells, row_h=h)

    def h(self, text):
        self.heading(text, gap_before=8)

    def build(self):
        # ---- Page 1: the fridge sheet, written for the person who arrives.
        self.title_block(self.title,
                         "One page for whoever comes to help. Many families "
                         "keep it on the refrigerator.")

        self.h("Who lives here")
        self.r([("Full name", "name", 0.62), ("Born", "born", 0.38)])
        self.r([("Lives alone?", "alone", 0.35),
                ("Languages spoken", "languages", 0.65)])
        self.r([("Hearing aids, glasses, walker, memory notes", "notes", 1.0)])

        self.h("Getting in")
        self.r([("Address, with apartment and floor", "address", 1.0)])
        self.r([("Door or gate code", "code", 0.38),
                  ("Who has a key", "key", 0.62)])
        self.r([("Building, manager or front desk", "building", 0.55),
                  ("Phone", "buildingphone", 0.45)])

        self.h("Health")
        self.r([("Medical conditions", "conditions", 1.0)])
        self.r([("Allergies, and what happens", "allergies", 1.0)])
        for i in range(1, 5):
            self.r([("Medication" if i == 1 else "", "med%d" % i, 0.5),
                    ("Dose and when" if i == 1 else "", "meddose%d" % i, 0.5)],
                   h=24)
        self.r([("The full medication list is kept", "medlist", 1.0)])

        self.h("People to call")
        for i in range(1, 4):
            self.r([("Name and relationship" if i == 1 else "",
                     "contact%d" % i, 0.62),
                    ("Phone" if i == 1 else "", "contactphone%d" % i, 0.38)],
                   h=24)

        self.h("Doctor and pharmacy")
        self.r([("Doctor", "doctor", 0.62), ("Phone", "doctorphone", 0.38)])
        self.r([("Pharmacy", "pharmacy", 0.62), ("Phone", "pharmacyphone", 0.38)])

        self.h("Also good to know")
        self.r([("Pets in the home", "pets", 0.5),
                  ("Preferred hospital", "hospital", 0.5)])
        self.r([("Insurance cards and papers are kept", "insurance", 1.0)])

        # ---- Page 2: for the adult child.
        self.new_page()
        self.heading("For you, before you need it", size=15,
                     gap_before=0, gap_after=8)
        self.guidance([
            ("Fill it in while nothing is wrong.",
             "This sheet is ten minutes on a calm afternoon or an impossible "
             "job during a frightening one. Most of it your parent knows cold "
             "and you half-know, which is exactly why it belongs on paper."),
            ("Put it where someone helping would look.",
             "The refrigerator door is the convention for a reason: people "
             "who come to help are used to checking it. A drawer keeps it "
             "private and keeps it useless."),
            ("Keep a copy yourself.",
             "If you're the one making calls from far away, you'll be asked "
             "for the address, the conditions, the medications and who has a "
             "key. Reading them off your copy beats trying to remember them "
             "while frightened."),
            ("Update it when the medications change.",
             "A sheet that lists last year's medicines is worse than no sheet, "
             "because it looks current. Rewrite the health block after any "
             "hospital visit and any new prescription."),
            ("Know where the bigger papers live.",
             "This page carries what helps in the first hour. Insurance "
             "documents, legal papers and the full medical history need a "
             "home too, and the line below is for writing down where that is."),
        ])
        self.y -= 6
        self.row([("The folder with the full papers is kept", "papers", 1.0)])
        self.row([("Date filled in", "datefilled", 0.4),
                  ("Updated", "updated", 0.6)])


if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    emit(EmergencySheet,
         os.path.join(root, "site", "public", "resources", "emergency-info"),
         "emergency-info-print.pdf", "emergency-info-fillable.pdf")

"""Builds wave-1 asset #3, "Changes I've noticed", as two PDFs.

Per DECISIONS 198 this asset is not an SEO bet: it ships as the download
attached to asset #1's guidance ("the same item still true in three months"
needs somewhere to write the item down) and as the companion to asset #2's
baseline. Page 1 is the log; page 2 is what to do with a filled one.

Regenerate with:

    python3 tools/printables/asset3_changes_tracker.py
"""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from sheetlib import BaseSheet, emit  # noqa: E402


class ChangesSheet(BaseSheet):
    title = "Changes I've noticed"
    subject = "Write it down when you notice it. Read it back before you act."

    ENTRIES = 9

    def build(self):
        self.title_block(self.title,
                         "Write it down when you notice it. Read it back "
                         "before you act.")
        self.small(
            "One line per thing, dated, in plain words. \"Third time the "
            "stove was left on.\" \"Didn't come to the phone all Tuesday.\" "
            "The date matters more than it seems: it is how a feeling "
            "becomes a timeline.")
        self.y -= 4

        for i in range(1, self.ENTRIES + 1):
            self.row([("Date" if i == 1 else "", "date%d" % i, 0.22),
                      ("What I noticed" if i == 1 else "", "what%d" % i, 0.78)],
                     row_h=26)
            self.row([("Still true a month later?" if i == 1 else "",
                       "still%d" % i, 1.0)], row_h=24)
            self.y -= 4

        # Page 2: what a filled page means.
        self.new_page()
        self.heading("When the page starts to fill up", size=15,
                     gap_before=0, gap_after=8)
        self.guidance([
            ("One entry is a bad day.",
             "People forget things, skip meals and sleep badly, and always "
             "have. This sheet earns its keep on the entries that repeat, "
             "and on the ones still true when you re-read them a month on."),
            ("Compare it with normal, not with perfect.",
             "A change only means something against what your parent's "
             "days usually look like. If you haven't written that down, "
             "the normal-day sheet in this series is the place, and doing "
             "it makes this page twice as useful."),
            ("Clusters matter more than counts.",
             "Three entries about food in a month say more than five "
             "entries about five different things. When a theme shows up, "
             "that theme is the sentence to say out loud."),
            ("Take the dates to the doctor, not the worry.",
             "\"Since March: two falls she didn't mention, the stove twice, "
             "weight down\" is a history a doctor can act on. \"I'm worried "
             "about my mother\" is a feeling they can only nod at. This "
             "page, read aloud, is the first version."),
            ("Some entries mean today, not the doctor.",
             "Anything about the stove, smoke, driving, or medicine doubled "
             "up is not a watch-and-wait line. Treat those as things to fix "
             "this week, and write down what you changed."),
            ("Start a fresh page every few months.",
             "Date the old one and keep it. Two filled pages side by side "
             "answer the hardest question there is here, which is whether "
             "things are actually different or you are just frightened "
             "today."),
        ])
        self.y -= 6
        self.row([("Page started", "started", 0.4),
                  ("Page ended", "ended", 0.6)])


if __name__ == "__main__":
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    emit(ChangesSheet,
         os.path.join(root, "site", "public", "resources", "changes-tracker"),
         "changes-tracker-print.pdf", "changes-tracker-fillable.pdf")

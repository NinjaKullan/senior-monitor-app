"""Builds wave-1 asset #2, "What does a normal day look like?", as two PDFs.

House print spec, DECISIONS 198: body type 14pt, black on white, no patterned
background, left-aligned, 50-65 characters per line, US Letter with margins
generous enough that A4 auto-scaling cannot clip anything.

Page 1 is the sheet and carries no explanation, because 198 judges this asset
on whether it gets kept rather than on search traffic, and a sheet gets kept
when the useful part is the part you can see. The explanation is page 2.

Regenerate with:

    python3 tools/printables/asset2_normal_day.py

Outputs land in site/public/resources/normal-day/. If a third sheet arrives,
the page mechanics shared with asset1_okay_living_alone.py are worth lifting
into one module; with two, the duplication is cheaper than the abstraction.
"""

import os

from reportlab.lib.colors import black, white
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas as pdfcanvas

TITLE = "What does a normal day look like?"
FRAME = "Know what normal looks like. Notice when it changes."

# (heading, [row, ...]) where a row is a list of (label, key, width_share).
BLOCKS = [
    ("A normal morning", [
        [("Awake by", "awake", 0.5), ("Out of the bedroom by", "outofroom", 0.5)],
        [("Breakfast around", "breakfast", 0.5), ("First thing they do", "firstthing", 0.5)],
    ]),
    ("A normal day", [
        [("Lunch around", "lunch", 0.5), ("Naps?", "naps", 0.5)],
        [("Out of the house on", "outdays", 1.0)],
        [("Speaks to, most days", "speaksto", 1.0)],
    ]),
    ("A normal evening", [
        [("Dinner around", "dinner", 0.5), ("In bed by", "bed", 0.5)],
        [("The evening usually looks like", "evening", 1.0)],
        [("Up in the night?", "night", 1.0)],
    ]),
    ("A normal week", [
        [("Days that are different, and why", "week1", 1.0)],
        [("", "week2", 1.0)],
        [("Who comes to the house, and when", "visitors", 1.0)],
    ]),
    ("The phone", [
        [("Usually answers between", "answers", 0.5), ("Rarely during", "rarely", 0.5)],
        [("The phone lives", "phonelives", 1.0)],
    ]),
]

LAST_BLOCK_HEADING = "For them, this would not be normal"
LAST_BLOCK_PROMPT = (
    "Not \"a fall\". Things that would actually be out of character: no answer "
    "by lunchtime two days running. Missing Friday prayers. Not calling back "
    "at all."
)
LAST_BLOCK_ROWS = 4

GUIDANCE = [
    ("Fill it in on a good week.",
     "A baseline written during a bad month records the bad month. If they've "
     "just come out of hospital, wait until things have settled and write down "
     "what settled looks like."),
    ("Fill it in with them if they'll have it.",
     "Most parents are fine with this one, because it isn't a list of things "
     "they can't do any more. It's a description of their life, and they are "
     "the expert on it. If they'd rather not, fill it in from what you already "
     "know and don't make it a negotiation."),
    ("One different day is a different day.",
     "People go out, sleep badly, skip lunch. What this sheet is for is the "
     "second week of something, not the first afternoon of it."),
    ("Give it to whoever might need it.",
     "A sibling who visits twice a year, the neighbor with the spare key, "
     "whoever would answer the phone if you couldn't. The sheet is worth the "
     "paper it's on only if the person who needs to know what usual looks like "
     "has seen it."),
    ("Write the date, and rewrite it once a year.",
     "Normal moves. A baseline from three years ago will tell you something "
     "has changed when what actually changed was three years passing."),
    ("The last box does the work.",
     "Everything above it is description. Those four lines are the ones that "
     "turn \"I have a feeling something's off\" into a sentence you can act on, "
     "and the one to read first when you have that feeling."),
]

FOOTER = "heykettle.com"

PAGE_W, PAGE_H = LETTER
MARGIN_X = 90.0
MARGIN_TOP = 46.0
MARGIN_BOTTOM = 46.0
TEXT_W = PAGE_W - 2 * MARGIN_X
BODY = 14
LEAD = 17.5
GUTTER = 14.0
ROW_H = 27.0
FIELD_H = 19.0


class Sheet:
    def __init__(self, path, fillable, total_pages=None):
        self.c = pdfcanvas.Canvas(path, pagesize=LETTER)
        self.c.setTitle(TITLE)
        self.c.setAuthor("HeyKettle")
        self.c.setSubject(FRAME)
        self.fillable = fillable
        self.total_pages = total_pages
        self.y = PAGE_H - MARGIN_TOP
        self.page = 1

    def footer(self):
        self.c.setFont("Helvetica", 10)
        self.c.setFillColor(black)
        self.c.drawString(MARGIN_X, MARGIN_BOTTOM - 24, FOOTER)
        label = ("Page %d of %d" % (self.page, self.total_pages)
                 if self.total_pages else "Page %d" % self.page)
        self.c.drawRightString(PAGE_W - MARGIN_X, MARGIN_BOTTOM - 24, label)

    def new_page(self):
        self.footer()
        self.c.showPage()
        self.page += 1
        self.y = PAGE_H - MARGIN_TOP

    def need(self, amount):
        if self.y - amount < MARGIN_BOTTOM:
            self.new_page()

    def para(self, text, font="Helvetica", size=BODY, lead=LEAD):
        for line in simpleSplit(text, font, size, TEXT_W):
            self.need(lead)
            self.c.setFont(font, size)
            self.c.setFillColor(black)
            self.c.drawString(MARGIN_X, self.y - size, line)
            self.y -= lead

    def heading(self, text, size=14, gap_before=9, gap_after=2):
        self.need(gap_before + size + gap_after + ROW_H)
        self.y -= gap_before
        self.c.setFont("Helvetica-Bold", size)
        self.c.setFillColor(black)
        self.c.drawString(MARGIN_X, self.y - size, text)
        self.y -= size + gap_after

    def field(self, label, key, x, width):
        """One labelled write-on line: label above, rule or form field below."""
        if label:
            self.c.setFont("Helvetica", 10.5)
            self.c.setFillColor(black)
            self.c.drawString(x, self.y - 10.5, label)
        top = self.y - 14
        if self.fillable:
            self.c.acroForm.textfield(
                name=key, tooltip=label or key,
                x=x, y=top - FIELD_H + 4, width=width, height=FIELD_H,
                fontSize=12, borderWidth=0.5, borderColor=black,
                fillColor=white, textColor=black, forceBorder=True,
            )
        else:
            self.c.setLineWidth(0.5)
            self.c.setStrokeColor(black)
            self.c.line(x, top - FIELD_H + 4, x + width, top - FIELD_H + 4)

    def row(self, cells):
        self.need(ROW_H)
        x = MARGIN_X
        total_gutter = GUTTER * (len(cells) - 1)
        for label, key, share in cells:
            width = (TEXT_W - total_gutter) * share
            self.field(label, key, x, width)
            x += width + GUTTER
        self.y -= ROW_H

    def build(self):
        # Page 1: the sheet. Title, one line of frame, then fields only.
        self.c.setFont("Helvetica-Bold", 20)
        self.c.setFillColor(black)
        self.c.drawString(MARGIN_X, self.y - 20, TITLE)
        self.y -= 22
        self.c.setFont("Helvetica", 12)
        self.c.drawString(MARGIN_X, self.y - 12, FRAME)
        self.y -= 16

        for heading, rows in BLOCKS:
            self.heading(heading)
            for cells in rows:
                self.row(cells)

        self.heading(LAST_BLOCK_HEADING)
        self.c.setFont("Helvetica-Oblique", 10.5)
        self.c.setFillColor(black)
        for line in simpleSplit(LAST_BLOCK_PROMPT, "Helvetica-Oblique", 10.5, TEXT_W):
            self.need(12)
            self.c.drawString(MARGIN_X, self.y - 10.5, line)
            self.y -= 12
        self.y -= 3
        for i in range(LAST_BLOCK_ROWS):
            self.row([("", "notnormal_%d" % (i + 1), 1.0)])

        # Page 2: how to use it.
        self.new_page()
        self.heading("How to use this sheet", size=15, gap_before=0, gap_after=8)
        for lead, rest in GUIDANCE:
            self.need(LEAD * 3)
            self.c.setFont("Helvetica-Bold", BODY)
            self.c.setFillColor(black)
            width = self.c.stringWidth(lead, "Helvetica-Bold", BODY)
            self.c.drawString(MARGIN_X, self.y - BODY, lead)
            first = simpleSplit(rest, "Helvetica", BODY, TEXT_W - width - 5)
            if first:
                self.c.setFont("Helvetica", BODY)
                self.c.drawString(MARGIN_X + width + 5, self.y - BODY, first[0])
            self.y -= LEAD
            remainder = rest[len(first[0]):].strip() if first else rest
            if remainder:
                self.para(remainder)
            self.y -= 7

        self.y -= 10
        self.row([("Date filled in", "datefilled", 0.5)])

        self.footer()
        self.c.save()


def main():
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    out = os.path.join(root, "site", "public", "resources", "normal-day")
    os.makedirs(out, exist_ok=True)
    for fillable, name in ((False, "normal-day-print.pdf"),
                           (True, "normal-day-fillable.pdf")):
        path = os.path.join(out, name)
        counter = Sheet(os.devnull, fillable)
        counter.build()
        Sheet(path, fillable, total_pages=counter.page).build()
        print("wrote %s (%d pages, %d bytes)"
              % (name, counter.page, os.path.getsize(path)))


if __name__ == "__main__":
    main()

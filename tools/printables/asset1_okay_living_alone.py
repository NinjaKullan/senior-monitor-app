"""Builds wave-1 asset #1, "Is Mom or Dad okay living alone?", as two PDFs.

House print spec, DECISIONS 198 (from NIA's senior-friendly print guidance):
body type 14pt, black on white, no patterned background, left-aligned,
50-65 characters per line, US Letter with margins generous enough that A4
auto-scaling cannot clip anything.

Both files are generated from the CONTENT block below, so the print-only and
fillable versions can never drift apart. Regenerate with:

    python3 tools/printables/asset1_okay_living_alone.py

Outputs land in site/public/resources/okay-living-alone/.
"""

import os

from reportlab.lib.colors import black, white
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas as pdfcanvas

TITLE = "Is Mom or Dad okay living alone?"
SUBTITLE = "30 things worth noticing. A checklist for adult children."

INTRO = [
    "A list of things worth noticing, for the visit where everything looks "
    "fine and you still drive home uneasy. There's no score at the bottom.",
    "Answer for how things are now compared with a year ago. One check mark "
    "means nothing on its own. Three or four in the same section is worth a "
    "conversation, with them or with their doctor. Fill it in afterwards, "
    "not in front of them.",
]

SECTIONS = [
    ("Food and the kitchen", [
        "There's food gone bad in the fridge, or very little food in it at all.",
        "They're eating the same one or two simple things every day.",
        "Pans, the stove or the microwave show signs of something burned.",
        "They've lost or gained noticeable weight since you last saw them.",
        "Cooking has quietly stopped, and it used to be something they did.",
    ]),
    ("The house", [
        "Dishes, laundry or trash are piling up in a way they never used to.",
        "Something has been broken for months and nobody has fixed it.",
        "There are rugs, cords or piles in the walking routes through the house.",
        "There's nothing to hold on to in the bathroom.",
        "The route from the bed to the bathroom is dark at night.",
    ]),
    ("Medicines", [
        "There's no one place where all the medicines live.",
        "You find pills loose on counters, tables or the floor.",
        "They can't tell you what one of their medicines is for.",
        "Bottles are running out much faster or much slower than they should.",
        "Nobody outside the house has a current list of what they take.",
    ]),
    ("Getting around", [
        "They hold on to furniture or walls to cross a room.",
        "They've had a fall, or you think they've had one they didn't mention.",
        "Stairs, the tub, or getting out of a chair have become an event.",
        "There are bruises they explain vaguely, or don't explain at all.",
        "They've stopped going somewhere they always went.",
    ]),
    ("Money and mail", [
        "Unopened mail is stacking up.",
        "Bills have gone unpaid, or been paid twice.",
        "There are charges, subscriptions or gifts you can't account for.",
        "Someone new is calling or visiting often, and money is involved.",
        "They're vague or defensive about money in a way they never used to be.",
    ]),
    ("How they seem, and reaching them", [
        "They repeat the same question or story inside one conversation.",
        "They've been unsure what day or date it is more than once.",
        "They've dropped a hobby, a group, or the friends they used to see.",
        "They seem flat, anxious, or angrier than is usual for them.",
        "You often can't reach them, and there's nobody nearby you could ask "
        "to go and knock on the door.",
    ]),
]

CLOSING = [
    ("One check mark is noise.",
     "People have bad weeks. What matters is a cluster in one section, or the "
     "same item still true in three months."),
    ("Take the specifics to their doctor, not the conclusion.",
     "\"She's had two falls she didn't tell me about and she's lost weight "
     "since March\" gets further than \"I'm worried about my mother.\" A "
     "doctor can also say the thing you can't say without it becoming a fight."),
    ("Fix the physical things first.",
     "A light on the landing, a bar in the bathroom, the rug that's been "
     "curling for a decade. Nobody argues about a light bulb, and these are "
     "the items here that are cheapest to close."),
    ("Number 30 is the one people skip.",
     "Being unreachable is not a small thing when there's nobody within "
     "twenty minutes of the front door. If that line is checked and you have "
     "no name to call, that's the first gap to close, before any of the others."),
]

CONTACTS_HEADING = "If you can't reach them"
CONTACTS_INTRO = (
    "Item 30 is the one worth closing today, and it takes ten minutes. "
    "Write down who lives close enough to walk to the door, and ask them "
    "first so the name on this line is a name that has agreed to it."
)
CONTACT_ROWS = [
    ("A neighbor", "neighbor"),
    ("Someone in the family who lives nearby", "family"),
    ("Their building, manager or front desk", "building"),
    ("Their doctor", "doctor"),
]

FOOTER = "heykettle.com"

PAGE_W, PAGE_H = LETTER
MARGIN_X = 90.0          # keeps lines at roughly 60 characters at 14pt
MARGIN_TOP = 54.0
MARGIN_BOTTOM = 54.0
TEXT_W = PAGE_W - 2 * MARGIN_X
BODY = 14
LEAD = 17.5
BOX = 12.5
INDENT = BOX + 4         # text column for checklist items


class Sheet:
    def __init__(self, path, fillable, total_pages=None):
        self.c = pdfcanvas.Canvas(path, pagesize=LETTER)
        self.c.setTitle(TITLE)
        self.c.setAuthor("HeyKettle")
        self.c.setSubject(SUBTITLE)
        try:
            self.c.setLanguage("en-US")   # document language, for readers
        except AttributeError:
            pass
        self.fillable = fillable
        self.y = PAGE_H - MARGIN_TOP
        self.page = 1
        self.n = 0
        self.total_pages = total_pages

    def space(self, amount):
        self.y -= amount

    def need(self, amount):
        if self.y - amount < MARGIN_BOTTOM:
            self.new_page()

    def new_page(self):
        self.footer()
        self.c.showPage()
        self.page += 1
        self.y = PAGE_H - MARGIN_TOP

    def footer(self):
        self.c.setFont("Helvetica", 10)
        self.c.setFillColor(black)
        self.c.drawString(MARGIN_X, MARGIN_BOTTOM - 24, FOOTER)
        if self.total_pages:
            label = "Page %d of %d" % (self.page, self.total_pages)
        else:
            label = "Page %d" % self.page
        self.c.drawRightString(PAGE_W - MARGIN_X, MARGIN_BOTTOM - 24, label)

    def para(self, text, font="Helvetica", size=BODY, lead=LEAD, indent=0.0):
        width = TEXT_W - indent
        for line in simpleSplit(text, font, size, width):
            self.need(lead)
            self.c.setFont(font, size)
            self.c.setFillColor(black)
            self.c.drawString(MARGIN_X + indent, self.y - size, line)
            self.y -= lead

    def heading(self, text, size, gap_before, gap_after, font="Helvetica-Bold"):
        self.need(gap_before + size + gap_after + LEAD)
        self.y -= gap_before
        self.c.setFont(font, size)
        self.c.setFillColor(black)
        self.c.drawString(MARGIN_X, self.y - size, text)
        self.y -= size + gap_after

    def item(self, text):
        lines = simpleSplit(text, "Helvetica", BODY, TEXT_W - INDENT - 20)
        block = max(LEAD * len(lines), BOX + 4)
        self.need(block + 1.5)
        self.n += 1
        top = self.y
        self.c.setFont("Helvetica", 11)
        self.c.setFillColor(black)
        self.c.drawRightString(MARGIN_X + INDENT + 14, top - BODY, "%d." % self.n)
        box_y = top - BODY - 1
        if self.fillable:
            self.c.acroForm.checkbox(
                name="item_%02d" % self.n,
                tooltip=text,
                x=MARGIN_X, y=box_y, size=BOX,
                buttonStyle="check", borderWidth=1,
                borderColor=black, fillColor=white, textColor=black,
                forceBorder=True,
            )
        else:
            self.c.setLineWidth(1)
            self.c.setStrokeColor(black)
            self.c.rect(MARGIN_X, box_y, BOX, BOX, stroke=1, fill=0)
        for i, line in enumerate(lines):
            self.c.setFont("Helvetica", BODY)
            self.c.drawString(MARGIN_X + INDENT + 20, top - BODY - i * LEAD, line)
        self.y = top - block - 1.5

    def notes(self, key):
        height = 132 if self.fillable else 110
        self.need(height + 22)
        self.space(6)
        self.c.setFont("Helvetica-Bold", 12)
        self.c.setFillColor(black)
        self.c.drawString(MARGIN_X, self.y - 12, "Anything else you noticed")
        self.y -= 18
        if self.fillable:
            self.c.acroForm.textfield(
                name="notes_%s" % key, tooltip="Notes",
                x=MARGIN_X, y=self.y - height, width=TEXT_W, height=height,
                fontSize=12, borderWidth=0.5, borderColor=black,
                fillColor=white, textColor=black, forceBorder=True,
                fieldFlags="multiline",
            )
            self.y -= height + 10
        else:
            self.c.setLineWidth(0.5)
            self.c.setStrokeColor(black)
            for _ in range(5):
                self.y -= 22
                self.c.line(MARGIN_X, self.y, MARGIN_X + TEXT_W, self.y)
            self.y -= 10

    def contacts(self):
        self.heading(CONTACTS_HEADING, 15, 14, 6)
        self.para(CONTACTS_INTRO)
        self.space(10)
        label_w = 250.0
        for label, key in CONTACT_ROWS:
            self.need(52)
            self.c.setFont("Helvetica", 12)
            self.c.setFillColor(black)
            self.c.drawString(MARGIN_X, self.y - 12, label)
            self.y -= 17
            if self.fillable:
                self.c.acroForm.textfield(
                    name="contact_%s_name" % key, tooltip="%s: name" % label,
                    x=MARGIN_X, y=self.y - 20, width=label_w, height=20,
                    fontSize=12, borderWidth=0.5, borderColor=black,
                    fillColor=white, textColor=black, forceBorder=True,
                )
                self.c.acroForm.textfield(
                    name="contact_%s_phone" % key, tooltip="%s: phone" % label,
                    x=MARGIN_X + label_w + 12, y=self.y - 20,
                    width=TEXT_W - label_w - 12, height=20,
                    fontSize=12, borderWidth=0.5, borderColor=black,
                    fillColor=white, textColor=black, forceBorder=True,
                )
            else:
                self.c.setLineWidth(0.5)
                self.c.setStrokeColor(black)
                self.c.line(MARGIN_X, self.y - 20, MARGIN_X + label_w, self.y - 20)
                self.c.line(MARGIN_X + label_w + 12, self.y - 20,
                            MARGIN_X + TEXT_W, self.y - 20)
                self.c.setFont("Helvetica", 9)
                self.c.drawString(MARGIN_X, self.y - 30, "Name")
                self.c.drawString(MARGIN_X + label_w + 12, self.y - 30, "Phone")
            self.y -= 38 if self.fillable else 48

    def build(self):
        self.c.setFont("Helvetica-Bold", 21)
        self.c.setFillColor(black)
        self.c.drawString(MARGIN_X, self.y - 21, TITLE)
        self.y -= 28
        self.c.setFont("Helvetica", 12)
        self.c.drawString(MARGIN_X, self.y - 12, SUBTITLE)
        self.y -= 22
        for p in INTRO:
            self.para(p)
            self.space(6)
        self.space(2)
        for title, items in SECTIONS:
            self.need(15 + 9 + 5 + LEAD * 4)   # heading plus two items, minimum
            self.heading(title, 15, 9, 5)
            for text in items:
                self.item(text)
            self.space(4)
        self.notes("general")
        # the guidance always starts a fresh page: it is the sheet people keep
        # after the checklist itself has been filled in
        self.new_page()
        self.heading("What to do with this", 15, 0, 8)
        for lead, rest in CLOSING:
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
            self.space(6)
        self.contacts()
        self.footer()
        self.c.save()


def main():
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    out = os.path.join(root, "site", "public", "resources", "okay-living-alone")
    os.makedirs(out, exist_ok=True)
    for fillable, name in ((False, "okay-living-alone-checklist-print.pdf"),
                           (True, "okay-living-alone-checklist-fillable.pdf")):
        path = os.path.join(out, name)
        # dry run first, purely to learn the page count for the footer
        counter = Sheet(os.devnull, fillable)
        counter.build()
        Sheet(path, fillable, total_pages=counter.page).build()
        print("wrote %s (%d pages, %d bytes)"
              % (name, counter.page, os.path.getsize(path)))


if __name__ == "__main__":
    main()

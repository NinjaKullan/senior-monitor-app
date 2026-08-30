"""Shared page mechanics for the wave-1 printables (DECISIONS 198 print spec).

Extracted when the third sheet arrived, per the note in
asset2_normal_day.py: with two sheets the duplication was cheaper than the
abstraction, with three it stopped being. asset1 and asset2 still carry
their own copies so their approved PDFs stay byte-stable; fold them in the
next time either one's copy changes anyway.

The spec, from NIA's senior-friendly print guidance as adopted in 198:
body type 14pt, black on white, no patterned backgrounds, left-aligned,
50-65 character lines, US Letter with margins generous enough that A4
auto-scaling cannot clip anything.
"""

import os

from reportlab.lib.colors import black, white
from reportlab.lib.pagesizes import LETTER
from reportlab.lib.utils import simpleSplit
from reportlab.pdfgen import canvas as pdfcanvas

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
FOOTER = "heykettle.com"


class BaseSheet:
    """One printable, rendered twice: ruled lines, or AcroForm fields."""

    title = ""
    subject = ""

    def __init__(self, path, fillable, total_pages=None):
        self.c = pdfcanvas.Canvas(path, pagesize=LETTER)
        self.c.setTitle(self.title)
        self.c.setAuthor("HeyKettle")
        self.c.setSubject(self.subject)
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

    def title_block(self, title, frame):
        self.c.setFont("Helvetica-Bold", 20)
        self.c.setFillColor(black)
        self.c.drawString(MARGIN_X, self.y - 20, title)
        self.y -= 22
        if frame:
            self.c.setFont("Helvetica", 12)
            self.c.drawString(MARGIN_X, self.y - 12, frame)
            self.y -= 16

    def para(self, text, font="Helvetica", size=BODY, lead=LEAD):
        for line in simpleSplit(text, font, size, TEXT_W):
            self.need(lead)
            self.c.setFont(font, size)
            self.c.setFillColor(black)
            self.c.drawString(MARGIN_X, self.y - size, line)
            self.y -= lead

    def small(self, text, gap=12):
        """An italic prompt under a heading, 10.5pt."""
        self.c.setFillColor(black)
        for line in simpleSplit(text, "Helvetica-Oblique", 10.5, TEXT_W):
            self.need(gap)
            self.c.setFont("Helvetica-Oblique", 10.5)
            self.c.drawString(MARGIN_X, self.y - 10.5, line)
            self.y -= gap
        self.y -= 3

    def heading(self, text, size=14, gap_before=9, gap_after=2):
        self.need(gap_before + size + gap_after + ROW_H)
        self.y -= gap_before
        self.c.setFont("Helvetica-Bold", size)
        self.c.setFillColor(black)
        self.c.drawString(MARGIN_X, self.y - size, text)
        self.y -= size + gap_after

    def field(self, label, key, x, width):
        """One write-on line, inline form style: the label sits at the left
        and the rule (or form field) runs from its end to the cell's edge,
        on the same baseline. Denser than label-above-line, and it cannot
        collide with the row above at any row height."""
        baseline = self.y - 15
        lw = 0.0
        if label:
            self.c.setFont("Helvetica", 10.5)
            self.c.setFillColor(black)
            self.c.drawString(x, baseline, label)
            lw = self.c.stringWidth(label, "Helvetica", 10.5) + 7
        if self.fillable:
            self.c.acroForm.textfield(
                name=key, tooltip=label or key,
                x=x + lw, y=baseline - 5, width=width - lw, height=FIELD_H,
                fontSize=11, borderWidth=0.5, borderColor=black,
                fillColor=white, textColor=black, forceBorder=True,
            )
        else:
            self.c.setLineWidth(0.5)
            self.c.setStrokeColor(black)
            self.c.line(x + lw, baseline - 2, x + width, baseline - 2)

    def row(self, cells, row_h=ROW_H):
        """cells: [(label, key, width_share), ...] sharing one line."""
        self.need(row_h)
        x = MARGIN_X
        total_gutter = GUTTER * (len(cells) - 1)
        for label, key, share in cells:
            width = (TEXT_W - total_gutter) * share
            self.field(label, key, x, width)
            x += width + GUTTER
        self.y -= row_h

    def guidance(self, items, gap_after=7):
        """Bold-lead paragraphs, the asset-1 'what to do with this' shape."""
        for lead, rest in items:
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
            self.y -= gap_after

    def build(self):
        raise NotImplementedError

    def finish(self):
        self.footer()
        self.c.save()


def emit(sheet_cls, out_dir, print_name, fillable_name):
    """Render both versions, dry-running first to learn the page count."""
    os.makedirs(out_dir, exist_ok=True)
    for fillable, name in ((False, print_name), (True, fillable_name)):
        path = os.path.join(out_dir, name)
        counter = sheet_cls(os.devnull, fillable)
        counter.build()
        counter.c.save()
        final = sheet_cls(path, fillable, total_pages=counter.page)
        final.build()
        final.finish()
        print("wrote %s (%d pages, %d bytes)"
              % (name, counter.page, os.path.getsize(path)))

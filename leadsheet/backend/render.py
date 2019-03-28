import logging
import os
import re
from io import StringIO

from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import cm
from reportlab.platypus.doctemplate import LayoutError

from svglib.svglib import svg2rlg

import settings
# from leadsheet.common import db

logger = logging.getLogger(__name__)


class PageBreakError(Exception):
    pass


class TooMuchContentError(Exception):
    pass


class SinglePageDocTemplate(SimpleDocTemplate):
    # def handle_pageBreak(self, slow=None):
    #     raise PageBreakError
    pass

class Page(object):
    """
    Base class for parsing a JSON document into a songbook page.
    """

    def __init__(self, jdoc):
        self.jdoc = jdoc
        self.page_style = getSampleStyleSheet()
        # self.page_style = page_style.update(settings.DEFAULT_STYLE)
        self.doc = SinglePageDocTemplate('../examples/example_song.pdf')
        self.story = []

    def _build(self):
        raise NotImplementedError

    def _add_title(self):
        self.story.append(Paragraph(
            text=self.jdoc['title'], style=self.page_style['Heading1']
        ))

    def _add_body(self):
        if self.__class__.__name__ == 'Song':
            # Try to fit everything on one page, using these strategies:
            # - Explicitly copy any repeats, and full size diagrams and text.
            # - Remove repeated sections and reference them
            # - Reduce font size in .5pt increments from 12pt to 10pt
            # - Reduce diagram size in 10% increments to 70%
            # - Fail

            strategy = {
                'repeat': 'explicit',
                'font_size': 12,
                'diagram_size': 1.0,
            }

            repeats = ['explicit', 'implicit']
            font_sizes = [12, 11.5, 11, 10.5, 10]
            diagram_sizes = [1.0, .9, .8, .7]

            success = 'Succeeded with strategy {}'
            failure = 'Failed with strategy {}'

            for repeat in repeats:
                strategy.update(repeat=repeat)
                if self._attempt_song_body(strategy):
                    print(success.format(strategy))
                    return
                else:
                    print(failure.format(strategy))

            for font_size in font_sizes:
                strategy.update(font_size=font_size)
                if self._attempt_song_body(strategy):
                    print(success.format(strategy))
                    return
                else:
                    print(failure.format(strategy))

            for diagram_size in diagram_sizes:
                strategy.update(diagram_size=diagram_size)
                if self._attempt_song_body(strategy):
                    print(success.format(strategy))
                    return
                else:
                    print(failure.format(strategy))

            raise TooMuchContentError

    def _attempt_song_body(self, strategy):
        old_story = self.story.copy()

        try:
            self._add_song_body(strategy)
            # doc.build consumes story, so use a copy to test the build
            story_copy = self.story.copy()
            self.doc.build(story_copy)
            print(self.story)
            return True
        except (PageBreakError, LayoutError):
            # Too many pages, revert to old
            self.story = old_story
            return False

    def _add_song_body(self, strategy):
        body = self.jdoc['body']
        sections = {
            name: section
            for name, section in zip(body['names'], body['sections'])
        }
        for index, entry in enumerate(body['order']):
            entry_story = []
            text = ''

            # Determine how to handle this entry if it is to be/has been
            # repeated
            is_a_repeat_section = (
                strategy['repeat'] == 'implicit'
                and not entry.isdigit()
            )
            repeat_initialised = entry in body['order'][:index]

            # Name and fill the first instance of an implicitly repeated
            # section.
            if is_a_repeat_section and not repeat_initialised:
                text += '<b>[{}]</b>\n'.format(entry)
                text += sections[entry]

            # Just reference the name of the entry if it has already been
            # intialised
            elif is_a_repeat_section and repeat_initialised:
                text += '<b>[{}]</b>\n'.format(entry)

            # If not a repeated section, just add the text
            else:
                text += sections[entry]

            for line in text.split('\n'):
                if line:
                    # Look for chords and bold them
                    for chord in re.findall(r'\(.*\)', line):
                        line = line.replace(
                            chord, '<b>{}</b>'.format(chord)
                        )
                    entry_story.append(Paragraph(
                        text=line, style=self.page_style['Normal']
                    ))
                else:
                    entry_story.append(Spacer(1, 0.2 * cm))
            entry_story.append(Spacer(1, 0.2 * cm))

            if is_a_repeat_section and not repeat_initialised:
                self.story.append(Table(
                    data=[[entry_story]],
                    style=[('BOX', (0, 0), (0, 0), 1, colors.black)]
                ))
                self.story.append(Spacer(1, 0.2 * cm))
            else:
                self.story += entry_story

    def render_pdf(self):
        self._build()
        print(self.story)
        self.doc.build(self.story)


class FrontCoverPage(Page):
    pass


class FrontInner(Page):
    pass


class PrimaryContentsPage(Page):
    pass


class SecondaryContentsPage(Page):
    pass


class Song(Page):
    def _build(self):
        self._add_title()
        self._add_body()


class BackInner(Page):
    pass


class BackCover:
    pass


# class Book(object):
#     """A songbook"""
#     pages = []
#     for uuid in uuids:
#         db.fetch(uuid=uuid)
#         page = create_page(**kwargs)
#         pages.append(page)
#
#     generate_contents(pages)

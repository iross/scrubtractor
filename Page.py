"""
Page.py
"Page" class modules for GeoDeepDive.
Should contain:
    Location of PDF/PNG on disk
    Location of OCR output on disk (txt)
    Location of OCR output on disk (hOCR)
Should have methods to:
    remove leading/trailing newlines
    "pop" repeated text from the object (and call remove leading/trailing newlines)
        Should also be able to handle case where a string is in the middle of two blank lines, e.g. when page numbers are under the left column and thus appear in the 'middle' of the OCRed text
    clean_newlines -> get rid of "\n\n\n\n" junk
    detect_line_gaps -> detect situations where a sentence is spread across lines but has a blank line between
    find_captions -> Extract [\nFig.*\n, \nTable.*\n] type things (maybe John's thing does this already?)
    table/figure extraction (may require document-level stuff as well.)
"""

class Document(object):

    """TODO"""

    def __init__(self):
        """TODO: to be defined1. """



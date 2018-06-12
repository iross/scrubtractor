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
from difflib import SequenceMatcher
import re
import codecs

class Page(object):

    """TODO"""

    def __init__(self, filepath, parent_document, page_index, *args, **kwargs):
        """
        self.page = ["The lines", "on the page", "which get read in here", "but could probably be done cleverly without reading into memory if I want/need"]
        """
        for key, val in kwargs.items():
            setattr(self, key, val)

        self.Document = parent_document # need access to the document's found headers, etc.
        self.filepath = {} # hocr, txt, png, pdf
        self.filepath["txt"] = filepath

        with codecs.open(self.filepath["txt"], 'r', 'utf-8') as fin:
            clean_page = []
            temp_page = fin.read().split("\n")
            non_empty_lines = [i for i, val in enumerate(temp_page) if (val != "" and val != "\n")]
            if non_empty_lines == []:
                clean_page = ['']
            else:
                try:
                    clean_page = (temp_page[non_empty_lines[0]:non_empty_lines[-1]+1])
                except:
                    import pdb; pdb.set_trace()
            self.page = clean_page

        self.page_index = page_index

        # get stuff from the Document and store it locally just because it's easier that way.
        self.expected_page_no = self.Document.expected_pagenumbers[self.page_index]
        self.found_page_no = self.Document.expected_pagenumbers[self.page_index]

    def get_firsttwo(self, footer_mode):
        """
        TODO: Docstring for get_firstwo.

        Args:
            footer_mode (TODO): TODO

        Returns: TODO

        """
        LINES = 8
        thesetwo = list()
        thesepagenos = list()
        linesaccepted = 0

        if footer_mode:
            lines_it = reversed(list(enumerate(self.page))) # gross..
        else:
            lines_it = enumerate(self.page)
        for idx, line in lines_it:

            if not footer_mode and idx > LINES:
                break
            elif footer_mode and idx < len(self.page) - LINES:
                break

            line = line.strip()
            if line.startswith('<') and line.endswith('>'):
                continue

            thesepagenos += [int(i.group(1)) for i in re.finditer(r'(\d+)', line)]

            line = "".join([x for x in line if not x.isdigit()])
            # We strip all numeric chars before the length check.

            # That may not get all roman numerals, because of OCR junk, so let's
            # attempt to get them by shrinking them below the length limit. This
            # will also have the collateral benefit of reducing the edit distance
            # for headers that contain roman numerals.
            line = line.replace("iii", "")
            line = line.replace("ii", "")
            line = line.replace("xx", "")

            if len(line) < 5:
                continue

            linesaccepted += 1
            thesetwo.append((line, idx))

            if linesaccepted >= 2:
                break

        return thesetwo, thesepagenos

    def cleanup(self, mode):
        """
        TODO: Docstring for remove_headers.

        Args:
            footer_mode (TODO): TODO

        Returns: TODO
        """

        LINES = 8

        valid_modes = ["header", "footer", "full_page"]
        if mode not in valid_modes:
            print("Invalid scan mode supplied! Choose one of (%s)" % (valid_modes))
        if mode == "header":
            lines = range(min(LINES, len(self.page)))
        elif mode == "footer":
            lines = range(max(0, len(self.page) - 1 - LINES), len(self.page))
        elif mode == "full_page":
            lines = range(1, len(self.page)-1)

        # remove pagenumbers based on string matching
        ignore_lines = []
        for i in lines:
            if mode == "full_page": # only check for similarity if the string is isolated
                if self.page[i-1] != "" or self.page[i+1] != "":
                    continue

            # loop over known headers, remove any any similar strings
            for rep in self.Document.repeated_phrases:
                rep = str(rep)
                try:
                    seq = SequenceMatcher(None, rep, self.page[i])
                except IndexError:
                    print(i)
                if seq.ratio() > 0.8:
                    ignore_lines.append(i)
            # remove any instance of the expected self.page number
            self.page[i] = self.page[i].replace(str(self.expected_page_no), "")

        cleaned_page = [val for i, val in enumerate(self.page) if i not in ignore_lines]
        non_empty_lines = [i for i, val in enumerate(cleaned_page) if re.match(r"^\s?$", val) is None]
        if non_empty_lines == []:
            cleaned_page = ['']
        else:
            cleaned_page = cleaned_page[non_empty_lines[0]:non_empty_lines[-1]+1]

        self.page = cleaned_page

    def remove_empties(self):
        """
        TODO: Docstring for remove_empties_page.

        Args:
            page (TODO): TODO

        Returns: TODO

        """
        temp = []
        ignore_lines = []
        for i in range(len(self.page)-1):
            if i in ignore_lines:
                continue
            if i+2 < len(self.page): # look forward -- if the next line looks like it's breaking a sentence, skip it on next iteration
                if self.page[i] != '' and self.page[i+1] == '' and self.page[i+2] != '' and not self.page[i].endswith('.') and self.page[i+2][0].islower():
                    ignore_lines.append(i+1)
            if not (self.page[i] == '' and self.page[i+1] == ''): # eliminate chains of ''
                temp.append(self.page[i])
        temp.append(self.page[-1])
        self.page = temp

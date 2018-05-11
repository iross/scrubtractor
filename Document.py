#!/usr/bin/env python3
# encoding: utf-8

"""
Document.py
"Document" class modules for GeoDeepDive.
Should contain:
    Metadata
    Page objects
Should have methods to:
    Apply normalization via DataMunging rules
    find_page_numbers
    find_headers
    find_footers
    remove_headers
    remove_footers
"""
from difflib import SequenceMatcher
import glob
import re
import sys
import signal
import shutil
import os
from os import path
import datetime
import subprocess
import codecs
from Page import Page

def call(cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=300):
    proc = subprocess.Popen(cmd, stdout=stdout, stderr=stderr, shell=True, preexec_fn=os.setsid)
    try:
        outs, errs = proc.communicate(timeout=timeout)
        print("OK", str(outs), str(errs), "finished at %s" % datetime.datetime.now())
        return 0, outs, errs
    except subprocess.TimeoutExpired:
        print("Process timed out at %s! cmd:" % datetime.datetime.now())
        print("\t%s" % cmd)
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        return 1, None, None


class Document(object):
    """

    TODO

    """

    def __init__(self, pdf_path = None, page_files = None, *args, **kwargs):
        self.pdf_path = pdf_path
        self.page_files = page_files

        for key, val in kwargs.items():
            setattr(self, key, val)

        if self.pdf_path is not None:
            code, outs, errs = call("gs -q -dNODISPLAY -c \"(%s) (r) file runpdfbegin pdfpagecount = quit\"" % self.pdf_path)
            try:
                self.number_of_pages = int(outs)
            except ValueError as e:
                print("ERROR\t Could not get number of pages. Possible document is not a PDF!")

        if self.page_files is not None:
            self.prep_pagefiles()
        else:
            self.page_files = []

        self.expected_page_numbers = [None]*len(self.page_files)

        if not hasattr(self, "working_dir"):
            self.working_dir = "./"

        self.repeated_phrases = set()
        if not self.working_dir.endswith("/"):
            self.working_dir += "/"

        self.working_dir = "/output/%s" % self.working_dir
        shutil.rmtree(self.working_dir + 'ocr_tmp', True)
        shutil.rmtree(self.working_dir + 'ocr', True)
        try:
            if not path.exists(self.working_dir):
                os.mkdir(self.working_dir)
            if not path.exists(self.working_dir + 'ocr_tmp'):
                os.mkdir(self.working_dir + 'ocr_tmp')
            if not path.exists(self.working_dir + 'ocr'):
                os.mkdir(self.working_dir + 'ocr')
        except OSError as ex:
            print("ERROR\tCould not create ocr_tmp folder")
            raise ex

    def __del__(self):
        # cleanup, etc
        shutil.rmtree(self.working_dir + 'ocr_tmp', True)

    def prep_pagefiles(self):
        """
        TODO
        """
        self.page_files = sorted(self.page_files,
                key=lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split('(\d+)', s)])
        self.repeated = list()
        self.found_pagenumbers = list()
        self.page_list = []
        for i, page_filepath in enumerate(self.page_files):
            self.repeated.append(set())
            self.found_pagenumbers.append(None)
            self.page_list.append(Page(page_filepath, self, i))

    def find_headers(self, footer_mode = False):
        '''
        Identifies repeated page headers and removes them from
        the pages; then returns the edited pagelist.


        Shamelessly poached, dismantled, and hacked to bits from
            https://github.com/tedunderwood/DataMunging

        # HeaderFinder.py
        #
        # Scans a list of pages for running headers, which we understand as lines, near
        # the top of a page, that are repeated within the space of two pages,
        # in either direction. The two-page window is necessary because headers
        # are sometimes restricted to recto or verso. A very common pattern
        # involves different, alternating recto and verso headers. We also use
        # fuzzy matching to allow for OCR errors and other minor variation (e.g.
        # page numbers that may be roman numerals).
        #
        # Once headers are identified, they can be treated in a range of different
        # ways. The first of these functions is not concerned to *separate* the header
        # from the original text but only to identify it so that it can be given extra
        # weight in page classification. The second function actually removes them.

        # In principle, this could all be done for footers as well. I haven't cared, because
        # it wasn't a big problem in the 19c volumes I've worked with so far. That
        # could change!
        '''

        # For very short documents, this is not a meaningful task.

        if len(self.page_list) < 5:
            return self.page_list

        firsttwos = list()
        potential_pagenumbers = list()
        # We construct a list of the first two substantial lines on
        # each page. We ignore short lines and lines that are just numbers,
        # and don't go deeper than five lines in any event.

        # We transform lines in this process -- e.g, by removing digits.
        # We also package them as tuples in order to preserve information
        # that will allow us to delete the lines identified as repeats.

        LINES = 8
        SIMILARITY_CUTOFF = 0.7
        for page in self.page_list:
            thesetwo, thesepagenos = page.get_firsttwo(footer_mode)
            firsttwos.append(thesetwo)
            potential_pagenumbers.append(thesepagenos)

        # Now our task is to iterate through the firsttwos, identifying lines that
        # repeat within a window, which we define as "this page and the two previous
        # pages."

        # We're going to do this with a list of sets. That way we can add things
        # without risk of duplication. Otherwise, when we add headers to previous
        # pages, we're always going to be checking whether they were already added.

        for index in range(2, len(firsttwos)):
            # We can be sure the 2 index is legal because we have previously filtered
            # short documents.

            indexedlines = firsttwos[index]

            for j in range (index - 2, index):

                previouslines = firsttwos[j]

                for lineA in indexedlines:
                    for lineB in previouslines:
                        s = SequenceMatcher(None, lineA[0], lineB[0])
                        # The zero indexes above are just selecting the string part
                        # of a string, index tuple.

                        similarity = s.ratio()
                        if similarity > .8:
                            self.repeated[index].add(lineA)
                            self.repeated[j].add(lineB) #TODO Hmm... why isn't this catching the author's name on page 2 (index 1)?
                            self.repeated_phrases.add(lineA[0])
                            self.repeated_phrases.add(lineB[0])

        # Now we have a list of sets that contain tuples
        # representing headers, in original page order, with empty sets where no headers
        # were found. We can now use the line indexes in the tuples to pop out the
        # relevant lines.

        #cleanup potential page numbers
        # for each potential page number, build the 'expected' list based on the doc's len(pages)
        # compare the expected list to observed and keep any potential number with significant overlap
        observed = set(y for x in potential_pagenumbers for y in x)
        for i, page in enumerate(potential_pagenumbers):
            for pageno in page:
                expected = set(range(pageno - i, pageno - i + len(potential_pagenumbers)))
                if float(len(expected.intersection(observed)))/len(potential_pagenumbers) > SIMILARITY_CUTOFF:
                    self.found_pagenumbers[i] = pageno

    def predict_pagenumbers(self):
        """
        TODO

        Returns: TODO

        """
        print("Found page numbers: %s" % self.found_pagenumbers)
        if all(i is None for i in self.found_pagenumbers):
            for i in range(len(self.page_list)):
                self.page_list[i].expected_page_no = None
        else:
            start, val = next((i, val) for i, val in enumerate(self.found_pagenumbers) if val is not None)
            self.expected_pagenumbers = range(val-start, val + len(self.found_pagenumbers) - start)
            for i, page in enumerate(self.page_list):
                self.page_list[i].expected_page_no = self.expected_pagenumbers[i]

    def remove_headers(self, mode):
        """
        TODO: Docstring for remove_headers.

        Args:
            footer_mode (TODO): TODO

        Returns: TODO
        """
        for page in self.page_list:
            page.cleanup(mode)

    def mid_page_cleanup(self):
        """
        TODO: Docstring for mid_page_cleanup.
        Returns: TODO

        """
        for page in self.page_list:
            page.cleanup(mode="full_page")

    def remove_empties(self):
        """
        TODO: Docstring for remove_empties.
        Returns: TODO

        """
        for page in self.page_list:
            page.remove_empties()

    def find_sections(self):
        """
        TODO: Docstring for find_sections.
        Returns: TODO

        """
        pass

    def ocr(self, cleanup = True):
        """
        Run OCR on the document.
        Returns: 0 if all pages successful, else 1

        """
        check = True
        for i in range(1,self.number_of_pages + 1):
            pagecheck, _, _ = call("gs -dFirstPage=%(page)s -dLastPage=%(page)s -dBATCH -dNOPAUSE -sDEVICE=png16m -dGraphicsAlphaBits=4 -dTextAlphaBits=4 -r600 -sOutputFile='%(working_dir)s/ocr_tmp/page-%(page)d.png' '%(input)s'" % {"working_dir" : self.working_dir, "page" : i, "input": self.pdf_path})
            tesscheck, _, _ = call("tesseract %(working_dir)s/ocr_tmp/page-%(page)s.png %(working_dir)s/ocr/page_%(page)s -l eng --psm 1 --oem 2 txt hocr" % {"working_dir" : self.working_dir,  "page" : i})
            if tesscheck == 0:
                self.page_files.append(self.working_dir + "/ocr/page_%(page)s.txt" %{"page" : i})
            check = check and pagecheck and tesscheck
        return check

def main():
    # ASSUME: This is going to be run _within_ the docker container that has gs, tesseract, etc installed
    if len(sys.argv) == 1:
        input_dir = os.getcwd() + "/input/"
    else:
        input_dir = path.abspath(sys.argv[1])
    print("Looking for PDFs in %s" % input_dir)
    for document_path in glob.glob(input_dir +"/*.pdf"):
        document = Document(pdf_path = document_path, working_dir = path.basename(document_path).replace(".pdf", ""))

        # TODO: parse options
        # TODO: run only those options

        document.ocr()
        document.prep_pagefiles()


        # cleanup headers/footers
        document.find_headers(footer_mode = True)
        document.find_headers(footer_mode = False)
        document.predict_pagenumbers() # requires found_pagenumbers, so should be after the find_headers calls
        document.remove_headers(mode = "footer")
        document.remove_headers(mode = "header")
        document.mid_page_cleanup() # keys in on blank lines, so needs to be _before_ remove_empties
        document.remove_empties()



        # TODO: incorporate the desired subset of the datamunging cleanup/spellchecker stuff

        document.text = ""
        for i, filename in enumerate(document.page_files):
            # TODO: one more pass? Clean up cases of \n<HEADER>\n to get 'first column'
            # TODO and clean up \n\n\n\n\n type stuff..
            new_filename = filename.replace(".txt", "_clean.txt")
            with codecs.open(new_filename, "w", "utf-8") as fout:
                document.page_list[i].page[-1] += "\n"
                fout.write("\n".join(document.page_list[i].page))
                document.text += "\n".join(document.page_list[i].page)
            # concatenate page text into one dump
            with codecs.open(document.working_dir + "ocr/document_clean.txt", "w", "utf-8") as fout:
                fout.write(document.text)



if __name__ == '__main__':
    main()

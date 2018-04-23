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
import shutil
import os
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

    """TODO"""

    def __init__(self, *args, **kwargs):
        for key, val in kwargs.items():
            setattr(self, key, val)

        if hasattr(self, 'pdf_path') and self.pdf_path is not None:
            code, outs, errs = call("gs -q -dNODISPLAY -c \"(%s) (r) file runpdfbegin pdfpagecount = quit\"" % self.pdf_path)
            try:
                self.number_of_pages = int(outs)
            except ValueError as e:
                print("ERROR\t Could not get number of pages. Possible document is not a PDF!")

        if hasattr(self, "page_files"):
            self.prep_pagefiles()
        else:
            self.page_files = []

        self.repeated_phrases = set()

        shutil.rmtree('ocr_tmp', True)
        try:
            os.mkdir('ocr_tmp')
        except OSError as e:
            print("ERROR\tCreate ocr_tmp folder")
            raise e


    def prep_pagefiles(self):
        self.page_files = sorted(self.page_files, key=lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split('(\d+)', s)])
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
        start, val = next((i, val) for i, val in enumerate(self.found_pagenumbers) if val is not None)
        self.expected_pagenumbers = range(val-start, val + len(self.found_pagenumbers) - start)
        for i, page in enumerate(self.page_list):
            self.page_list[i].expected_page_no = self.expected_pagenumbers[i]

        # get first and last non-zero
        pass


    # TODO: why do I need to pass in found_headers and found_pagenumbers
    ## they're accessible (but slightly different) in self.repeated
    ## TODO: actually the Page class will be aware of what potential page number it is..
#    def cleanup_page(self, page, mode, found_pagenumber):
#        """
#        TODO: Docstring for remove_headers.
#
#        Args:
#            footer_mode (TODO): TODO
#
#        Returns: TODO
#        """
#
#        LINES = 8
#
#        valid_modes = ["header", "footer", "full_page"]
#        if mode not in valid_modes:
#            print "Invalid scan mode supplied! Choose one of (%s)" % (valid_modes)
#
#        if mode == "header":
#            lines = xrange(LINES)
#        elif mode == "footer":
#            lines = xrange(len(page) - 1 - LINES, len(page))
#        elif mode == "full_page":
#            lines = xrange(1, len(page)-1)
#
#        # remove pagenumbers based on string matching
#        ignore_lines = []
#        for i in lines:
#            if mode == "full_page": # only check for similarity if the string is isolated
#                if page[i-1] != "" or page[i+1] != "":
#                    continue
#
#            # loop over known headers, remove any any similar strings
#            for rep in self.repeated_phrases:
#                rep = str(rep)
#                seq = SequenceMatcher(None, rep, page[i])
#                if seq.ratio() > 0.8:
#                    ignore_lines.append(i)
#            # remove any instance of the expected page number
#            page[i] = page[i].replace(str(found_pagenumber), "")
#
#        cleaned_page = [val for i, val in enumerate(page) if i not in ignore_lines]
#        non_empty_lines = [i for i, val in enumerate(cleaned_page) if (val!="" and val!="\n" and val!=' ')]
#        if non_empty_lines == []:
#            cleaned_page = ['']
#        else:
#            cleaned_page = cleaned_page[non_empty_lines[0]:non_empty_lines[-1]+1]
#
#        return cleaned_page
#
    def remove_headers(self, mode):
        """
        TODO: Docstring for remove_headers.

        Args:
            footer_mode (TODO): TODO

        Returns: TODO
        """

        for page, pageno in zip(self.page_list, self.found_pagenumbers):
            page.cleanup(mode)
#            cleaned_pages.append(page)
#        self.page_list = cleaned_pages

    def mid_page_cleanup(self):
        """
        TODO: Docstring for mid_page_cleanup.
        Returns: TODO

        """
        for j, page in enumerate(self.page_list):
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
            pagecheck, _, _ = call("gs -dFirstPage=%(page)s -dLastPage=%(page)s -dBATCH -dNOPAUSE -sDEVICE=png16m -dGraphicsAlphaBits=4 -dTextAlphaBits=4 -r600 -sOutputFile='ocr_tmp/page-%(page)d.png' '%(input)s'" % {"page" : i, "input": self.pdf_path})
            tesscheck, _, _ = call("tesseract ocr_tmp/page-%(page)s.png ocr/page_%(page)s -l eng --psm 1 --oem 2 txt hocr" % {"page" : i})
            if tesscheck == 0:
                self.page_files.append(os.getcwd() + "/ocr/page_%(page)s.txt" %{"page" : i})
            check = check and pagecheck and tesscheck
        return check

def main():
    # ASSUME: This is going to be run _within_ the docker container that has gs, tesseract, etc installed
    document = Document(pdf_path = "/home/input/1-s2.0-0031018280900164-main.pdf")


    # TODO: parse options
    # TODO: run only those options

    document.ocr()
    document.prep_pagefiles()


    import pdb; pdb.set_trace()



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
        with codecs.open("ocr/document_clean.txt", "w", "utf-8") as fout:
            fout.write(document.text)



if __name__ == '__main__':
    main()

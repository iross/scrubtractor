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

class Document(object):

    """TODO"""

    def __init__(self, *args, **kwargs):
        for key, val in kwargs.items():
            setattr(self, key, val)
        self.page_files = sorted(self.page_files, key=lambda s: [int(t) if t.isdigit() else t.lower() for t in re.split('(\d+)', s)])

        self.repeated = list()
        self.found_pagenumbers = list()
        for i in range(len(self.page_files)):
            self.repeated.append(set())
            self.found_pagenumbers.append(None)
        self.repeated_phrases = set()

        self.page_list = []
        for page in self.page_files:
            with open(page) as fin:
                clean_page = []
                temp_page = fin.read().split("\n")
                non_empty_lines = [i for i, val in enumerate(temp_page) if (val!="" and val!="\n")]
                if non_empty_lines == []:
                    clean_page = ['']
                else:
                    try:
                        clean_page = (temp_page[non_empty_lines[0]:non_empty_lines[-1]+1])
                    except:
                        import pdb; pdb.set_trace()
                self.page_list.append(clean_page)

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

            thesetwo = list()
            thesepagenos = list()
            linesaccepted = 0

            if footer_mode:
                lines_it = reversed(list(enumerate(page))) # gross..
            else:
                lines_it = enumerate(page)
            for idx, line in lines_it:

                if not footer_mode and idx > LINES:
                    break
                elif footer_mode and idx < len(page) - LINES:
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

        # TODO: build expected pagenumbers based on the found ones

    def predict_pagenumbers(self):
        """
        TODO

        Returns: TODO

        """
        print "Found page numbers: %s" % self.found_pagenumbers
        start, val = next((i, val) for i, val in enumerate(self.found_pagenumbers) if val is not None)
        self.expected_pagenumbers = range(val-start, val + len(self.found_pagenumbers) - start)
        # get first and last non-zero
        pass


    def remove_headers(self, footer_mode):
        """
        TODO: Docstring for remove_headers.

        Args:
            footer_mode (TODO): TODO

        Returns: TODO
        """

        LINES = 8
        removed = list()
        cleaned_pages = list()

        # TODO: a better 'pop' for my data structure -- should automatically remove newlines if they become 'head' or 'tail' after some cleanup
        # TODO: What I really want is to check the first X lines, remove known issues, and re-check to make sure I didn't miss anything, because
        #           sometimes page numbers are twenty+ blank lines "underneath" the header for some reason..
        # TODO: also it should try to remove 'end of a line but it\n\ncontinues on after' gaps

        for page, headerset, pageno in zip(self.page_list, self.repeated, self.found_pagenumbers):
            page = [i.strip() for i in page]
            for header in sorted(headerset, key = lambda tup: -tup[1]): # Make sure we pop from the back so indexes don't become invalid
                lineindex = header[1]
                print "Removing line %s" % lineindex
                try:
                    page[lineindex] = "\n"
                except IndexError:
                    import pdb; pdb.set_trace()
            if not footer_mode:
                for i in range(LINES):
                    page[i] = page[i].replace(str(pageno), "")
            elif footer_mode:
                print "Checking lines %s-%s for %s" % (len(page) - 1 - LINES, len(page) - 1, pageno)
                for i in range(len(page) - 1 - LINES, len(page) - 1):
                    page[i] = page[i].replace(str(pageno), "")
#            if str(pageno) in page:
#                page.pop(page.index(str(pageno)))
            # clean up trailing whitespace again, since we might have cut some out.

            # TODO: Hmm, this cleanup can break the line indexing for things stored in self.repeated...
#            non_empty = [i for i, val in enumerate(page) if val!="" and val!="\n"]
#            if non_empty == []:
#                cleaned_pages.append([''])
#            else:
#                cleaned_pages.append(page[non_empty[0]:non_empty[-1]+1])
            cleaned_pages.append(page)

        self.page_list = cleaned_pages
        return 0

    def mid_page_cleanup(self):
        """
        TODO: Docstring for mid_page_cleanup.
        Returns: TODO

        """
        repeated_dealies = set()
        repeated_dealies = repeated_dealies.union(self.repeated_phrases)
        repeated_dealies = repeated_dealies.union(set(self.expected_pagenumbers))
        # For each page
        ## for each line triplet
        ## if pattern is "\n" "<known pattern>" "\n", do some cleanup
        cleaned_page = list()
        for j, page in enumerate(self.page_list):
            ignore_lines = list()
            for line in range(1, len(page)-1):
                if page[line-1] != "" or page[line+1] != "": # only check for similarity if the string is isolated
                    continue
                if "alphamed" in page[line]:
                    for rep in repeated_dealies:
                        rep = str(rep)
                        seq = SequenceMatcher(None, rep, page[line])
                        if seq.ratio() > 0.8:
                            ignore_lines.append(line)
            cleaned_page = [val for i, val in enumerate(page) if i not in ignore_lines]
            if ignore_lines != []:
                print j

            # TODO: do the actual removal
        pass

    def remove_empties(self):
        """
        TODO: Docstring for remove_empties.
        Returns: TODO

        """
        for j, page in enumerate(self.page_list):
            temp = []
            ignore_lines = []
            for i in range(len(page)-1):
                if i in ignore_lines:
                    continue
                if i+2 < len(page): # look forward -- if the next line looks like it's breaking a sentence, skip it on next iteration
                    if page[i] != '' and page[i+1] == '' and page[i+2] != '' and not page[i].endswith('.') and page[i+2][0].islower():
                        ignore_lines.append(i+1)
                if not (page[i] == '' and page[i+1] == ''): # eliminite chains of ''
                    temp.append(page[i])

            temp.append(page[-1])
            self.page_list[j] = temp

    def find_sections(self):
        """
        TODO: Docstring for find_sections.
        Returns: TODO

        """
        pass


def main():
    document = Document(page_files = glob.glob("%s/output/TASK*/out/*.clean.txt" % sys.argv[1]))
    import pdb; pdb.set_trace()

    # cleanup headers/footers
    document.find_headers(footer_mode = True)
    document.find_headers(footer_mode = False)
    document.remove_headers(footer_mode = True)
#    document.remove_headers(footer_mode = False)
#    document.predict_pagenumbers() # requires found_pagenumbers, so should be after the find_headers calls
#    document.mid_page_cleanup() # keys in on blank lines, so needs to be _before_ remove_empties
    document.remove_empties()

    for i, filename in enumerate(document.page_files):
        # TODO: one more pass? Clean up cases of \n<HEADER>\n to get 'first column'
        # TODO and clean up \n\n\n\n\n type stuff..
        new_filename = filename.replace("clean.txt", "moreclean.txt")
        with open(new_filename, "w") as fout:
            fout.write("\n".join(document.page_list[i]))


if __name__ == '__main__':
    main()

import os

def importrules(rulepath):
    '''
    A function that creates global variables for the rest of this module
    to use. Probably not the clearest data encapulation strategy in
    the world. Wetware upgrades are expensive.
    '''

    global delchars, alleraser, mosteraser, Punctuation, delim,\
    foundcounter, englishcounter, pagedict, romannumerals, lexicon,\
    personalnames, correctionrules, hyphenrules, syncoperules,\
    fuserules, variants, punctuple\

    ## The following lines generate a translation map that zaps all
    ## non-alphanumeric characters in a token.

    delchars = ''.join(c for c in map(chr, range(256)) if not c.isalpha())
    alleraser = str.maketrans('', '', delchars)

    ## Translation map that only breaks selected punctuation marks
    ## likely to pose a problem. Does not break hyphens, does break dashes.

    ## Translation map that erases most punctuation, including hyphens.
    Punctuation = '.,():-—;"!?•$%@“”#<>+=/[]*^\'{}_■~\\|«»©&~`£·'
    mosteraser = str.maketrans('', '', Punctuation)

    punctuple = ('.', ',', '?', '!', ';', '"', '“', '”', ':', '--', '—', ')', "'", "(", "[", "]")

    delim = '\t'
    foundcounter = 0
    englishcounter = 0
    pagedict = dict()

    romannumerals = set()
    with open(os.path.join(rulepath, 'romannumerals.txt'), encoding = 'utf-8') as file:
        filelines = file.readlines()

    for line in filelines:
        line = line.rstrip()
        romannumerals.add(line)

    lexicon = dict()

    with open(os.path.join(rulepath, 'MainDictionary.txt'), encoding = 'utf-8') as file:
        filelines = file.readlines()

    for line in filelines:
        line = line.rstrip()
        fields = line.split(delim)
        englflag = int(fields[1])
        lexicon[fields[0]] = englflag

    personalnames = set()
    with open(os.path.join(rulepath, 'PersonalNames.txt'), encoding = 'utf-8') as file:
        filelines = file.readlines()

    for line in filelines:
        line = line.rstrip()
        line = line.lower()
        personalnames.add(line)

    correctionrules = dict()

    with open(os.path.join(rulepath, 'CorrectionRules.txt'), encoding = 'utf-8') as file:
        filelines = file.readlines()

    for line in filelines:
        line = line.rstrip()
        fields = line.split(delim)
        correctionrules[fields[0]] = fields[1]

    hyphenrules = dict()

    with open(os.path.join(rulepath, 'HyphenRules.txt'), encoding = 'utf-8') as file:
        filelines = file.readlines()
    filelines.reverse()
    # Doing this so that unhyphenated forms get read before hyphenated ones.

    for line in filelines:
        line = line.rstrip()
        fields = line.split(delim)
        Word = fields[0].rstrip()
        Corr = fields[1].rstrip()
        hyphenrules[Word] = Corr
        if " " not in Corr:
            lexicon[Corr] = 1
        else:
            StripWord = Word.replace("-", "")
            hyphenrules[StripWord] = Corr
            ## That's so that we split "tigermoth" as well as "tiger-moth" into "tiger moth."

        if "-" in Word:
            StripWord = Word.replace("-", "")
            StripCorr = Corr.replace(" ", "")
            StripCorr = StripCorr.replace("-", "")
            if StripWord != StripCorr and StripWord not in hyphenrules:
                hyphenrules[StripWord] = Corr
                print(Word, 'produced two corrections.')
        ## The purpose of this is a bit obscure to me. It may be deletable.

    fuserules = dict()
    with open(os.path.join(rulepath, 'FusingRules.txt'), encoding = 'utf-8') as file:
        filelines = file.readlines()

    for Line in filelines:
        Line = Line.rstrip()
        LineParts = Line.split(delim)
        Word = LineParts[0].rstrip()
        Word = tuple(Word.split(' '))
        Corr = LineParts[1].rstrip()
        fuserules[Word] = Corr

    syncoperules = dict()
    with open(os.path.join(rulepath, 'SyncopeRules.txt'), encoding = 'utf-8') as file:
        filelines = file.readlines()

    for line in filelines:
        line = line.rstrip()
        fields = line.split(delim)
        syncoperules[fields[0]] = fields[1]

    # IAR - 14.May.2018 this is the stuff that does a lot of the 'British-isation"
    variants = dict()
#    with open(os.path.join(rulepath, 'VariantSpellings.txt'), encoding = 'utf-8') as file:
#        filelines = file.readlines()
#
#    for line in filelines:
#        line = line.rstrip()
#        fields = line.split(delim)
#        variants[fields[0]] = fields[1]

    ## End loading of rulesets.

def as_stream(linelist, verbose = False):
    '''converts a list of lines to a list of tokens'''
    global lexicon, mosteraser

    tokens = list()
    for line in linelist:
        if len(line) < 1:
            continue
        if line == "\n":
            tokens.append(line)
            continue
        line = line.rstrip()
        if line.startswith('<') and line.endswith('>'):
            tokens.append(line)
            tokens.append('\n')
            continue

        line = line.replace('”', '” ')
        line = line.replace('“', ' “')
        line = line.replace(':', ': ')
        line = line.replace(';', '; ')
        line = line.replace(',"', '«!!»')
        line = line.replace(',', ', ')
        line = line.replace('—', ' — ')
        line = line.replace('--', ' -- ')
        line = line.replace('«!!»', ',"')
        ## Instead of zapping punctuation, we make sure it's followed by a space.
        ## The bit about «!!» is a crude hack intended to avoid separating quotation marks
        ## from a trailing comma

        ## Quotes require special treatment, because their position relative to
        ## the space can be significant.

##        if '"' in line:
##            nextindex = line.find('"')
##            while nextindex >= 0:
##                if nextindex >= (len(line) - 1):
##                    followedbyspace = True
##                    nextindex = -1
##                elif line[nextindex+1] == " ":
##                    followedbyspace = True
##                    nextindex = line.find('"', nextindex+1, len(line))
##                else:
##                    if nextindex > 0 and line[nextindex - 1] == " ":
##                        line = line[0:nextindex] + '“ ' + line[nextindex+1:]
##                        nextindex = line.find('"', nextindex+2, len(line))
##                        ## Okay, this is a teensy bit baroque. I know that correct_stream
##                        ## doesn't handle prefixed punctuation very well. So I don't want
##                        ## quotes to be prefixed to words. But I want to preserve the fact
##                        ## that they were opening quotes. So I use the special open-quote
##                        ## character if quote was prefixed to a word, and preceded by
##                        ## a space.
##
##                    elif nextindex == 0:
##                        line = '“' + line[nextindex+1:]
##                        nextindex = line.find('"', nextindex+2, len(line))
##                    else:
##                        line = line[0:nextindex] + '" ' + line[nextindex+1:]
##                        nextindex = line.find('"', nextindex+2, len(line))
##                        ## If not preceded by a space, this is ambiguous, and I leave
##                        ## the character ambiguous.


        lineparts = line.split()
        tokens.extend(lineparts)
        tokens.append('\n')

    counter = 0
    englishcounter = 0
    allcounter = 0

    tokencount = len(tokens)

    for i in range(0, tokencount):
        token = tokens[i].lower()
        if token in lexicon:
            counter += 1
            allcounter += 1
            if lexicon[token] > 0:
                englishcounter += 1
        elif token == '\n' or token.startswith('<') or mostly_numeric(token):
            next
        elif i < (tokencount-1):
            token = token.translate(mosteraser)
            if token in lexicon:
                counter += 1
                allcounter += 1
                if lexicon[token] > 0:
                    englishcounter += 1
            else:
                nexttoken = tokens[i+1].lower()
                fused = token + nexttoken.translate(mosteraser)
                if fused in lexicon:
                    counter += 1
                    allcounter += 1
                    if lexicon[fused] > 0:
                        englishcounter += 1
                else:
                    allcounter += 1
        else:
            allcounter += 1

    if allcounter > 0:
        percentfound = counter / allcounter
        percentenglish = englishcounter / allcounter
    else:
        percentfound = 0
        percentenglish = 0

    return tokens, percentfound, percentenglish

def strip_punctuation(astring):
    global punctuple
    keepclipping = True
    suffix = ""
    while keepclipping == True:
        keepclipping = False
        if astring.endswith(punctuple):
            suffix = astring[-1:] + suffix
            astring = astring[:-1]
            keepclipping = True

    keepclipping = True
    prefix = ""
    while keepclipping == True:
        keepclipping = False
        if astring.startswith(punctuple):
            prefix = prefix + astring[0]
            astring = astring[1:]
            keepclipping = True

    return(astring, prefix, suffix)

def normalize_case(astring):
    if astring.islower():
        case = 'lower'
    elif astring.replace("'", "").isupper():
        case = 'upper'
    elif astring.istitle():
        case = 'title'
    elif astring.replace("'", "").istitle():
        case = "title"
    # The replace part is important lest all possessive words get interpreted
    # as heterogenous-case.
    else:
        case = 'heterogenous'

    if case != "heterogenous":
        normalizedstring = astring.lower()
    else:
        normalizedstring = astring

    return normalizedstring, case

def mostly_numeric(astring):
    counter = 0
    for c in astring:
        if c.isdigit():
            counter += 1
    if len(astring) < 1:
        return False
    elif counter/len(astring) > .35:
        return True
    else:
        return False

def is_punctuation(astring):
    ispunct = True

    for character in astring:
        if character.isalpha():
            ispunct = False
            break
        if character.isdigit():
            ispunct = False
            break

    return ispunct

def is_word(astring):
    global lexicon
    if astring in lexicon:
        return True
    elif astring.lower() in lexicon:
        return True
    elif (astring.lower() + "'s") in lexicon:
        return True
    else:
        return False

def logandreset(astring, caseflag, possessive, prefix, suffix):
    ''' We normalize case at moments in the checking process, and
    also remove trailing apostrophe-s and punctuation. This routine ensures that
    both aspects of the token are restored to their original condition.
    Note that it does so only after logging the word, which means that
    possessive inflections are not registered in our wordcount.
    That's my only gesture toward lemmatization.'''

    global pagedict, lexicon, syncoperules, variants, foundcounter, englishcounter


    if astring in syncoperules:
        astring = syncoperules[astring]
    if astring in variants:
        astring = variants[astring]

    inDict = False

    if astring in lexicon:
        foundcounter += 1
        inDict = True
        if lexicon[astring] == 1:
            englishcounter += 1
    elif astring == "romannumeral" or astring == "arabicnumeral":
        foundcounter += 1
        englishcounter += 1

    if inDict or astring == "romannumeral" or astring == "arabicnumeral":

        if astring.lower() in pagedict:
            pagedict[astring.lower()] += 1
        else:
            pagedict[astring.lower()] = 1

    if caseflag == "lower":
        astring = astring.lower()
    elif caseflag == "upper":
        astring = astring.upper()
    elif caseflag == "title":
        astring = astring[0].upper() + astring[1:].lower()
        # I don't use "astring.title()" because You'Ll.
    else:
        astring = astring.lower()

    if possessive:
        astring = astring + "'s"

    if len(suffix) > 0:
        astring = astring + suffix

    if len(prefix) > 0:
        astring = prefix + astring

    return astring


def correct_stream(tokens, verbose = False):
    global lexicon, hyphenrules, fuserules, syncoperules, correctionrules, romannumerals, pagedict, foundcounter, englishcounter, personalnames

    corrected = list()
    streamlen = len(tokens)
    skipflag = False
    wordsfused = 0
    pagecounter = 0
    pagedict = dict()
    pages = list()
    foundcounter = 0
    englishcounter = 0
    paratext = 0

    for i in range(0, streamlen):

        thisword = tokens[i]
        if len(thisword) < 1:
            continue

        originalword = thisword

        if thisword == "<pb>":
            pages.append(pagedict)
            pagedict = dict()
            # log the old page dictionary and start a new one
            corrected.append(thisword)
            paratext +=1
            continue

        if (thisword.startswith('<') and thisword.endswith('>')) or thisword == '\n':
            corrected.append(thisword)
            paratext += 1
            continue

        if (is_punctuation(thisword)):
            corrected.append(thisword)
            continue

        ## Notice the sequence here. We don't reset skipflag if we're just skipping newlines or
        ## xml markup.

        if skipflag:
            skipflag = False
            continue

        # get the next word, ignoring newlines and xml markup
        for j in range(1, 4):
            if i < (streamlen-j):
                nextword = tokens[i+j]
                if nextword.startswith('<') or nextword=='\n':
                    continue
                else:
                    break
            else:
                nextword = "#EOFile"
                break

        thisword, thiscase = normalize_case(thisword)
        nextword, nextcase = normalize_case(nextword)
        ## All words in homogenouscase (upper/lower) or titlecase go to lowercase
        ## HeterOGENous words retain existing case.

        thisword, thisprefix, thissuffix = strip_punctuation(thisword)
        nextword, nextprefix, nextsuffix = strip_punctuation(nextword)

        ## We also strip and record apostrophe-s to simplify checks.

        thispossessive = False
        nextpossessive = False

        if (thisword.endswith("'s") or thisword.endswith("'S")) and len(thisword) > 2:
            thispossessive = True
            thisword = thisword[0:-2]

        if (nextword.endswith("'s") or nextword.endswith("'S")) and len(nextword) > 2:
            nextpossessive = True
            nextword = nextword[0:-2]

        thislower = thisword.lower()
        nextlower = nextword.lower()

        # Is this a number?

        if thislower in romannumerals:
            numeral = logandreset("romannumeral", thiscase, False, thisprefix, thissuffix)
            corrected.append(thisword.upper())
            continue

        if mostly_numeric(thisword):
            numeral = logandreset("arabicnumeral", thiscase, False, thisprefix, thissuffix)
            corrected.append(thisprefix + thisword + thissuffix)
            continue

        if (thiscase=="title" or thiscase=="upper") and thisword in personalnames:
            newtoken = logandreset(thisword, thiscase, thispossessive, thisprefix, thissuffix)
            corrected.append(newtoken)
            continue

        # Is this part of a phrase that needs fusing?

        if is_word(thisword) and is_word(nextword):
            fusetuple = (thislower, nextlower)
            if fusetuple in fuserules:
                print("they're both words")
                newtoken = fuserules[fusetuple]
                newtoken = logandreset(newtoken, thiscase, nextpossessive, thisprefix, nextsuffix)
                corrected.append(newtoken)
                wordsfused += 1
                skipflag = True
                continue

            else:
                thisword = logandreset(thisword, thiscase, thispossessive, thisprefix, thissuffix)
                corrected.append(thisword)
                continue

        if is_word(thisword):
            thisword = logandreset(thisword, thiscase, thispossessive, thisprefix, thissuffix)
            corrected.append(thisword)
            continue

        ## At this point we know that thisword doesn't match lexicon. Maybe it's a word fragment
        ## that needs to be joined to nextword, after erasure of hyphens, etc.

        thistrim = thisword.translate(mosteraser)
        nexttrim = nextword.translate(mosteraser)
        possiblefusion = thistrim + nexttrim

        if is_word(possiblefusion):
            print("possible fusion is word!")
            newtoken = logandreset(possiblefusion, thiscase, nextpossessive, thisprefix, nextsuffix)
            corrected.append(newtoken)
            wordsfused += 1
            skipflag = True
            continue

        #maybe both parts need to be corrected
        if possiblefusion.lower() in correctionrules:
            print("both parts corrected")
            thiscorr = correctionrules[possiblefusion.lower()]
            newtoken = logandreset(thiscorr, thiscase, nextpossessive, thisprefix, nextsuffix)
            corrected.append(newtoken)
            wordsfused += 1
            skipflag = True
            continue

        if thisword in correctionrules:
            thiscorr = correctionrules[thisword]
        elif thistrim in correctionrules:
            thiscorr = correctionrules[thistrim]
        else:
            thiscorr = thisword.lower()

        if nextword in correctionrules:
            nextcorr = correctionrules[nextword]
        elif nexttrim in correctionrules:
            nextcorr = correctionrules[nexttrim]
        else:
            nextcorr = nextword.lower()

        ## Since we're past the correction rules, there's no reason any longer to
        ## retain words in Heter-Ogenous case.

        ## Now we have to check one last time for possible fusing.

        fusetuple = (thiscorr, nextcorr)
        if fusetuple in fuserules:
            print("checking one last time")
            newtoken = fuserules[fusetuple]
            newtoken = logandreset(newtoken, thiscase, nextpossessive, thisprefix, nextsuffix)
            corrected.append(newtoken)
            wordsfused += 1
            skipflag = True
            continue

        ## But otherwise, if the correction worked, move on.

        if is_word(thiscorr):
            thiscorr = logandreset(thiscorr, thiscase, thispossessive, thisprefix, thissuffix)
            corrected.append(thiscorr)
            continue

        if thiscorr in hyphenrules:
            thiscorr = hyphenrules[thiscorr]

        ## Maybe the correction is multiple words. That's a split that could have happened as a result
        ## of correctionrules or hyphenrules.

        if " " in thiscorr:
            theseparts = thiscorr.split()
            for j in range(0, len(theseparts)):
                part = theseparts[j]
                if j == 0:
                    partcase = thiscase
                else:
                    partcase = "lower"

                newtoken = logandreset(part, partcase, False, "", "")
                if j == (len(theseparts) - 1):
                    newtoken = newtoken + thissuffix
                corrected.append(newtoken)
            continue

        ## Ordinary correction rules didn't work. Now we try syncope.

        if thiscorr in syncoperules:
            thiscorr = syncoperules[thiscorr]

        if is_word(thiscorr):
            thiscorr = logandreset(thiscorr, thiscase, thispossessive, thisprefix, thissuffix)
            corrected.append(thiscorr)
            continue

        ## If we still have a hyphen, try splitting there.

        if "-" in thiscorr:
            splitcorr = thiscorr.replace("-", " ")
            theseparts = splitcorr.split()
            for j in range(0, len(theseparts)):
                part = theseparts[j]
                if j == 0:
                    partcase = thiscase
                else:
                    partcase = "lower"

                newtoken = logandreset(part, partcase, False, "", "")
                if j == (len(theseparts) - 1):
                    newtoken = newtoken + thissuffix
                corrected.append(newtoken)
            continue

        #last-ditch move. zap all nonalphabetic characters

        thispurged = thiscorr.translate(alleraser)

        if is_word(thispurged):
            thiscorr = logandreset(thispurged, thiscase, thispossessive, thisprefix, thissuffix)
            corrected.append(thiscorr)
            continue
        else:
            originalword = logandreset(thiscorr, thiscase, thispossessive, thisprefix, thissuffix)
            corrected.append(originalword)
            ## The word will in fact only be logged in the page dictionary if it
            ## matches the dictionary. Variant spellings will be normalized in the
            ## logandreset function.
            continue

    if verbose:
        print('There were', wordsfused, 'fused words.')

    totaltokens = len(corrected) - paratext
    if totaltokens > 0:
        percentmatched = foundcounter / totaltokens
        percentenglish = englishcounter / totaltokens
    else:
        percentmatched = 0
        percentenglish = 0
    return corrected, pages, percentmatched, percentenglish

    # The method returns a vector of all tokens, including xml tags and linebreaks,
    # plus a list of page dictionaries, plus a count of words that matched, and the
    # number of those words that were english.










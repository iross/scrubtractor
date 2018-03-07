Helper classes for document or page level 'stuff' for GeoDeepDive.

# Philsophy
The idea is that these things would be usable for basic document processing,
especially  in a bundled HTC job. Include these scripts and some OCR
executables and have an all-in-one way of:

    1. OCRing
    2. Normalizing the OCR (make sure that ligatures, spellings, etc are consistent)
    3. Cleanup the text (remove headers/page numbers, do the easy formatting to get the text 'true' to the content instead of the PDF)
    4. Recognize features (where REFERENCES start, what pages contain captions/figures, etc)
    5. Extract figures/tables via John's magic

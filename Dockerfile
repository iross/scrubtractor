FROM ubuntu:16.04 
RUN apt-get update && apt-get install -y software-properties-common && add-apt-repository -y ppa:alex-p/tesseract-ocr 
RUN apt-get update && apt-get install -y tesseract-ocr 
RUN apt-get update && apt-get install -y tesseract-ocr-eng
RUN apt-get update && apt-get install -y ghostscript
RUN apt-get update && apt-get install -y vim

# for some reason the above doesn't install the LSTM-trained models -- this 
# file is from https://github.com/tesseract-ocr/tessdata commit b594dabeab60aa8e1344b0a2c259c0e94aba24e9
ADD eng.traineddata /usr/share/tesseract-ocr/4.00/tessdata

RUN mkdir /input
RUN mkdir /output

ADD Document.py /usr/bin/
ADD Page.py /usr/bin/
ADD Volume2.py /usr/bin/
ADD rulesets/ /usr/bin/rulesets

#ENTRYPOINT ["Document.py"]
#CMD ["--help"]

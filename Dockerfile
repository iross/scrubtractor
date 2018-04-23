FROM ubuntu:16.04 
RUN apt-get update && apt-get install -y software-properties-common && add-apt-repository -y ppa:alex-p/tesseract-ocr 
RUN apt-get update && apt-get install -y tesseract-ocr 
RUN apt-get update && apt-get install -y tesseract-ocr-eng
RUN apt-get update && apt-get install -y ghostscript

RUN mkdir /home/work 
RUN mkdir /home/input
RUN mkdir /home/work/ocr/

# for some reason the above doesn't install the LSTM-trained models -- this 
# file is from https://github.com/tesseract-ocr/tessdata commit b594dabeab60aa8e1344b0a2c259c0e94aba24e9
ADD eng.traineddata /usr/share/tesseract-ocr/4.00/tessdata

ADD Document.py /home/work
ADD Page.py /home/work

ADD input/1-s2.0-0031018280900164-main.pdf /home/input
#ADD ocr /home/work/ocr

WORKDIR /home/work

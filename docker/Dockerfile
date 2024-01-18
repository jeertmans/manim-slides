# Mostly a copy from https://github.com/ManimCommunity/manim/blob/68bd79093e1ebc1ed9f8051942ffe6e72a9e66a7/docker/Dockerfile
FROM python:3.11-slim

RUN apt-get update -qq \
    && apt-get install --no-install-recommends -y \
        ffmpeg \
        build-essential \
        gcc \
        cmake \
        libcairo2-dev \
        libffi-dev \
        libpango1.0-dev \
        freeglut3-dev \
        pkg-config \
        make \
        wget \
        ghostscript

# setup a minimal texlive installation
COPY docker/texlive-profile.txt /tmp/
ENV PATH=/usr/local/texlive/bin/armhf-linux:/usr/local/texlive/bin/aarch64-linux:/usr/local/texlive/bin/x86_64-linux:$PATH
RUN wget -O /tmp/install-tl-unx.tar.gz http://mirror.ctan.org/systems/texlive/tlnet/install-tl-unx.tar.gz && \
    mkdir /tmp/install-tl && \
    tar -xzf /tmp/install-tl-unx.tar.gz -C /tmp/install-tl --strip-components=1 && \
    /tmp/install-tl/install-tl --profile=/tmp/texlive-profile.txt \
    && tlmgr install \
        amsmath babel-english cbfonts-fd cm-super ctex doublestroke dvisvgm everysel \
        fontspec frcursive fundus-calligra gnu-freefont jknapltx latex-bin \
        mathastext microtype ms physics preview ragged2e relsize rsfs \
        setspace standalone tipa wasy wasysym xcolor xetex xkeyval

# clone and build manim-slides
COPY . /opt/manim-slides
WORKDIR /opt/manim-slides
RUN pip install --no-cache manim[jupyterlab] .[sphinx-directive]

ARG NB_USER=manimslidesuser
ARG NB_UID=1000
ENV USER ${NB_USER}
ENV NB_UID ${NB_UID}
ENV HOME /manim-slides

RUN adduser --disabled-password \
    --gecos "Default user" \
    --uid ${NB_UID} \
    ${NB_USER}

# create working directory for user to mount local directory into
WORKDIR ${HOME}
USER root
RUN chown -R ${NB_USER}:${NB_USER} ${HOME}
RUN chmod 777 ${HOME}
USER ${NB_USER}

CMD [ "/bin/bash" ]

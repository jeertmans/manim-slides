---
title: 'Manim Slides: A Python package for presenting Manim content anywhere'
tags:
  - Python
  - manim
  - animations
  - teaching
  - conference presentations
  - tool
authors:
  - name: Jérome Eertmans
    orcid: 0000-0002-5579-5360
    affiliation: 1
affiliations:
 - name: ICTEAM, UCLouvain, Belgium
   index: 1
date: 2 March 2023
bibliography: paper.bib
---

# Summary

Manim Slides is a Python package that makes presenting Manim animations
straightforward. With minimal changes required to pre-existing code, one can
slide through animations in a *PowerPoint-like* manner, or share its slides
*online* using ReavealJS' power.

# Introduction

Presenting educational content has always been a difficult task, especially
when it uses temporal or iterative concepts. During the last decades, the
presence of computers in classrooms for educational purposes has increased
enormously, allowing teachers to show animated or interactive content.

With the democratization of YouTube, many people have decided to use this
platform to share educational content. Among these people, Grant Sanderson, a
YouTuber presenting videos on the theme of mathematics, quickly became known
for his original and quality animations. In 2018, Grant announced in a video
that he creates his animations using a self-developed Python tool called Manim
[@manim-announcement]. In 2019, he made the Manim source code public [@manimgl],
so anyone can use his tool. Very quickly, the community came together and, in
2020, created a "fork" of the original GitHub repository [@manimce], in order to
create a more accessible and better documented version of this tool. Since then,
the two versions are differentiated by using ManimGL for Grant Sanderson's
version, as it uses OpenGL for rendering, and ManimCE for the community edition
(CE).

Despite the many advantages of the Manim tool in terms of illustrating
mathematical concepts, one cannot help but notice that most presentations,
whether in the classroom or at a conference, are mainly done with PowerPoint
or PDF slides. One of the many advantages of these formats, as opposed to videos
created with Manim, is the ability to pause, rewind, etc., whenever you want.

To face this problem, in 2021, the manim-presentation tool was created
[@manim-presentation]. This tool allows you to present Manim animations as you
would present slides: with pauses, slide jumps, etc. However, this tool has
evolved very little since its inception and does not work with ManimGL.

In 2022, Manim Slides has been created from manim-presentation, with the aim
to make it a more complete tool, better documented, and usable on all platforms
and with ManimCE or ManimGL. After almost a year of existence, Manim Slides has
evolved a lot, has built a small community of contributors, and continues to
provide new features on a regular basis.

# Easy to Use Commitment

Manim Slides is commited to be an easy to use tool, when minimal installation
procedure and few modification required. It can either be used locally with its
graphical user interface (GUI), or shared via HTML thanks to the RevealJS
Javascript package [@revealjs].

This work has a very similar syntax to Manim and offers a comprehensive
documentation hosted on [GitHub pages](https://eertmans.be/manim-slides/), see
\autoref{fig:docs}.

![Manim Slides' documentation homepage.\label{fig:docs}](docs.png)

# Example usage

We have used an manim-presentation for our presentation at the COST
Interact, hosted in Lyon, 2022, and
[available online](https://eertmans.be/research/cost-interact-presentation/).
This experience highly motivated the development of Manim Slides, and our
EuCAP 2023 presentation slides are already
[available online](https://eertmans.be/research/eucap-presentation/), thanks
to Manim Slides' HTML feature.

Also, one of our user created a short
[video tutorial](https://www.youtube.com/watch?v=Oc9g89VzKsY&ab_channel=TheoremofBeethoven)
and posted it on YouTube.

# Stability and releases

Manim Slides is continously tested on most recent Python versions, both ManimCE
and ManimGL, and on all major platforms: **Ubuntu**, **macOS** and **Windows**. As of Manim
Slide's exposed API begin very minimal, and the variaty of tests that are
performed, this tool can be considered stable over time.

New releases are very frequent, as they mostly introduce enhancements or small
documention fixes, and the command-line tool automatically notifies for new
available updates. Therefore, regularly updating Manim Slides is highly
recommended.

# Statement of Need

Similar tools to Manim Slides also exist, such as its predecessor,
manim-presentation [@manim-presentation], or the web-based alternative, Manim
Editor [@manim-editor], but none of them provide the documentation level nor the
amount of features that Manim Slides strives to. This work makes the task of
presenting Manim content in front of an audience much easier than before,
allowing presenters to focus more on the content of their slides, rather than on
how to actually present them efficiently.

# Acknowledgements

We acknowledge the work of [@manim-presentation] that paved the initial structure
of Manim Slides with the `manim-presentation` Python package.

We also acknowledge Grant Sanderson for its termendous work on Manim, as well as
well as the Manim Community contributors.

Finally, we also acknowledge contributions from the GitHub contributors on the
Manim Slides repository.

# References

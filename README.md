ANASIME
=======

Analogy Simulation Environment in Python

This repository is the product of a master internship at the Donders Centre for Cogntion and Radboud University Nijmegen (see Grootswagers, 2013).
It was used to systematically assess algorithms for Structure-Mapping Theory (SMT), one of the most influential theories for human analogy derivation (Gentner, 1983).
To promote further research on this topic, the code is made available here under the GPLv3 license.

This repository contains the following:

- A predicate structure pair generator (generator.py) that generates pairs with specific characteristics according to SMT
- An implementation for the Structure-Mapping Engine (sme.py), as described in Falkenhainer, Forbus & Gentner (1989), and its adapted greedy heuristic (Forbus & Oblinger ,1990)).
- Two fp-tractable algorithms for SMT (fpto.py and fptp.py), as described in van Rooij, Evans, Muller, Gedge, & Wareham (2008) and Wareham, Evans, & van Rooij (2011).
- An example module to systematically test the algorithms (simulator.py) and an example script to run a simulation (sim_example.py)

Depencies
---------

- python (2.6 or higher)
- networkx, for graph functionality
- pygraphviz [optional] to visualize graphs
- psutil, to keep track of algorithm runtimes

These dependencies can be found in the pypi repository and are also included in the repositories of most popular linux distributions.

DISCLAIMER
----------

This software is only tested on Linux (Arch Linux and Ubuntu), and I can not guarantee anything regarding compability with other operating systems.
On the other hand, as python is cross-platform, I don't expect any issues.

AUTHOR
------

Tijl Grootswagers

REFERENCES
----------

- Falkenhainer, B., Forbus, K., & Gentner, D. (1989). The structure-mapping engine: Algorithm and examples. Artificial Intelligence, 41 , 1–63.

- Forbus, K., & Oblinger, D. (1990). Making SME greedy and pragmatic. In Proceedings of the twelfth annual conference of the Cognitive Science Society (pp. 61–68).

- Gentner, D. (1983). Structure-mapping: A theoretical framework for analogy. Cognitive Science, 7 (2), 155–170.

- Grootswagers, T. (2013). Having your cake and eating it too: Towards a fast and optimal method for analogy derivation. Unpublished MSc. Thesis, Department of Artificial Intelligence, Radboud University Nijmegen.

- van Rooij, I., Evans, P., Muller, M., Gedge, J., & Wareham, T. (2008). Identifying sources of intractability in cognitive models: An illustration using analogical structure mapping. In Proceedings of the 30th Annual Conference of the Cognitive Science Society (pp. 915–920).

- Wareham, T., Evans, P., & van Rooij, I. (2011). What does (and doesn’t) make analogical problem solving easy? a complexity-theoretic perspective. The Journal of Problem Solving, 3 (2), 3.

LICENSE
-------

Copyright (c) 2013  Tijl Grootswagers

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

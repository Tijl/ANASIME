#!/usr/bin/python2
import simulator

'''
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

Copyright (c) 2013, Tijl Grootswagers
'''

#
# BEGIN CONFIGURATION SECTION
#

#algorithms and their corresponding run functions
import fpto,fptp,sme

A = [
    ('fpt-o',fpto.run),
    ('fpt-p',fptp.run),
    ('sme-e',sme.runsme),
    ('sme-h',sme.runsmeh),
]

#Output file name
OUTFILENAME = 'results_example.data'

#number of trials to run
TRIALS = 100

#attempts to generate a predicate structure the first time, to see if it is possible at all in the current dimension
ATTEMPTS = 10

#dimensions over which to test as (name,levels) tuples
D = [
   ('predicates',[5,6,7,8,9,10]), #total number of predicates (expressions+functions+relations)
   ('types',[10,]), # total number of possible predicate types (with the same amount of arity-1 as arity-2 types)
   ('objects',[1,2,3,4]), #total number of objects
   ('height',[2,3,4]), #longest path to an object
   ('chance_function',[1.0,]), #probability of arity-1 predicates being functions
   ('preservation',[0.5]), #closeness of the graphs
   ('typeshape',['random']) #shape of predicate type distribution
   ('heightshape',['square']) #shape of height distribution
   ('max_arity',[2]) #max arity of predicates
   ('preservationdecay',[0]) #decay of preservation parameter per layer
   ('scaling',[1.0]) #size of the target graph compared to base
]


#
# END CONFIGURATION SECTION
#

simulator.run(A,D,TRIALS,ATTEMPTS,OUTFILENAME)

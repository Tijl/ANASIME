#!/usr/bin/python2

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

import sys,re,itertools
import networkx as nx
from utils import *

def run(base,target,maxsearchspace=100000):

    #start logging
    logger = Logger()

    result = {}

    leafsbase = [x for x in base.nodes() if not base.successors(x)]
    leafstarget = [x for x in target.nodes() if not target.successors(x)]

    functionsbase = [x for x in base.nodes() if isfunction(base.node[x]['type']) and base.predecessors(x)]
    functionstarget = [x for x in target.nodes() if isfunction(target.node[x]['type']) and target.predecessors(x)]

    solutions = []

    def consistent(bc,tc,gmap):
        '''returns true if the gmap can be extended with a mapping from bc to tc 
        (i.e. whether all successors of bc and tc are in the gmap)
        '''
        if base.node[bc]['ordered']:
            #ordered, so the successors must match in the same order
            return all([gmap[bs]==ts for bs,ts in zip(base.node[bc]['connections'],target.node[tc]['connections'])])
        else:
            #unordered, so check if all children of bc are in target
            targets = [gmap[bs] for bs in base.successors(bc)]
            return all([ts in targets for ts in target.successors(tc)])

    pools = [(leafsbase,leafstarget),(functionsbase,functionstarget)]

    result['inputsize'] = bijectionsproductsize(pools)

    if result['inputsize']>maxsearchspace:
        return result

    for ob in bijections(leafsbase,leafstarget):
        gmap = makegmap(ob)
        for fb in bijections([x for x in functionsbase if base.node[x]['connections'][0] in gmap.keys()],
                [x for x in functionstarget if target.node[x]['connections'][0] in gmap.values()]):
            gmap = makegmap(ob+fb) #the mapping from base to target
            if not gmap: #no conflicting assignments
                continue
            if not supported(gmap,base,target): #all children (except for leafs) must be in the gmap
                continue
            marked = set(leafsbase+functionsbase) #keep a list of items that are already checked
            candidates = True # the list of candidate mappings
            #print 'checking..',bcore,tcore
            while candidates:
                # for all items at this height in base, see if there is a match in target
                # candidates is the set of unconsidered nodes that have all their successors in the gmap
                candidates = [x for x in base.nodes() if x not in marked and all([y in gmap for y in base.successors(x)])]
                for bc in candidates:
                    #mark the candidate so it does not get considered again
                    marked.add(bc)
                    #compare this candidate to all possible target candidates
                    for tc in target.nodes():
                        # must not be already in the mapping
                        if tc in gmap.values():
                            continue
                        if not all([x in gmap.values() for x in target.successors(tc)]):
                            continue
                        #must be of the same arity
                        if len(target.successors(tc))!=len(base.successors(bc)):
                            continue
                        # must be of the same type or must be functions
                        tx,ty = base.node[bc]['type'],target.node[tc]['type']
                        if tx!=ty and not (isfunction(tx) and isfunction(ty)):
                            continue
                        #check if consistent match, i.e. their successors must map to eachother
                        if consistent(bc,tc,gmap):
                            gmap[bc]=tc
                            break
            gmap = validate(gmap,base) #remove 'dangling' functions and objects
            s = score(base.subgraph(gmap.keys())) #SES score
            if not solutions or (s==solutions[0][0]) and not member(gmap,solutions):
                solutions.append((s,gmap))
            elif s>solutions[0][0]:
                solutions = [(s,gmap)]

    if solutions:
        result['score'] = solutions[0][0]
        result['solutions'] = [x[1] for x in solutions]
    else:
        result['score']=0
        result['solutions'] = []

    '''
    print '\nFPT-O found %s optimal results\n'%len(solutions)
    d = ['name','type']
    for i,(s,gmap) in enumerate(solutions):
        print 'solution',i+1,'score:',s
        for b,t in gmap.iteritems():
            print '\t',[str(base.node[b][x]) for x in d],'\t-->\t',[str(target.node[t][x]) for x in d]
        print
    '''

    #end logging
    result['time'] = logger.time()
    
    return result


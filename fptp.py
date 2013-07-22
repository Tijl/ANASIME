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

    #store all objects
    leafsbase = [x for x in base.nodes() if not base.successors(x)]
    leafstarget = [x for x in target.nodes() if not target.successors(x)]
    #store all functions
    functionsbase = [x for x in base.nodes() if isfunction(base.node[x]['type'])]
    functionstarget = [x for x in target.nodes() if isfunction(target.node[x]['type'])]
    #pseudographs of all predicates and functions
    pseudobase = makefullsubgraph(base,[x for x in base.nodes() if base.successors(x)])
    pseudotarget = makefullsubgraph(target,[x for x in target.nodes() if target.successors(x)])

    solutions = []

    def couldmap(x,y):
        '''True if the types match, or both are functions'''
        tx,ty = base.node[x]['type'],target.node[y]['type']
        return tx==ty or isfunction(tx) and isfunction(ty)

    #make pools
    types = set(filter(lambda x:not isfunction(x),[base.node[x]['type'] for x in pseudobase.nodes()]+[target.node[x]['type'] for x in pseudotarget.nodes()]))

    pools = [(functionsbase,functionstarget)]
    for t in types:
        bt = [x for x in pseudobase.nodes() if base.node[x]['type']==t]
        tt = [x for x in pseudotarget.nodes() if target.node[x]['type']==t]
        pools.append((bt,tt))

    result['inputsize'] = bijectionsproductsize(pools)

    if result['inputsize']>maxsearchspace:
        return result

    for m in bijectionsproduct(pools):
        # 3 if Gm and G'm are pseudo-concept-graphs
        gmap = makegmap(m)
        if not gmap: #no conflicting assignments
            continue
        if not supported(gmap,pseudobase,pseudotarget): #all children (except for leafs) must be in the gmap
            continue
        # 4 L=L'={}
        Lb,Lt,c = {},{},True
        # 5 Obj(G,Gm) is the set of leafs in G that have at least one of their predicates in Gmap
        for v in leafsbase:
            for p in set(base.predecessors(v)).intersection(set(gmap.keys())):
                Lb[(gmap[p],base.node[p]['connections'].index(v))] = v
        # 8 Obj(G',Gm') is the set of leafs in G' that have at least one of their predicates in Gmap
        for v in leafstarget:
            for p in set(target.predecessors(v)).intersection(set(gmap.values())):
                Lt[(p,target.node[p]['connections'].index(v))] = v
        # 11 if L = L'
        if set(Lb.keys())!=set(Lt.keys()):
            continue
        for key,bc in Lb.iteritems():
            tc = Lt[key]
            if bc in gmap and gmap[bc]!=tc: #if this object is already mapped to a different target, break
                c = False
                break
            gmap[bc]=tc
            if gmap.values().count(tc)>1: #if a target has been mapped twice, break
                c = False
                break
        if not c or not supported(gmap,base,target): #do we support all predicates?
            continue
        gmap = validate(gmap,base)
        s = score(base.subgraph(gmap.keys()))
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
    print '\nFPT-P found %s optimal results\n'%len(solutions)
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


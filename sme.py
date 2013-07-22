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

def run(base,target,EXHAUSTIVE=True,maxsearchspace=100000):

    #start logging
    logger = Logger()

    finalresult = {}

    #construct match hypotheses (mh)

    def filterrules(mh):
        '''
            Checks if these two candidates are of the same type and are both expressions
        '''
        bc,tc=mh
        tx,ty = base.node[bc]['type'],target.node[tc]['type']
        return len(base.successors(bc))==len(target.successors(tc))>1 and tx==ty
        
    def internalrules(mh):
        '''
            Returns a set of match hypotheses following from the internal rules
        '''
        bc,tc=mh
        result = set()
        #compatible arguments?
        if base.successors(bc) and target.successors(tc): #we are dealing with 'expressions', not 'entities'
            if base.node[bc]['ordered'] and target.node[tc]['ordered']: #ordered
                ev = zip(base.node[bc]['connections'], target.node[tc]['connections'])
            else: #unordered?
                ev = itertools.product(base.successors(bc), target.successors(tc))
            for bchild,tchild in ev:
                if len(base.successors(bchild))==len(target.successors(tchild))<=1:
                    #both children are either entities or functions (arity one or less)
                    tx,ty = base.node[bchild]['type'],target.node[tchild]['type']
                    if (not base.successors(bchild) and not target.successors(tchild)) or (isfunction(tx) and isfunction(ty)) or (tx==ty):
                        result.add((bchild,tchild))
        return result

    def buildhypothesisstructure():
        #first try every combination to get mh roots
        mhs = set()
        ev = filter(filterrules,itertools.product(base.nodes(),target.nodes()))
        #for root in ev:
        #    mhs.add(root)
        #work downwards to find other mhs
        justified = {}
        while ev:
            c = ev.pop(0)
            ir = internalrules(c)
            mhs.add(c)
            if ir:
                justified[c] = set()
                for r in ir:
                    mhs.add(r)
                    justified[c].add(r)
                    ev.append(r)
        #build mhstructure
        mhstructure = {}
        for mh in mhs:
            mhstructure[mh] = {'base':mh[0],'target':mh[1],'emaps':set()}
            #initial emaps is just ourselves if we are one, for the rest. this will be filled later
            if not base.successors(mh[0]) and not target.successors(mh[1]) or isfunction(base.node[mh[0]]['type']) and isfunction(target.node[mh[1]]['type']):
                mhstructure[mh]['emaps'].add(mh)
            #nogood is every mh mapping same target or base
            nogood = set()
            for x in mhs:
                if mh!=x and (mh[0]==x[0] or mh[1]==x[1]):
                    nogood.add(x)
            mhstructure[mh]['nogood'] = nogood
            #our children are mhs that map our arguments (so children does not equal our entire set of descendants)
            mhstructure[mh]['children'] = set()#justified.get(mh,set()) #entities justified by this one
            for x in mhs:
                if mh!=x and x[0] in base.node[mh[0]]['connections'] and x[1] in target.node[mh[1]]['connections'] and base.node[mh[0]]['connections'].index(x[0])==target.node[mh[1]]['connections'].index(x[1]):
                    mhstructure[mh]['children'].add(x)
            
        #propagate nogood and emaps upwards
        def collect(x,item):
            r = mhstructure[x][item]
            for child in mhstructure[x]['children']:
                r = r.union(collect(child,item))
            return r
        for mh in mhstructure:
            mhstructure[mh]['emaps'] = collect(mh,'emaps')
            mhstructure[mh]['nogood'] = collect(mh,'nogood')
        return mhstructure

    def consistent(mh):
        #true if mh is consistent, meaning none of its emaps are in its nogoods
        return not mhstructure[mh]['emaps'].intersection(mhstructure[mh]['nogood'])

    def supported(mh):
        #true if a mh is supported, meaning for every mh, its arguments are in its children (ordered version)
        for bc,tc in zip(base.node[mh[0]]['connections'],target.node[mh[1]]['connections']):
            if (bc,tc) not in mhstructure[mh]['children']:
                return False
        #recurse on offspring
        for x in mhstructure[mh]['children']:
            if not supported(x):
                return False
        return True

    def findroots():
        '''Returns only the root hypotheses, ie. those that are not children of any other hypothesis.'''
        allchildren = set()
        for x in mhstructure:
            allchildren = allchildren.union(mhstructure[x]['children'])
        return set(mhstructure.keys()).difference(allchildren)

    def collectchildren(root):
        '''Returns a set of all descendants of a root.'''
        r = set([root])
        for child in mhstructure[root]['children']:
            r = r.union(collectchildren(child))
        return r

    def makegmap(root):
        gmap = {}
        gmap['roots'] = set([root])
        gmap['mhs'] = collectchildren(root)
        gmap['nogood'] = mhstructure[root]['nogood']
        gmap['emaps'] = mhstructure[root]['emaps']
        return gmap

    def computeinitialgmaps():
        '''Given match hypothesis information, builds a set of initial gmaps.'''
        gmaps = set()
        def formgmap(mh):
            if len(base.successors(mh[0]))<=1:return set() #only work on relations
            #print mh,supported(mh),consistent(mh),mhstructure[mh]['children']
            if consistent(mh) and supported(mh): return set([mh])
            else: #recurse on offspring
                result = set()
                for child in mhstructure[mh]['children']:
                    result = result.union(formgmap(child))
                return result
        for root in findroots():
            gmaps = gmaps.union(formgmap(root))
        gmaps = map(makegmap,gmaps)
        return gmaps

    def gmapsconsistent(gma,gmb):
        return not gma['mhs'].intersection(gmb['nogood']).union(gmb['mhs'].intersection(gma['nogood']))

    def gmapsetsconsistent(seta,setb):
        '''True if both collections of gmaps are fully consistent with each other.'''
        for gma,gmb in itertools.product(seta,setb):
            if not gmapsconsistent(gma,gmb):return False
        return True

    def gmapsetinternallyconsistent(seta):
        '''True if the given set of gmaps is internally consistent.'''
        return gmapsetsconsistent(seta,seta)

    def scoregmap(gmap):
        '''Compute the gmap score by converting it to a graph'''
        return score(base.subgraph([x[0] for x in gmap['mhs']]))

    def combinegmaps(gmaps,exhaustive=1):
        '''1) Exhaustive: Combine all gmaps in all maximal, consistent ways.'''
        if exhaustive:
            consistentsets = []
            for x in powerset(gmaps):
                if x and gmapsetinternallyconsistent(x):
                    consistentsets.append(x)
            return consistentsets
        '''2) Heuristic; Start with highest scoring gmap, then add next highest if consistent'''
        consistentset = []
        gmaps = sorted(gmaps,key=scoregmap,reverse=True)
        for gmap in gmaps:
            if gmapsetinternallyconsistent(consistentset+[gmap]):
                consistentset.append(gmap)
        return [consistentset]

    def mergegmaps(consistentsets):
        '''Given a collection of sets of gmaps, merges the gmaps in each set into a single gmap.'''
        gmaps = []
        for x in consistentsets:
            d = {'root':set(),'mhs':set(),'nogood':set(),'emaps':set()}
            for gmap in x:
                for key,value in gmap.iteritems():
                    d[key] = d.get(key,set()).union(value)
            if d['mhs'] not in [x['mhs'] for x in gmaps]:
                gmaps.append(d)
        return gmaps

    def scoregmaps(gmaps):
        for gmap in gmaps:
            gmap['score'] = scoregmap(gmap)

    mhstructure = buildhypothesisstructure()
    gmaps = computeinitialgmaps()

    #compute search space for intractable step
    finalresult['inputsize'] = powersetsize(len(gmaps))

    if EXHAUSTIVE and finalresult['inputsize']>maxsearchspace:
        return finalresult
    
    consistentsets = combinegmaps(gmaps,EXHAUSTIVE)
    gmaps = mergegmaps(consistentsets)

    if not gmaps:
        #print 'SME-%s found 0 results\n score: 0'%('E' if EXHAUSTIVE else 'H')
        finalresult['solutions'] = []
        finalresult['score'] = 0
    else:
        scoregmaps(gmaps)
        maxscore = max(gmaps,key=lambda x:x['score'])['score']

        solutions = [dict(gmap['mhs']) for gmap in gmaps if gmap['score']==maxscore]

        finalresult['score'] = maxscore
        finalresult['solutions'] = solutions

        '''
        print '\nSME-%s found %s optimal results\n'%('E' if EXHAUSTIVE else 'H', len(solutions))
        d = ['name','type']
        for i,s in enumerate(solutions):
            print 'solution',i+1,'score:',s['score']
            for b,t in sorted(s['mhs']):
                print '\t',[str(base.node[b][x]) for x in d],'\t-->\t',[str(target.node[t][x]) for x in d]
            print
        '''

    #end logging
    finalresult['time'] = logger.time()
    
    return finalresult

def runsme(base,target,maxsearchspace=100000):
    return run(base,target,True,maxsearchspace)

def runsmeh(base,target,maxsearchspace=100000):
    return run(base,target,False,maxsearchspace)

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

import math,itertools,copy
import networkx as nx
import psutil,os

'''
This module contains some common functions that are used by all algorithms, for example keeping track of their CPU time.
'''



class Logger:
    '''
        A logger reporting cpu time everytime it's string function is called
    '''

    def __init__(self):
        self.p = psutil.Process(os.getpid())
        self.startcpu = self.p.get_cpu_times()

    def __str__(self):
        endcpu = self.p.get_cpu_times()
        return 'cpu-time: %s'%(sum(endcpu)-sum(self.startcpu),)

    def time(self):
        endcpu = self.p.get_cpu_times()
        return sum(endcpu)-sum(self.startcpu)




def printsolutions(solutions,base,target,name='Algorithm'):
    print '\n%s found %s optimal results\n'%(name,len(solutions))
    d = ['name','type']
    for i,gmap in enumerate(solutions):
        print 'solution',i+1
        for b,t in gmap.iteritems():
            print '\t',[str(base.node[b][x]) for x in d],'\t-->\t',[str(target.node[t][x]) for x in d]
        print


def score(graph,trd=1,lm=1,pval=lambda x:1):
    '''SES Score'''
    def val(v):
        children = graph.successors(v)
        return (pval(v) if children else lm) + sum([trd*val(w) for w in graph.predecessors(v)])
    return sum(map(val,graph.nodes()))

def isfunction(ptype):
    return ptype.startswith('function')

def powersetsize(n):
    '''size of powerset is the sum of #combinations per set size (0 to n)'''
    size = 1 #empty set
    for r in range(1,n+1):size += math.factorial(n)/(math.factorial(r)*math.factorial(n-r))
    return size

def bijections(x,y):
    for r in range(1+min([len(x),len(y)])):
        for b,t in itertools.product(itertools.permutations(x,r),itertools.combinations(y,r)):
            yield zip(b,t)

def bijectionsproduct(pools):
    bpools = [bijections(x,y) for x,y in pools]
    for f in itertools.product(*bpools):
        yield itertools.chain.from_iterable(f)

def bijectionssize(b,t):
    b,t = len(b),len(t)
    def perms(n,k): return math.factorial(n)/math.factorial(n-k)
    def combs(n,k): return math.factorial(n)/math.factorial(k)/math.factorial(n-k)
    return sum([perms(b,r)*combs(t,r) for r in range(1+min([b,t]))])

def bijectionsproductsize(pools):
    return reduce(lambda x,y:x*y, [bijectionssize(b,t) for b,t in pools])
    
    

def powerset(iterable):
    "powerset([1,2,3]) --> () (1,) (2,) (3,) (1,2) (1,3) (2,3) (1,2,3)"
    s = list(iterable)
    return itertools.chain.from_iterable(itertools.combinations(s, r) for r in range(len(s)+1))

def validate(gmap,ps):
    '''remove all objects and attributes/functions that have no predecessors'''
    graph = ps.subgraph(gmap.keys())
    for i in (1,0): #first work on attributes/functions, then on objects
        for x in gmap.keys():
            if len(graph.successors(x))==i and not graph.predecessors(x):
                del(gmap[x])
                graph.remove_node(x)
    return gmap

def makefullsubgraph(graph,nodes):
    result = copy.deepcopy(graph).subgraph(nodes)
    for n in result.nodes():
        result.node[n]['connections'] = [c for c in result.node[n]['connections'] if c in result.nodes()]
    return result

def makegmap(mapping):
    '''returns a gmap from a set of mappings from basenode to targetnode
    returns False if this is not possible due to double assignments'''
    gmap = {}
    for x,y in mapping:
        if x in gmap.keys() or y in gmap.values():
            return False
        gmap[x] = y
    return gmap

def supported(gmap,psbase,pstarget):
    '''if the gmap is supported (whether for all items, the successors in the origional predicate structures
    map to the same items.
    '''
    for x,y in gmap.iteritems():
        if psbase.node[x]['ordered']:
            #ordered, so the successors must match in the same order
            for bc,tc in zip(psbase.node[x]['connections'],pstarget.node[y]['connections']):
                if bc not in gmap or not gmap[bc]==tc:
                    return False
        else:
            #unordered, so check if all children of x are in target
            targets = set()
            for bc in psbase.successors(x):
                if bc in gmap:
                    targets.add(gmap[bc])
                else:
                    return False
            for tc in pstarget.successors(y):
                if tc not in targets:
                    return False
    return True

def equal(gmapa,gmapb):
    '''true if gmapa and gmapb are equal'''
    if set(gmapa.keys()).symmetric_difference(set(gmapb.keys())):
        return False
    for k in gmapa.keys():
        if gmapa[k]!=gmapb[k]:
            return False
    return True

def member(gmap,gmapset):
    '''true if gmap is in gmapset'''
    for x,gmapb in gmapset:
        if equal(gmap,gmapb):
            return True
    return False

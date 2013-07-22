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

import argparse,ConfigParser,random,math,re,itertools,copy
import networkx as nx


def exportasgraph(ps,core=set(),f='ps.svg'):
    import pygraphviz as pgv
    G=pgv.AGraph(directed=True)
    if core:core = core.nodes()
    for x in ps.nodes():
        G.add_node(x,
                label= '%s :: %s'%(ps.node[x]['name'],ps.node[x]['type']),
                fillcolor= 'lightgray' if x in core else 'white',
                style= 'filled',
                color= 'brown' if len(ps.successors(x)) > 3 else ['blue','green','purple','red'][len(ps.successors(x))])
    for x in ps.edges():G.add_edge(x)
    G.layout(prog='dot')
    G.draw(f)

def exportaspickle(ps,name):
    nx.write_gpickle(ps,name)


def createheightdist(heights,shape,p):
    '''
        Returns a list of number of predicates per height level based on h,p and shape
    '''
    if shape == 'square':heightdist = [1 for x in range(heights)]
    elif shape == 'diamond':heightdist = [0.5*heights+0.5-abs(0.5*heights-0.5-x) for x in range(heights)]
    elif shape == 'inverse':heightdist = [1+x for x in range(heights)]
    elif shape == 'triangle':heightdist = [heights-x for x in range(heights)]
    if len(heightdist)>p:raise Exception('<h> can not be larger than <p>')
    m = float(sum(heightdist))
    heightdist = [int(math.ceil(p*x/m)) for x in heightdist]
    #remove some predicates at random to end up with <p> predicates
    for i in random.sample([i for i,v in enumerate(heightdist) if v>1], sum(heightdist)-p):heightdist[i]-=1
    return heightdist

def createtypedist(types,shape,max_arity):
    '''
        Returns a list of predicate types with their arity
    '''
    if types<max_arity:raise Exception('<a> can not be larger than <t>')
    #create type-arity dist, uniform for now
    if shape=='random':typedist = [1 for x in range(max_arity)]
    elif shape=='exp':typedist = [2**(max_arity-x-1) for x in range(max_arity)]
    m,predicatetypes = float(sum(typedist)),[]
    typedist = [int(math.ceil(types*x/m)) for x in typedist]
    #remove some predicate types at random to end up with <t> predicate types
    for i in random.sample([x for x,v in enumerate(typedist) if v>1], sum(typedist)-types):typedist[i]-=1
    for i,x in enumerate(typedist):predicatetypes.extend([i+1 for j in xrange(x)])
    return predicatetypes

def createpools(config):
    '''
        Creates predicate and objectpools
    '''
    o = int(config['objects'])
    p = int(config['predicates'])
    a = int(config['max_arity'])
    if o>p: raise Exception('<o> can not be larger than <p>')
    functionchance = float(config['chance_function'])
    #create a height distribution if we were not given one:
    heightdist = config.get('heightlist',[])
    if not heightdist:
        h = int(config['height'])
        shape = config.get('heightshape','square')
        if not shape:shape = 'square'
        heightdist = createheightdist(h,shape,p)
    #create a type distribution if we were not given one:
    predicatetypes = config.get('typelist',[])
    if not predicatetypes:
        t = int(config['types'])
        shape = config.get('typeshape','random')
        if not shape:shape = 'random'
        predicatetypes = createtypedist(t,shape,a)
    #start with the objectpool, which is trivial
    objectpool = [{'name':'o%s'%i,'type':'object','arity':0,'height':0,'ordered':True,'connections':[]} for i in xrange(o)]
    #create the predicatepool
    predicatepool = []
    for h,x in enumerate(heightdist):
        height = h+1
        maxa = len(predicatepool)+o #maximum arity for this level
        mina = 1
        if h: mina=2 #minimum arity for this level (makes sure functions and relations link to objects)
        for p in xrange(x):
            pt,arity = random.choice([(x,v) for x,v in enumerate(predicatetypes) if mina<=v<=maxa])
            ordered = True #TODO make this a parameter
            pt = 'function%s'%pt if arity==1 and random.random() < functionchance else 'type%s'%pt
            predicatepool.append({
                        'name':'p%s'%len(predicatepool),
                        'type':pt,
                        'arity':arity,
                        'height':height,
                        'ordered':ordered,
                        })
    return objectpool,predicatepool

def addobject(ps,o):
    ps.add_node(o['name'])
    for k,v in o.iteritems():
        ps.node[o['name']][k] = v
    return True

def addpredicate(ps,predicate,p2=nx.DiGraph()):
    #add the node and its data
    ps.add_node(predicate['name'])
    for k,v in predicate.iteritems():
        ps.node[predicate['name']][k] = v
    allcandidates = [x for x in ps.nodes() if ps.node[x]['height']<predicate['height']]
    allcandidates = list(itertools.combinations(allcandidates,predicate['arity']))
    random.shuffle(allcandidates)
    candidates = []
    #move candidates that connect 1(!) unconnected object to the front of the list
    #this makes it more likely to create connected graphs
    for c in allcandidates:
        if predicate['arity']<2 or sum([bool(ps.successors(x) or ps.predecessors(x)) for x in c])!=1:
            candidates.append(c)
        else:
            candidates.insert(0,c)
    while candidates:
        connections = candidates.pop(0)
        # at least one of them must be at 1 height level below ourselves
        if not any([ps.node[c]['height'] == predicate['height']-1 for c in connections]):
            continue
        # the same structure must not exist yet
        if any([set(ps.successors(x))==set(connections) for x in ps.nodes() if ps.node[x]['type']==predicate['type']]):
            continue
        # this must also hold for the second ps (base), if it is given
        if any([set(p2.successors(x))==set(connections) for x in p2.nodes() if p2.node[x]['type']==predicate['type']]):
            continue
        # we have a match, so add the connections and return
        for c in connections:
            ps.add_edge(predicate['name'],c)
        ps.node[predicate['name']]['connections'] = list(connections)
        return True
    return False


def generatepredicatestructure(config):
    connected = False
    max_attempts = int(config['max_attempts'])
    attempts = 0
    while (not connected or errors) and attempts<max_attempts:
        objectpool,predicatepool = createpools(config)
        attempts += 1
        ps = nx.DiGraph()
        errors = False
        #create objects
        for o in objectpool:
            addobject(ps,o)
        #start with height 1 and work up to max height
        for h in xrange(1,1+max([x['height'] for x in predicatepool])):
            if errors:break
            predicates = [x for x in predicatepool if x['height']==h]
            random.shuffle(predicates)
            for p in predicates:
                if not addpredicate(ps,p):
                    errors = True
                    break
        connected = nx.is_connected(nx.Graph(ps))
    if not connected:
        raise Exception('no connected predicate structure found')
    return ps,predicatepool

def extractcore(ps,config):
    connected = False
    max_attempts = int(config['max_attempts'])
    preservation = float(config['preservation'])
    decay = float(config['preservationdecay'])
    attempts = 0
    while not connected and attempts<max_attempts:
        core,h,preserved = nx.DiGraph(),0,[]
        attempts+=1
        while not h or preserved:
            candidates = [d for x,d in ps.nodes(data=True) if d['height']==h and all([y in core for y in ps.successors(x)])]
            p = int(round(len(candidates)*(preservation-h*decay)))
            preserved = random.sample(candidates,min((len(candidates),p)))
            for d in preserved:
                core.add_node(d['name'])
                for k,v in d.iteritems():
                    core.node[d['name']][k] = v
                for x in ps.node[d['name']]['connections']:
                    core.add_edge(d['name'],x)
                core.node[d['name']]['connections'] = [x for x in ps.node[d['name']]['connections']]
            h+=1
        connected = not core.nodes() or nx.is_connected(nx.Graph(core))
    if not connected:
        raise Exception('no connected core predicate structure found')
    #if not checkconnections(core): exit('Core extraction went wrong')
    return core

def regrow(core,ps,predicatepool,config):
    max_attempts = int(config['max_attempts'])
    scaling = float(config['scaling'])
    if scaling>1.0:scaling=1.0
    #add more objects if needed
    psobjects = len([x for x,d in ps.nodes(data=True) if not d['height']])
    cobjects = len([x for x,d in core.nodes(data=True) if not d['height']])
    m = int(round((psobjects-cobjects)*scaling))
    newcorebase = nx.DiGraph(core)
    for i in xrange(m):
        addobject(newcorebase,{'name':'+o%s'%(psobjects+i,),'type':'object','arity':0,'height':0,'ordered':True,'connections':[]})
    connected = False
    attempts = 0
    while (not connected or errors) and attempts<max_attempts:
        attempts+=1
        errors = 0
        pid = 0
        newcore = copy.deepcopy(newcorebase)
        for h in xrange(1,max([ps.node[x]['height'] for x in ps.nodes()])):
            if errors:break
            mina = 1
            if h>1:mina = 2 #functions and relations may only link to objects
            predicates = [x for x in predicatepool if x['height']==h and x['arity']>=mina and x['name'] not in newcore.nodes()]
            psobjects = len([x for x in ps.nodes() if ps.node[x]['height']==h]) #the number of ps we have in the base
            cobjects = len([x for x in core.nodes() if core.node[x]['height']==h]) #the number objects we have in core
            m = int(round((psobjects-cobjects)*scaling)) #how many we should add
            if m>len(predicates):m=len(predicates) #insurance for if we can not grow large enough
            for p in random.sample(predicates,m):
                p['name'] = '+p%s'%pid
                #try to connect the predicate to the newcore
                if not addpredicate(newcore,p,ps):
                    errors+=1
                    break
                pid += 1
        #check for connectivity
        connected = nx.is_connected(nx.Graph(newcore))
    if not connected:
        raise Exception('no connected predicate structure found while regrowing')
    #if not checkconnections(newcore): exit('Newcore extraction went wrong')
    return newcore

def checkconnections(ps):
    for x in ps.nodes():
        if set(ps.successors(x)) != set(ps.node[x]['connections']):
            return False
    return True

def generate(config):
    try:
        #print 'Creating base predicate structure..'
        base,predicatepool = generatepredicatestructure(config)
        #print 'Extracting core analogy..'
        core = extractcore(base,config)
        #print 'Deriving target predicate structure..'
        target = regrow(core,base,predicatepool,config)
    except KeyboardInterrupt:
        raise
    except Exception as e:
        return False
    return base,target  
    

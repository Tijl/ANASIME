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


from subprocess import call
import random,sys,re,os,itertools,time
import generator
from utils import *
from datetime import datetime

def prepareoutfile(filename,dimensions):

    #header for the resultfile
    header = ' '.join(dimensions)+' Trial Algorithm Time MaxMem Inputsize Score ScoreDistance'

    #backup results.data if needed:
    if os.path.exists(filename) and len(open(filename).read().splitlines())>10:
        start,end = filename.split('.',1)
        call(['cp -v results.data BACKUP/%s_%s.%s'%(start,datetime.now().strftime('%Y%m%d%H%M%S'),end)],shell=True)

    #see if we can continue where we left off
    print 'looking for a %s file..'%filename
    processed = []
    try:
        ch = open(filename).read().splitlines()
        if ch[0]==header: 
            for x in ch[1:]: processed.append(x.split()[:len(dimensions)+1])
        print 'found %s file with %s entries'%(filename,len(processed))
    except: pass

    #create a results file if we are starting over
    if not processed:
        print 'creating new %s file..'%filename
        open(filename,'w').write(header)
    
    return processed

def testalgorithms(prefix,base,target,names,algorithms,outfilename):
    results = []
    optimal = 0
    arb = []
    found = False
    for an,a in zip(names,algorithms):
        ar = apply(a,[base,target])
        arb.append(ar)
        if 'score' in ar:
            found = True
        optimal = max((optimal,ar.get('score',0)))
        results.append(prefix+[an]+[ar.get(x,'-') for x in ('time','memory','inputsize','score')])
    for x in results:
        if x[-1]=='-': x.append('-')
        else: x.append(optimal-int(x[-1]))
    open(outfilename,'a').write('\n'+'\n'.join([' '.join(map(str,x)) for x in results]))

def writeemptyresult(prefix,names,outfilename):
    #in case generation has failed, write nothing in the results
    results = [prefix+[an,'-','-','-','-','-'] for an in names]
    open(outfilename,'a').write('\n'+'\n'.join([' '.join(map(str,x)) for x in results]))

def generate(cfg,ATTEMPTS,keepgoing=False):
    fails = 0
    while (keepgoing or fails<ATTEMPTS):
        s = generator.generate(cfg)
        if s:return s
        else:fails+=1
        print 'generation failed:',fails,'/',ATTEMPTS
        if fails > 50:break
    return False #did not generate

def run(A,D,TRIALS,ATTEMPTS,OUTFILENAME):
    
    #proper/readable names for the algorithms
    algorithms = [x[1] for x in A]
    names = [x[0] for x in A]

    dimensions = [x[0] for x in D]
    dimensionvalues = [x[1] for x in D]

    tests = list(itertools.product(*dimensionvalues))
    TESTS = len(tests)
    print 'preparing to do %s trials (%s conditions)'%(TESTS*TRIALS,TESTS)
    del(tests)

    processed = prepareoutfile(OUTFILENAME,dimensions)

    config = {}
    config['max_attempts']=10

    for index,d in enumerate(itertools.product(*dimensionvalues)):
        s = False #keep track of whether we have successfully generated at least one ps-pair
        #update configuration values
        for i,var in enumerate(dimensions):
            config[var] = d[i]
                
        #start testing

        if not index%500:print '%s/%s'%(index,TESTS)
        for trial in range(1,TRIALS+1):
            prefix = list(d)+[trial] 
            strprefix = map(str,prefix)
            if strprefix in processed: continue
            if not trial%10:
                print 'Sleep 10s...'
                time.sleep(10)
                print '%s/%s'%(index,TESTS),'\t',' '.join(['%s'%(x,) for x in dimensions+['Trial']])
            print '%s/%s'%(index,TESTS),'\t',' '.join(['%s'%(x,) for x in prefix])
            s = generate(config,ATTEMPTS,s)
            
            if s:
                base,target = s
                s = True
                try:testalgorithms(prefix,base,target,names,algorithms,OUTFILENAME)
                except:
                    generator.exportaspickle(base,'base.ps')
                    generator.exportasgraph(base,f='base.svg')
                    generator.exportaspickle(target,'target.ps')
                    generator.exportasgraph(target,f='target.svg')
                    print config
                    raise
            else:writeemptyresult(prefix,names,OUTFILENAME)

        

        




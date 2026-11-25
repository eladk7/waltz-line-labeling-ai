from src.loader import load_csp
from src.events import CancellationToken
from src.waltz import waltz
from src.hill_climbing import random_restart_hc
from src.genetic_algorithm import genetic_algorithm
from src.playback import replay
from src.validation import objective

for solver,params in [(waltz,{}),(random_restart_hc,{'S':5,'return_stats':True}),(genetic_algorithm,{'p_m':.15})]:
    csp=load_csp('instances/cube.json'); events=[]
    result,stats=solver(csp,on_event=events.append,**params)
    assert objective(csp,result)==0 and replay(events,csp).solved
    token=CancellationToken(); token.cancel(); events=[]
    solver(csp,on_event=events.append,cancel=token,**params)
    assert replay(events,csp).status=='CANCELLED'
    print(solver.__name__, 'events and cancellation passed')

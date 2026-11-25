import argparse
import csv
import json
import platform
import random
from pathlib import Path
from src.loader import load_csp
from src.validation import objective
from src.waltz_enumeration import enumerate_waltz
from src.hill_climbing import random_assignment, random_restart_hc
from src.genetic_algorithm import random_chromosome, decode, genetic_algorithm

ROOT = Path('instances/benchmark')
SEEDS = [42,43,44,45,46]
METHODS = ['Waltz','HC','GA']

def run(item, method, seed, timeout, cap):
    csp = load_csp(ROOT / item['file'])
    if method == 'Waltz':
        solutions, stats = enumerate_waltz(csp,N=1,seed=seed,timeout=timeout)
        assignment = solutions[0] if solutions else None
        reason = 'SOLVED' if solutions else stats.status
    elif method == 'HC':
        assignment, stats = random_restart_hc(csp,budget=cap+1,seed=seed,S=10,return_stats=True,max_evaluations=cap,timeout=timeout)
        reason = stats.stop_reason
    else:
        assignment, stats = genetic_algorithm(csp,P=100,p_c=.8,p_m=.02,seed=seed,max_evaluations=cap,timeout=timeout)
        reason = stats.stop_reason
    h = objective(csp,assignment) if assignment is not None else None
    solved = h == 0
    assert solved == (reason == 'SOLVED'), (method,reason,h)
    assert not (solved and item['expected']=='UNSAT')
    evaluations = getattr(stats,'objective_evaluations',None)
    assert evaluations is None or evaluations <= cap
    return dict(instance=item['name'],group=item['group'],edges=item['edges'],expected=item['expected'],method=method,seed=seed,solved=solved,stop_reason=reason,runtime_ms=stats.runtime_ms,best_h=h,objective_evaluations=evaluations,constraint_checks=stats.constraint_checks,search_nodes=getattr(stats,'search_nodes',None),decisions=getattr(stats,'decisions',None),backtracks=getattr(stats,'backtracks',None),max_depth=getattr(stats,'max_depth',None),decided_by_propagation=getattr(stats,'decided_by_propagation',None),restarts=getattr(stats,'restarts',None),steps=getattr(stats,'steps',None),sideways_steps=getattr(stats,'sideways_steps',None),generations=getattr(stats,'generations',None))

def main():
    parser=argparse.ArgumentParser(); parser.add_argument('--smoke',action='store_true'); args=parser.parse_args()
    items=json.loads((ROOT/'manifest.json').read_text(encoding='utf-8-sig'))
    assert len(items)==15
    for item in items:
        csp=load_csp(ROOT/item['file'])
        for seed in SEEDS:
            assert random_assignment(csp,random.Random(seed))==decode(csp,random_chromosome(csp,random.Random(seed)))
    print('Shared initialization: 75/75 PASS',flush=True)
    timeout,cap=(.2,500) if args.smoke else (10,100000)
    selected=[items[0],items[-1]] if args.smoke else items
    seeds=SEEDS[:1] if args.smoke else SEEDS
    for method in METHODS: run(items[0],method,0,timeout,cap)
    out=Path('results'); out.mkdir(exist_ok=True)
    path=out/('benchmark_smoke.csv' if args.smoke else 'benchmark.csv')
    total=len(selected)*len(seeds)*len(METHODS); count=0
    with path.open('w',newline='',encoding='utf-8') as f:
        writer=None
        for item in selected:
            for seed in seeds:
                for method in METHODS:
                    row=run(item,method,seed,timeout,cap)
                    if writer is None:
                        writer=csv.DictWriter(f,fieldnames=list(row)); writer.writeheader()
                    writer.writerow(row); f.flush(); count+=1
                    print(f"{count}/{total} {item['name']} {seed} {method} {row['stop_reason']} h={row['best_h']}",flush=True)
    path.with_suffix('.json').write_text(json.dumps(dict(seeds=seeds,timeout=timeout,max_evaluations=cap,warmups=3,python=platform.python_version(),platform=platform.platform(),HC_S=10,GA_P=100,p_c=.8,p_m=.02),indent=2),encoding='utf-8')
    print(f'Completed {count}/{total}: {path}')

if __name__=='__main__': main()

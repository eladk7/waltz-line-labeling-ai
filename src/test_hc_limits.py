from src.loader import load_csp
from src.hill_climbing import random_restart_hc
from src.validation import objective

csp = load_csp('instances/cube.json')
for cap in (0, 1, 2, 10, 28, 100):
    a,s = random_restart_hc(csp, seed=42, S=10, max_evaluations=cap, return_stats=True)
    assert s.objective_evaluations <= cap
    assert s.stop_reason in ('SOLVED','EVALUATION_LIMIT')
    if a is not None:
        assert objective(csp,a) == s.best_h
    print('Evaluation cap',cap,'PASS',s.stop_reason,s.objective_evaluations)
a,s = random_restart_hc(csp, timeout=0, return_stats=True)
assert a is None and s.stop_reason == 'TIME_LIMIT' and s.objective_evaluations == 0
print('Timeout PASS')
csp.edges['e1'].domain = ('R',)
a,s = random_restart_hc(csp, seed=42, S=10, max_evaluations=100000, return_stats=True)
b,t = random_restart_hc(csp, seed=42, S=10, max_evaluations=100000, return_stats=True)
assert a == b and s.objective_evaluations == t.objective_evaluations
assert a['e1'] == 'R' and objective(csp,a) == s.best_h == 0 and s.stop_reason == 'SOLVED'
print('Reproducibility, fixed edge and solution PASS')

import copy
import json
from pathlib import Path
from src.loader import load_csp
from src.validation import objective
from src.waltz_enumeration import enumerate_waltz

ROOT = Path('instances')
OUT = ROOT / 'benchmark'

def polygon(points):
    n = len(points)
    edges = [dict(id=f'e{i}', u=f'v{i}', v=f'v{(i+1)%n}') for i in range(n)]
    nodes = [dict(id=f'v{i}', type='L', edges=[f'e{i}', f'e{(i-1)%n}'], x=x,y=y) for i,(x,y) in enumerate(points)]
    return dict(edges=edges,junctions=nodes), {e['id']:'R' for e in edges}

def occlusion():
    a, sa = polygon([(0,0),(2,0),(2,1),(2,2),(0,2)])
    b, sb = polygon([(4,0),(6,0),(6,2),(4,2),(4,1)])
    data, sol = combine([(a,sa),(b,sb)], spacing=0)
    u,v='c0_v2','c1_v4'
    data['edges'].append(dict(id='bridge',u=u,v=v))
    for j in data['junctions']:
        if j['id'] in (u,v):
            j['type']='T'; j['edges'].append('bridge')
    sol['bridge']='+'
    return data,sol

def combine(parts, spacing=8):
    data=dict(edges=[],junctions=[]); sol={}
    for i,(part,known) in enumerate(parts):
        prefix=f'c{i}_'
        for e in part['edges']:
            data['edges'].append(dict(id=prefix+e['id'],u=prefix+e['u'],v=prefix+e['v']))
        for j in part['junctions']:
            node=copy.deepcopy(j); node['id']=prefix+j['id']; node['edges']=[prefix+e for e in j['edges']]; node['x']+=spacing*i
            data['junctions'].append(node)
        sol.update({prefix+k:v for k,v in known.items()})
    return data,sol

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    cube=json.loads((ROOT/'cube.json').read_text(encoding='utf-8-sig'))
    c=(cube,{f'e{i}': 'R' if i<=6 else '+' for i in range(1,10)})
    concave=(cube,{**c[1],'e1':'-','e2':'-'})
    tri=polygon([(0,0),(2,0),(1,2)])
    rect=polygon([(0,0),(3,0),(3,2),(0,2)])
    notch=polygon([(0,0),(3,0),(3,1),(1,1),(1,3),(0,3)])
    t=occlusion()
    specs=[('small_triangle',[tri]),('small_rectangle',[rect]),('small_cube',[c]),('small_T',[t]),('medium_concave',[concave,notch]),('medium_mixed',[c,t]),('medium_polygons',[tri,rect,notch,rect]),('medium_cubes',[c,concave,c]),('large_mixed',[c,t,notch,c]),('large_cubes',[c]*4),('large_T',[t]*4),('large_varied',[tri,rect,notch,c,t,c]),('unsat_small',[c]),('unsat_medium',[c,t]),('unsat_large',[c]*4)]
    manifest=[]
    for name,parts in specs:
        data,known=combine(parts); data['name']=name
        unsat=name.startswith('unsat')
        # Force a concave interpretation in the dedicated example.
        if name=='medium_concave':
            for e in data['edges']:
                if e['id'] in ('c0_e1','c0_e2'): e['domain']=['-']
        if unsat:
            next(e for e in data['edges'] if e['id']=='c0_e7')['domain']=['-']
        path=OUT/(name+'.json'); path.write_text(json.dumps(data,indent=2),encoding='utf-8')
        csp=load_csp(path)
        solutions,stats=enumerate_waltz(csp,N=2,timeout=10)
        if unsat: assert stats.status=='UNSAT',name
        else:
            assert objective(csp,known)==0,name
            assert solutions and all(objective(csp,s)==0 for s in solutions),name
        n=len(csp.edges); free=sum(len(e.domain)>1 for e in csp.edges.values()); assert free*2>=n
        group='small' if n<=12 else 'medium' if n<=30 else 'large'; assert 3<=n<=60
        manifest.append(dict(name=name,file=path.name,group=group,edges=n,free_edges=free,expected='UNSAT' if unsat else 'SOLVABLE',ambiguous=len(solutions)>=2,known_solution=None if unsat else known,construction='Synthetic catalog-consistent graph; components: '+str(len(parts))))
        print(name,n,free,stats.status,len(solutions))
    assert len(manifest)==15 and sum(m['ambiguous'] for m in manifest)>=2
    for group in ('small','medium','large'): assert sum(m['group']==group and m['expected']=='SOLVABLE' for m in manifest)==4
    (OUT/'manifest.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
    print('All 15 instances verified!')

if __name__=='__main__': main()

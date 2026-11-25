"""Interactive search viewer; launch with python -m src.gui."""
import json, queue, threading, tkinter as tk
from tkinter import ttk, filedialog, messagebox
from dataclasses import asdict
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from src.loader import load_csp
from src.domains import build_domains
from src.validation import junction_violations
from src.events import CancellationToken
from src.playback import ViewState, apply_event, event_summary
from src.graph_view import draw_graph, hit_test
from src.waltz import waltz
from src.hill_climbing import random_restart_hc
from src.genetic_algorithm import genetic_algorithm, decode

class App:
    def __init__(self, root):
        self.root=root; root.title('Waltz | Search laboratory'); root.geometry('1250x800')
        self.csp=None; self.state=ViewState(); self.events=[]; self.index=0; self.bus=queue.Queue(); self.worker=None; self.token=None; self.auto=True; self.selected=(None,None); self.override=None
        bar=ttk.Frame(root); bar.pack(fill='x')
        for name,fn in [('Load JSON',self.load),('Save JSON',self.save),('Run',self.run),('Stop',self.stop),('Pause / Play',self.toggle),('Next',self.next),('Previous',self.previous),('Best assignment',self.best)]:
            ttk.Button(bar,text=name,command=fn).pack(side='left')
        self.algorithm=tk.StringVar(value='Waltz'); ttk.Combobox(bar,textvariable=self.algorithm,values=['Waltz','Hill Climbing','Genetic Algorithm'],state='readonly',width=20).pack(side='left')
        params=ttk.Frame(root); params.pack(fill='x'); self.params={}
        for name,value in [('seed',42),('budget',100),('S',0),('P',100),('p_c',.8),('p_m',.02),('max_evaluations',100000),('timeout',10)]:
            ttk.Label(params,text=name).pack(side='left'); v=tk.StringVar(value=str(value)); self.params[name]=v; ttk.Entry(params,textvariable=v,width=8).pack(side='left')
        self.status=tk.StringVar(); ttk.Label(root,textvariable=self.status).pack(fill='x')
        pane=ttk.Panedwindow(root,orient='horizontal'); pane.pack(fill='both',expand=True)
        left=ttk.Frame(pane); right=ttk.Frame(pane); pane.add(left,weight=3); pane.add(right,weight=2)
        self.fig=Figure(figsize=(7,6)); self.ax=self.fig.add_subplot(211); self.t=self.fig.add_subplot(223); self.e=self.fig.add_subplot(224); self.fig.subplots_adjust(hspace=.5,wspace=.4)
        self.canvas=FigureCanvasTkAgg(self.fig,master=left); self.canvas.get_tk_widget().pack(fill='both',expand=True); self.canvas.mpl_connect('button_press_event',self.click)
        self.log=tk.Listbox(right,height=12); self.log.pack(fill='both',expand=True); self.log.bind('<<ListboxSelect>>',self.jump)
        selectors=ttk.Frame(right); selectors.pack(fill='x'); self.gen=tk.StringVar(); self.ind=tk.StringVar(); self.op=tk.StringVar()
        for label,var in [('Generation',self.gen),('Individual',self.ind),('Operation',self.op)]:
            ttk.Label(selectors,text=label).pack(side='left'); cb=ttk.Combobox(selectors,textvariable=var,width=6,state='readonly'); cb.pack(side='left'); cb.bind('<<ComboboxSelected>>',self.choose); setattr(self,label.lower()+'_box',cb)
        self.details=tk.Text(right,wrap='word',height=22); self.details.pack(fill='both',expand=True)
        self.root.protocol('WM_DELETE_WINDOW',self.close); self.open('instances/cube.json'); self.root.after(50,self.poll)
    def busy(self): return self.worker is not None and self.worker.is_alive()
    def open(self,path):
        self.csp=load_csp(path); self.allowed=build_domains(self.csp); self.reset(); self.render()
    def load(self):
        if self.busy(): return
        path=filedialog.askopenfilename(filetypes=[('JSON','*.json')]);
        if path:
            try: self.open(path)
            except Exception as e: messagebox.showerror('Load',str(e))
    def save(self):
        if not self.csp: return
        path=filedialog.asksaveasfilename(defaultextension='.json');
        if path:
            with open(path,'w',encoding='utf8') as f: json.dump({'edges':[asdict(e) for e in self.csp.edges.values()],'junctions':[asdict(j) for j in self.csp.junctions.values()]},f,indent=2)
    def reset(self):
        self.state=ViewState(); self.events=[]; self.index=0; self.log.delete(0,'end'); self.override=None; self.selected=(None,None); self.gen.set(''); self.ind.set(''); self.op.set('')
    def run(self):
        if self.busy() or not self.csp: return
        try:
            p={k:(float(v.get()) if k in ('p_c','p_m','timeout') else int(v.get())) for k,v in self.params.items()}
        except ValueError as e: messagebox.showerror('Parameters',str(e)); return
        self.reset(); self.auto=True; self.token=CancellationToken(); alg=self.algorithm.get(); csp=self.csp; token=self.token
        def work():
            try:
                kw={'on_event':lambda e:self.bus.put(('event',e)), 'cancel':token}
                if alg=='Waltz': waltz(csp,**kw)
                elif alg=='Hill Climbing': random_restart_hc(csp,budget=p['budget'],seed=p['seed'],S=p['S'],**kw)
                else: genetic_algorithm(csp,**{k:p[k] for k in ('P','p_c','p_m','max_evaluations','timeout','seed')},**kw)
            except Exception as e: self.bus.put(('error',str(e)))
        self.worker=threading.Thread(target=work,daemon=True); self.worker.start()
    def stop(self):
        if self.token: self.token.cancel()
    def close(self): self.stop(); self.root.destroy()
    def toggle(self): self.auto=not self.auto
    def poll(self):
        for _ in range(300):
            try: kind,value=self.bus.get_nowait()
            except queue.Empty: break
            if kind=='error': messagebox.showerror('Search',value)
            else: self.events.append(value); self.log.insert('end',event_summary(value))
        if self.auto and self.index<len(self.events):
            for _ in range(min(30,len(self.events)-self.index)): self.advance()
            self.render()
        self.root.after(50,self.poll)
    def advance(self):
        apply_event(self.state,self.events[self.index],self.csp); self.index+=1; self.override=None
    def next(self):
        self.auto=False
        if self.index<len(self.events): self.advance(); self.render()
    def seek(self,n):
        self.auto=False; self.state=ViewState(); self.index=0
        while self.index<n: self.advance()
        self.render()
    def previous(self): self.seek(max(0,self.index-1))
    def jump(self,event):
        sel=self.log.curselection()
        if sel: self.seek(sel[0]+1)
    def best(self): self.auto=False; self.override=self.state.best_assignment; self.render()
    def click(self,event):
        if event.inaxes==self.ax: self.selected=hit_test(self.csp,event.xdata,event.ydata); self.render()
    def choose(self,event=None):
        self.auto=False; self.override=None; self.render()
    def render(self):
        s=self.state; labels=self.override or s.labels; lines=[]
        gens=s.generations; self.generation_box['values']=list(range(len(gens)))
        if gens:
            gi=min(int(self.gen.get() or len(gens)-1),len(gens)-1); g=gens[gi]; pop=g['population']; ops=g['operations']; self.individual_box['values']=list(range(len(pop))); self.operation_box['values']=list(range(len(ops))); lines.append('Generation metrics: '+str(g['metrics']))
            if self.ind.get() and int(self.ind.get())<len(pop): labels=decode(self.csp,pop[int(self.ind.get())][0]); lines.append('Individual: '+str(pop[int(self.ind.get())]))
            if self.op.get() and int(self.op.get())<len(ops): lines.append('Reproduction: '+str(ops[int(self.op.get())]))
        bad=set(s.empty_junctions)
        if len(labels)==len(self.csp.edges) and all(v is not None for v in labels.values()): bad={k for k,v in junction_violations(self.csp,labels,self.allowed).items() if v}
        kind,key=self.selected; draw_graph(self.ax,self.csp,labels,bad,key if kind=='junction' else None,key if kind=='edge' else None)
        if kind=='junction':
            j=self.csp.junctions[key]; lines.extend([f'Junction {key} | type {j.type}',f'Current tuple: {tuple(labels.get(e) for e in j.edges)}',f'Allowed: {self.allowed[key]}'])
        elif kind=='edge':
            e=self.csp.edges[key]; lines.extend([f'Edge {key} | {e.u} -> {e.v}',f'Domain: {e.domain}',f'Label: {labels.get(key)} (R: u to v; L: v to u)'])
        if s.domains is not None: lines.extend(['Domains: '+str(s.domains),'Queue: '+str(s.queue),'Current arc: '+str(s.current_arc),'Removed: '+str(s.removed_tuples),'Decision tree:']+['  '*r['depth']+r['text'] for r in s.tree])
        if s.hc_current is not None: lines.extend([f'Current h: {s.hc_current_h}; best h: {s.hc_best_h}',f'Steps: {s.hc_steps}; restarts: {s.hc_restarts}; sideways: {s.hc_sideways}',f'Current: {s.hc_current}',f'Best: {s.hc_best}',f'Move: {s.hc_move}'])
        self.details.delete('1.0','end'); self.details.insert('end','\n\n'.join(lines)); self.status.set(f'Event {self.index}/{len(self.events)} | {s.status} | best h={s.best_h} | evaluations={s.objective_evaluations}')
        for ax,key,title in [(self.t,'time_ms','Elapsed ms'),(self.e,'evaluations','Objective evaluations')]:
            ax.clear(); ax.set_xlabel(title); ax.set_ylabel('Best h'); ax.step([x[key] for x in s.samples],[x['best_h'] for x in s.samples],where='post')
        self.canvas.draw_idle()

if __name__=='__main__':
    root=tk.Tk(); App(root); root.mainloop()

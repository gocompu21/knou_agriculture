# -*- coding: utf-8 -*-
"""도면을 다른 축척으로 옮긴 뒤 템플릿 구멍을 새 축척에 맞춰 다시 고른다(cad_to400 → cad_srfix → 이것).
같은 호라도 종이 위 지름이 축척에 따라 달라 구멍 번호가 바뀐다(1:800 2mm → 1:400 4mm).
    python tools/cad_tplfix.py 입력.json 출력.json 400
"""
import json, math, sys, collections
cpx = 0.3584; gpx = 1/3.69
gx = lambda px: (px-26)*gpx; gy = lambda py: (py-245)*gpx
r1=[[1,32],[1.5,44],[2,57],[2.5,71],[3,88],[3.5,104],[4,122],[4.5,143],[5,164],[5.5,187],[6,211],[6.5,237],[7,264],[7.5,292],[8,322],[8.5,354],[9,387],[9.5,421],[10,457],[10.5,494],[11,533],[11.5,572],[12,612]]
r2=[[22,60],[21,133],[20,203],[19,270],[18,333],[17,394],[16,454],[15,509],[14,561],[13,612]]
r3=[[23,60],[25,150],[28,246],[30,351],[33,460],[36,580]]
H={'circle':[(d,px*cpx,57*cpx) for d,px in r1]+[(d,px*cpx,123*cpx) for d,px in r2]+[(d,px*cpx,220*cpx) for d,px in r3],
   'geo':[(d,gx(x),gy(320)) for d,x in zip([1,2,3,4,5,6,7,8,9,10,12,14,16,18,20],[71,91,114,142,174,211,252,296,343,399,461,536,619,709,805])]}
def arc_center(a,b,r,cw,big):
    ch=math.hypot(b[0]-a[0],b[1]-a[1]); R=max(r,ch/2); k=math.sqrt(max(0,R*R-ch*ch/4))
    s=1 if bool(big)!=bool(cw) else -1
    return ((a[0]+b[0])/2+s*k*(a[1]-b[1])/ch,(a[1]+b[1])/2+s*k*(b[0]-a[0])/ch,R)
def best(R,den,pref):
    k=den/1000; dmm=2*R/k; out=None
    for kind in dict.fromkeys([pref,'circle','geo']):
        for d,x,y in H[kind]:
            e=abs(d-dmm)
            if out is None or e<out[0]: out=(e,kind,d,x,y)
    return out,k,dmm
src,dst,den=sys.argv[1],sys.argv[2],int(sys.argv[3])
doc=json.load(open(src,encoding='utf-8')); d=doc['d']
P={p['n'] if 'n' in p else i:(p['x'],p['y']) for i,p in enumerate(d['pts'])} if isinstance(d['pts'],list) else {int(k):(v['x'],v['y']) if isinstance(v,dict) else tuple(v) for k,v in d['pts'].items()}
tab=collections.Counter(); bad=[]; chk=[]
for o in d['ops']:
    if o.get('t') not in ('circle','arc'): continue
    tp=(o.get('tl') or {}).get('tpl')
    if not tp: continue
    if o['t']=='circle': cx,cy=P[o['c']]; R=o['v']/2 if o.get('mode')=='d' else o['v']
    else: cx,cy,R=arc_center(P[o['a']],P[o['b']],o['r'],o.get('dir')=='cw',o.get('big'))
    # 옛 기록(1:800) 확인
    b8,k8,_=best(R,800,tp.get('kind','circle'))
    chk.append(math.hypot(tp['x']+b8[3]*k8-cx, tp['y']+b8[4]*k8-cy) if b8[1]==tp.get('kind') else -1)
    b,k,dmm=best(R,den,tp.get('kind','circle'))
    tab[(round(R,2),b8[2],b[1],b[2],round(dmm,2))]+=1
    if b[0]>1: bad.append((o['id'],round(R,2),round(dmm,1))); continue
    o['tl']['tpl']={**tp,'kind':b[1],'rot':0,'x':round(cx-b[3]*k,3),'y':round(cy-b[4]*k,3),'den':den}
for k,v in sorted(tab.items()): print('R',k[0],'m  1:800 구멍',k[1],'→ 1:%d'%den,k[2],k[3],'(필요',k[4],'mm) x',v)
print('옛 기록 중심 어긋남 최대', max(chk), '종류다름', chk.count(-1))
print('맞는 구멍 없음', bad)
json.dump(doc,open(dst,'w',encoding='utf-8'),ensure_ascii=False)
for o in d['ops']:
    t = (o.get('tl') or {}).get('tpl')
    if t: t['den'] = den
json.dump(doc, open(dst, 'w', encoding='utf-8'), ensure_ascii=False)

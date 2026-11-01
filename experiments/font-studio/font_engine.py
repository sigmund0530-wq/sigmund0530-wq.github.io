"""MGD font studio: editable Hangul components -> real, installable TTF/WOFF2.

A monoline experimental font generated from user-drawn SVG-like centerlines.
FontTools + Shapely under their permissive licenses. This is not a professional
Hangul design engine, does not import/edit commercial or third-party fonts.
"""
from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
from hashlib import sha256
from io import BytesIO
import math
import re
import unicodedata

from fontTools.fontBuilder import FontBuilder
from fontTools.pens.ttGlyphPen import TTGlyphPen
from fontTools.ttLib import TTFont
from shapely.geometry import LineString, Point, Polygon
from shapely.geometry.polygon import orient
from shapely.ops import unary_union

L = 'ㄱㄲㄴㄷㄸㄹㅁㅂㅃㅅㅆㅇㅈㅉㅊㅋㅌㅍㅎ'
V = 'ㅏㅐㅑㅒㅓㅔㅕㅖㅗㅘㅙㅚㅛㅜㅝㅞㅟㅠㅡㅢㅣ'
T = ['','ㄱ','ㄲ','ㄳ','ㄴ','ㄵ','ㄶ','ㄷ','ㄹ','ㄺ','ㄻ','ㄼ','ㄽ','ㄾ','ㄿ','ㅀ','ㅁ','ㅂ','ㅄ','ㅅ','ㅆ','ㅇ','ㅈ','ㅊ','ㅋ','ㅌ','ㅍ','ㅎ']
VERTICAL = set('ㅏㅐㅑㅒㅓㅔㅕㅖㅣ')
HORIZONTAL = set('ㅗㅛㅜㅠㅡ')
FONT_FORMAT = 'mgd-font-work-v1'
MAX_PROJECT_BYTES = 600_000


class InputError(ValueError):
    pass


def path(*coords, smooth=False, closed=False):
    return {'kind':'path','pts':[{'x':x,'y':y} for x,y in coords], 'smooth':smooth, 'closed':closed}


def ellipse(cx,cy,rx,ry):
    return {'kind':'ellipse','cx':cx,'cy':cy,'rx':rx,'ry':ry}


CONSONANTS={
'ㄱ':[path((16,20),(83,20),(83,82))], 'ㄴ':[path((18,18),(18,82),(85,82))],
'ㄷ':[path((83,18),(18,18),(18,83),(83,83))],
'ㄹ':[path((16,18),(82,18),(82,48),(17,48),(17,82),(86,82))],
'ㅁ':[path((18,18),(82,18),(82,83),(18,83),(18,18))],
'ㅂ':[path((22,17),(22,84)),path((78,17),(78,84)),path((22,50),(78,50)),path((17,84),(83,84))],
'ㅅ':[path((49,16),(16,84)),path((49,16),(85,84))], 'ㅇ':[ellipse(50,50,31,31)],
'ㅈ':[path((14,20),(86,20)),path((50,30),(18,84)),path((50,30),(82,84))],
'ㅊ':[path((50,7),(50,15)),path((12,31),(88,31)),path((50,39),(18,86)),path((50,39),(83,86))],
'ㅋ':[path((16,19),(83,19),(83,84)),path((45,52),(83,52))],
'ㅌ':[path((84,18),(17,18),(17,82),(84,82)),path((18,50),(83,50))],
'ㅍ':[path((14,18),(86,18)),path((28,22),(28,78)),path((72,22),(72,78)),path((14,82),(86,82))],
'ㅎ':[path((50,4),(50,13)),path((17,23),(83,23)),ellipse(50,65,28,24)],
}
DOUBLE={'ㄲ':'ㄱ','ㄸ':'ㄷ','ㅃ':'ㅂ','ㅆ':'ㅅ','ㅉ':'ㅈ'}
CLUSTER={'ㄳ':'ㄱㅅ','ㄵ':'ㄴㅈ','ㄶ':'ㄴㅎ','ㄺ':'ㄹㄱ','ㄻ':'ㄹㅁ','ㄼ':'ㄹㅂ','ㄽ':'ㄹㅅ','ㄾ':'ㄹㅌ','ㄿ':'ㄹㅍ','ㅀ':'ㄹㅎ','ㅄ':'ㅂㅅ'}


def transform(s, x,y,w,h):
    s=deepcopy(s)
    if s['kind']=='ellipse':
        s.update(cx=x+s['cx']*w/100,cy=y+s['cy']*h/100,rx=s['rx']*w/100,ry=s['ry']*h/100)
    else:
        s['pts']=[{'x':x+p['x']*w/100,'y':y+p['y']*h/100} for p in s['pts']]
    return s


def _initial(c):
    if c in DOUBLE:
        b=_initial(DOUBLE[c]);return [transform(s,0,0,45,100) for s in b]+[transform(s,53,0,45,100) for s in b]
    return deepcopy(CONSONANTS[c])


def _final(c):
    if c in CLUSTER:
        a,b=CLUSTER[c];return [transform(s,0,0,45,100) for s in _initial(a)]+[transform(s,53,0,45,100) for s in _initial(b)]
    return _initial(c)


def _medial(c):
    def vertical(right=False,two=False,side=False):
        x=72 if right else 28
        z=[path((x,10),(x,90))]
        for y in (37,66) if two else (52,): z.append(path((x,y),(12 if right else 88,y)))
        if side:z.append(path((45 if right else 55,10),(45 if right else 55,90)))
        return z
    m={'ㅏ':(False,False,False),'ㅑ':(False,True,False),'ㅐ':(False,False,True),'ㅒ':(False,True,True),
       'ㅓ':(True,False,False),'ㅕ':(True,True,False),'ㅔ':(True,False,True),'ㅖ':(True,True,True)}
    if c in m:return vertical(*m[c])
    if c=='ㅣ':return [path((50,11),(50,90))]
    if c=='ㅡ':return [path((10,50),(90,50))]
    if c=='ㅗ':return [path((11,75),(89,75)),path((50,75),(50,14))]
    if c=='ㅛ':return [path((11,75),(89,75)),path((31,75),(31,18)),path((69,75),(69,18))]
    if c=='ㅜ':return [path((11,28),(89,28)),path((50,28),(50,90))]
    if c=='ㅠ':return [path((11,28),(89,28)),path((31,28),(31,89)),path((69,28),(69,89))]
    if c in ('ㅘ','ㅙ','ㅚ'):
        b={'ㅘ':'ㅏ','ㅙ':'ㅐ','ㅚ':'ㅣ'}[c]
        return [transform(s,1,3,56,94) for s in _medial('ㅗ')]+[transform(s,58,0,39,100) for s in _medial(b)]
    if c in ('ㅝ','ㅞ','ㅟ'):
        b={'ㅝ':'ㅓ','ㅞ':'ㅔ','ㅟ':'ㅣ'}[c]
        return [transform(s,1,3,56,94) for s in _medial('ㅜ')]+[transform(s,58,0,39,100) for s in _medial(b)]
    if c=='ㅢ':return [transform(s,2,0,58,100) for s in _medial('ㅡ')]+[transform(s,63,0,34,100) for s in _medial('ㅣ')]
    raise InputError('Invalid medial')


def default_bases():
    return {'L':{c:_initial(c) for c in L}, 'V':{c:_medial(c) for c in V},
            'T':{c:_final(c) for c in T[1:]}}


def default_project():
    return {'format':FONT_FORMAT,'data':{'bases':default_bases(),'overrides':{},'weight':8,'width':100,'round':True}}


def is_number(n):return isinstance(n,(int,float)) and not isinstance(n,bool) and math.isfinite(n)


def validate_shapes(shapes):
    if not isinstance(shapes,list) or len(shapes)>100:raise InputError('획은 글자당 최대 100개까지 가능합니다.')
    for s in shapes:
        if not isinstance(s,dict):raise InputError('잘못된 획 형식입니다.')
        kind=s.get('kind')
        if kind=='ellipse':
            if not all(is_number(s.get(k)) and -500<=s[k]<=500 for k in ('cx','cy','rx','ry')):raise InputError('원 좌표 오류')
            if s['rx']<=0 or s['ry']<=0:raise InputError('원의 반지름 오류')
        elif kind=='path':
            pts=s.get('pts')
            if not isinstance(pts,list) or len(pts)>250:raise InputError('한 획은 점 250개 이하로 만들 수 있습니다.')
            for p in pts:
                if not isinstance(p,dict) or not all(is_number(p.get(k)) and -500<=p[k]<=500 for k in ('x','y')):raise InputError('점 좌표 오류')
            if type(s.get('smooth',False))!=bool or type(s.get('closed',False))!=bool:raise InputError('곡선 형식 오류')
        else:raise InputError('지원되지 않는 획 형식입니다.')


def validate_project(obj):
    if not isinstance(obj,dict) or obj.get('format') not in (FONT_FORMAT,'mgd-font-work-v03'):
        raise InputError('무가당 폰트 작업 파일이 아닙니다.')
    d=obj.get('data')
    if not isinstance(d,dict):raise InputError('데이터가 비어 있습니다.')
    if not is_number(d.get('weight')) or not 2<=d['weight']<=17:raise InputError('획 굵기는 2~17만 가능합니다.')
    if not is_number(d.get('width')) or not 65<=d['width']<=135:raise InputError('가로폭은 65~135%만 가능합니다.')
    if type(d.get('round'))!=bool:raise InputError('획 끝 설정이 올바르지 않습니다.')
    bases=d.get('bases')
    if not isinstance(bases,dict):raise InputError('자모가 없습니다.')
    for mode,letters in (('L',L),('V',V),('T',T[1:])):
        m=bases.get(mode)
        if not isinstance(m,dict) or set(m)!=set(letters):raise InputError('한글 자모가 누락되었습니다.')
        for c in letters:validate_shapes(m[c])
    overrides=d.get('overrides',{})
    if not isinstance(overrides,dict) or len(overrides)>1000:raise InputError('개별 보정은 최대 1,000자까지 가능합니다.')
    for c,shapes in overrides.items():
        if len(c)!=1 or not (0xAC00<=ord(c)<=0xD7A3):raise InputError('보정 대상은 완성형 한글이어야 합니다.')
        validate_shapes(shapes)
    return d


def _quad_points(pts, steps=9):
    if len(pts)<3:return pts
    out=[pts[0]]
    # Matches frontend SVG shorthand: M first, Q control-midpoint pairs, then L last.
    for i in range(1,len(pts)-1):
        a=pts[i-1] if i==1 else ((pts[i-1][0]+pts[i][0])/2,(pts[i-1][1]+pts[i][1])/2)
        c=pts[i];b=((pts[i][0]+pts[i+1][0])/2,(pts[i][1]+pts[i+1][1])/2)
        # First curve starts at initial point; subsequent at prior midpoint.
        if i==1:a=pts[0]
        for n in range(1,steps+1):
            t=n/steps;out.append(((1-t)**2*a[0]+2*(1-t)*t*c[0]+t*t*b[0],
                                  (1-t)**2*a[1]+2*(1-t)*t*c[1]+t*t*b[1]))
    out.append(pts[-1]);return out


def _shape_geometry(s,thickness,roundcap):
    if s['kind']=='ellipse':
        cx,cy,rx,ry=(s[k] for k in ('cx','cy','rx','ry'))
        n=64
        pts=[(cx+rx*math.cos(2*math.pi*i/n),cy+ry*math.sin(2*math.pi*i/n)) for i in range(n+1)]
        return LineString(pts).buffer(thickness/2,cap_style=1 if roundcap else 3,join_style=1 if roundcap else 2,quad_segs=5)
    pts=[(p['x'],p['y']) for p in s.get('pts',[])]
    if not pts:return None
    if len(pts)==1:return Point(*pts[0]).buffer(thickness/2)
    if s.get('smooth') and len(pts)>=3:pts=_quad_points(pts)
    if s.get('closed') and pts[-1]!=pts[0]:pts.append(pts[0])
    return LineString(pts).buffer(thickness/2,cap_style=1 if roundcap else 3,join_style=1 if roundcap else 2,quad_segs=5)


def _shape_to_pen(shapes,thickness,roundcap,scale,tx,ty,glyphs=None):
    pen=TTGlyphPen(glyphs)
    geom=[_shape_geometry(s,thickness,roundcap) for s in shapes]
    geom=[g for g in geom if g is not None and not g.is_empty]
    if not geom:return pen.glyph()
    united=unary_union(geom)
    if united.geom_type=='Polygon':polys=[united]
    else:polys=[x for x in getattr(united,'geoms',[]) if x.geom_type=='Polygon']
    for poly in polys:
        # fontTools expects clockwise exterior contours in its y-up coordinates.
        poly=orient(poly,sign=1)
        for ring in [poly.exterior,*poly.interiors]:
            coords=list(ring.coords)[:-1]
            if len(coords)<3:continue
            points=[(round(tx+scale*x),round(ty-scale*y)) for x,y in coords]
            # Omit consecutive duplicate points due to rounding.
            clean=[]
            for point in points:
                if not clean or clean[-1]!=point:clean.append(point)
            if len(clean)<3:continue
            pen.moveTo(clean[0]);[pen.lineTo(p) for p in clean[1:]];pen.closePath()
    return pen.glyph()


def _glyph_layout(cp):
    n=cp-0xAC00;li=n//588;vi=(n%588)//28;ti=n%28
    v=V[vi];has=ti!=0
    if v in VERTICAL:
        placements=[('L',li,6,6,41 if has else 42,68 if has else 88),('V',vi,51,7,40,66 if has else 86)]
    elif v in HORIZONTAL:
        placements=[('L',li,19,4,62,47 if has else 53),('V',vi,12,53 if has else 60,76,23 if has else 29)]
    else:
        placements=[('L',li,5,7,42,64 if has else 86),('V',vi,51,7,43,64 if has else 86)]
    if has:placements.append(('T',ti-1,19,75,62,23))
    return placements


def _component_transform(x,y,w,h,width):
    ww=width/100
    return (w*ww/100,0,0,h/100, round((x*ww+(100-width)/2)*10),round((100-y-h)*10))


def compile_font(project,label='나의 글꼴',format='ttf'):
    d=validate_project(project)
    if not isinstance(label,str) or not label.strip() or len(label)>30 or re.search(r'[\x00-\x1f\\/]',label):raise InputError('폰트 이름은 1~30자여야 합니다.')
    label=unicodedata.normalize('NFC',label.strip())
    if format not in ('ttf','woff2'):raise InputError('지원하지 않는 파일 형식')
    weight=d['weight']/2.9
    component_weight=d['weight']  # Component scaling shrinks strokes; compensate.
    width=d['width']
    glyphs={}
    for mode,chars in (('L',L),('V',V),('T',T[1:])):
        for i,c in enumerate(chars):
            glyphs[f'{mode}{i}']=_shape_to_pen(d['bases'][mode][c],component_weight,d['round'],8,0,800)
    glyphs['.notdef']=_shape_to_pen([path((20,20),(80,20),(80,80),(20,80),(20,20))],3,True,8,0,800)
    glyphs['space']=TTGlyphPen(None).glyph()
    cmap={0x20:'space',0xA0:'space'}
    advances={n:(1000,0) for n in glyphs};advances['space']=(300,0)
    glyphset=glyphs
    for cp in range(0xAC00,0xD7A4):
        name=f'uni{cp:04X}';c=chr(cp)
        if c in d['overrides']:
            # Glyph-specific overrides live in entire 0..100 canvas and no longer
            # follow component edits (unless the override is reset explicitly).
            glyphs[name]=_shape_to_pen(d['overrides'][c],weight,d['round'],10*width/100,(100-width)*5,1000)
        else:
            pen=TTGlyphPen(glyphset)
            for mode,i,x,y,w,h in _glyph_layout(cp):
                pen.addComponent(f'{mode}{i}',_component_transform(x,y,w,h,width))
            glyphs[name]=pen.glyph()
        cmap[cp]=name;advances[name]=(1000,0)
    # Basic punctuation. Latin/numerals are rendered by an app's fallback font.
    punct={'.':[ellipse(50,78,4,4)], ',':[ellipse(50,80,4,4),path((50,81),(46,93))],
           '!':[path((50,15),(50,64)),ellipse(50,81,4,4)],
           ':':[ellipse(50,39,4,4),ellipse(50,78,4,4)],
           '-':[path((31,56),(69,56))], '?':[path((30,28),(40,18),(63,18),(71,33),(50,54),(50,65)),ellipse(50,82,4,4)]}
    for c,shapes in punct.items():
        name=f'uni{ord(c):04X}';glyphs[name]=_shape_to_pen(shapes,weight,d['round'],10,0,1000)
        advances[name]=(460,0);cmap[ord(c)]=name
    order=['.notdef','space',*([f'L{i}' for i in range(len(L))]),*([f'V{i}' for i in range(len(V))]),*([f'T{i}' for i in range(len(T)-1)]),
           *([f'uni{cp:04X}' for cp in range(0xAC00,0xD7A4)]),*([f'uni{ord(c):04X}' for c in punct])]
    builder=FontBuilder(1000,isTTF=True)
    builder.setupGlyphOrder(order)
    builder.setupCharacterMap(cmap)
    builder.setupGlyf(glyphs)
    builder.setupHorizontalMetrics(advances)
    builder.setupHorizontalHeader(ascent=940,descent=-200)
    digest=sha256(repr((label,d)).encode()).hexdigest()[:12]
    family='MGD '+label
    builder.setupNameTable({'familyName':family,'styleName':'Regular',
                            'uniqueFontIdentifier':'MGD Original '+digest,
                            'fullName':family+' Regular','psName':'MGD-'+digest,
                            'version':'Version 1.0','description':'Original, geometric Korean component font. User edited strokes.'})
    builder.setupOS2(sTypoAscender=940,sTypoDescender=-200,usWinAscent=1000,usWinDescent=200,
                     usWeightClass=400,usWidthClass=5)
    builder.setupPost();builder.setupMaxp()
    font=builder.font
    if format=='woff2':font.flavor='woff2'
    out=BytesIO();font.save(out);raw=out.getvalue()
    return raw,{'family':family,'hangul_syllables':11172,'base_components':len(L)+len(V)+len(T)-1,
                'overrides':len(d['overrides']),'bytes':len(raw),'sha256':sha256(raw).hexdigest(), 'format':format}

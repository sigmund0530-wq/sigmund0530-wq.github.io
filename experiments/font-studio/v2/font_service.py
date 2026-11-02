"""Local-first font workshop: OFL templates + actual editable TrueType glyph contours.

Does not bundle fonts. The bootstrap downloads unmodified upstream OFL font files.
Only TTF glyf fonts are accepted; the proof of quality is original professional
outlines and user-editable per-glyph contours, not simulated CSS transformations.
"""
from __future__ import annotations
from io import BytesIO
from pathlib import Path
from functools import lru_cache
from hashlib import sha256
from urllib.request import Request, urlopen
from urllib.error import URLError
import json
import math
import re
import unicodedata
import threading

from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._g_l_y_f import Glyph, GlyphCoordinates, flagOnCurve
from fontTools.ttLib.tables.ttProgram import Program

ROOT=Path(__file__).resolve().parent
FONTS_DIR=ROOT/'runtime'/'fonts'
FONTS={
 'gothic':{'label':'단정한 고딕','file':'NanumGothic-Regular.ttf','url':'https://raw.githubusercontent.com/google/fonts/main/ofl/nanumgothic/NanumGothic-Regular.ttf','license':'https://github.com/google/fonts/blob/main/ofl/nanumgothic/OFL.txt'},
 'gothic-bold':{'label':'또렷한 고딕','file':'NanumGothic-Bold.ttf','url':'https://raw.githubusercontent.com/google/fonts/main/ofl/nanumgothic/NanumGothic-Bold.ttf','license':'https://github.com/google/fonts/blob/main/ofl/nanumgothic/OFL.txt'},
 'myeongjo':{'label':'차분한 명조','file':'NanumMyeongjo-Regular.ttf','url':'https://raw.githubusercontent.com/google/fonts/main/ofl/nanummyeongjo/NanumMyeongjo-Regular.ttf','license':'https://github.com/google/fonts/blob/main/ofl/nanummyeongjo/OFL.txt'},
 'gowun':{'label':'부드러운 돋움','file':'GowunDodum-Regular.ttf','url':'https://raw.githubusercontent.com/google/fonts/main/ofl/gowundodum/GowunDodum-Regular.ttf','license':'https://github.com/google/fonts/blob/main/ofl/gowundodum/OFL.txt'},
 'batang':{'label':'따뜻한 바탕','file':'GowunBatang-Regular.ttf','url':'https://raw.githubusercontent.com/google/fonts/main/ofl/gowunbatang/GowunBatang-Regular.ttf','license':'https://github.com/google/fonts/blob/main/ofl/gowunbatang/OFL.txt'},
}
MAX_PROJECT_BYTES=1_300_000
MAX_OVERRIDES=256
MAX_POINTS=1800
SCHEMA='mgd-font-studio-v2'
DEFAULT_TEXT='기록은 오래 남아, 우리의 하루를 닮는다.\n오늘의 마음을 나만의 글씨로 적어 봐.'
class StudioError(ValueError): pass


def font_path(font_id):
 if font_id not in FONTS:raise StudioError('알 수 없는 기본 글꼴입니다.')
 return FONTS_DIR/FONTS[font_id]['file']


def _check_font(path):
 f=TTFont(str(path),lazy=False)
 try:
  if 'glyf' not in f or 'hmtx' not in f: raise StudioError('TrueType 윤곽이 있는 TTF만 지원합니다.')
  cmap=f.getBestCmap() or {}
  if sum(1 for c in range(0xAC00,0xD7A4) if c in cmap)!=11172:
   raise StudioError('한글 11,172자가 없는 파일입니다.')
 finally:f.close()


def ensure_font(font_id):
 path=font_path(font_id)
 if path.exists():return path
 FONTS_DIR.mkdir(parents=True,exist_ok=True)
 try:
  req=Request(FONTS[font_id]['url'],headers={'User-Agent':'MGD-Font-Studio/2.0'})
  with urlopen(req, timeout=20) as resp:
   if int(resp.headers.get('Content-Length','0') or 0)>12_000_000:raise StudioError('원본 폰트가 너무 큽니다.')
   raw=resp.read(12_000_001)
  if len(raw)>12_000_000:raise StudioError('원본 폰트가 너무 큽니다.')
  # Reject unexpected/broken binary before persisting.
  tmp=path.with_suffix('.tmp')
  tmp.write_bytes(raw)
  try:_check_font(tmp);tmp.replace(path)
  finally:tmp.unlink(missing_ok=True)
 except (OSError,URLError) as exc:
  raise StudioError('기본 폰트를 내려받지 못했습니다. 인터넷 연결을 확인하세요.') from exc
 return path


@lru_cache(maxsize=6)
def read_font_info(font_id):
 path=ensure_font(font_id)
 with TTFont(path) as f:
  cmap=f.getBestCmap() or {}
  return {'id':font_id,'label':FONTS[font_id]['label'],'hangul_count':sum(1 for c in range(0xAC00,0xD7A4) if c in cmap),
          'upm':f['head'].unitsPerEm,'ascent':f['hhea'].ascent,'descent':f['hhea'].descent,
          'license':FONTS[font_id]['license']}


def clean_name(s):
 if not isinstance(s,str):raise StudioError('폰트 이름이 올바르지 않습니다.')
 s=unicodedata.normalize('NFC',s.strip())
 if not 1<=len(s)<=28 or re.search(r'[\\/\x00-\x1f]',s):raise StudioError('폰트 이름은 1~28자로 입력하세요.')
 compressed=re.sub(r'\s+','',s).lower()
 if any(t in compressed for t in ('nanum','나눔','naver','네이버','gowun','고운')):
  raise StudioError('원본 글꼴의 보호된 이름 대신 새로운 이름을 사용하세요.')
 return s


def validate_project(p):
 if not isinstance(p,dict) or p.get('version')!=SCHEMA:raise StudioError('올바른 무가당 작업 파일이 아닙니다.')
 if p.get('font') not in FONTS:raise StudioError('기본 서체가 올바르지 않습니다.')
 clean_name(p.get('name',''))
 for field,lo,hi in (('width',75,125),('slant',-14,14),('tracking',-70,140)):
  v=p.get(field)
  if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not lo<=v<=hi:
   raise StudioError(f'{field} 설정이 허용 범위를 벗어났습니다.')
 overrides=p.get('overrides',{})
 if not isinstance(overrides,dict) or len(overrides)>MAX_OVERRIDES:
  raise StudioError(f'개별 보정은 {MAX_OVERRIDES}글자까지 가능합니다.')
 for ch, contours in overrides.items():
  if not isinstance(ch,str) or len(ch)!=1 or ord(ch)<32:
   raise StudioError('수정 대상 글자가 올바르지 않습니다.')
  if not isinstance(contours,list) or len(contours)>150:raise StudioError('글리프 윤곽 개수가 너무 많습니다.')
  count=0
  for contour in contours:
   if not isinstance(contour,list) or len(contour)<3:raise StudioError('윤곽은 3개 이상의 점을 가져야 합니다.')
   count+=len(contour)
   for pt in contour:
    if not isinstance(pt,list) or len(pt)!=3 or not all(isinstance(v,(int,float)) and not isinstance(v,bool) and math.isfinite(v) for v in pt[:2]):raise StudioError('점 좌표가 올바르지 않습니다.')
    if not -600<=pt[0]<=1600 or not -600<=pt[1]<=1600 or not isinstance(pt[2],bool):raise StudioError('점 좌표 범위를 벗어났습니다.')
  if count>MAX_POINTS:raise StudioError('한 글자의 편집점이 너무 많습니다.')
 return p


def project_default(font_id='gothic'):
 return {'version':SCHEMA,'name':'나의 글씨','font':font_id,'width':100,'slant':0,'tracking':0,'overrides':{}}


def _glyph_contours(f,char):
 cmap=f.getBestCmap() or {};name=cmap.get(ord(char))
 if name is None:raise StudioError('선택한 글자가 이 폰트에 없습니다.')
 glyph=f['glyf'][name];coords,ends,flags=glyph.getCoordinates(f['glyf'])
 upm=f['head'].unitsPerEm;asc=f['hhea'].ascent
 contours=[];start=0
 for end in ends:
  contours.append([[round(coords[j][0]*1000/upm,2),round((asc-coords[j][1])*1000/upm,2),bool(flags[j]&flagOnCurve)] for j in range(start,end+1)])
  start=end+1
 return name,contours


def glyph_outline(font_id,char):
 if len(char)!=1:raise StudioError('한 글자만 선택하세요.')
 with TTFont(ensure_font(font_id)) as f:
  name,contours=_glyph_contours(f,char)
  advance=f['hmtx'][name][0]*1000/f['head'].unitsPerEm
  return {'char':char,'contours':contours,'advance':round(advance,2),'font':font_id,'points':sum(map(len,contours))}


def _glyph_from_contours(contours,upm,asc):
 coords=GlyphCoordinates();flags=bytearray();ends=[]
 for contour in contours:
  for x,y,on in contour:
   coords.append((int(round(x*upm/1000)),int(round(asc-y*upm/1000))))
   flags.append(int(flagOnCurve) if on else 0)
  ends.append(len(coords)-1)
 g=Glyph();g.numberOfContours=len(contours)
 g.coordinates=coords;g.flags=flags;g.endPtsOfContours=ends
 g.program=Program();g.program.fromBytecode([])
 return g


def _strip_hints(f):
 for tag in ('fpgm','prep','cvt '):
  if tag in f:del f[tag]
 glyf=f['glyf']
 for name in f.getGlyphOrder():
  g=glyf[name]
  if hasattr(g,'program'):g.removeHinting()
 if 'maxp' in f and hasattr(f['maxp'],'maxSizeOfInstructions'):f['maxp'].maxSizeOfInstructions=0


def _transform(f,width,slant,tracking):
 """Affine scale and shear on simple contours; translated components updated.
 Composite non-translation matrices may need design review (tested templates use
 standard TrueType components). Font coordinates remain true outlines, not CSS.
 """
 sx=width/100.0;sh=math.tan(math.radians(slant))
 glyf=f['glyf'];hmtx=f['hmtx'].metrics
 # Edit only outlines and component anchor translations; bbox recalculated after.
 for name in f.getGlyphOrder():
  g=glyf[name]
  if g.isComposite():
   for c in g.components:
    if hasattr(c,'x') and hasattr(c,'y'):
     c.x=int(round(c.x*sx+c.y*sh))
  elif g.numberOfContours>0:
   old=g.coordinates
   g.coordinates=GlyphCoordinates([(int(round(x*sx+y*sh)),int(y)) for x,y in old])
  advance,lsb=hmtx[name]
  hmtx[name]=(min(65535,max(0,int(round(advance*sx)+(int(tracking) if advance>0 else 0)))),int(round(lsb*sx)))
 # The font may still have GPOS and kern pairs with their original spacing;
 # remove legacy kern for tracked designs so distance is predictable.
 if (tracking or width!=100) and 'kern' in f:del f['kern']
 # Recalculate bounds and left side bearings for all modified glyphs.
 if width!=100 or slant!=0:
  for name in f.getGlyphOrder():
   g=glyf[name]
   try:
    g.recalcBounds(glyf)
    a,_=hmtx[name]
    if hasattr(g,'xMin'):hmtx[name]=(a,max(-32768,min(32767,int(g.xMin))))
   except (AttributeError,ValueError):pass
  _strip_hints(f)


def _rename(f,name,digest):
 family='MGD '+name
 post='MGD-'+digest[:16].upper()
 table=f['name']
 rename={1:family,2:'Regular',3:'MGD-Modified-'+digest[:18],4:family+' Regular',6:post,16:family,17:'Regular'}
 for nid,value in rename.items():
  table.removeNames(nameID=nid)
  table.setName(value,nid,3,1,0x409)
 if 'OS/2' in f:
  f['OS/2'].usWeightClass=400
  f['OS/2'].fsSelection &= ~0x21
  f['OS/2'].fsSelection |= 0x40
 if 'head' in f:f['head'].macStyle &=~3
 # Retain original OFL license and copyright records from source.
 return family


def build_font(project,format='ttf'):
 p=validate_project(project)
 if format not in ('ttf','woff2'):raise StudioError('TTF 또는 WOFF2를 선택하세요.')
 with TTFont(ensure_font(p['font'])) as f:
  upm=f['head'].unitsPerEm;asc=f['hhea'].ascent;cmap=f.getBestCmap() or {}
  for ch,contours in p['overrides'].items():
   gname=cmap.get(ord(ch))
   if gname is None:raise StudioError(f'수정한 글자 {ch}가 원본 폰트에 없습니다.')
   f['glyf'][gname]=_glyph_from_contours(contours,upm,asc)
  if p['width']!=100 or p['slant'] or p['tracking'] or p['overrides']:
   _transform(f,p['width'],p['slant'],p['tracking'])
   if p['overrides'] and p['width']==100 and p['slant']==0:
    _strip_hints(f)
  digest=sha256(json.dumps(p,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()).hexdigest()
  family=_rename(f,clean_name(p['name']),digest)
  if format=='woff2':f.flavor='woff2'
  out=BytesIO();f.save(out);raw=out.getvalue()
  return raw,{'name':family,'bytes':len(raw),'sha256':sha256(raw).hexdigest(),
             'format':format,'modified_glyphs':len(p['overrides']),
             'hangul':sum(1 for cp in range(0xAC00,0xD7A4) if cp in cmap),
             'source':p['font']}
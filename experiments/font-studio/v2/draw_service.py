"""Vector painting/boolean geometry for editable TrueType outlines.

Contours are normalized to 1000 em units, origin top-left. We use an even-odd
fill rule to match the SVG editor, then orient output for nonzero TrueType fill.
The returned contours are normal editable on-curve points, not raster images.
"""
from __future__ import annotations
import math
from shapely.geometry import Polygon, MultiPolygon, GeometryCollection, LineString, Point, box
from shapely.ops import unary_union
from shapely.geometry.polygon import orient
from shapely.validation import make_valid
from font_service import StudioError, MAX_POINTS

MAX_STROKE_POINTS=700
MAX_CONTOURS=120
BOUNDS=(-600.0,1600.0)


def _num(v):
 if isinstance(v,bool) or not isinstance(v,(int,float)) or not math.isfinite(v) or not BOUNDS[0]<=v<=BOUNDS[1]:
  raise StudioError('그리기 좌표가 올바르지 않습니다.')
 return float(v)


def _points(value,limit=MAX_STROKE_POINTS):
 if not isinstance(value,list) or not 1<=len(value)<=limit:
  raise StudioError('획에 포함된 점의 개수가 올바르지 않습니다.')
 pts=[]
 for point in value:
  if not isinstance(point,(list,tuple)) or len(point)<2:raise StudioError('그리기 점 형식이 올바르지 않습니다.')
  pts.append((_num(point[0]),_num(point[1])))
 return pts


def _flatten(contour):
 """Quadratic outlines with implied points between consecutive off-curve controls."""
 pts=contour
 n=len(pts)
 if n<3:return []
 if pts[0][2]:start=0;current=(pts[0][0],pts[0][1])
 elif pts[-1][2]:start=n-1;current=(pts[-1][0],pts[-1][1])
 else:start=n-1;current=((pts[-1][0]+pts[0][0])/2,(pts[-1][1]+pts[0][1])/2)
 out=[current]
 i=1
 while i<=n:
  a=pts[(start+i)%n]
  if a[2]:
   current=(a[0],a[1]);out.append(current);i+=1
  else:
   b=pts[(start+i+1)%n]
   if b[2]:end=(b[0],b[1]);i+=2
   else:end=((a[0]+b[0])/2,(a[1]+b[1])/2);i+=1
   # Bound curve error while preventing unbounded geometry growth.
   length=math.dist(current,(a[0],a[1]))+math.dist((a[0],a[1]),end)
   steps=min(24,max(3,int(math.ceil(length/18))))
   for k in range(1,steps+1):
    t=k/steps;u=1-t
    out.append((u*u*current[0]+2*u*t*a[0]+t*t*end[0],u*u*current[1]+2*u*t*a[1]+t*t*end[1]))
   current=end
 return out


def _polygons(geometry):
 if geometry.is_empty:return []
 if isinstance(geometry,Polygon):return [geometry]
 if isinstance(geometry,MultiPolygon):return list(geometry.geoms)
 if isinstance(geometry,GeometryCollection):
  return [p for g in geometry.geoms for p in _polygons(g)]
 return []


def _clean(geometry):
 if not geometry.is_valid:geometry=make_valid(geometry)
 return unary_union(_polygons(geometry))


def contours_to_geometry(contours):
 if not isinstance(contours,list) or len(contours)>MAX_CONTOURS:raise StudioError('윤곽 개수가 너무 많습니다.')
 g=GeometryCollection()
 total=0
 for contour in contours:
  if not isinstance(contour,list) or len(contour)<3:raise StudioError('잘못된 윤곽입니다.')
  total+=len(contour)
  if total>MAX_POINTS:raise StudioError('편집 점이 너무 많습니다.')
  for pt in contour:
   if not isinstance(pt,list) or len(pt)!=3 or not isinstance(pt[2],bool):raise StudioError('잘못된 윤곽 점입니다.')
   _num(pt[0]);_num(pt[1])
  points=_flatten(contour)
  poly=Polygon(points)
  if poly.is_empty:continue
  poly=_clean(poly)
  if not poly.is_empty:g=g.symmetric_difference(poly)
 return _clean(g)


def _paint_geometry(req):
 mode=req.get('tool')
 points=_points(req.get('points'))
 if mode in ('brush','eraser'):
  width=_num(req.get('width'))
  if not 2<=width<=160:raise StudioError('획 굵기는 2~160 사이여야 합니다.')
  return Point(points[0]).buffer(width/2,quad_segs=12) if len(points)==1 else LineString(points).buffer(width/2,cap_style=1,join_style=1,quad_segs=12)
 if mode in ('rect','rectangle'):
  if len(points)!=2:raise StudioError('사각형에는 시작점과 끝점이 필요합니다.')
  x0,y0=points[0];x1,y1=points[1]
  if abs(x0-x1)<3 or abs(y0-y1)<3:raise StudioError('사각형을 더 크게 그려 주세요.')
  return box(min(x0,x1),min(y0,y1),max(x0,x1),max(y0,y1))
 if mode=='ellipse':
  if len(points)!=2:raise StudioError('원에는 시작점과 끝점이 필요합니다.')
  (x0,y0),(x1,y1)=points
  rx=abs(x1-x0)/2;ry=abs(y1-y0)/2
  if rx<2 or ry<2:raise StudioError('원을 더 크게 그려 주세요.')
  cx=(x0+x1)/2;cy=(y0+y1)/2
  # ellipse follows our existing normalized em coordinate system.
  from shapely import affinity
  return affinity.translate(affinity.scale(Point(0,0).buffer(1,quad_segs=32),rx,ry,origin=(0,0)),cx,cy)
 if mode=='polygon':
  if len(points)<3:raise StudioError('펜은 점을 세 개 이상 찍어야 합니다.')
  return _clean(Polygon(points))
 raise StudioError('지원하지 않는 그리기 도구입니다.')


def geometry_to_contours(geometry):
 result=[]
 for p in _polygons(_clean(geometry)):
  # With screen y growing down, CCW exteriors become clockwise in font y-up.
  p=orient(p,sign=1.0)
  rings=[p.exterior,*p.interiors]
  for ring in rings:
   # Simplification is done with topology preservation to avoid tiny spikes.
   coords=list(ring.coords)[:-1]
   if len(coords)<3:continue
   if len(result)>=MAX_CONTOURS:raise StudioError('윤곽이 너무 복잡합니다. 일부 획을 지워 주세요.')
   result.append([[round(x,2),round(y,2),True] for x,y in coords])
 if sum(len(x) for x in result)>MAX_POINTS:
  # Simplify the entire shape, not individual rings; respect holes.
  simplify=_clean(geometry).simplify(1.8,preserve_topology=True)
  result=[]
  for p in _polygons(simplify):
   p=orient(p,sign=1.0)
   for ring in [p.exterior,*p.interiors]:
    coords=list(ring.coords)[:-1]
    if len(coords)>=3:result.append([[round(x,2),round(y,2),True] for x,y in coords])
  if len(result)>MAX_CONTOURS or sum(len(x) for x in result)>MAX_POINTS:
   raise StudioError('그림이 복잡합니다. 획을 더 짧게 나누거나 굵게 그려 주세요.')
 # Avoid numerical rounding dropping three distinct vertices.
 return [c for c in result if len(set((x,y) for x,y,_ in c))>=3]


def apply_paint(data):
 if not isinstance(data,dict):raise StudioError('올바른 그리기 요청이 아닙니다.')
 old=contours_to_geometry(data.get('contours',[]))
 fresh=_paint_geometry(data)
 if not fresh.is_valid:fresh=_clean(fresh)
 if data.get('tool')=='eraser':new=old.difference(fresh)
 else:new=old.union(fresh)
 # Restrict all generated contours to the allowable glyph coordinate range.
 new=_clean(new).intersection(box(BOUNDS[0],BOUNDS[0],BOUNDS[1],BOUNDS[1]))
 return {'contours':geometry_to_contours(new),
         'changed':not new.equals(old),
         'area':round(new.area,1)}
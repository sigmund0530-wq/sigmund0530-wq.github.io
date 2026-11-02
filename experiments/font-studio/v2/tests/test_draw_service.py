"""Test actual painting/erasing and glyph export, not CSS-only effects."""
import io,sys,unittest,copy
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fontTools.ttLib import TTFont
from font_service import build_font,project_default,glyph_outline,StudioError
from draw_service import apply_paint,contours_to_geometry

class DrawingTests(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.base=glyph_outline('gothic','가')['contours']
 def test_brush_and_eraser_change_geometry(self):
  a=contours_to_geometry(self.base).area
  paint=apply_paint({'tool':'brush','contours':self.base,'width':92,'points':[[100,360],[330,350],[680,410]]})
  self.assertTrue(paint['changed'])
  self.assertGreater(paint['area'],a)
  erase=apply_paint({'tool':'eraser','contours':paint['contours'],'width':125,'points':[[80,360],[820,360]]})
  self.assertTrue(erase['changed']);self.assertLess(erase['area'],paint['area'])
  self.assertNotEqual(paint['contours'],erase['contours'])
 def test_shapes_and_pen(self):
  base=[]
  rect=apply_paint({'tool':'rect','contours':base,'points':[[100,100],[700,700]]})
  circle=apply_paint({'tool':'ellipse','contours':rect['contours'],'points':[[350,350],[870,850]]})
  triangle=apply_paint({'tool':'polygon','contours':circle['contours'],'points':[[100,90],[240,100],[210,260]]})
  self.assertGreater(triangle['area'],rect['area'])
  self.assertTrue(all(len(contour)>=3 for contour in triangle['contours']))
 def test_blank_or_drawn_export(self):
  res=apply_paint({'tool':'brush','contours':[],'width':70,'points':[[130,800],[450,220],[750,770]]})
  p=project_default();p['overrides']['가']=res['contours']
  raw,_=build_font(p)
  f=TTFont(io.BytesIO(raw))
  glyph=f['glyf'][f.getBestCmap()[ord('가')]]
  self.assertGreater(glyph.numberOfContours,0)
  self.assertEqual(len([c for c in f.getBestCmap() if 0xAC00<=c<=0xD7A3]),11172)
  f.close()
 def test_eraser_preserves_existing_holes(self):
  rect=apply_paint({'tool':'rect','contours':[],'points':[[100,100],[700,700]]})
  # cut a hole inside center, outside boundary unaffected
  er=apply_paint({'tool':'eraser','contours':rect['contours'],'width':120,'points':[[320,380],[480,380]]})
  self.assertEqual(len(er['contours']),2)
  self.assertAlmostEqual(contours_to_geometry(er['contours']).area,er['area'],delta=3)
  p=project_default();p['overrides']['가']=er['contours'];raw,_=build_font(p)
  with TTFont(io.BytesIO(raw)) as ft:
   self.assertEqual(ft['glyf'][ft.getBestCmap()[ord('가')]].numberOfContours,2)
 def test_validation(self):
  examples=[{'tool':'brush','contours':[],'width':800,'points':[[5,5]]},
            {'tool':'brush','contours':[],'width':12,'points':[[float('nan'),9]]},
            {'tool':'eraser','contours':[],'width':12,'points':[[1,1]]*701},
            {'tool':'polygon','contours':[],'points':[[1,2],[2,3]]}]
  for d in examples:
   with self.subTest(d=d['tool']):
    with self.assertRaises(StudioError):apply_paint(d)

if __name__=='__main__':unittest.main()
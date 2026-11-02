import io
import sys
import copy
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from fontTools.ttLib import TTFont
from font_service import (read_font_info,StudioError,project_default,validate_project,
                          glyph_outline,build_font,clean_name)

class FontTests(unittest.TestCase):
 def test_license_and_11172_coverage(self):
  for key in ('gothic','gothic-bold','myeongjo'):
   info=read_font_info(key)
   self.assertEqual(info['hangul_count'],11172)
   self.assertEqual(info['license'].split('/')[-1],'OFL.txt')

 def test_font_roundtrip_and_faithful_outline(self):
  base=project_default()
  raw,info=build_font(base)
  f=TTFont(io.BytesIO(raw));self.assertEqual(info['hangul'],11172)
  cmap=f.getBestCmap()
  self.assertTrue(all(cp in cmap for cp in range(0xAC00,0xD7A4)))
  self.assertTrue(f['name'].getDebugName(1).startswith('MGD '))
  self.assertTrue(any(n.nameID==13 for n in f['name'].names),'Source license metadata must remain')
  with TTFont(str(Path(__file__).resolve().parents[1]/'runtime/fonts/NanumGothic-Regular.ttf')) as source:
   orig=source['glyf'][source.getBestCmap()[ord('가')]].getCoordinates(source['glyf'])[0]
   actual=f['glyf'][cmap[ord('가')]].getCoordinates(f['glyf'])[0]
   self.assertEqual(list(orig),list(actual))
  f.close()

 def test_individual_edit_and_metrics(self):
  p=project_default();orig=glyph_outline('gothic','각');edit=copy.deepcopy(orig['contours'])
  edit[0][0][0]+=85
  p['overrides']={'각':edit};p['width']=110;p['slant']=6;p['tracking']=35
  ttf,meta=build_font(p)
  f=TTFont(io.BytesIO(ttf))
  self.assertEqual(meta['modified_glyphs'],1)
  self.assertEqual(meta['hangul'],11172)
  self.assertNotEqual(list(f['glyf'][f.getBestCmap()[ord('각')]].getCoordinates(f['glyf'])[0]),
                      list(f['glyf'][f.getBestCmap()[ord('가')]].getCoordinates(f['glyf'])[0]))
  woff,meta2=build_font(p,'woff2')
  self.assertLess(len(woff),len(ttf))
  wf=TTFont(io.BytesIO(woff));self.assertEqual(wf.flavor,'woff2');self.assertIn(ord('각'),wf.getBestCmap())

 def test_validation_dangerous_data(self):
  p=project_default()
  for v in ['나눔고딕','NanumGothic','   ', 'a/b']:
   with self.assertRaises(StudioError):clean_name(v)
  for bad in [dict(width=0),dict(slant=90),dict(tracking=10000),dict(version='evil'),dict(overrides={'가':[[[1,2,True]]]})]:
   other=copy.deepcopy(p);other.update(bad)
   with self.assertRaises(StudioError):validate_project(other)

if __name__=='__main__':unittest.main()
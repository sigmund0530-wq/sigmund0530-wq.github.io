import copy
import io
import json
import sys
import unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).parents[1]))
from fontTools.ttLib import TTFont
from font_engine import (default_project,compile_font,InputError,L,V,T,validate_project)

class FontStudioTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.project=default_project()
        cls.fontbytes,cls.meta=compile_font(cls.project,'테스트',format='ttf')
        cls.font=TTFont(io.BytesIO(cls.fontbytes))

    def test_all_syllables_are_supported(self):
        cmap=self.font.getBestCmap()
        self.assertEqual(11172,self.meta['hangul_syllables'])
        self.assertEqual(67,self.meta['base_components'])
        self.assertTrue(all(cp in cmap for cp in range(0xAC00,0xD7A4)))
        for cp in (0xAC00,0xAC01,0xB098,0xD7A3):
            self.assertTrue(self.font['glyf'][cmap[cp]].isComposite())
        self.assertEqual(self.font['name'].getDebugName(1),'MGD 테스트')

    def test_l_edit_changes_source_and_linked_588_syllables(self):
        p=copy.deepcopy(self.project)
        p['data']['bases']['L']['ㄱ'][0]['pts'][0]['x']=35
        edit,_=compile_font(p,'테스트')
        f=TTFont(io.BytesIO(edit))
        g=self.font['glyf'];g2=f['glyf']
        self.assertNotEqual(g['L0'].compile(g),g2['L0'].compile(g2))
        self.assertEqual(g['L2'].compile(g),g2['L2'].compile(g2))
        cmap=f.getBestCmap()
        self.assertEqual(sum(g2[cmap[cp]].isComposite() and g2[cmap[cp]].components[0].glyphName=='L0' for cp in range(0xAC00,0xD7A4)),588)

    def test_custom_glyph_override_is_not_composite(self):
        p=copy.deepcopy(self.project)
        p['data']['overrides']['가']=[{'kind':'path','pts':[{'x':10,'y':20},{'x':90,'y':80}], 'smooth':False, 'closed':False}]
        b,meta=compile_font(p)
        f=TTFont(io.BytesIO(b));self.assertFalse(f['glyf']['uniAC00'].isComposite())
        self.assertTrue(f['glyf']['uniAC01'].isComposite())
        self.assertEqual(meta['overrides'],1)

    def test_woff2_roundtrip(self):
        b,meta=compile_font(self.project,format='woff2')
        f=TTFont(io.BytesIO(b))
        self.assertEqual(f.flavor,'woff2')
        self.assertIn(0xD7A3,f.getBestCmap())
        self.assertLess(len(b),len(self.fontbytes))

    def test_invalid_data_rejected(self):
        for edit in (lambda p:p['data'].update(weight=123),
                     lambda p:p['data']['bases']['L'].pop('ㄱ'),
                     lambda p:p['data']['overrides'].update({'Z':[]}),
                     lambda p:p['data']['bases']['L']['ㄱ'][0]['pts'][0].update(x=float('nan'))):
            p=copy.deepcopy(self.project);edit(p)
            with self.assertRaises(InputError):compile_font(p)

    def test_smooth_and_ellipse_produce_curves_or_outlines(self):
        p=copy.deepcopy(self.project)
        p['data']['bases']['L']['ㄱ']=[{'kind':'path','pts':[{'x':10,'y':10},{'x':48,'y':80},{'x':90,'y':10}], 'smooth':True,'closed':False}, {'kind':'ellipse','cx':50,'cy':50,'rx':20,'ry':30}]
        b,_=compile_font(p)
        f=TTFont(io.BytesIO(b))
        self.assertGreater(f['glyf']['L0'].numberOfContours,0)

if __name__=='__main__':unittest.main()

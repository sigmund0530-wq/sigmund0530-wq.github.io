(()=>{
'use strict';
const $=id=>document.getElementById(id), SVG='http://www.w3.org/2000/svg';
const STORAGE='mgd.fontstudio.v2.projects';
const DEFAULT_TEXT='기록은 오래 남아, 우리의 하루를 닮는다.\n오늘의 마음을 나만의 글씨로 적어 봐.';
const SAMPLE={diary:DEFAULT_TEXT,title:'오늘도 내 방식대로.\n무가당 글자공방',poem:'오래된 마음에\n새로운 글씨를 입히면\n우리의 오늘은 조금 달라진다.'};
const FONTS=[{id:'gothic',label:'단정한 고딕'},{id:'gothic-bold',label:'또렷한 고딕'},{id:'myeongjo',label:'차분한 명조'},{id:'gowun',label:'부드러운 돋움'},{id:'batang',label:'따뜻한 바탕'}];
const DEFAULT={version:'mgd-font-studio-v2',name:'나의 글씨',font:'gothic',width:100,slant:0,tracking:0,overrides:{}};
const uuid=()=>Date.now().toString(36)+'-'+Math.random().toString(36).slice(2,7);
const clone=o=>structuredClone(o);
const safeText=s=>String(s||'').replace(/[\u0000-\u001f]/g,' ').slice(0,500);
const now=()=>new Date().toISOString();
let entries=[],currentId=null,project=null,screen='compose';
let editorChar='가',contours=[],originContours=[],glyphContour=0,pointIndex=-1,tool='select',drag=null,glyphToken=0;
let paintStroke=null,penPoints=[],paintingBusy=false,zoom=100,centerX=500,centerY=520;
let history=[],redo=[],fontLoading={},verifiedFont=null,verifiedObjectUrl=null,toastTimer=0,saveTimer=0;
function notify(message,error=false){const t=$('toast');t.textContent=message;t.style.background=error?'#7e3333':'#23392a';t.hidden=false;clearTimeout(toastTimer);toastTimer=setTimeout(()=>t.hidden=true,4100)}
function stored(){try{const raw=JSON.parse(localStorage.getItem(STORAGE)||'null');return Array.isArray(raw)?raw.filter(e=>e&&e.id&&e.project&&e.project.version===DEFAULT.version).slice(0,12):[]}catch{return []}}
function initProjects(){entries=stored();if(!entries.length)entries=[{id:uuid(),project:clone(DEFAULT),specimen:DEFAULT_TEXT,updated:now()}];currentId=entries[0].id;project=entries[0].project;save();}
const entry=()=>entries.find(e=>e.id===currentId);
function save(){if(!project)return;entry().project=project;entry().updated=now();try{localStorage.setItem(STORAGE,JSON.stringify(entries))}catch{notify('브라우저 저장 공간이 부족합니다. JSON으로 백업하세요.',true)}$('save-indicator').textContent='자동 저장됨';renderProjectList()}
function scheduleSave(){clearTimeout(saveTimer);$('save-indicator').textContent='저장 중...';saveTimer=setTimeout(save,210)}
function record(){history.push(JSON.stringify(project));if(history.length>45)history.shift();redo=[]}
function changed(shouldRender=true){verifiedFont=null;dropAccurate();scheduleSave();if(shouldRender){updateAll();if(screen==='glyph')drawGlyph()}}
function undo(){if(!history.length)return;redo.push(JSON.stringify(project));project=JSON.parse(history.pop());entry().project=project;updateAll();if(screen==='glyph')loadGlyph(editorChar);scheduleSave();notify('한 단계 되돌렸어요.')}
function redoAction(){if(!redo.length)return;history.push(JSON.stringify(project));project=JSON.parse(redo.pop());entry().project=project;updateAll();if(screen==='glyph')loadGlyph(editorChar);scheduleSave();notify('다시 적용했어요.')}
function renderProjectList(){$('project-count').textContent=entries.length+'개';$('project-list').replaceChildren();entries.forEach(e=>{const b=document.createElement('button');b.className='project-item'+(e.id===currentId?' active':'');const g=document.createElement('span');g.className='picon';g.textContent='가';const m=document.createElement('span');m.className='pmeta';const strong=document.createElement('strong');strong.textContent=e.project.name;const small=document.createElement('small');small.textContent=(FONTS.find(f=>f.id===e.project.font)?.label||'나의 글꼴')+' · '+(Object.keys(e.project.overrides||{}).length)+'글자 보정';m.append(strong,small);b.append(g,m);b.addEventListener('click',()=>switchProject(e.id));$('project-list').append(b)})}
function renderTemplates(){$('template-list').replaceChildren();FONTS.forEach(f=>{const b=document.createElement('button');b.className='template'+(f.id===project.font?' active':'');const preview=document.createElement('span');preview.className='template-preview';preview.textContent='가';preview.style.fontFamily='Source-'+f.id+',serif';const content=document.createElement('span');content.innerHTML='<strong></strong><small>한글 전체 지원 · OFL</small>';content.firstChild.textContent=f.label;b.append(preview,content);b.onclick=()=>chooseFont(f.id);$('template-list').append(b)})}
function switchProject(id){if(currentId===id)return;save();const found=entries.find(e=>e.id===id);if(!found)return;currentId=id;project=found.project;history=[];redo=[];verifiedFont=null;dropAccurate();$('specimen').value=found.specimen||DEFAULT_TEXT;updateAll();renderProjectList();if(screen==='glyph')loadGlyph(editorChar);setMenu(false)}
function chooseFont(id){if(project.font===id)return;if(Object.keys(project.overrides).length&&!confirm('다른 서체를 선택하면 지금까지 이 글꼴에서 수정한 글자 윤곽이 초기화됩니다. 계속할까요?'))return;record();project.font=id;project.overrides={};changed();renderTemplates();loadSourceFont(id);if(screen==='glyph')loadGlyph(editorChar);notify('새로운 기본 서체를 선택했어요.');setMenu(false)}
function newProject(){if(entries.length>=12){notify('프로젝트는 최대 12개까지 저장할 수 있어요. 작업 파일로 백업하세요.',true);return}save();let e={id:uuid(),project:clone(DEFAULT),specimen:DEFAULT_TEXT,updated:now()};e.project.name='새로운 글씨 '+(entries.length+1);entries.unshift(e);currentId=e.id;project=e.project;history=[];redo=[];dropAccurate();$('specimen').value=DEFAULT_TEXT;selectScreen('compose');updateAll();save();setMenu(false);notify('새로운 폰트 작업을 만들었어요.')}
function setMenu(open){$('sidebar').classList.toggle('open',open);$('backdrop').hidden=!open}
function updateAll(){if(!project)return;$('top-name').textContent=project.name;$('font-name').value=project.name;for(const id of ['width','slant','tracking'])$(id).value=project[id];$('width-output').textContent=project.width+'%';$('slant-output').textContent=(project.slant>0?'+':'')+project.slant+'°';$('tracking-output').textContent=(project.tracking>0?'+':'')+project.tracking;$('preview-source').textContent=(FONTS.find(x=>x.id===project.font)?.label||'기본 서체')+' · 직접 수정 '+Object.keys(project.overrides).length+'글자';renderTemplates();renderProjectList();applyPreview();updatePreset();$('license-url').href=project.font.includes('gothic')?'https://github.com/google/fonts/blob/main/ofl/nanumgothic/OFL.txt':project.font==='myeongjo'?'https://github.com/google/fonts/blob/main/ofl/nanummyeongjo/OFL.txt':project.font==='gowun'?'https://github.com/google/fonts/blob/main/ofl/gowundodum/OFL.txt':'https://github.com/google/fonts/blob/main/ofl/gowunbatang/OFL.txt'}
function updatePreset(){const selected=project.width===100&&project.tracking===0&&project.slant===0?'neutral':project.width===107&&project.tracking===60&&project.slant===0?'soft':project.width===92&&project.tracking===-15&&project.slant===0?'sharp':'';document.querySelectorAll('[data-preset]').forEach(b=>b.classList.toggle('active',b.dataset.preset===selected))}
async function loadSourceFont(id){if(fontLoading[id])return fontLoading[id];fontLoading[id]=(async()=>{try{const f=new FontFace('Source-'+id,`url('/api/fonts/${id}')`);await f.load();document.fonts.add(f);if(id===project.font){applyPreview();renderTemplates()}return true}catch(e){notify('기본 글꼴을 불러오지 못했습니다. 다운로드 설정을 확인하세요.',true);delete fontLoading[id];return false}})();return fontLoading[id]}
function dropAccurate(){if(verifiedObjectUrl){URL.revokeObjectURL(verifiedObjectUrl);verifiedObjectUrl=null}verifiedFont=null;$('final-state').textContent='현재 설정의 화면 미리보기 · 정확한 파일 결과는 생성 후 확인'}
function applyPreview(){const useExact=!!verifiedFont;const source=useExact?verifiedFont:'Source-'+project.font;const tgts=[$('specimen'),$('final-specimen')];tgts.forEach(node=>{node.style.fontFamily=`"${source}","Apple SD Gothic Neo",sans-serif`;node.style.fontStyle=useExact?'normal':`oblique ${project.slant}deg`;node.style.letterSpacing=useExact?'normal':(project.tracking/1000*30)+'px';node.style.transform=useExact?'none':`scaleX(${project.width/100})`;node.style.transformOrigin='left center';node.style.width=useExact?'100%':`${10000/project.width}%`});}
function selectScreen(key){screen=key;for(const s of ['compose','glyph','export']){const on=s===key;$(s+'-screen').hidden=!on;const tab=$(s==='compose'?'tab-compose':s==='glyph'?'tab-glyph':'tab-export');tab.classList.toggle('on',on);tab.setAttribute('aria-selected',String(on))}if(key==='glyph'){loadGlyph(editorChar)}if(key==='export')applyPreview();if(key==='compose')updateAll();window.scrollTo({top:0,behavior:'smooth'})}
function download(blob,name){const url=URL.createObjectURL(blob);const link=document.createElement('a');link.href=url;link.download=name;document.body.append(link);link.click();link.remove();setTimeout(()=>URL.revokeObjectURL(url),10000)}
async function fontOutput(fmt,previewOnly=false){const buttons=['download-ttf','download-woff2','render-accurate','precise-preview'];buttons.forEach(x=>$(x).disabled=true);const label=$('save-indicator');label.textContent='폰트 생성 중...';try{const response=await fetch('/api/build',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({project,format:previewOnly?'woff2':fmt})});if(!response.ok){let message='폰트 생성 오류';try{message=(await response.json()).error||message}catch{}throw Error(message)}const blob=await response.blob();if(previewOnly){if(verifiedObjectUrl)URL.revokeObjectURL(verifiedObjectUrl);verifiedObjectUrl=URL.createObjectURL(blob);const family='MGD-Preview-'+Date.now();const face=new FontFace(family,`url("${verifiedObjectUrl}")`);await face.load();document.fonts.add(face);verifiedFont=family;applyPreview();$('final-state').textContent='실제 WOFF2 생성 결과로 확인 중 · 한글 전체 포함';notify('실제 폰트 파일로 미리보기를 갱신했어요.');}else{const safe=(project.name.trim().replace(/[\\/<>:"|?*]/g,'_')||'나의-글씨');download(blob,`MGD-${safe}.${fmt}`);notify('실제 '+fmt.toUpperCase()+' 글꼴 파일을 받았어요.');}return true}catch(e){notify(e.message||'폰트 파일을 만드는 데 실패했어요.',true);return false}finally{buttons.forEach(x=>$(x).disabled=false);label.textContent='자동 저장됨'}}
function exportJSON(){save();const data={source:'무가당 글자공방',exportedAt:now(),specimen:$('specimen').value,project};download(new Blob([JSON.stringify(data,null,2)],{type:'application/json'}),`MGD-${project.name.replace(/[\\/<>:"|?*]/g,'_')}-작업.json`);notify('편집 가능한 작업 파일을 저장했어요.')}
async function importJSON(input){try{if(!input.files?.length)return;const f=input.files[0];if(f.size>1_300_000)throw Error('작업 파일이 너무 큽니다.');const p=JSON.parse(await f.text());const data=p.project||p;if(data.version!==DEFAULT.version)throw Error('v2 글자공방의 작업 JSON이 아니에요.');if(!FONTS.some(f=>f.id===data.font)||!data.overrides||typeof data.overrides!=='object')throw Error('작업 데이터가 올바르지 않아요.');if(Object.keys(data.overrides).length>256)throw Error('수정 글자가 너무 많아요.');if(entries.length>=12)throw Error('프로젝트가 너무 많아요. JSON 백업 후 정리해 주세요.');const e={id:uuid(),project:clone(data),specimen:typeof p.specimen==='string'?p.specimen:DEFAULT_TEXT,updated:now()};entries.unshift(e);currentId=e.id;project=e.project;history=[];redo=[];$('specimen').value=e.specimen;dropAccurate();save();updateAll();loadSourceFont(project.font);selectScreen('compose');notify('작업 파일을 가져왔어요.')}catch(e){notify(e.message,true)}finally{input.value=''}}
function updateGlyphQuicklist(){const sample=$('specimen').value;const found=[...new Set([...sample].filter(ch=>/^[가-힣]$/.test(ch)))].slice(0,12);if(!found.includes(editorChar))found.unshift(editorChar);$('glyph-quicklist').replaceChildren();for(const char of found){const b=document.createElement('button');b.textContent=char;b.className=char===editorChar?'active':'';b.title=char+' 편집';b.onclick=()=>loadGlyph(char);$('glyph-quicklist').append(b)}}
async function loadGlyph(ch){if(!ch||[...ch].length!==1)return;cancelPainting();editorChar=ch;$('glyph-input').value=ch;$('inspector-char').textContent=ch;$('glyph-canvas-label').textContent=ch+' · '+(project.overrides[ch]?'수정 중':'원본 윤곽');$('glyph-status').textContent=project.overrides[ch]?'개별 수정된 글자':'원본 글자';$('glyph-point-count').textContent='불러오는 중...';updateGlyphQuicklist();const token=++glyphToken;try{const resp=await fetch(`/api/glyph?font=${encodeURIComponent(project.font)}&char=${encodeURIComponent(ch)}`);const data=await resp.json();if(!resp.ok)throw Error(data.error||'글자를 가져올 수 없습니다.');if(token!==glyphToken)return;originContours=data.contours;contours=clone(project.overrides[ch]||data.contours);glyphContour=Math.min(glyphContour,Math.max(0,contours.length-1));pointIndex=-1;drawGlyph()}catch(e){if(token!==glyphToken)return;contours=[];originContours=[];drawGlyph();notify(e.message,true)}}
// TrueType Q curves: consecutive off-curve points receive an implied midpoint.
function contourPath(points){if(!points||points.length<3)return'';const n=points.length,pts=points;let startIndex=0,start;if(pts[0][2]){start=pts[0];startIndex=0}else if(pts[n-1][2]){start=pts[n-1];startIndex=n-1}else{start=[(pts[0][0]+pts[n-1][0])/2,(pts[0][1]+pts[n-1][1])/2,true];startIndex=n-1}
let d=`M${start[0]} ${start[1]}`;let i=1;while(i<=n){const a=pts[(startIndex+i)%n];if(a[2]){d+=`L${a[0]} ${a[1]}`;i++}else{const b=pts[(startIndex+i+1)%n];if(b[2]){d+=`Q${a[0]} ${a[1]} ${b[0]} ${b[1]}`;i+=2}else{const x=(a[0]+b[0])/2,y=(a[1]+b[1])/2;d+=`Q${a[0]} ${a[1]} ${x} ${y}`;i++}}}return d+'Z'}
function el(tag,attrs={}){const node=document.createElementNS(SVG,tag);Object.entries(attrs).forEach(([k,v])=>node.setAttribute(k,String(v)));return node}
function drawGlyph(){
 const target=$('glyph-fill'),hits=$('glyph-hit'),handles=$('glyph-handles');
 target.setAttribute('d',contours.map(contourPath).join(' '));
 hits.replaceChildren();handles.replaceChildren();
 contours.forEach((points,idx)=>{
  const path=el('path',{d:contourPath(points),class:'outline-hit'+(glyphContour===idx?' selected':''),'data-index':idx});
  path.addEventListener('pointerdown',ev=>{
   if(tool!=='select'&&tool!=='move')return;
   ev.stopPropagation();
   glyphContour=idx;pointIndex=-1;
   if(tool==='move')startContourMove(ev,idx);
   drawGlyph();
  });hits.append(path);
 });
 if(tool==='select'||tool==='move'){
  const pts=contours[glyphContour]||[];
  pts.forEach((p,i)=>{
   if(!p[2]){
    const prev=pts[(i-1+pts.length)%pts.length],next=pts[(i+1)%pts.length];
    for(const q of [prev,next])if(q)handles.append(el('path',{d:`M${p[0]} ${p[1]}L${q[0]} ${q[1]}`,class:'handle-line'}));
   }
   const circle=el('circle',{cx:p[0],cy:p[1],r:pointIndex===i?11:8,class:'handle'+(!p[2]?' off':'')+(pointIndex===i?' current':''),'pointer-events':'none'});
   const hit=el('circle',{cx:p[0],cy:p[1],r:25,fill:'transparent',class:'handle-grab','data-index':i,tabindex:'0',role:'button','aria-label':(i+1)+'번째 점 이동'});
   hit.addEventListener('pointerdown',ev=>startDrag(ev,glyphContour,i));
   hit.addEventListener('click',()=>{glyphContour=Math.min(glyphContour,contours.length-1);pointIndex=i;drawGlyph()});
   handles.append(circle,hit);
  });
 }
 $('glyph-point-count').textContent=contours.length+'개 윤곽 · '+contours.reduce((x,c)=>x+c.length,0)+'개 점';
 $('glyph-status').textContent=project.overrides[editorChar]?'내가 수정한 글자':'원본 글자';
 $('glyph-canvas-label').textContent=editorChar+' · '+(project.overrides[editorChar]?'개별 수정됨':'원본 윤곽');
 $('editor-undo').disabled=!history.length;$('editor-redo').disabled=!redo.length;
}
function coordsFromEvent(ev){const svg=$('glyph-canvas');const pt=svg.createSVGPoint();pt.x=ev.clientX;pt.y=ev.clientY;const inv=svg.getScreenCTM()?.inverse();if(!inv)return[0,0];const v=pt.matrixTransform(inv);return [Math.round(v.x*10)/10,Math.round(v.y*10)/10]}
function persistGlyph(){project.overrides[editorChar]=clone(contours);changed(false);drawGlyph()}
function startDrag(ev,c,p){ev.stopPropagation();if(tool!=='select')return;ev.preventDefault();glyphContour=c;pointIndex=p;record();drag={kind:'point',pointerId:ev.pointerId,c,p};$('glyph-canvas').setPointerCapture(ev.pointerId);drawGlyph()}
function startContourMove(ev,c){ev.preventDefault();record();drag={kind:'move',pointerId:ev.pointerId,c,start:coordsFromEvent(ev),initial:clone(contours[c])};$('glyph-canvas').setPointerCapture(ev.pointerId)}
function clamp(v){return Math.max(-560,Math.min(1560,v))}
function updateZoom(){const v=100/zoom,w=1160*v,h=1240*v;$('glyph-canvas').setAttribute('viewBox',`${centerX-w/2} ${centerY-h/2} ${w} ${h}`);$('zoom-value').textContent=zoom+'%'}
function changeZoom(delta){zoom=Math.min(300,Math.max(60,Math.round(zoom+delta)));updateZoom()}
function glyphTool(name){
 if(tool==='polygon'&&name!=='polygon')cancelPainting();
 tool=name;
 const canv=$('glyph-canvas');canv.classList.remove('brush-mode','eraser-mode','move-mode','pan-mode','pen-mode');
 canv.classList.add(({brush:'brush-mode',eraser:'eraser-mode',move:'move-mode',pan:'pan-mode',polygon:'pen-mode',rectangle:'pen-mode',ellipse:'pen-mode'})[name]||'');
 document.querySelectorAll('[data-tool]').forEach(b=>b.classList.toggle('active',b.dataset.tool===name));
 const guide={select:'점과 곡선을 직접 끌어 글자를 바꾸세요. 점은 선택 후 직선/곡선 전환도 가능해요.',move:'옮길 윤곽의 경계를 잡고 끌어 보세요. 오른쪽에서 복제·회전·크기 조절도 가능해요.',brush:'손가락·마우스로 직접 획을 그려요. 그린 획은 실제 폰트 윤곽에 합쳐져요.',eraser:'글자의 지우고 싶은 부분을 직접 문지르세요. 투명한 공간으로 잘려 나가요.',polygon:'점을 차례대로 찍어 형태를 만들어요. Enter 또는 첫 점을 다시 누르면 닫히고, Esc로 취소돼요.',rectangle:'드래그해서 사각형을 그리세요.',ellipse:'드래그해서 타원을 그리세요.',pan:'끌어서 도화지를 이동하세요. 확대/축소는 위의 +/− 버튼을 사용하세요.'};
 $('editor-hint').textContent=guide[name]||'';drawGlyph();
}
function cancelPainting(){paintStroke=null;penPoints=[];if($('paint-preview'))$('paint-preview').replaceChildren()}
function updatePaintPreview(pointer){
 const grp=$('paint-preview');grp.replaceChildren();
 if(penPoints.length){
  const v=pointer?[...penPoints,pointer]:penPoints;
  grp.append(el('path',{d:v.map((p,i)=>(i?'L':'M')+p[0]+' '+p[1]).join(' '),class:'polygon-preview',fill:'none'}));
  penPoints.forEach((p,i)=>grp.append(el('circle',{cx:p[0],cy:p[1],r:i===0?10:7,fill:i===0?'#de9e48':'#4f8059'})));
 }
 if(!paintStroke)return;
 const pts=paintStroke.points;
 if(paintStroke.kind==='brush'||paintStroke.kind==='eraser'){
  const d=pts.length===1?`M${pts[0][0]} ${pts[0][1]}l0.1 0`:pts.map((p,i)=>(i?'L':'M')+p[0]+' '+p[1]).join(' ');
  grp.append(el('path',{d,class:paintStroke.kind==='eraser'?'erase-stroke':'brush-stroke','stroke-width':paintStroke.width}));
 } else if(pts.length>=2){
  const [a,b]=pts;const x=Math.min(a[0],b[0]),y=Math.min(a[1],b[1]),w=Math.abs(b[0]-a[0]),h=Math.abs(b[1]-a[1]);
  grp.append(el(paintStroke.kind==='rectangle'?'rect':'ellipse',paintStroke.kind==='rectangle'?{x,y,width:w,height:h,class:'shape-preview'}:{cx:x+w/2,cy:y+h/2,rx:w/2,ry:h/2,class:'shape-preview'}));
 }
}
async function commitPaint(kind,points,width=32){
 if(paintingBusy)return;
 const selectedChar=editorChar;
 const source=clone(contours);
 paintingBusy=true;$('editor-hint').textContent='벡터 윤곽을 계산하고 있어요…';
 try{
  const resp=await fetch('/api/paint',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({tool:kind,contours:source,points,width})});
  const data=await resp.json();if(!resp.ok)throw Error(data.error||'그리기를 적용하지 못했어요.');
  if(editorChar!==selectedChar)return;
  if(data.changed){record();contours=data.contours;glyphContour=Math.max(0,contours.length-1);pointIndex=-1;persistGlyph();notify(kind==='eraser'?'글자 일부를 지웠어요.':'그린 모양이 글자 윤곽에 적용됐어요.');}
  else notify('변경된 영역이 없어요.');
 }catch(e){notify(e.message||'그리기 실패',true)}
 finally{paintingBusy=false;$('editor-hint').textContent='다른 획을 더 그리거나, 점 선택으로 바꿔 자세히 수정할 수 있어요.'}
}
async function finishPen(){
 if(penPoints.length<3){notify('점을 최소 3개 찍어 주세요.',true);return}
 const points=penPoints.slice();penPoints=[];updatePaintPreview();await commitPaint('polygon',points);
}
function canvasDown(ev){
 if(ev.button!==0||paintingBusy||drag)return;
 const svg=$('glyph-canvas');
 if(tool==='polygon'){
  ev.preventDefault();const p=coordsFromEvent(ev);
  if(penPoints.length>=3&&Math.hypot(p[0]-penPoints[0][0],p[1]-penPoints[0][1])<24){finishPen();return}
  penPoints.push(p);updatePaintPreview();if(ev.detail>=2&&penPoints.length>=3)finishPen();return;
 }
 if(!['brush','eraser','rectangle','ellipse','pan'].includes(tool))return;
 ev.preventDefault();
 const point=coordsFromEvent(ev);
 paintStroke={kind:tool,pointerId:ev.pointerId,points:[point],width:+$('stroke-size').value,startView:[centerX,centerY],startClient:[ev.clientX,ev.clientY]};
 if(tool==='rectangle'||tool==='ellipse')paintStroke.points.push(point);
 svg.setPointerCapture(ev.pointerId);updatePaintPreview();
}
function svgMove(ev){
 if(paintStroke&&paintStroke.pointerId===ev.pointerId){
  const t=paintStroke;
  if(t.kind==='pan'){
   const rect=$('glyph-canvas').getBoundingClientRect();const dims=$('glyph-canvas').viewBox.baseVal;
   centerX=t.startView[0]-(ev.clientX-t.startClient[0])*dims.width/rect.width;
   centerY=t.startView[1]-(ev.clientY-t.startClient[1])*dims.height/rect.height;
   updateZoom();return;
  }
  const p=coordsFromEvent(ev);
  if(t.kind==='rectangle'||t.kind==='ellipse')t.points[1]=p;
  else if(t.points.length<700 && Math.hypot(p[0]-t.points.at(-1)[0],p[1]-t.points.at(-1)[1])>2.2)t.points.push(p);
  updatePaintPreview();return;
 }
 if(penPoints.length&&tool==='polygon'){updatePaintPreview(coordsFromEvent(ev));return}
 if(!drag||drag.pointerId!==ev.pointerId)return;
 const [x,y]=coordsFromEvent(ev);
 if(drag.kind==='point')contours[drag.c][drag.p]=[clamp(x),clamp(y),contours[drag.c][drag.p][2]];
 else if(drag.kind==='move'){
  const dx=x-drag.start[0],dy=y-drag.start[1];
  contours[drag.c]=drag.initial.map(pt=>[clamp(pt[0]+dx),clamp(pt[1]+dy),pt[2]]);
 }
 project.overrides[editorChar]=clone(contours);drawGlyph();
}
async function svgUp(ev){
 if(paintStroke&&paintStroke.pointerId===ev.pointerId){
  const t=paintStroke;paintStroke=null;updatePaintPreview();
  if(t.kind==='pan')return;
  // Ignore tiny accidental taps for shapes; a single brush tap draws a dot.
  if(['rectangle','ellipse'].includes(t.kind)&&Math.hypot(t.points[0][0]-t.points[1][0],t.points[0][1]-t.points[1][1])<4)return;
  await commitPaint(t.kind,t.points,t.width);return;
 }
 if(!drag||drag.pointerId!==ev.pointerId)return;
 drag=null;persistGlyph();notify('글자 윤곽을 저장했어요.');
}
function transformContour(kind){
 const src=contours[glyphContour];if(!src){notify('변형할 윤곽이 없습니다.');return}
 const xs=src.map(p=>p[0]),ys=src.map(p=>p[1]);const cx=(Math.min(...xs)+Math.max(...xs))/2,cy=(Math.min(...ys)+Math.max(...ys))/2;
 const rad=(kind==='rotate-left'?-15:15)*Math.PI/180;
 function convert(pt){let x=pt[0]-cx,y=pt[1]-cy;
  if(kind==='flip-h')x=-x;
  if(kind==='flip-v')y=-y;
  if(kind.startsWith('rotate-'))[x,y]=[x*Math.cos(rad)-y*Math.sin(rad),x*Math.sin(rad)+y*Math.cos(rad)];
  if(kind==='grow'||kind==='shrink'){const v=kind==='grow'?1.1:1/1.1;x*=v;y*=v}
  return [Math.round(clamp(cx+x)*10)/10,Math.round(clamp(cy+y)*10)/10,pt[2]]
 }
 record();
 if(kind==='duplicate'){
  if(contours.length>=120){notify('윤곽 개수가 너무 많아요.',true);return}
  contours.push(src.map(pt=>[clamp(pt[0]+45),clamp(pt[1]+45),pt[2]]));glyphContour=contours.length-1;
 }else contours[glyphContour]=src.map(convert);
 pointIndex=-1;persistGlyph();
}
function blankGlyph(){
 if(!confirm(editorChar+' 글자의 원본 윤곽을 지우고 빈 도화지에서 시작할까요? (되돌리기 가능)'))return;
 record();contours=[];glyphContour=0;pointIndex=-1;persistGlyph();glyphTool('brush');notify('빈 도화지에서 자유롭게 그려 보세요.');
}
function glyphAction(kind){if(!contours.length)return;const pts=contours[glyphContour];if(!pts)return;if(kind==='delete-contour'){record();contours.splice(glyphContour,1);glyphContour=Math.max(0,glyphContour-1);pointIndex=-1}
else if(kind==='delete-point'){if(pointIndex<0){notify('먼저 점을 선택하세요.');return}if(pts.length<=3){notify('윤곽에는 최소 3개의 점이 필요해요.',true);return}record();pts.splice(pointIndex,1);pointIndex=-1}
else if(kind==='add-point'){record();const i=pointIndex>=0?pointIndex:pts.length-1;const a=pts[i],b=pts[(i+1)%pts.length];pts.splice(i+1,0,[(a[0]+b[0])/2,(a[1]+b[1])/2,true]);pointIndex=i+1}
else if(kind==='toggle-point'){if(pointIndex<0){notify('먼저 점을 선택하세요.');return}record();pts[pointIndex][2]=!pts[pointIndex][2]}
else if(kind==='left'||kind==='right'){record();pts.forEach(p=>p[0]+=kind==='left'?-12:12)}
persistGlyph()}
function resetGlyph(){if(!project.overrides[editorChar]){notify('이미 원본 글자예요.');return}if(!confirm(editorChar+' 글자의 개별 수정 내용을 초기화할까요?'))return;record();delete project.overrides[editorChar];contours=clone(originContours);glyphContour=0;pointIndex=-1;changed();drawGlyph()}
function setup(){initProjects();$('specimen').value=entry().specimen||DEFAULT_TEXT;renderProjectList();renderTemplates();updateAll();loadSourceFont(project.font);
$('open-menu').onclick=()=>setMenu(true);$('close-menu').onclick=()=>setMenu(false);$('backdrop').onclick=()=>setMenu(false);$('new-project').onclick=newProject;
$('tab-compose').onclick=()=>selectScreen('compose');$('tab-glyph').onclick=()=>selectScreen('glyph');$('tab-export').onclick=()=>selectScreen('export');$('go-glyph').onclick=()=>selectScreen('glyph');$('export-top').onclick=()=>selectScreen('export');
$('help-button').onclick=()=>$('help-dialog').showModal();$('help-close').onclick=()=>$('help-dialog').close();
$('specimen').addEventListener('input',()=>{entry().specimen=$('specimen').value;scheduleSave();if(screen==='glyph')updateGlyphQuicklist()});
for(const id of ['width','slant','tracking']){const input=$(id);input.addEventListener('pointerdown',record);input.addEventListener('input',()=>{project[id]=+input.value;updateAll();dropAccurate();applyPreview()});input.addEventListener('change',()=>{project[id]=+input.value;changed();notify('전체 글꼴의 비율을 바꿨어요.')})}
$('reset-settings').onclick=()=>{record();project.width=100;project.slant=0;project.tracking=0;changed()};
document.querySelectorAll('[data-preset]').forEach(btn=>btn.onclick=()=>{record();const p={neutral:[100,0,0],soft:[107,0,60],sharp:[92,0,-15]}[btn.dataset.preset];[project.width,project.slant,project.tracking]=p;changed()});
document.querySelectorAll('[data-sample]').forEach(btn=>btn.onclick=()=>{const key=btn.dataset.sample;$('specimen').value=SAMPLE[key];entry().specimen=SAMPLE[key];scheduleSave();document.querySelectorAll('[data-sample]').forEach(b=>b.classList.toggle('on',b===btn))});
$('precise-preview').onclick=()=>fontOutput('woff2',true);$('render-accurate').onclick=()=>fontOutput('woff2',true);$('download-ttf').onclick=()=>fontOutput('ttf');$('download-woff2').onclick=()=>fontOutput('woff2');
$('font-name').addEventListener('input',ev=>{project.name=ev.target.value;$('top-name').textContent=project.name;scheduleSave();renderProjectList()});
$('save-backup').onclick=exportJSON;$('backup-from-export').onclick=exportJSON;$('load-backup').onchange=ev=>importJSON(ev.target);
$('glyph-input').oninput=ev=>{const chars=[...ev.target.value];const ch=chars.length?chars.at(-1):'';if(ch)loadGlyph(ch)};
document.querySelectorAll('[data-tool]').forEach(btn=>btn.onclick=()=>glyphTool(btn.dataset.tool));
$('glyph-canvas').addEventListener('pointerdown',canvasDown);$('glyph-canvas').addEventListener('pointermove',svgMove);
 $('glyph-canvas').addEventListener('pointerup',svgUp);
 $('glyph-canvas').addEventListener('pointercancel',ev=>{if(paintStroke?.pointerId===ev.pointerId){cancelPainting();return}svgUp(ev)});
 $('glyph-canvas').addEventListener('dblclick',ev=>{if(tool==='polygon'&&penPoints.length>=3)finishPen()});
 $('stroke-size').oninput=ev=>$('stroke-value').textContent=ev.target.value;
 $('zoom-out').onclick=()=>changeZoom(-25);$('zoom-in').onclick=()=>changeZoom(25);$('zoom-fit').onclick=()=>{zoom=100;centerX=500;centerY=520;updateZoom()};updateZoom();
$('editor-undo').onclick=undo;$('editor-redo').onclick=redoAction;$('glyph-reset').onclick=resetGlyph;
$('blank-glyph').onclick=blankGlyph;
 $('cancel-pen').onclick=()=>{cancelPainting();notify('펜 입력을 취소했어요.')};
 for(const [id,action] of [['contour-duplicate','duplicate'],['contour-flip-h','flip-h'],['contour-flip-v','flip-v'],['contour-rotate-left','rotate-left'],['contour-rotate-right','rotate-right'],['contour-grow','grow'],['contour-shrink','shrink']])$(id).onclick=()=>transformContour(action);
 $('point-add').onclick=()=>glyphAction('add-point');$('point-delete').onclick=()=>glyphAction('delete-point');$('point-type').onclick=()=>glyphAction('toggle-point');$('contour-delete').onclick=()=>glyphAction('delete-contour');$('contour-left').onclick=()=>glyphAction('left');$('contour-right').onclick=()=>glyphAction('right');$('check-glyph').onclick=()=>{selectScreen('compose');$('specimen').focus();notify('글자를 수정했어요. 정확한 결과는 「실제 파일로 확인」을 눌러보세요.')};
$('glyph-canvas').addEventListener('keydown',ev=>{
  if((ev.ctrlKey||ev.metaKey)&&ev.key.toLowerCase()==='z'){ev.preventDefault();ev.shiftKey?redoAction():undo()}
  else if(ev.key==='Enter'&&tool==='polygon'){ev.preventDefault();finishPen()}
  else if(ev.key==='Escape'){cancelPainting();glyphTool('select')}
  else if(ev.key==='Backspace'&&pointIndex>=0){ev.preventDefault();glyphAction('delete-point')}
  else if(!ev.ctrlKey&&!ev.metaKey){const key={b:'brush',e:'eraser',p:'polygon',v:'select',m:'move',h:'pan'}[ev.key.toLowerCase()];if(key){ev.preventDefault();glyphTool(key)}}
 });
selectScreen('compose');}
if(document.readyState==='loading')document.addEventListener('DOMContentLoaded',setup);else setup();
})();
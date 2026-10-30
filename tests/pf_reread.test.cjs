// 브라우저 없이 원문 재사용·공개 범위·정확한 값 매칭을 확인.
const fs=require('node:fs'),vm=require('node:vm'),assert=require('node:assert/strict');
const html=fs.readFileSync(new URL('../src/app.html',`file://${__filename}`),'utf8');
const cut=(a,b)=>html.slice(html.indexOf(a),html.indexOf(b,html.indexOf(a)));
const code=cut('const PF_TYPES=','const pfPresets=')+cut('function pfGroupKey','const pfSearchBase=')+cut('function pfLeadIndex','function pfReread(');
const context=vm.createContext({uid:()=> 'generated',records:{posts:[]},postVisible:p=>p.visibility==='public',byDate:(a,b)=>b.date.localeCompare(a.date),pfNorm:s=>String(s).toLowerCase().replace(/\s+/g,'')});
vm.runInContext(code,context);
const group={id:'one',schemaId:'reading',name:'독서 기록',fields:[{id:'a',key:'book',name:'책 이름',type:'text',value:'가상 도서',options:[]}]};
const make=(id,visibility,status='published',g=group)=>({id,visibility,status,date:'2026-10-01',body:'자유롭게 쓴 원래 이야기',functions:[g]});
context.records.posts=[make('public','public'),make('private','private'),make('draft','public','draft'),make('different','public','published',{...group,fields:[{...group.fields[0],value:'다른 책'}]})];
context.g=group;const before=JSON.stringify(context.records);
assert.deepEqual(Array.from(vm.runInContext('pfRelatedPosts(g,g.fields[0])',context),p=>p.id),['public']);
assert.equal(JSON.stringify(context.records),before);
assert.deepEqual(Array.from(vm.runInContext('pfRelatedPosts(g,null)',context),p=>p.id),['public','different']);
vm.runInContext('blank=pfBlank(g)',context);assert.equal(context.blank.fields[0].value,'');assert.equal(context.blank.schemaId,'reading');assert.equal(context.blank.fields[0].key,'book');
assert.equal(vm.runInContext("pfMatchValue({type:'number',value:''},'eq','0')",context),false);
assert.equal(vm.runInContext("pfMatchValue({type:'number',value:'0'},'eq','0')",context),true);
assert.equal(vm.runInContext("pfLeadIndex({fields:[{type:'date'},{type:'number'}]})",context),1);
console.log('PASS: exact matching, privacy, drafts, original preservation, reusable structure, zero/blank, first input');

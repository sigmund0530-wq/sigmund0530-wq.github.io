(function(){
const L=()=>{try{return JSON.parse(localStorage.getItem("mockdb"))||null}catch(e){return null}};
let db=L()||{users:[],tables:{profiles:[],private_docs:[],categories:[],posts:[],rooms:[],media:[],feedback:[]},files:{},invites:{"MUGADANG-BETA":0}};
const save=()=>localStorage.setItem("mockdb",JSON.stringify(db));window.__mock={get db(){return db},calls:[],fail:0};
const PK={profiles:"id",private_docs:"owner",rooms:"owner"};const pk=t=>PK[t]||"id";
const sess=()=>{try{return JSON.parse(localStorage.getItem("mocksess"))}catch(e){return null}};
const uidNow=()=>(sess()||{}).user&&sess().user.id;
const wait=v=>new Promise(r=>setTimeout(()=>r(v),15));
const E=m=>({data:null,error:{message:m}});
class Q{constructor(t){this.t=t;this.f=[];this.op="select"}
  select(){if(this.op==="select")this.op="select";return this}eq(k,v){this.f.push(r=>r[k]==v);return this}in(k,vs){this.f.push(r=>vs.includes(r[k]));return this}
  maybeSingle(){this.one=true;return this}upsert(rows){this.op="upsert";this.rows=[].concat(rows);return this}update(o){this.op="update";this.obj=o;return this}
  delete(){this.op="delete";return this}insert(o){this.op="insert";this.rows=[].concat(o);return this}
  then(res,rej){return wait(this.run()).then(res,rej)}
  run(){const u=uidNow(),T=db.tables[this.t];window.__mock.calls.push(this.t+":"+this.op);
    if(window.__mock.fail>0&&this.op!=="select"){window.__mock.fail--;return E("Failed to fetch")}
    if(!u)return E("JWT required");const own=r=>(r.owner||r.id)===u;
    if(this.op==="select"){let rs=T.filter(r=>this.f.every(f=>f(r)));rs=rs.filter(own);rs=JSON.parse(JSON.stringify(rs));return {data:this.one?(rs[0]||null):rs,error:null}}
    if(this.op==="upsert"||this.op==="insert"){for(const r of this.rows){if(this.t==="feedback"){r.owner=r.owner||u}if(!own(r))return E("new row violates row-level security policy");
      const i=T.findIndex(x=>x[pk(this.t)]===r[pk(this.t)]);if(i>=0){if(!own(T[i]))return E("rls");if(this.op==="insert")return E("duplicate");T[i]=Object.assign({},T[i],JSON.parse(JSON.stringify(r)))}else T.push(JSON.parse(JSON.stringify(r)))}save();return {data:null,error:null}}
    if(this.op==="update"){T.filter(r=>this.f.every(f=>f(r))&&own(r)).forEach(r=>Object.assign(r,JSON.parse(JSON.stringify(this.obj))));save();return {data:null,error:null}}
    if(this.op==="delete"){db.tables[this.t]=T.filter(r=>!(this.f.every(f=>f(r))&&own(r)));save();return {data:null,error:null}}}}
const toData=b=>new Promise(r=>{const f=new FileReader();f.onload=()=>r(f.result);f.readAsDataURL(b)});
window.supabase={createClient(url,key){return {
  auth:{async getSession(){await wait();return {data:{session:sess()},error:null}},
    async signUp({email,password}){await wait();if(db.users.some(u=>u.email===email))return E("User already registered");const user={id:"u-"+Math.random().toString(36).slice(2,10)+"-0000-0000-0000-000000000000",email,password};db.users.push(user);save();const s={user:{id:user.id,email}};localStorage.setItem("mocksess",JSON.stringify(s));return {data:{user:s.user,session:s},error:null}},
    async signInWithPassword({email,password}){await wait();const u=db.users.find(u=>u.email===email&&u.password===password);if(!u)return E("Invalid login credentials");const s={user:{id:u.id,email}};localStorage.setItem("mocksess",JSON.stringify(s));return {data:{user:s.user,session:s},error:null}},
    async signOut(){localStorage.removeItem("mocksess");return {error:null}},async resetPasswordForEmail(){return {data:{},error:null}}},
  async rpc(fn,a){await wait();window.__mock.calls.push("rpc:"+fn);const u=uidNow();
    if(fn==="handle_available")return {data:!db.tables.profiles.some(p=>p.handle===a.p_handle),error:null};
    if(fn==="invite_ok")return {data:(a.p_code||"").trim().toUpperCase() in db.invites,error:null};
    if(fn==="create_profile"){if(!u)return E("not_signed_in");if(db.tables.profiles.some(p=>p.id===u))return E("already_exists");if(!((a.p_code||"").trim().toUpperCase() in db.invites))return E("invite_invalid");
      if(db.tables.profiles.some(p=>p.handle===a.p_handle))return E("handle_unavailable");
      db.tables.profiles.push({id:u,handle:a.p_handle,display_name:a.p_name||"",status:"",space_name:null,photo_id:null,look:{},data:{}});db.tables.private_docs.push({owner:u,data:{}});db.tables.rooms.push({owner:u,visibility:"public",layout:{},media_ids:[]});db.invites["MUGADANG-BETA"]++;save();return {data:null,error:null}}
    return E("no fn")},
  from:t=>new Q(t),
  storage:{from:b=>({async upload(path,blob){const u=uidNow();if(path.split("/")[0]!==u)return E("rls");if(window.__mock.fail>0){window.__mock.fail--;return E("Failed to fetch")}db.files[path]=await toData(blob);save();window.__mock.calls.push("upload");return {data:{path},error:null}},
    async createSignedUrl(p){return {data:{signedUrl:db.files[p]||null},error:null}},async createSignedUrls(ps){return {data:ps.map(p=>({path:p,signedUrl:db.files[p]||null})),error:null}},
    async remove(ps){ps.forEach(p=>delete db.files[p]);save();window.__mock.calls.push("remove");return {data:null,error:null}}})}}}};
})();

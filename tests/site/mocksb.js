(function(){
const L=()=>{try{return JSON.parse(localStorage.getItem("mockdb"))||null}catch(e){return null}};
let db=L()||{users:[],tables:{profiles:[],private_docs:[],categories:[],posts:[],rooms:[],media:[],feedback:[]},files:{},invites:{"MUGADANG-BETA":0}};
["follows","close_friends","notes","note_blocks"].forEach(k=>{if(!db.tables[k])db.tables[k]=[]});
/* 행 단위 보안 흉내(2026-11-02): server/schema.sql 의 can_read_* · note_ok 와 같은 규칙 */
const OWNF={follows:"follower",notes:"sender",note_blocks:"owner",close_friends:"owner"};
const isF=(v,o)=>db.tables.follows.some(f=>f.follower===v&&f.followee===o),isC=(o,v)=>db.tables.close_friends.some(c=>c.owner===o&&c.friend===v);
const canPost=(p,u)=>p.owner===u||(p.status==="published"&&(p.visibility==="public"||(p.visibility==="followers"&&isF(u,p.owner))||(p.visibility==="close"&&isC(p.owner,u))||(p.visibility==="custom"&&(p.allow||[]).includes(u))));
const canRoom=(r,u)=>r.owner===u||r.visibility==="public"||(r.visibility==="followers"&&isF(u,r.owner));
const canMedia=(m,u)=>m.owner===u||db.tables.profiles.some(pr=>pr.id===m.owner&&(pr.photo_id===m.id||(pr.look||{}).coverId===m.id))||db.tables.posts.some(p=>p.owner===m.owner&&(p.media_ids||[]).includes(m.id)&&canPost(p,u))||db.tables.rooms.some(r=>r.owner===m.owner&&(r.media_ids||[]).includes(m.id)&&canRoom(r,u))||db.tables.notes.some(n=>n.media_id===m.id&&n.sender===m.owner&&n.recipient===u&&!n.recipient_hidden);
const READ={profiles:()=>true,posts:canPost,rooms:canRoom,media:canMedia,categories:(c,u)=>c.owner===u||c.visibility!=="private",follows:(f,u)=>f.follower===u||f.followee===u,notes:(n,u)=>(n.sender===u&&!n.sender_hidden)||(n.recipient===u&&!n.recipient_hidden)};
const noteOk=(to,u)=>{const P=db.tables.profiles.find(x=>x.id===to);if(!P||to===u)return false;if(db.tables.note_blocks.some(b=>b.owner===to&&b.blocked===u))return false;
  const nf=P.note_from||"all";if(nf==="none"||(nf==="close"&&!isC(to,u))||(nf==="followers"&&!isF(to,u)))return false;
  return db.tables.notes.some(n=>n.sender===to&&n.recipient===u)||isF(to,u)||isC(to,u)||!db.tables.notes.some(n=>n.sender===u&&n.recipient===to)};
const save=()=>localStorage.setItem("mockdb",JSON.stringify(db));window.__mock={get db(){return db},calls:[],fail:0};
const PK={profiles:"id",private_docs:"owner",rooms:"owner"};const pk=t=>PK[t]||"id";
const sess=()=>{try{return JSON.parse(localStorage.getItem("mocksess"))}catch(e){return null}};
const uidNow=()=>(sess()||{}).user&&sess().user.id;
const wait=v=>new Promise(r=>setTimeout(()=>r(v),15));
const E=m=>({data:null,error:{message:m}});
class Q{constructor(t){this.t=t;this.f=[];this.op="select"}
  select(){if(this.op==="select")this.op="select";return this}eq(k,v){this.f.push(r=>r[k]==v);return this}in(k,vs){this.f.push(r=>vs.includes(r[k]));return this}
  neq(k,v){this.f.push(r=>r[k]!=v);return this}order(k,o){this.ord=[k,!o||o.ascending!==false];return this}limit(n){this.lim=n;return this}
  or(str){const parts=str.split(",").map(x=>x.split("."));this.f.push(r=>parts.some(([k,op,...v])=>{const pat=v.join(".");if(op==="ilike"){const re=new RegExp("^"+pat.replace(/[.*+?^${}()|[\]\\]/g,"\\$&").replace(/%/g,".*")+"$","i");return re.test(String(r[k]||""))}if(op==="eq")return String(r[k])===pat;return false}));return this}
  maybeSingle(){this.one=true;return this}upsert(rows){this.op="upsert";this.rows=[].concat(rows);return this}update(o){this.op="update";this.obj=o;return this}
  delete(){this.op="delete";return this}insert(o){this.op="insert";this.rows=[].concat(o);return this}
  then(res,rej){return wait(this.run()).then(res,rej)}
  run(){const u=uidNow(),T=db.tables[this.t];window.__mock.calls.push(this.t+":"+this.op);
    if(window.__mock.fail>0&&this.op!=="select"){window.__mock.fail--;return E("Failed to fetch")}
    if(!u)return E("JWT required");const of=OWNF[this.t];const own=r=>(of?r[of]:(r.owner||r.id))===u;
    if(this.op==="select"){let rs=T.filter(r=>this.f.every(f=>f(r)));rs=rs.filter(r=>READ[this.t]?READ[this.t](r,u):own(r));
      if(this.ord){const [k,asc]=this.ord;rs.sort((a,b)=>(String(a[k]||"")<String(b[k]||"")?-1:String(a[k]||"")>String(b[k]||"")?1:0)*(asc?1:-1))}if(this.lim)rs=rs.slice(0,this.lim);
      rs=JSON.parse(JSON.stringify(rs));return {data:this.one?(rs[0]||null):rs,error:null}}
    if(this.op==="upsert"||this.op==="insert"){for(const r of this.rows){if(this.t==="feedback"){r.owner=r.owner||u}
      if(this.t==="notes"){r.sender=r.sender||u;r.id=r.id||("n-"+Math.random().toString(36).slice(2,10));r.created_at=r.created_at||new Date(Date.now()+db.tables.notes.length).toISOString();r.ctx=r.ctx||{};r.sender_hidden=false;r.recipient_hidden=false;
        if(r.sender!==u||!noteOk(r.recipient,u)||(r.media_id&&!db.tables.media.some(m=>m.id===r.media_id&&m.owner===u)))return E("new row violates row-level security policy for table \"notes\"")}
      if(this.t==="follows"&&(r.follower!==u||r.followee===u))return E("new row violates row-level security policy");
      if(this.t==="follows"||this.t==="note_blocks"||this.t==="close_friends"){const k2=this.t==="follows"?["follower","followee"]:this.t==="note_blocks"?["owner","blocked"]:["owner","friend"];if(T.some(x=>x[k2[0]]===r[k2[0]]&&x[k2[1]]===r[k2[1]])){if(this.op==="insert")return E("duplicate key value");continue}}
      if(!own(r))return E("new row violates row-level security policy");
      const i=T.findIndex(x=>x[pk(this.t)]===r[pk(this.t)]);if(i>=0){if(!own(T[i]))return E("rls");if(this.op==="insert")return E("duplicate");T[i]=Object.assign({},T[i],JSON.parse(JSON.stringify(r)))}else T.push(JSON.parse(JSON.stringify(r)))}save();return {data:null,error:null}}
    if(this.op==="update"){T.filter(r=>this.f.every(f=>f(r))&&own(r)).forEach(r=>Object.assign(r,JSON.parse(JSON.stringify(this.obj))));save();return {data:null,error:null}}
    if(this.op==="delete"){db.tables[this.t]=T.filter(r=>!(this.f.every(f=>f(r))&&own(r)));save();return {data:null,error:null}}}}
const toData=b=>new Promise(r=>{const f=new FileReader();f.onload=()=>r(f.result);f.readAsDataURL(b)});
window.supabase={createClient(url,key){return {
  auth:{async getSession(){await wait();const s=sess();return {data:{session:s?Object.assign({access_token:"mock-token"},s):null},error:null}},
    async signUp({email,password}){await wait();if(db.users.some(u=>u.email===email))return E("User already registered");const user={id:"u-"+Math.random().toString(36).slice(2,10)+"-0000-0000-0000-000000000000",email,password};db.users.push(user);save();const s={user:{id:user.id,email}};localStorage.setItem("mocksess",JSON.stringify(s));return {data:{user:s.user,session:s},error:null}},
    async signInWithPassword({email,password}){await wait();const u=db.users.find(u=>u.email===email&&u.password===password);if(!u)return E("Invalid login credentials");const s={user:{id:u.id,email}};localStorage.setItem("mocksess",JSON.stringify(s));return {data:{user:s.user,session:s},error:null}},
    async signOut(){localStorage.removeItem("mocksess");return {error:null}},async updateUser(o){await wait();const u=db.users.find(x=>x.id===uidNow());if(!u)return E("JWT required");if(o.password)u.password=o.password;if(o.email)u.pendingEmail=o.email;save();return {data:{user:{id:u.id,email:u.email}},error:null}},async resetPasswordForEmail(){return {data:{},error:null}}},
  async rpc(fn,a){await wait();window.__mock.calls.push("rpc:"+fn);const u=uidNow();
    if(fn==="handle_available")return {data:!db.tables.profiles.some(p=>p.handle===a.p_handle),error:null};
    if(fn==="invite_ok")return {data:(a.p_code||"").trim().toUpperCase() in db.invites,error:null};
    if(fn==="create_profile"){if(!u)return E("not_signed_in");if(db.tables.profiles.some(p=>p.id===u))return E("already_exists");if(!((a.p_code||"").trim().toUpperCase() in db.invites))return E("invite_invalid");
      if(db.tables.profiles.some(p=>p.handle===a.p_handle))return E("handle_unavailable");
      db.tables.profiles.push({id:u,handle:a.p_handle,display_name:a.p_name||"",status:"",space_name:null,photo_id:null,look:{},data:{}});db.tables.private_docs.push({owner:u,data:{}});db.tables.rooms.push({owner:u,visibility:"public",layout:{},media_ids:[]});db.invites["MUGADANG-BETA"]++;save();return {data:null,error:null}}
    if(fn==="change_handle"){const p=db.tables.profiles.find(x=>x.id===u);if(!p)return E("no_profile");if(p.handle===a.p_handle)return {data:"same",error:null};if(p.handle_changed_at)return E("handle_changed_once");
      if(db.tables.profiles.some(x=>x.handle===a.p_handle)||(db.released||{})[a.p_handle])return E("handle_unavailable");db.released=db.released||{};db.released[p.handle]=1;p.handle=a.p_handle;p.handle_changed_at=new Date().toISOString();save();return {data:"ok",error:null}}
    if(fn==="hide_note"){db.tables.notes.forEach(n=>{if(n.id===a.p_id){if(n.sender===u)n.sender_hidden=true;if(n.recipient===u)n.recipient_hidden=true}});save();return {data:"ok",error:null}}
    if(fn==="delete_my_account"){if(!u)return E("not_signed_in");const p=db.tables.profiles.find(x=>x.id===u);db.released=db.released||{};if(p)db.released[p.handle]=1;
      for(const t of Object.keys(db.tables))db.tables[t]=db.tables[t].filter(r=>![r.owner,r.id,r.follower,r.followee,r.sender,r.recipient,r.blocked,r.friend].includes(u));db.users=db.users.filter(x=>x.id!==u);save();return {data:"ok",error:null}}
    return E("no fn")},
  from:t=>new Q(t),
  storage:{from:b=>({async upload(path,blob){const u=uidNow();if(path.split("/")[0]!==u)return E("rls");if(window.__mock.fail>0){window.__mock.fail--;return E("Failed to fetch")}db.files[path]=await toData(blob);save();window.__mock.calls.push("upload");return {data:{path},error:null}},
    async createSignedUrl(p){return {data:{signedUrl:db.files[p]||null},error:null}},async createSignedUrls(ps){return {data:ps.map(p=>({path:p,signedUrl:db.files[p]||null})),error:null}},
    async remove(ps){ps.forEach(p=>delete db.files[p]);save();window.__mock.calls.push("remove");return {data:null,error:null}}})}}}};
})();

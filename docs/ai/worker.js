// 무가당 '알아서 모으기' — Cloudflare Worker (Workers AI)
// 글을 받아 책·물건·장소·음식·음악·영화·드라마를 찾아 돌려줘요.
// Cloudflare는 Workers AI로 처리한 내용을 학습에 쓰지 않고, 처리 후 보관하지 않아요(공식 문서).
// 설정: 이 Worker의 Settings → Bindings → Workers AI, 변수 이름 AI
// 위젯 인터넷 중계(2026-11-02): POST /relay — 아래 relay() 설명
// 짤 검색(2026-11-02): POST /zzal/search {q, src:"gif"|"kr", page} → {items:[{id,thumb,full,w,h,title}]}
//   POST /zzal/img {u} → 그림 바이트(무가당 서버가 대신 받아 줘서, 짤 회사는 누가 찾았는지 몰라요)
//   비밀 값(Settings → Variables and Secrets, 주인이 직접 넣음): KLIPY_KEY, NAVER_ID·NAVER_SECRET(네이버 클라우드 API HUB 키). 없으면 {items:[], need:"key"}
const MODEL = "@cf/qwen/qwen3-30b-a3b-fp8";
const ALLOW = ["https://sigmund0530-wq.github.io"];
// 잠금: 무가당에 로그인한 사람만. 앱이 보낸 로그인 토큰을 Supabase에 물어 확인해요(공개 키만 씀, 비밀 키 없음).
const SB_URL = "https://idahhgtpawkrdikuvfbv.supabase.co";
const SB_PUBLISHABLE = "sb_publishable_lRONSNzx0aDW360_AxJwBA_NgyvxkX0";
// 앱·서비스·교통수단은 모아 보기 대상이 아니라서 걸러요.
const SKIP = new Set(["당근","당근마켓","넷플릭스","유튜브","카카오톡","인스타","인스타그램","배민","쿠팡","KTX","SRT","지하철","버스","택시"]);
const PROMPT = `다음은 한국어 개인 블로그 글이야. 나중에 '읽은 책', '내 물건', '다녀온 곳', '먹은 것', '들은 음악', '본 것'으로 모아 볼 대상을 빠짐없이 찾아.
종류(kind)는 아래 여섯 개 중 하나만 써:
- 책: 책 제목만 (작가 이름은 빼)
- 물건: 사거나 팔거나 잃어버리거나 선물받은 물건. 브랜드만 따로 뽑지 말고 물건 이름으로
- 장소: 간 곳. 나라·도시·동네(제주도, 부산, 망원동)도, 그 안의 가게·공원·바다도 각각 따로 뽑아
- 음식: 먹거나 마시거나 산 음식
- 음악: 가수, 곡 제목, 앨범 (가수 이름이 나오면 꼭 넣어)
- 영화·드라마: 영화, 드라마, 예능 제목
넣지 마: 사람(가족·친구·작가), 반려동물, 행사(결혼식·출장), 시간, 날씨, 가격, 앱·서비스(넷플릭스·당근), 교통수단(KTX).
word는 글에 나온 그대로의 가장 짧고 정확한 이름(조사·따옴표 빼고). 없으면 빈 목록.
예) "을지로 '커피한약방'에서 라떼를 마셨다" → {"items":[{"word":"을지로","kind":"장소"},{"word":"커피한약방","kind":"장소"},{"word":"라떼","kind":"음식"}]}
예) "중고로 아이패드를 30만 원에 샀다. 요즘 뉴진스만 듣는 중" → {"items":[{"word":"아이패드","kind":"물건"},{"word":"뉴진스","kind":"음악"}]}
JSON으로만 답해: {"items":[{"word":"","kind":""}]}

글: `;
const KINDS = { "책":"책","물건":"물건","장소":"장소","음식":"음식","음악":"음악","영화·드라마":"영화·드라마","영화/드라마":"영화·드라마","영화":"영화·드라마","드라마":"영화·드라마" };
const norm = w => String(w||"").trim().replace(/^[『「'"‘“《\s]+|[』」'"’”》\s]+$/g,"");

function cors(origin){
  const ok = ALLOW.includes(origin);
  return { "Access-Control-Allow-Origin": ok ? origin : ALLOW[0], "Access-Control-Allow-Methods":"POST, OPTIONS", "Access-Control-Allow-Headers":"Content-Type, Authorization", "Access-Control-Max-Age":"86400", "Vary":"Origin" };
}
function textOf(r){
  if (!r) return "";
  if (typeof r.response === "string") return r.response;
  if (r.response && typeof r.response === "object") return JSON.stringify(r.response);
  const c = r.choices && r.choices[0]; return (c && c.message && c.message.content) || "";
}
function clean(items, text){
  let g = [];
  for (const x of Array.isArray(items) ? items : []) {
    const word = norm(x && x.word), kind = KINDS[String(x && x.kind || "").trim()];
    if (!word || !kind || SKIP.has(word) || word.length < 2 || !text.includes(word) || /\d+\s*(만|천)?\s*원/.test(word)) continue;
    if (!g.some(y => y.word === word)) g.push({ word, kind });
  }
  return g.filter(a => !g.some(b => b.word !== a.word && b.word.includes(a.word))); // 겹치면 긴 이름만
}

// 로그인 확인은 같은 토큰이면 5분 동안 다시 묻지 않아요(짤 썸네일을 여러 장 받을 때 Supabase를 덜 부름)
const seen = new Map();
async function loggedIn(auth){
  if (!/^Bearer\s+\S+/.test(auth)) return false;
  const t = seen.get(auth); if (t && t > Date.now()) return true;
  const who = await fetch(SB_URL + "/auth/v1/user", { headers: { Authorization: auth, apikey: SB_PUBLISHABLE } });
  if (!who.ok) return false;
  if (seen.size > 500) seen.clear(); seen.set(auth, Date.now() + 5 * 60 * 1000); return true;
}
const strip = s => String(s || "").replace(/<[^>]*>/g, "").replace(/&quot;/g, '"').replace(/&amp;/g, "&").replace(/&lt;|&gt;/g, "").slice(0, 80);
async function zzalSearch(body, env){
  const q = String(body && body.q || "").trim().slice(0, 60), src = body && body.src === "kr" ? "kr" : "gif", page = Math.max(1, Math.min(20, +body.page || 1));
  if (src === "gif") {
    if (!env.KLIPY_KEY) return { items: [], need: "key" };
    const path = q ? "gifs/search?q=" + encodeURIComponent(q) + "&" : "gifs/trending?";
    const r = await fetch(`https://api.klipy.com/api/v1/${env.KLIPY_KEY}/${path}per_page=24&page=${page}&locale=ko_KR&rating=pg-13`);
    if (!r.ok) return { items: [], error: r.status };
    const j = await r.json(); const list = Array.isArray(j.data) ? j.data : (j.data && j.data.data) || [];
    const pick = (f, ks, ts) => { for (const k of ks) for (const t of ts) { const v = f && f[k] && f[k][t]; if (v && v.url) return v; } return null; };
    return { items: list.map(x => { const f = x.file || x.files || {}; const th = pick(f, ["xs", "sm"], ["gif", "webp", "jpg"]), full = pick(f, ["sm", "md", "hd"], ["gif"]);
      return full && th ? { id: "k" + x.id, thumb: th.url, full: full.url, w: full.width || 0, h: full.height || 0, title: strip(x.title) } : null; }).filter(Boolean), more: !!(j.data && j.data.has_next) };
  }
  if (!env.NAVER_ID || !env.NAVER_SECRET) return { items: [], need: "key" };
  if (!q) return { items: [] };
  // 네이버 검색 API는 2026-07-31부터 네이버 클라우드 API HUB로 옮겨 감(개발자센터 새 신청 막힘). 키는 API HUB 콘솔에서 받은 것
  const r = await fetch(`https://naverapihub.apigw.ntruss.com/search/v1/image?query=${encodeURIComponent(q + " 짤")}&display=30&start=${(page - 1) * 30 + 1}&filter=all`, { headers: { "X-NCP-APIGW-API-KEY-ID": env.NAVER_ID, "X-NCP-APIGW-API-KEY": env.NAVER_SECRET } });
  if (!r.ok) return { items: [], error: r.status };
  const j = await r.json();
  return { items: (j.items || []).filter(x => /^https?:\/\//.test(x.link || "")).map((x, i) => ({ id: "n" + page + "-" + i, thumb: x.thumbnail || x.link, full: x.link, w: +x.sizewidth || 0, h: +x.sizeheight || 0, title: strip(x.title) })), more: (j.total || 0) > page * 30 };
}
async function zzalImg(body, h){
  let u; try { u = new URL(String(body && body.u || "")); } catch { return new Response("bad url", { status: 400, headers: h }); }
  if (!/^https?:$/.test(u.protocol) || /^(localhost|127\.|10\.|192\.168\.|169\.254\.)/.test(u.hostname)) return new Response("bad url", { status: 400, headers: h });
  const r = await fetch(u.toString(), { headers: { "User-Agent": "Mozilla/5.0", Referer: u.origin + "/" }, redirect: "follow", cf: { cacheTtl: 86400, cacheEverything: true } });
  const type = (r.headers.get("Content-Type") || "").split(";")[0];
  if (!r.ok || !/^image\//.test(type)) return new Response("not image", { status: 415, headers: h });
  const len = +(r.headers.get("Content-Length") || 0); if (len > 6 * 1024 * 1024) return new Response("too big", { status: 413, headers: h });
  const buf = await r.arrayBuffer(); if (buf.byteLength > 6 * 1024 * 1024) return new Response("too big", { status: 413, headers: h });
  return new Response(buf, { headers: { ...h, "Content-Type": type, "Cache-Control": "private, max-age=86400" } });
}

// 위젯 인터넷 중계(2026-11-02): POST /relay {u} → {status, type, body}
//   위젯이 무가당에 부탁하면 이 서버가 대신 가져옴(쿠키·로그인 정보 없이). 가져오기(GET)만, 1MB, 글자·JSON·그림(data: 주소로)만.
//   로그인한 사람만, 사람(토큰)마다 1분에 60번.
const relayLog = new Map();
const PRIVATE_HOST = /^(localhost|0\.|127\.|10\.|192\.168\.|169\.254\.|172\.(1[6-9]|2\d|3[01])\.|\[|::1)|\.(local|internal|localhost)$/i;
function b64(buf){ let s = ""; const a = new Uint8Array(buf); for (let i = 0; i < a.length; i += 0x8000) s += String.fromCharCode.apply(null, a.subarray(i, i + 0x8000)); return btoa(s); }
async function relay(body, auth, h){
  const t = Date.now(), L = (relayLog.get(auth) || []).filter(x => t - x < 60000);
  if (L.length >= 60) return Response.json({ error: "rate" }, { status: 429, headers: h });
  L.push(t); if (relayLog.size > 2000) relayLog.clear(); relayLog.set(auth, L);
  let u; try { u = new URL(String(body && body.u || "")); } catch { return Response.json({ error: "bad_url" }, { status: 400, headers: h }); }
  if (!/^https?:$/.test(u.protocol) || u.username || u.password || PRIVATE_HOST.test(u.hostname) || /workers\.dev$|supabase\.co$/i.test(u.hostname))
    return Response.json({ error: "bad_url" }, { status: 400, headers: h });
  let r; try { r = await fetch(u.toString(), { headers: { "User-Agent": "MugadangRelay/1 (+https://sigmund0530-wq.github.io)", Accept: "*/*" }, redirect: "follow" }); }
  catch { return Response.json({ error: "fetch" }, { status: 502, headers: h }); }
  const type = (r.headers.get("Content-Type") || "").split(";")[0].trim().toLowerCase();
  const isImg = /^image\/(png|jpeg|gif|webp|svg\+xml|avif)$/.test(type), isText = /^text\/|^application\/(json|xml|rss\+xml|atom\+xml|[\w.+-]+\+json)$/.test(type);
  if (!isImg && !isText) return Response.json({ error: "type" }, { status: 415, headers: h });
  if (+(r.headers.get("Content-Length") || 0) > 1048576) return Response.json({ error: "too_big" }, { status: 413, headers: h });
  const buf = await r.arrayBuffer(); if (buf.byteLength > 1048576) return Response.json({ error: "too_big" }, { status: 413, headers: h });
  const out = isImg ? `data:${type};base64,${b64(buf)}` : new TextDecoder().decode(buf);
  return Response.json({ status: r.status, type, body: out }, { headers: { ...h, "Cache-Control": "no-store" } });
}

export default {
  async fetch(req, env) {
    const h = cors(req.headers.get("Origin") || "");
    if (req.method === "OPTIONS") return new Response(null, { headers: h });
    if (req.method !== "POST") return new Response("POST only", { status: 405, headers: h });
    if (!(await loggedIn(req.headers.get("Authorization") || ""))) return new Response("login required", { status: 401, headers: h });
    let body; try { body = await req.json(); } catch { return new Response("bad json", { status: 400, headers: h }); }
    const path = new URL(req.url).pathname;
    if (path === "/zzal/search") return Response.json(await zzalSearch(body, env), { headers: h });
    if (path === "/zzal/img") return zzalImg(body, h);
    if (path === "/relay") return relay(body, req.headers.get("Authorization") || "", h);
    const text = String(body && body.text || "").slice(0, 4000);
    if (!text.trim()) return Response.json({ items: [] }, { headers: h });
    const r = await env.AI.run(MODEL, { messages: [{ role: "user", content: PROMPT + text + " /no_think" }], max_tokens: 400, temperature: 0 });
    const raw = textOf(r).replace(/<think>[\s\S]*?<\/think>/g, "");
    const m = raw.match(/\{[\s\S]*\}|\[[\s\S]*\]/);
    let items = [];
    try { const o = JSON.parse(m ? m[0] : "{}"); items = Array.isArray(o) ? o : (o.items || []); } catch {}
    return Response.json({ items: clean(items, text) }, { headers: h });
  }
};

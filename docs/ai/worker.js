// 무가당 '알아서 모으기' — Cloudflare Worker (Workers AI)
// 글을 받아 책·물건·장소·음식·음악·영화·드라마를 찾아 돌려줘요.
// Cloudflare는 Workers AI로 처리한 내용을 학습에 쓰지 않고, 처리 후 보관하지 않아요(공식 문서).
// 설정: 이 Worker의 Settings → Bindings → Workers AI, 변수 이름 AI
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
  return { "Access-Control-Allow-Origin": ok ? origin : ALLOW[0], "Access-Control-Allow-Methods":"POST, OPTIONS", "Access-Control-Allow-Headers":"Content-Type, Authorization", "Vary":"Origin" };
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

export default {
  async fetch(req, env) {
    const h = cors(req.headers.get("Origin") || "");
    if (req.method === "OPTIONS") return new Response(null, { headers: h });
    if (req.method !== "POST") return new Response("POST only", { status: 405, headers: h });
    const auth = req.headers.get("Authorization") || "";
    if (!/^Bearer\s+\S+/.test(auth)) return new Response("login required", { status: 401, headers: h });
    const who = await fetch(SB_URL + "/auth/v1/user", { headers: { Authorization: auth, apikey: SB_PUBLISHABLE } });
    if (!who.ok) return new Response("login required", { status: 401, headers: h });
    let body; try { body = await req.json(); } catch { return new Response("bad json", { status: 400, headers: h }); }
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

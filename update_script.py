content = open('D:/love-scorebook/index.html', encoding='utf-8').read()
start = content.index('<script>')
end = content.index('</script>') + len('</script>')
before = content[:start]
after = content[end:]

new_script = r"""
// ===== API CONFIG =====
const API = '';

async function api(method, path, body) {
  const opts = { method, headers: {'Content-Type':'application/json'} };
  if (body) opts.body = JSON.stringify(body);
  const r = await fetch((API||'') + path, opts);
  return r.json();
}

// ===== DATA =====
const CATS = {
  positive: [
    {id:'date',    name:'约会',      emoji:'🌹'},
    {id:'gift',   name:'送礼物',    emoji:'🎁'},
    {id:'chat',   name:'聊天/关心', emoji:'💬'},
    {id:'romantic',name:'惊喜/浪漫', emoji:'✨'},
    {id:'kiss',   name:'亲亲抱抱',  emoji:'😘'},
    {id:'home',   name:'回家见父母', emoji:'🏠'},
    {id:'help',   name:'帮忙做事',  emoji:'🤝'},
    {id:'patience',name:'包容理解',  emoji:'🫂'},
    {id:'other',  name:'其他甜蜜',  emoji:'💕'},
  ],
  negative: [
    {id:'fight',  name:'吵架',      emoji:'😤'},
    {id:'cold',   name:'冷暴力',    emoji:'🥶'},
    {id:'lie',    name:'说谎/欺骗', emoji:'🙈'},
    {id:'ignore', name:'忽视对方',  emoji:'😞'},
    {id:'late',   name:'迟到/爽约', emoji:'⏰'},
    {id:'selfish',name:'自私/任性', emoji:'😓'},
    {id:'other',  name:'其他矛盾',  emoji:'💔'},
  ]
};

const ACHIEVES = [
  {id:'first_date',  name:'初次约会',   desc:'记录第一次约会',     emoji:'🌸', fn: d => d.h.filter(h=>h.cat==='date').length >= 1},
  {id:'gift_5',      name:'礼物达人',   desc:'送出5份礼物',         emoji:'🎁', fn: d => d.h.filter(h=>h.cat==='gift').length >= 5},
  {id:'score_100',  name:'百分甜蜜',   desc:'甜蜜值达到100',       emoji:'💯', fn: d => d.stats.pos >= 100},
  {id:'score_500',  name:'五百甜蜜',   desc:'甜蜜值达到500',       emoji:'💖', fn: d => d.stats.pos >= 500},
  {id:'kiss_10',    name:'亲亲十连',   desc:'记录10次亲亲',       emoji:'😘', fn: d => d.h.filter(h=>h.cat==='kiss').length >= 10},
  {id:'romantic_3', name:'浪漫达人',   desc:'3次惊喜浪漫',         emoji:'✨', fn: d => d.h.filter(h=>h.cat==='romantic').length >= 3},
  {id:'forgive_5',  name:'包容之心',   desc:'记录5次包容理解',     emoji:'🫂', fn: d => d.h.filter(h=>h.cat==='patience').length >= 5},
  {id:'date_10',    name:'约会达人',   desc:'约会10次',             emoji:'💑', fn: d => d.h.filter(h=>h.cat==='date').length >= 10},
  {id:'chat_20',    name:'话痨情侣',   desc:'聊天关心记录20次',     emoji:'💬', fn: d => d.h.filter(h=>h.cat==='chat').length >= 20},
  {id:'first_gift', name:'第一份礼物', desc:'送出第一份礼物',       emoji:'🎀', fn: d => d.h.filter(h=>h.cat==='gift').length >= 1},
  {id:'no_fight_7', name:'甜蜜一周',   desc:'连续7天无吵架',       emoji:'😇', fn: d => checkStreak(d)},
  {id:'neg_zero',    name:'零矛盾周',   desc:'最近7天无矛盾',       emoji:'🕊️', fn: d => checkNoRecentNeg(d)},
];

// ===== STATE =====
let st = { mode:'positive', selCat:null, intensity:2, emoji:'🥰', entries:[], coupleName:'', unlocked:[], pos:0, neg:0 };

function checkStreak(d) {
  const now=Date.now(), weekAgo=now-7*86400000;
  return d.h.filter(h=>h.neg&&h.t>weekAgo).length===0;
}
function checkNoRecentNeg(d) {
  const now=Date.now(), weekAgo=now-7*86400000;
  return d.h.filter(h=>h.neg&&h.t>weekAgo).length===0;
}

// ===== INIT =====
async function init() {
  await loadFromServer();
  if (!st.coupleName) {
    document.getElementById('modal-overlay').classList.add('open');
  } else {
    document.getElementById('display-name').textContent = st.coupleName;
  }
  renderCats();
  updateScore();
  renderHistory();
  renderAchieve();
  renderStats();
  renderToday();
}

async function loadFromServer() {
  try {
    const data = await api('GET', '/api/data');
    st.entries = data.entries || [];
    st.coupleName = data.coupleName || '';
    st.unlocked = data.unlocked || [];
    recalc();
  } catch(e) {
    try {
      const s = localStorage.getItem('lsb-v1');
      if (s) { const d=JSON.parse(s); st.entries=d.entries||[]; st.coupleName=d.coupleName||''; st.unlocked=d.unlocked||[]; }
      recalc();
    } catch(e2) {}
  }
}

async function saveToServer() {
  try {
    await api('POST', '/api/data', {entries:st.entries, coupleName:st.coupleName, unlocked:st.unlocked});
  } catch(e) {
    localStorage.setItem('lsb-v1', JSON.stringify({entries:st.entries, coupleName:st.coupleName, unlocked:st.unlocked}));
  }
}

function recalc() {
  st.pos = st.entries.filter(e=>!e.neg).reduce((s,e)=>s+e.v,0);
  st.neg = st.entries.filter(e=>e.neg).reduce((s,e)=>s+e.v,0);
}

// ===== TABS =====
function switchTab(name) {
  document.querySelectorAll('.tbtn').forEach(b=>b.classList.remove('active'));
  document.getElementById('btn-'+name).classList.add('active');
  document.querySelectorAll('.tpanel').forEach(p=>p.classList.remove('active'));
  document.getElementById('panel-'+name).classList.add('active');
  if (name==='history') renderHistory();
  if (name==='achieve') renderAchieve();
  if (name==='stats') renderStats();
}

// ===== MODE =====
function setMode(m) {
  st.mode=m; st.selCat=null;
  document.getElementById('tab-pos').classList.toggle('active', m==='positive');
  document.getElementById('tab-neg').classList.toggle('active', m==='negative');
  renderCats();
}

// ===== CATS =====
function renderCats() {
  const cats = CATS[st.mode];
  const grid = document.getElementById('cat-grid');
  grid.innerHTML = cats.map(c =>
    '<button class="cbtn'+(st.selCat===c.id?' sel':'')+'" onclick="selCat(\''+c.id+'\')">'+
    '<span style="font-size:1.2em">'+c.emoji+'</span><br>'+c.name+'</button>'
  ).join('');
}
function selCat(id) { st.selCat=id; renderCats(); }

// ===== INTENSITY =====
function setIntensity(v) {
  st.intensity=v;
  document.querySelectorAll('.ibtn').forEach(b=>b.classList.toggle('sel', parseInt(b.dataset.v)===v));
}

// ===== EMOJI =====
function setEmoji(el) {
  st.emoji=el.dataset.e;
  document.querySelectorAll('.em').forEach(e=>e.classList.remove('sel'));
  el.classList.add('sel');
}

// ===== SUBMIT =====
async function submitEntry() {
  if (!st.selCat) { alert('请先选择一个类别哦～'); return; }
  const cat = CATS[st.mode].find(c=>c.id===st.selCat);
  const note = document.getElementById('note-input').value.trim();
  const entry = { id:Date.now(), cat:st.selCat, cname:cat.name, emoji:st.emoji, v:st.intensity, neg:st.mode==='negative', note, t:Date.now() };
  try { await api('POST', '/api/entry', entry); } catch(e) {}
  st.entries.unshift(entry);
  recalc();
  checkAchieve();
  saveToServer();
  updateScore();
  renderHistory();
  renderAchieve();
  renderStats();
  renderToday();
  document.getElementById('note-input').value = '';
  st.selCat=null; renderCats();
  triggerConfetti();
}

// ===== SCORE =====
function updateScore() {
  const total = st.pos - st.neg;
  document.getElementById('total-score').textContent = Math.max(0,total);
  document.getElementById('score-cap').textContent = 1000;
  document.getElementById('val-positive').textContent = '+'+st.pos;
  document.getElementById('val-negative').textContent = '-'+st.neg;
  document.getElementById('bar-positive').style.width = Math.min(st.pos/200*100,100)+'%';
  document.getElementById('bar-negative').style.width = Math.min(st.neg/200*100,100)+'%';
  let tip='开始记录我们的故事吧 💕';
  if(total>=500) tip='💖 超级甜蜜情侣！';
  else if(total>=200) tip='💕 感情升温中～';
  else if(total>=50) tip='😊 甜蜜小日子';
  else if(total<0) tip='💔 需要好好沟通哦';
  else tip='🥰 记录每一个瞬间';
  document.getElementById('score-tip').textContent=tip;
}

// ===== TODAY =====
function renderToday() {
  const today = new Date(); today.setHours(0,0,0,0);
  const todayEntries = st.entries.filter(e => new Date(e.t) >= today);
  const posT=todayEntries.filter(e=>!e.neg), negT=todayEntries.filter(e=>e.neg);
  const posS=posT.reduce((s,e)=>s+e.v,0), negS=negT.reduce((s,e)=>s+e.v,0);
  document.getElementById('today-stats').innerHTML = st.entries.length===0
    ? '暂无记录，开始第一笔吧！'
    : '<div style="margin-bottom:8px">今日甜蜜: <b style="color:var(--pink)">+'+posS+'</b> &nbsp;|&nbsp; 今日矛盾: <b style="color:var(--purple)">-'+negS+'</b></div><div style="color:#aaa;font-size:0.8em">共 '+st.entries.length+' 条记录，'+todayEntries.length+' 条今日</div>';
}

// ===== HISTORY =====
function renderHistory() {
  const list = document.getElementById('history-list');
  document.getElementById('history-count').textContent = '('+st.entries.length+'条记录)';
  if (!st.entries.length) { list.innerHTML='<div class="empty"><span class="es">💌</span>还没有记录哦～<br>开始记录你们的甜蜜时刻吧！</div>'; return; }
  list.innerHTML = st.entries.map(e => {
    const d = new Date(e.t);
    const ts = (d.getMonth()+1)+'月'+d.getDate()+'日 '+d.getHours().toString().padStart(2,'0')+':'+d.getMinutes().toString().padStart(2,'0');
    return '<div class="hitem '+(e.neg?'neg':'pos')+'">'+
      '<span class="hem">'+e.emoji+'</span>'+
      '<div class="hbody">'+
      '<div class="htitle">'+e.emoji+' '+e.cname+' '+(e.neg?'-':'+')+e.v+'分</div>'+
      (e.note?'<div class="hnote">"'+e.note+'"</div>':'')+
      '<div class="hmeta"><span class="htag">'+(e.neg?'💔':'💕')+'</span></div>'+
      '<div class="htime">'+ts+'</div></div>'+
      '<span class="hdel" onclick="delEntry('+e.id+')">✕</span></div>';
  }).join('');
}

async function delEntry(id) {
  try { await api('DELETE', '/api/entry/'+id); } catch(e) {}
  st.entries = st.entries.filter(e=>e.id!==id);
  recalc();
  saveToServer();
  updateScore(); renderHistory(); renderAchieve(); renderStats(); renderToday();
}

async function confirmReset() {
  if (!confirm('确定要清空所有记录吗？不可恢复哦！😢')) return;
  try { await api('POST', '/api/reset'); } catch(e) {}
  st.entries=[]; recalc(); saveToServer();
  updateScore(); renderHistory(); renderAchieve(); renderStats(); renderToday();
}

// ===== ACHIEVE =====
function checkAchieve() {
  const data = { h:st.entries, stats:{pos:st.pos} };
  ACHIEVES.forEach(a => {
    if (!st.unlocked.includes(a.id) && a.fn(data)) {
      st.unlocked.push(a.id);
      saveToServer();
      setTimeout(()=>triggerConfetti(), 200);
    }
  });
}

function renderAchieve() {
  const grid = document.getElementById('achieve-grid');
  const count = (st.unlocked||[]).length;
  document.getElementById('achieve-progress').textContent = '('+count+'/'+ACHIEVES.length+')';
  grid.innerHTML = ACHIEVES.map(a => {
    const ok = (st.unlocked||[]).includes(a.id);
    return '<div class="aitem '+(ok?'unlocked':'locked')+'">'+
      '<span class="aicon">'+a.emoji+'</span>'+
      '<div class="aname">'+a.name+'</div>'+
      '<div class="adesc">'+a.desc+'</div>'+
      (!ok?'<span class="alock">🔒</span>':'')+'</div>';
  }).join('');
}

// ===== STATS =====
function renderStats() {
  const grid = document.getElementById('stats-grid');
  const total=st.pos-st.neg;
  const posE=st.entries.filter(e=>!e.neg), negE=st.entries.filter(e=>e.neg);
  const avgPos=posE.length?(st.pos/posE.length).toFixed(1):'0';
  const avgNeg=negE.length?(st.neg/negE.length).toFixed(1):'0';
  const first=st.entries.length?new Date(st.entries[st.entries.length-1].t):null;
  const days=first?Math.floor((Date.now()-first.getTime())/86400000):0;
  const top=getTopCat(posE);
  grid.innerHTML =
    '<div class="sitem"><div class="sv">'+Math.max(0,total)+'</div><div class="sl">当前积分</div></div>'+
    '<div class="sitem"><div class="sv">'+st.entries.length+'</div><div class="sl">总记录</div></div>'+
    '<div class="sitem"><div class="sv">'+posE.length+'</div><div class="sl">甜蜜时刻</div></div>'+
    '<div class="sitem"><div class="sv">'+negE.length+'</div><div class="sl">小矛盾</div></div>'+
    '<div class="sitem"><div class="sv">'+avgPos+'</div><div class="sl">均甜蜜分</div></div>'+
    '<div class="sitem"><div class="sv">'+avgNeg+'</div><div class="sl">均矛盾分</div></div>'+
    '<div class="sitem"><div class="sv">'+(days||'-')+'</div><div class="sl">在一起(天)</div></div>'+
    '<div class="sitem"><div class="sv">'+(top.emoji||'💕')+'</div><div class="sl">最高频</div></div>';
}

function getTopCat(entries) {
  const m={}; entries.forEach(e=>{ m[e.cat]=(m[e.cat]||0)+1; });
  const arr=Object.entries(m).sort((a,b)=>b[1]-a[1]);
  if(!arr.length) return {};
  return CATS.positive.find(c=>c.id===arr[0][0]) || {};
}

// ===== MODAL =====
function openModal() { document.getElementById('modal-overlay').classList.add('open'); document.getElementById('couple-name-input').value=st.coupleName||''; document.getElementById('couple-name-input').focus(); }
function closeModal() { document.getElementById('modal-overlay').classList.remove('open'); }

async function saveCoupleName() {
  const n = document.getElementById('couple-name-input').value.trim();
  if (!n) return;
  st.coupleName = n;
  try { await api('POST', '/api/couple-name', {name:n}); } catch(e) {}
  saveToServer();
  document.getElementById('display-name').textContent = n;
  closeModal();
}
document.getElementById('modal-overlay').addEventListener('click', e => { if(e.target===document.getElementById('modal-overlay')) closeModal(); });

// ===== CONFETTI =====
function triggerConfetti() {
  const cv=document.getElementById('confetti'), ctx=cv.getContext('2d');
  cv.width=window.innerWidth; cv.height=window.innerHeight;
  const colors=['#ff6b9d','#f5c518','#e91e63','#9c27b0','#ff80ab','#ffd54f','#ff4081'];
  const ps=[];
  for(let i=0;i<60;i++) ps.push({x:Math.random()*cv.width,y:-20,vx:(Math.random()-0.5)*4,vy:Math.random()*3+2,c:colors[Math.floor(Math.random()*colors.length)],s:Math.random()*8+4,r:Math.random()*360,rv:(Math.random()-0.5)*10});
  let fr=0;
  function draw() {
    ctx.clearRect(0,0,cv.width,cv.height);
    ps.forEach(p=>{ p.x+=p.vx;p.y+=p.vy;p.vy+=0.08;p.r+=p.rv;
      ctx.save();ctx.translate(p.x,p.y);ctx.rotate(p.r*Math.PI/180);
      ctx.fillStyle=p.c;ctx.fillRect(-p.s/2,-p.s/2,p.s,p.s);ctx.restore(); });
    fr++;
    if(fr<120) requestAnimationFrame(draw); else ctx.clearRect(0,0,cv.width,cv.height);
  }
  draw();
}

init();
"""

new_content = before + '<script>\n' + new_script + '\n' + after
open('D:/love-scorebook/index.html', 'w', encoding='utf-8').write(new_content)
print('Done! New length:', len(new_content))

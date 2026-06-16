#!/usr/bin/env python3
"""微信聊天记录分析 → 生成 HTML 报告网页"""
import re, json, sys, os
from collections import Counter
from datetime import datetime

# ─── 配置 ───
GROUP_NAME = "交流2群🌲2026IP训练营"
GROUP_SIZE = "~500"
TOPIC_CATEGORIES_JSON = """[
  {"topic":"环境搭建与工具安装","percentage":35,"keywords":["Claude Code","CC Switch","DeepSeek","API","Node.js","Git","VS Code","WorkBuddy","Codex","谷歌账号","魔法/上网"],"description":"群聊最主要话题。大量新人请教安装配置、解决环境问题。"},
  {"topic":"教程与资源分享","percentage":25,"keywords":["星野微信教程","阿扶耶AI全栈指南","期善Mic新手网站","cclearning.cn","claude-tutorial.pages.dev","hermes教程"],"description":"核心贡献者制作了大量中文教程网站，帮助新人快速上手。"},
  {"topic":"AI项目展示与交流","percentage":20,"keywords":["网页","网站","部署","GitHub Pages","Netlify","Surge","游戏","生图","视频"],"description":"群友展示用AI做的项目：游戏、网站、AI模特图、思维导图等。"},
  {"topic":"AI趋势与认知讨论","percentage":12,"keywords":["Token","API价格","Fable","Opus","算力","生产资料","技术扩散"],"description":"讨论AI行业趋势、模型优劣对比、费用、技术扩散理念。"},
  {"topic":"接单与变现","percentage":8,"keywords":["接单","有偿","代充","红包","闲鱼","aipayok.com","代付"],"description":"部分成员讨论通过帮人配置环境、代充API、做项目赚取报酬。"}
]"""
INSIGHT_TEXT = """📈 群聊呈现<strong>双峰模式</strong>：下午13-14点是第一个高峰（午休时间），深夜22-23点是第二个也是最高的高峰（夜猫子模式）。凌晨0-1点仍有不少人在交流。上午相对安静。<br>🎯 群文化核心：<span class="orange">行动至上</span> · 开源共享 · AI Native · 技术扩散"""

# ─── 解析聊天记录 ───
def parse_chat(filepath):
    with open(filepath, 'r', encoding='utf-8-sig', errors='replace') as f:
        lines = f.readlines()

    msgs = []
    pattern = re.compile(r'^\[(\d{4}-\d{2}-\d{2}) (\d{2}):(\d{2}):(\d{2})\] (.+?)\((wxid_[^)]+)\).*?:\s*(.*)')

    for line in lines:
        m = pattern.match(line.strip())
        if m:
            msgs.append({
                'date': m.group(1), 'hour': int(m.group(2)),
                'name': m.group(5).strip(), 'wxid': m.group(6),
                'content': m.group(7)
            })
    return msgs

# ─── 分析 ───
def analyze(msgs):
    total = len(msgs)
    speakers = Counter(m['wxid'] for m in msgs)
    speaker_names = {}
    for m in msgs:
        if m['wxid'] not in speaker_names:
            speaker_names[m['wxid']] = m['name']

    daily = Counter(m['date'] for m in msgs)
    hourly = Counter(m['hour'] for m in msgs)
    dates = sorted(daily.keys())
    active_days = len(dates)

    # Top speakers
    top = speakers.most_common(10)
    top_json = []
    for i, (wxid, cnt) in enumerate(top):
        top_json.append({
            'rank': i+1, 'name': speaker_names.get(wxid, wxid),
            'wxid': wxid, 'count': cnt,
            'role': '核心贡献者' if i == 0 else ('活跃成员' if i < 5 else '')
        })

    # Daily distribution
    daily_json = [{'date': d, 'messages': daily[d]} for d in dates]

    # Hourly distribution
    hourly_json = [{'hour': h, 'count': hourly.get(h, 0)} for h in range(24)]

    # Chinese keywords
    all_text = ' '.join(m['content'] for m in msgs)
    cn_words = re.findall(r'[一-鿿]{2,4}', all_text)
    word_counts = Counter(cn_words).most_common(15)
    # Filter common words
    stop = {'可以','一个','这个','什么','怎么','不是','没有','已经','现在','就是','这个','的话','还是','一下','那个'}
    word_json = [{'word': w, 'count': c} for w, c in word_counts if w not in stop][:15]

    # Peaks
    peak_hour = max(range(24), key=lambda h: hourly.get(h, 0))
    peak_count = hourly.get(peak_hour, 0)
    peak_day = max(daily, key=daily.get)
    peak_day_count = daily[peak_day]
    avg_daily = total // max(active_days, 1)

    return {
        'total': total, 'speakers': len(speakers), 'active_days': active_days,
        'avg_daily': avg_daily, 'peak_day': peak_day, 'peak_day_count': peak_day_count,
        'peak_hour': peak_hour, 'peak_count': peak_count,
        'first_date': dates[0], 'last_date': dates[-1],
        'top_speakers': top_json, 'daily': daily_json, 'hourly': hourly_json,
        'words': word_json
    }

# ─── 生成 HTML ───
def generate_html(stats, output_path):
    data_json_top_speakers = json.dumps(stats['top_speakers'], ensure_ascii=False)
    data_json_hourly = json.dumps(stats['hourly'], ensure_ascii=False)
    data_json_words = json.dumps(stats['words'], ensure_ascii=False)

    peak_hour_str = f"{stats['peak_hour']:02d}:00"

    html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8"><meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{GROUP_NAME} - 群聊分析报告</title>
<style>
:root {{ --bg:#000; --green:#00ff41; --green2:#00cc33; --orange:#ff6a00; --orange2:#ff8c00; --card-bg:#0a0a0a; --border:#1a1a1a; }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:-apple-system,BlinkMacSystemFont,"PingFang SC","Microsoft YaHei",sans-serif; background:var(--bg); color:#fff; overflow:hidden; height:100vh; -webkit-font-smoothing:antialiased; user-select:none; }}
.slides {{ position:relative; width:100vw; height:100vh; }}
.slide {{ position:absolute; top:0; left:0; width:100%; height:100%; display:flex; flex-direction:column; align-items:center; justify-content:center; opacity:0; transform:scale(.92); transition:opacity .6s cubic-bezier(.16,1,.3,1),transform .6s cubic-bezier(.16,1,.3,1); pointer-events:none; padding:40px 24px; }}
.slide.active {{ opacity:1; transform:scale(1); pointer-events:auto; z-index:1; }}
.nav {{ position:fixed; bottom:28px; left:50%; transform:translateX(-50%); z-index:100; display:flex; gap:10px; align-items:center; }}
.nav-dot {{ width:8px; height:8px; border-radius:50%; background:#333; cursor:pointer; transition:all .3s; }}
.nav-dot.active {{ background:var(--green); width:24px; border-radius:4px; box-shadow:0 0 12px var(--green); }}
.nav-arrow {{ position:fixed; top:50%; transform:translateY(-50%); z-index:100; width:44px; height:44px; border-radius:50%; border:1px solid #222; background:rgba(10,10,10,.8); color:#888; font-size:20px; display:flex; align-items:center; justify-content:center; cursor:pointer; transition:all .3s; backdrop-filter:blur(10px); }}
.nav-arrow:hover {{ border-color:var(--green); color:var(--green); box-shadow:0 0 20px rgba(0,255,65,.15); }}
.nav-prev {{ left:20px; }} .nav-next {{ right:20px; }}
.slide-num {{ position:fixed; top:24px; right:28px; z-index:100; font-family:monospace; font-size:13px; color:#555; letter-spacing:2px; }}
.bgm-toggle {{ position:fixed; top:24px; left:28px; z-index:100; width:36px; height:36px; border-radius:50%; border:1px solid #222; background:rgba(10,10,10,.8); color:#555; font-size:16px; display:flex; align-items:center; justify-content:center; cursor:pointer; transition:all .3s; backdrop-filter:blur(10px); }}
.bgm-toggle.on {{ border-color:var(--orange); color:var(--orange); }}
.glow-text {{ text-shadow:0 0 40px rgba(0,255,65,.3),0 0 80px rgba(0,255,65,.1); }}
.glow-orange {{ text-shadow:0 0 40px rgba(255,106,0,.3),0 0 80px rgba(255,106,0,.1); }}
.overline {{ font-family:monospace; font-size:11px; letter-spacing:4px; color:var(--orange); text-transform:uppercase; margin-bottom:8px; }}
.huge {{ font-size:clamp(60px,12vw,120px); font-weight:900; letter-spacing:-3px; line-height:1; }}
.big {{ font-size:clamp(32px,6vw,56px); font-weight:800; letter-spacing:-1px; line-height:1.1; }}
.green {{ color:var(--green); }} .orange {{ color:var(--orange); }} .dim {{ color:#444; font-size:13px; }} .muted {{ color:#666; font-size:14px; }}
@keyframes fadeUp {{ from {{ opacity:0; transform:translateY(30px); }} to {{ opacity:1; transform:translateY(0); }} }}
@keyframes fadeIn {{ from {{ opacity:0; }} to {{ opacity:1; }} }}
@keyframes pulse {{ 0%,100% {{ opacity:1; }} 50% {{ opacity:.5; }} }}
.anim-fadeup {{ animation:fadeUp .8s cubic-bezier(.16,1,.3,1) both; }}
.anim-fadein {{ animation:fadeIn 1s ease both; }}
/* S1 */ .s1-grid {{ display:grid; grid-template-columns:1fr 1fr; gap:40px; max-width:900px; width:100%; align-items:center; }}
.s1-left {{ text-align:left; }} .s1-right {{ display:flex; flex-direction:column; gap:16px; }}
.s1-stat {{ border-left:2px solid var(--green); padding-left:16px; }}
.s1-stat .val {{ font-size:42px; font-weight:900; color:var(--green); line-height:1; }}
.s1-stat .lbl {{ font-size:12px; color:#555; margin-top:4px; letter-spacing:1px; }}
.title-line {{ width:60px; height:3px; background:var(--orange); margin:16px 0; }}
.scroll-hint {{ position:absolute; bottom:60px; color:#333; font-size:12px; letter-spacing:2px; animation:pulse 2s infinite; }}
/* S2 */ .stats-row {{ display:flex; gap:20px; flex-wrap:wrap; justify-content:center; max-width:900px; width:100%; }}
.stat-box {{ flex:1; min-width:130px; max-width:170px; background:var(--card-bg); border:1px solid var(--border); border-radius:16px; padding:28px 16px; text-align:center; position:relative; overflow:hidden; transition:all .3s; }}
.stat-box:hover {{ border-color:var(--green); transform:translateY(-4px); }}
.stat-box::after {{ content:''; position:absolute; bottom:0; left:0; right:0; height:2px; background:linear-gradient(90deg,transparent,var(--green),transparent); opacity:0; transition:opacity .3s; }}
.stat-box:hover::after {{ opacity:1; }}
.stat-box .num {{ font-size:clamp(32px,5vw,48px); font-weight:900; color:var(--green); line-height:1; font-family:monospace; }}
.stat-box .lbl {{ font-size:12px; color:#555; margin-top:8px; letter-spacing:1px; }}
/* S3 */ .lb-wrap {{ max-width:700px; width:100%; display:flex; flex-direction:column; gap:10px; }}
.lb-item {{ display:flex; align-items:center; gap:14px; padding:12px 16px; background:var(--card-bg); border:1px solid var(--border); border-radius:12px; position:relative; overflow:hidden; transition:all .3s; }}
.lb-item:hover {{ border-color:var(--green); }}
.lb-item::before {{ content:''; position:absolute; left:0; top:0; bottom:0; width:3px; }}
.lb-item:nth-child(1)::before {{ background:var(--orange); box-shadow:0 0 10px var(--orange); }}
.lb-item:nth-child(2)::before {{ background:var(--orange2); }}
.lb-item:nth-child(3)::before {{ background:var(--green); }}
.lb-rank-num {{ font-family:monospace; font-size:20px; font-weight:900; width:30px; text-align:center; }}
.lb-item:nth-child(1) .lb-rank-num {{ color:var(--orange); }}
.lb-item:nth-child(2) .lb-rank-num {{ color:var(--orange2); }}
.lb-item:nth-child(3) .lb-rank-num {{ color:var(--green); }}
.lb-item:nth-child(n+4) .lb-rank-num {{ color:#333; }}
.lb-av {{ width:38px; height:38px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:13px; font-weight:700; flex-shrink:0; }}
.lb-av.c1 {{ background:var(--orange); color:#000; }} .lb-av.c2 {{ background:var(--orange2); color:#000; }} .lb-av.c3 {{ background:var(--green); color:#000; }} .lb-av.c4 {{ background:#1a1a1a; color:#555; }}
.lb-info {{ flex:1; min-width:0; }} .lb-name {{ font-weight:600; font-size:15px; white-space:nowrap; overflow:hidden; text-overflow:ellipsis; }} .lb-role {{ font-size:11px; color:#333; }}
.lb-bar-wrap {{ flex:1; height:4px; background:#111; border-radius:2px; max-width:200px; overflow:hidden; }}
.lb-bar-fill {{ height:100%; border-radius:2px; }}
.lb-count {{ font-family:monospace; font-size:16px; font-weight:700; color:var(--green); width:40px; text-align:right; }}
/* S4 */ .hm-wrap {{ max-width:900px; width:100%; }}
.hm-grid {{ display:flex; gap:4px; align-items:flex-end; justify-content:center; height:260px; }}
.hm-col {{ flex:1; display:flex; flex-direction:column; align-items:center; gap:6px; }}
.hm-bar {{ width:100%; max-width:32px; border-radius:4px; }}
.hm-bar.peek {{ background:var(--orange); }} .hm-bar.hot {{ background:var(--green); }}
.hm-count {{ font-family:monospace; font-size:11px; color:#555; }}
.hm-label {{ font-size:9px; color:#333; letter-spacing:1px; }}
.hm-legend {{ display:flex; gap:16px; justify-content:center; margin-top:16px; font-size:12px; color:#333; }}
.hm-legend .dot {{ width:8px; height:8px; border-radius:2px; display:inline-block; }}
.hm-legend .dot.low {{ background:var(--orange); }} .hm-legend .dot.high {{ background:var(--green); }}
/* S5 */ .kw-wrap {{ max-width:800px; display:flex; flex-wrap:wrap; gap:12px; justify-content:center; align-items:center; padding:20px; }}
.kw-tag {{ padding:8px 22px; border-radius:24px; font-weight:600; border:1px solid #1a1a1a; transition:all .4s; cursor:default; animation:fadeUp .6s cubic-bezier(.16,1,.3,1) both; }}
.kw-tag:hover {{ transform:scale(1.1); }}
.kw-tag.g {{ color:var(--green); border-color:var(--green); }} .kw-tag.g:hover {{ background:rgba(0,255,65,.1); box-shadow:0 0 30px rgba(0,255,65,.15); }}
.kw-tag.o {{ color:var(--orange); border-color:var(--orange); }} .kw-tag.o:hover {{ background:rgba(255,106,0,.1); box-shadow:0 0 30px rgba(255,106,0,.15); }}
.kw-xl {{ font-size:clamp(24px,4vw,36px); }} .kw-lg {{ font-size:clamp(18px,3vw,26px); }} .kw-md {{ font-size:16px; }} .kw-sm {{ font-size:13px; }}
/* S6 */ .tp-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(250px,1fr)); gap:16px; max-width:1000px; width:100%; }}
.tp-card {{ background:var(--card-bg); border:1px solid var(--border); border-radius:16px; padding:24px; position:relative; overflow:hidden; transition:all .3s; }}
.tp-card:hover {{ border-color:var(--green); transform:translateY(-2px); }}
.tp-card::before {{ content:''; position:absolute; top:0; left:0; right:0; height:3px; }}
.tp-card:nth-child(1)::before {{ background:var(--green); }} .tp-card:nth-child(2)::before {{ background:var(--orange); }} .tp-card:nth-child(3)::before {{ background:var(--green); }} .tp-card:nth-child(4)::before {{ background:var(--orange); }} .tp-card:nth-child(5)::before {{ background:var(--green); }}
.tp-pct {{ font-family:monospace; font-size:36px; font-weight:900; line-height:1; margin-bottom:6px; }}
.tp-card:nth-child(odd) .tp-pct {{ color:var(--green); }} .tp-card:nth-child(even) .tp-pct {{ color:var(--orange); }}
.tp-title {{ font-weight:700; font-size:16px; margin-bottom:8px; }}
.tp-desc {{ color:#555; font-size:12px; line-height:1.6; margin-bottom:10px; }}
.tp-tags {{ display:flex; flex-wrap:wrap; gap:5px; }}
.tp-tags span {{ font-size:11px; padding:3px 8px; border-radius:4px; background:#111; color:#444; }}
/* S7 */ .in-wrap {{ max-width:800px; width:100%; display:flex; flex-direction:column; gap:16px; }}
.in-row {{ display:flex; gap:16px; flex-wrap:wrap; }}
.in-item {{ flex:1; min-width:180px; background:var(--card-bg); border:1px solid var(--border); border-radius:12px; padding:20px; }}
.in-item .in-num {{ font-family:monospace; font-size:28px; font-weight:900; color:var(--orange); }}
.in-item .in-lbl {{ font-size:12px; color:#555; margin-top:4px; }}
.in-text {{ color:#666; font-size:14px; line-height:1.8; padding:20px; background:var(--card-bg); border:1px solid var(--border); border-radius:12px; }}
/* S8 */ .end-wrap {{ text-align:center; }}
.end-qr {{ width:80px; height:80px; background:#111; border:1px solid #222; border-radius:12px; margin:24px auto; display:flex; align-items:center; justify-content:center; font-size:32px; }}
body::after {{ content:''; position:fixed; top:0; left:0; width:100%; height:100%; background:repeating-linear-gradient(0deg,transparent,transparent 2px,rgba(0,0,0,.03) 2px,rgba(0,0,0,.03) 4px); pointer-events:none; z-index:999; opacity:.3; }}
@media (max-width:640px) {{
.slide {{ padding:20px 14px; }} .s1-grid {{ grid-template-columns:1fr; gap:24px; }}
.s1-right {{ flex-direction:row; flex-wrap:wrap; gap:8px; }} .s1-stat {{ flex:1; min-width:100px; }}
.stats-row {{ gap:10px; }} .stat-box {{ min-width:100px; padding:20px 10px; }}
.lb-bar-wrap {{ display:none; }} .tp-grid {{ grid-template-columns:1fr; }}
.hm-grid {{ gap:2px; height:180px; }} .hm-label {{ font-size:7px; }} .hm-count {{ font-size:9px; }}
.nav-arrow {{ width:32px; height:32px; font-size:14px; }} .nav-prev {{ left:8px; }} .nav-next {{ right:8px; }}
}}
</style></head><body>

<div class="bgm-toggle" id="bgmBtn" onclick="toggleBGM()" title="BGM">♪</div>
<div class="slide-num" id="slideNum">01 / 08</div>
<div class="nav-arrow nav-prev" onclick="goSlide(-1)">◂</div>
<div class="nav-arrow nav-next" onclick="goSlide(1)">▸</div>
<div class="nav" id="navDots"></div>

<div class="slides" id="slides">

<!-- S1: Title -->
<div class="slide active"><div class="s1-grid">
<div class="s1-left">
<div class="overline anim-fadeup" style="animation-delay:0s">2026 IP TRAINING CAMP</div>
<h1 class="huge anim-fadeup" style="animation-delay:.1s"><span class="glow-text">{GROUP_NAME.replace('🌲','')}</span><br><span style="font-size:.6em;color:#fff;">群聊分析报告</span></h1>
<div class="title-line anim-fadeup" style="animation-delay:.3s"></div>
<p class="muted anim-fadeup" style="animation-delay:.4s">{stats['first_date']} ~ {stats['last_date']} · {stats['active_days']}天 · {stats['speakers']}人</p>
</div>
<div class="s1-right">
<div class="s1-stat anim-fadeup" style="animation-delay:.2s"><div class="val glow-text">{stats['total']:,}</div><div class="lbl">TOTAL MESSAGES</div></div>
<div class="s1-stat anim-fadeup" style="animation-delay:.35s"><div class="val glow-orange">{stats['peak_count']}</div><div class="lbl">PEAK {peak_hour_str}</div></div>
<div class="s1-stat anim-fadeup" style="animation-delay:.5s"><div class="val" style="color:#fff;">{GROUP_SIZE}</div><div class="lbl">GROUP MEMBERS</div></div>
</div></div><div class="scroll-hint anim-fadein" style="animation-delay:1s;">按 → 或点击右侧箭头翻页</div></div>

<!-- S2: Overview -->
<div class="slide"><div class="overline" style="margin-bottom:12px;">// OVERVIEW</div><h2 class="big" style="margin-bottom:32px;">📊 <span class="glow-text">群聊数据</span>概览</h2><div class="stats-row" id="statBoxes"></div></div>

<!-- S3: Leaderboard -->
<div class="slide"><div class="overline" style="margin-bottom:12px;">// LEADERBOARD</div><h2 class="big" style="margin-bottom:28px;">🏆 活跃<span class="glow-orange">排行榜</span> TOP 10</h2><div class="lb-wrap" id="lbWrap"></div></div>

<!-- S4: Heatmap -->
<div class="slide"><div class="overline" style="margin-bottom:12px;">// ACTIVITY HEATMAP</div><h2 class="big" style="margin-bottom:28px;">🔥 <span class="glow-text">24小时</span>活跃分布</h2><div class="hm-wrap"><div class="hm-grid" id="hmGrid"></div><div class="hm-legend"><span><span class="dot low"></span> 普通活跃</span><span><span class="dot high"></span> 高频时段</span></div></div></div>

<!-- S5: Keywords -->
<div class="slide"><div class="overline" style="margin-bottom:12px;">// KEYWORDS</div><h2 class="big" style="margin-bottom:28px;">🏷️ 热门<span class="glow-text">关键词</span></h2><div class="kw-wrap" id="kwWrap"></div></div>

<!-- S6: Topics -->
<div class="slide"><div class="overline" style="margin-bottom:12px;">// TOPICS</div><h2 class="big" style="margin-bottom:28px;">🧭 话题<span class="glow-orange">方向</span>分类</h2><div class="tp-grid" id="tpGrid"></div></div>

<!-- S7: Insights -->
<div class="slide"><div class="overline" style="margin-bottom:12px;">// INSIGHTS</div><h2 class="big" style="margin-bottom:28px;">💡 <span class="glow-text">深度</span>洞察</h2><div class="in-wrap"><div class="in-row" id="insightRow"></div><div class="in-text" id="insightText"></div></div></div>

<!-- S8: End -->
<div class="slide"><div class="end-wrap"><div class="overline" style="margin-bottom:12px;">// END</div><h2 class="huge glow-text" style="font-size:clamp(40px,8vw,80px);">谢谢观看</h2><div class="title-line" style="margin:24px auto;width:80px;"></div><p class="muted">{GROUP_NAME}</p><p class="dim" style="margin-top:8px;">数据更新于 {datetime.now().strftime('%Y-%m-%d %H:%M')} · 每日自动分析</p><div class="end-qr">🌲</div><p style="color:#333;font-size:12px;margin-top:12px;">Made with ❤️ for the community</p></div></div>

</div>

<script>
var TOTAL_MSGS = {stats['total']};
var TOTAL_SPEAKERS = {stats['speakers']};
var ACTIVE_DAYS = {stats['active_days']};
var AVG_DAILY = {stats['avg_daily']};
var PEAK_DAY_MSGS = {stats['peak_day_count']};
var GROUP_NAME = '{GROUP_NAME}';
var GROUP_FULL_NAME = '{GROUP_NAME}';
var DATE_RANGE = '{stats["first_date"]} ~ {stats["last_date"]}';
var EXPORT_INFO = '数据更新于 {datetime.now().strftime("%Y-%m-%d %H:%M")}';
var PEAK_COUNT = {stats['peak_count']};
var PEAK_HOUR = '{peak_hour_str}';
var GROUP_SIZE = '{GROUP_SIZE}';

var topSpeakers = {data_json_top_speakers};
var hourlyDist = {data_json_hourly};
var topWords = {data_json_words};
var topicCategories = {TOPIC_CATEGORIES_JSON};

// Slide system
var current=0,total=8,slides=document.querySelectorAll('.slide'),dots=[];
var navDots=document.getElementById('navDots');
for(var i=0;i<total;i++){{(function(idx){{var d=document.createElement('div');d.className='nav-dot'+(idx===0?' active':'');d.onclick=function(){{goTo(idx)}};navDots.appendChild(d);dots.push(d)}})(i)}}
function goTo(n){{if(n===current)return;slides[current].classList.remove('active');dots[current].classList.remove('active');current=n;slides[current].classList.add('active');dots[current].classList.add('active');document.getElementById('slideNum').textContent=('0'+(current+1)).slice(-2)+' / 0'+total;if(!window._entered)window._entered={{}};if(!window._entered[n]){{window._entered[n]=true;if(n===1)animateCounters();if(n===3)renderHeatmap()}}}}
function goSlide(d){{var n=current+d;if(n>=0&&n<total)goTo(n)}}
document.addEventListener('keydown',function(e){{if(e.key==='ArrowRight'||e.key==='ArrowDown')goSlide(1);if(e.key==='ArrowLeft'||e.key==='ArrowUp')goSlide(-1);if(e.key===' '){{e.preventDefault();toggleBGM()}}}});
var tx=0;document.addEventListener('touchstart',function(e){{tx=e.touches[0].clientX}});document.addEventListener('touchend',function(e){{var dx=e.changedTouches[0].clientX-tx;if(Math.abs(dx)>50)goSlide(dx<0?1:-1)}});

function animateCounters(){{var nums=document.querySelectorAll('.stat-box .num');nums.forEach(function(el){{var t=parseInt(el.textContent.replace(/,/g,''))||0,d=1200,s=performance.now();el.textContent='0';function tick(n){{var p=Math.min((n-s)/d,1);p=1-Math.pow(1-p,3);el.textContent=Math.round(p*t).toLocaleString();if(p<1)requestAnimationFrame(tick);else el.textContent=t.toLocaleString()}}requestAnimationFrame(tick)}})}}

// Stat boxes
(function(){{var boxes=[{{t:TOTAL_MSGS,l:'总消息数'}},{{t:TOTAL_SPEAKERS,l:'发言人数'}},{{t:ACTIVE_DAYS,l:'统计天数'}},{{t:AVG_DAILY,l:'日均消息'}},{{t:PEAK_DAY_MSGS,l:'最高单日'}}];var h='';boxes.forEach(function(b){{h+='<div class="stat-box"><div class="num">'+b.t.toLocaleString()+'</div><div class="lbl">'+b.l+'</div></div>'}});document.getElementById('statBoxes').innerHTML=h}})();

// Leaderboard
(function(){{var m=topSpeakers[0]?topSpeakers[0].count:1,h='';topSpeakers.forEach(function(p,i){{var c=i<3?'c'+(i+1):'c4',init=p.name.replace(/[^一-龥a-zA-Z]/g,'').slice(0,2)||'?';h+='<div class="lb-item anim-fadeup" style="animation-delay:'+(i*.08)+'s"><div class="lb-rank-num">'+(i<9?'0':'')+(i+1)+'</div><div class="lb-av '+c+'">'+init+'</div><div class="lb-info"><div class="lb-name">'+p.name+'</div><div class="lb-role">'+(p.role||'活跃成员')+'</div></div><div class="lb-bar-wrap"><div class="lb-bar-fill" style="width:'+Math.round(p.count/m*100)+'%;background:'+(i%2===0?'#00ff41':'#ff6a00')+'"></div></div><div class="lb-count">'+p.count+'</div></div>'}});document.getElementById('lbWrap').innerHTML=h}})();

// Heatmap
function renderHeatmap(){{var m=Math.max.apply(null,hourlyDist.map(function(d){{return d.count}})),th=m*.5,h='';hourlyDist.forEach(function(d){{var is=d.count>=th,ht=Math.max(d.count/m*220,4);h+='<div class="hm-col"><div class="hm-count">'+(d.count||'')+'</div><div class="hm-bar '+(is?'hot':'peek')+'" style="height:'+ht+'px"></div><div class="hm-label">'+d.hour+'h</div></div>'}});document.getElementById('hmGrid').innerHTML=h}}

// Keywords
(function(){{var m=topWords[0]?topWords[0].count:1,h='',cm=['g','g','o','g','o','g','o','o','g','g','o','g','o','o','g'];topWords.forEach(function(w,i){{var c;if(w.count>=15)c='kw-xl';else if(w.count>=10)c='kw-lg';else if(w.count>=7)c='kw-md';else c='kw-sm';var cl=cm[i]||(i%2?'o':'g');h+='<span class="kw-tag '+c+' '+cl+'" style="animation-delay:'+(i*.06)+'s">'+w.word+'</span>'}});document.getElementById('kwWrap').innerHTML=h}})();

// Topics
(function(){{var h='';topicCategories.forEach(function(t,i){{h+='<div class="tp-card anim-fadeup" style="animation-delay:'+(i*.12)+'s"><div class="tp-pct">'+t.percentage+'%</div><div class="tp-title">'+t.topic+'</div><div class="tp-desc">'+t.description+'</div><div class="tp-tags">';t.keywords.forEach(function(k){{h+='<span>#'+k+'</span>'}});h+='</div></div>'}});document.getElementById('tpGrid').innerHTML=h}})();

// Insights
(function(){{var items=[{{n:'{peak_hour_str}',l:'双峰时段 · 夜猫子模式'}},{{n:'{stats["peak_day"]}',l:'最活跃日 '+PEAK_DAY_MSGS+' 条'}},{{n:'TREND',l:'每日消息趋势'}}];var h='';items.forEach(function(it){{h+='<div class="in-item"><div class="in-num">'+it.n+'</div><div class="in-lbl">'+it.l+'</div></div>'}});document.getElementById('insightRow').innerHTML=h;document.getElementById('insightText').innerHTML='{INSIGHT_TEXT.replace("'","\\'")}';}})();

// BGM
var bgmOn=false,audioCtx=null,bgmNodes=[];
function toggleBGM(){{bgmOn=!bgmOn;var b=document.getElementById('bgmBtn');if(bgmOn){{b.classList.add('on');startBGM()}}else{{b.classList.remove('on');stopBGM()}}}}
function startBGM(){{if(!audioCtx)audioCtx=new(window.AudioContext||window.webkitAudioContext)();var n=audioCtx.currentTime,p=audioCtx.createOscillator();p.type='sine';p.frequency.value=55;var g=audioCtx.createGain();g.gain.setValueAtTime(0,n);g.gain.linearRampToValueAtTime(.08,n+.5);p.connect(g);g.connect(audioCtx.destination);p.start(n);bgmNodes.push({{osc:p,gain:g}});var b=audioCtx.createOscillator();b.type='triangle';b.frequency.value=110;var bg=audioCtx.createGain();bg.gain.setValueAtTime(0,n);bg.gain.linearRampToValueAtTime(.04,n+.8);b.connect(bg);bg.connect(audioCtx.destination);b.start(n);bgmNodes.push({{osc:b,gain:bg}});var h=audioCtx.createOscillator();h.type='sine';h.frequency.value=880;var hg=audioCtx.createGain();hg.gain.setValueAtTime(0,n);hg.gain.linearRampToValueAtTime(.015,n+1);h.connect(hg);hg.connect(audioCtx.destination);h.start(n);bgmNodes.push({{osc:h,gain:hg}});var l=audioCtx.createOscillator();l.type='sine';l.frequency.value=.15;var lg=audioCtx.createGain();lg.gain.value=5;l.connect(lg);lg.connect(p.frequency);l.start(n);bgmNodes.push({{osc:l,gain:lg}})}}
function stopBGM(){{bgmNodes.forEach(function(n){{var t=audioCtx.currentTime;n.gain.gain.linearRampToValueAtTime(0,t+.3);n.osc.stop(t+.4)}});bgmNodes=[]}}
document.getElementById('slideNum').textContent='01 / 08';
var astart=function(){{if(!bgmOn)toggleBGM();document.removeEventListener('click',astart);document.removeEventListener('keydown',astart)}};document.addEventListener('click',astart);document.addEventListener('keydown',astart);
</script>
</body></html>'''

    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(html)


# ─── Main ───
if __name__ == '__main__':
    input_file = sys.argv[1] if len(sys.argv) > 1 else 'messages.txt'
    output_file = sys.argv[2] if len(sys.argv) > 2 else 'index.html'

    if not os.path.exists(input_file):
        print(f"❌ 找不到文件: {input_file}")
        sys.exit(1)

    print(f"📊 分析: {input_file}")
    msgs = parse_chat(input_file)
    print(f"  ✓ 解析到 {len(msgs)} 条消息")

    stats = analyze(msgs)
    print(f"  ✓ {stats['total']} 条消息, {stats['speakers']} 人, {stats['active_days']} 天")
    print(f"  ✓ 最活跃: {stats['peak_day']} ({stats['peak_day_count']}条)")
    print(f"  ✓ 峰值时段: {stats['peak_hour']:02d}:00 ({stats['peak_count']}条)")

    print(f"🎨 生成: {output_file}")
    generate_html(stats, output_file)
    print(f"✅ 完成! 用浏览器打开 {output_file}")

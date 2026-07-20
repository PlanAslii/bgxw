# pages.py
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="fa" dir="rtl" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>X4G Core Pro - Advanced Dashboard</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        black: '#030303',
                        neutral: { 850: '#151515', 900: '#0d0d0d', 950: '#050505' },
                        primary: '#3b82f6',
                        accent: '#10b981'
                    },
                    fontFamily: { sans: ['Tahoma', 'Vazirmatn', 'Arial', 'sans-serif'], mono: ['Fira Code', 'monospace'] }
                }
            }
        }
    </script>
    <style>
        @import url('https://fonts.googleapis.com/css2?family=Vazirmatn:wght@300;400;700;900&display=swap');
        body { background-color: #000; color: #f1f1f1; font-family: 'Vazirmatn', sans-serif; overflow-x: hidden; }
        .glass-panel { background: rgba(15, 15, 15, 0.85); backdrop-filter: blur(16px); border: 1px solid #222; box-shadow: 0 8px 32px 0 rgba(0,0,0,0.5); }
        .btn-primary { background: linear-gradient(135deg, #3b82f6 0%, #2563eb 100%); color: #fff; transition: all 0.3s; font-weight: bold; }
        .btn-primary:hover { filter: brightness(1.2); transform: translateY(-1px); }
        .btn-danger { background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%); color: #fff; }
        .btn-danger:hover { filter: brightness(1.2); }
        input, select { background: #0a0a0a; border: 1px solid #333; color: white; padding: 0.6rem 1rem; border-radius: 0.5rem; width: 100%; outline: none; transition: border 0.2s; }
        input:focus, select:focus { border-color: #3b82f6; box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2); }
        .fade-in { animation: fadeIn 0.4s cubic-bezier(0.4, 0, 0.2, 1); }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(15px); } to { opacity: 1; transform: translateY(0); } }
        
        /* طراحی اسکرول بار حرفه ای */
        ::-webkit-scrollbar { width: 8px; height: 8px; }
        ::-webkit-scrollbar-track { background: #050505; }
        ::-webkit-scrollbar-thumb { background: #333; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #555; }
        
        /* ترمینال زنده */
        .terminal { background: #0a0a0a; font-family: 'Fira Code', monospace; color: #4ade80; border: 1px solid #222; }
        .stat-card { position: relative; overflow: hidden; }
        .stat-card::after { content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 2px; background: linear-gradient(90deg, transparent, var(--color), transparent); opacity: 0.5; }
    </style>
</head>
<body class="min-h-screen flex selection:bg-primary selection:text-white">
    
    <aside class="w-64 glass-panel border-l border-neutral-800 hidden md:flex flex-col h-screen sticky top-0 z-40">
        <div class="p-6 border-b border-neutral-800 flex items-center justify-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-blue-800 flex items-center justify-center font-bold text-xl shadow-lg shadow-blue-900/50">X</div>
            <div class="text-2xl font-black tracking-tighter">X4G <span class="text-primary font-light">PRO</span></div>
        </div>
        <nav class="flex-1 p-4 space-y-2">
            <button onclick="showTab('dashboard')" id="nav-dashboard" class="w-full flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-xl bg-primary/10 text-primary transition">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M3 12l2-2m0 0l7-7 7 7M5 10v10a1 1 0 001 1h3m10-11l2 2m-2-2v10a1 1 0 01-1 1h-3m-6 0a1 1 0 001-1v-4a1 1 0 011-1h2a1 1 0 011 1v4a1 1 0 001 1m-6 0h6"></path></svg>
                داشبورد اصلی
            </button>
            <button onclick="showTab('links')" id="nav-links" class="w-full flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-xl text-gray-400 hover:bg-neutral-800 hover:text-white transition">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"></path></svg>
                مدیریت کانفیگ‌ها
            </button>
        </nav>
        <div class="p-4 border-t border-neutral-800">
            <div class="text-xs text-center text-gray-500">هسته هوشمند X4G-Core v3.1</div>
            <div class="text-xs text-center text-gray-600 mt-1">VLESS • Trojan • Shadowsocks</div>
        </div>
    </aside>

    <main class="flex-1 overflow-y-auto">
        <!-- Mobile Navbar -->
        <nav class="md:hidden glass-panel sticky top-0 z-50 px-4 py-3 flex justify-between items-center">
            <div class="text-xl font-black">X4G <span class="text-primary font-light">PRO</span></div>
            <div class="flex gap-2">
                <button onclick="showTab('dashboard')" class="text-xs font-medium text-gray-300 bg-neutral-800 px-3 py-1.5 rounded">داشبورد</button>
                <button onclick="showTab('links')" class="text-xs font-medium text-gray-300 bg-neutral-800 px-3 py-1.5 rounded">مدیریت</button>
            </div>
        </nav>

        <div class="container mx-auto p-4 md:p-8 max-w-7xl">
            
            <div id="tab-dashboard" class="space-y-8 fade-in">
                <!-- System Vitals (CPU/RAM) -->
                <div class="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div class="glass-panel stat-card p-5 rounded-2xl flex flex-col" style="--color: #3b82f6;">
                        <div class="text-gray-400 text-xs font-bold uppercase tracking-wider mb-2">مصرف پردازنده (CPU)</div>
                        <div class="text-3xl font-black flex items-end gap-1"><span id="sys-cpu">0</span><span class="text-lg text-gray-500 font-normal">%</span></div>
                        <div class="w-full bg-neutral-800 h-1.5 rounded-full mt-3 overflow-hidden"><div id="bar-cpu" class="bg-primary h-full rounded-full transition-all duration-1000" style="width: 0%"></div></div>
                    </div>
                    <div class="glass-panel stat-card p-5 rounded-2xl flex flex-col" style="--color: #8b5cf6;">
                        <div class="text-gray-400 text-xs font-bold uppercase tracking-wider mb-2">مصرف حافظه (RAM)</div>
                        <div class="text-3xl font-black flex items-end gap-1"><span id="sys-ram">0</span><span class="text-lg text-gray-500 font-normal">%</span></div>
                        <div class="w-full bg-neutral-800 h-1.5 rounded-full mt-3 overflow-hidden"><div id="bar-ram" class="bg-purple-500 h-full rounded-full transition-all duration-1000" style="width: 0%"></div></div>
                    </div>
                    <div class="glass-panel stat-card p-5 rounded-2xl flex flex-col" style="--color: #10b981;">
                        <div class="text-gray-400 text-xs font-bold uppercase tracking-wider mb-2">کاربران آنلاین</div>
                        <div class="text-3xl font-black text-accent" id="stat-online">0</div>
                    </div>
                    <div class="glass-panel stat-card p-5 rounded-2xl flex flex-col" style="--color: #f59e0b;">
                        <div class="text-gray-400 text-xs font-bold uppercase tracking-wider mb-2">ترافیک کل سیستم</div>
                        <div class="text-3xl font-black text-yellow-500" id="stat-traffic">0 GB</div>
                    </div>
                </div>

                <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    <!-- Chart Section -->
                    <div class="lg:col-span-2 glass-panel p-6 rounded-2xl">
                        <h3 class="text-lg font-bold mb-4 flex items-center gap-2">
                            <span class="w-2 h-2 rounded-full bg-accent animate-pulse"></span>
                            ترافیک زنده شبکه
                        </h3>
                        <div class="relative h-64 w-full">
                            <canvas id="trafficChart"></canvas>
                        </div>
                    </div>

                    <div class="glass-panel p-6 rounded-2xl border border-neutral-800 relative overflow-hidden">
                        <div class="absolute top-0 right-0 w-32 h-32 bg-primary/10 rounded-full blur-3xl -mr-10 -mt-10"></div>
                        <h2 class="text-lg font-bold mb-5 relative z-10">🚀 ساخت سریع مولتی‌پک</h2>
                        <p class="text-xs text-gray-400 mb-5 leading-relaxed relative z-10">شامل تمامی پروتکل‌های نسل جدید: VLESS, Trojan و Shadowsocks AEAD برای عبور از سخت‌ترین فایروال‌ها.</p>
                        
                        <form id="multipack-form" class="space-y-4 relative z-10" onsubmit="createMultipack(event)">
                            <div>
                                <label class="block text-xs font-semibold text-gray-400 mb-1">نام/شناسه کاربر</label>
                                <input type="text" id="mp-label" required placeholder="User-XYZ">
                            </div>
                            <div class="grid grid-cols-2 gap-4">
                                <div>
                                    <label class="block text-xs font-semibold text-gray-400 mb-1">حجم (GB) - 0=نامحدود</label>
                                    <input type="number" id="mp-volume" min="0" value="50" required>
                                </div>
                                <div>
                                    <label class="block text-xs font-semibold text-gray-400 mb-1">اعتبار (روز) - 0=دائمی</label>
                                    <input type="number" id="mp-days" min="0" value="30" required>
                                </div>
                            </div>
                            <button type="submit" class="btn-primary w-full py-3 rounded-xl mt-2 flex items-center justify-center gap-2">
                                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M12 6v6m0 0v6m0-6h6m-6 0H6"></path></svg>
                                ایجاد کانفیگ روی سرور
                            </button>
                        </form>
                    </div>
                </div>
                
                <div class="glass-panel p-6 rounded-2xl">
                    <h3 class="text-lg font-bold mb-4">🖥️ ترمینال زنده اتصالات</h3>
                    <div class="terminal rounded-xl p-4 h-48 overflow-y-auto text-xs leading-relaxed" id="live-logs">
                        <div class="text-gray-500"># X4G Pro Core Initialized. Awaiting connections...</div>
                    </div>
                </div>
            </div>

            <div id="tab-links" class="hidden space-y-6 fade-in">
                <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                    <div>
                        <h2 class="text-2xl font-black">مدیریت لایسنس‌ها و کاربران</h2>
                        <p class="text-gray-400 text-sm mt-1">کنترل کامل روی حجم، زمان و دسترسی‌های پروتکل</p>
                    </div>
                    <button onclick="loadLinks()" class="btn-primary px-4 py-2 rounded-lg text-sm flex items-center gap-2">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
                        به‌روزرسانی لیست
                    </button>
                </div>
                <div class="glass-panel rounded-2xl overflow-hidden border border-neutral-800">
                    <div class="overflow-x-auto">
                        <table class="w-full text-right text-sm whitespace-nowrap">
                            <thead class="bg-neutral-900/80 border-b border-neutral-800 text-gray-400 text-xs uppercase tracking-wider">
                                <tr>
                                    <th class="p-5 font-semibold">شناسه / نام</th>
                                    <th class="p-5 font-semibold">وضعیت مصرف</th>
                                    <th class="p-5 font-semibold">وضعیت اتصال</th>
                                    <th class="p-5 font-semibold text-center">ابزارهای پیشرفته</th>
                                </tr>
                            </thead>
                            <tbody id="links-tbody" class="divide-y divide-neutral-800">
                                <!-- Rows will be injected here via JS -->
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

        </div>
    </main>

    <!-- Modal for showing Subscription Link -->
    <div id="sub-modal" class="fixed inset-0 bg-black/90 backdrop-blur-md hidden z-50 flex items-center justify-center p-4">
        <div class="glass-panel p-6 md:p-8 rounded-3xl max-w-2xl w-full relative fade-in border border-primary/30 shadow-2xl shadow-primary/20">
            <button onclick="closeModal()" class="absolute top-5 left-5 w-8 h-8 flex items-center justify-center rounded-full bg-neutral-800 text-gray-400 hover:text-white transition">✕</button>
            <div class="w-12 h-12 bg-primary/20 text-primary rounded-2xl flex items-center justify-center mb-6">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"></path></svg>
            </div>
            <h3 class="text-2xl font-black mb-2">لینک هوشمند سابسکرایپشن</h3>
            <p class="text-sm text-gray-400 mb-6 leading-relaxed">این لینک شامل چندین کانکشن هوشمند (VLESS, Trojan xHTTP/WS) و یک تونل اختصاصی Shadowsocks AEAD است که در نرم‌افزارهای V2rayNG, Nekobox و Streisand به صورت خودکار ایمپورت می‌شود.</p>
            
            <div class="bg-neutral-950 p-5 rounded-xl border border-neutral-800 font-mono text-sm break-all mb-6 select-all relative group cursor-text shadow-inner" id="sub-link-display">
                https://example.com/sub/...
                <div class="absolute inset-0 bg-primary/5 opacity-0 group-hover:opacity-100 transition pointer-events-none rounded-xl"></div>
            </div>
            <button onclick="copySubLink()" class="btn-primary w-full py-4 rounded-xl text-lg flex items-center justify-center gap-2 shadow-lg">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3"></path></svg>
                کپی کردن لینک در کلیپ‌بورد
            </button>
        </div>
    </div>

    <script>
        // UI Navigation
        function showTab(tab) {
            document.getElementById('tab-dashboard').classList.add('hidden');
            document.getElementById('tab-links').classList.add('hidden');
            document.getElementById(`tab-${tab}`).classList.remove('hidden');
            
            // Update sidebar active states
            document.querySelectorAll('aside nav button').forEach(b => {
                b.className = "w-full flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-xl text-gray-400 hover:bg-neutral-800 hover:text-white transition";
            });
            const activeBtn = document.getElementById(`nav-${tab}`);
            if(activeBtn) activeBtn.className = "w-full flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-xl bg-primary/10 text-primary transition";

            if(tab === 'dashboard') loadStats();
            if(tab === 'links') loadLinks();
        }

        // Utils
        function formatBytes(bytes) {
            if (bytes === 0) return '0 B';
            const k = 1024, sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }

        // API Helper
        async function fetchAPI(endpoint, method = 'GET', body = null) {
            const opts = { method, headers: {'Content-Type': 'application/json'} };
            if (body) opts.body = JSON.stringify(body);
            const res = await fetch(`/api/panel${endpoint}`, opts);
            return res.json();
        }

        // Chart Initialization
        let trafficChart;
        const chartData = { labels: [], datasets: [{ label: 'ترافیک لحظه‌ای (MB)', data: [], borderColor: '#3b82f6', backgroundColor: 'rgba(59, 130, 246, 0.1)', borderWidth: 2, fill: true, tension: 0.4 }] };

        function initChart() {
            const ctx = document.getElementById('trafficChart').getContext('2d');
            Chart.defaults.color = '#666';
            Chart.defaults.font.family = 'Vazirmatn';
            trafficChart = new Chart(ctx, {
                type: 'line',
                data: chartData,
                options: {
                    responsive: true, maintainAspectRatio: false,
                    plugins: { legend: { display: false } },
                    scales: {
                        y: { beginAtZero: true, grid: { color: '#222' } },
                        x: { grid: { display: false } }
                    },
                    animation: { duration: 0 }
                }
            });
        }
        initChart();

        // System Polling Loop
        let lastTraffic = 0;
        async function loadStats() {
            if(document.getElementById('tab-dashboard').classList.contains('hidden')) return;
            try {
                const data = await fetchAPI('/stats');
                document.getElementById('stat-traffic').innerText = formatBytes(data.total_traffic_bytes);
                document.getElementById('stat-online').innerText = data.online_users;
                
                // Update System Vitals
                if(data.system) {
                    document.getElementById('sys-cpu').innerText = data.system.cpu;
                    document.getElementById('bar-cpu').style.width = `${data.system.cpu}%`;
                    document.getElementById('sys-ram').innerText = data.system.ram;
                    document.getElementById('bar-ram').style.width = `${data.system.ram}%`;
                }

                // Update Chart
                const now = new Date();
                const timeStr = `${now.getHours()}:${now.getMinutes()}:${now.getSeconds()}`;
                const currentTrafficMB = data.total_traffic_bytes / (1024*1024);
                let diff = currentTrafficMB - lastTraffic;
                if (lastTraffic === 0) diff = 0; // First load
                lastTraffic = currentTrafficMB;

                if(chartData.labels.length > 15) { chartData.labels.shift(); chartData.datasets[0].data.shift(); }
                chartData.labels.push(timeStr);
                chartData.datasets[0].data.push(diff);
                trafficChart.update();

                // Update Terminal Log
                const term = document.getElementById('live-logs');
                if(data.active_connections && data.active_connections.length > 0) {
                    const conn = data.active_connections[Math.floor(Math.random() * data.active_connections.length)];
                    const div = document.createElement('div');
                    div.innerHTML = `<span class="text-blue-400">[${timeStr}]</span> Connection via <span class="text-yellow-400">${conn.transport}</span> from IP <span class="text-white">${conn.ip}</span> [${formatBytes(conn.bytes)}]`;
                    term.appendChild(div);
                    if(term.childElementCount > 20) term.removeChild(term.firstChild);
                    term.scrollTop = term.scrollHeight;
                }

            } catch(e) { console.error(e); }
        }
        
        setInterval(loadStats, 3000); // 3-second live update

        // Link Management
        async function loadLinks() {
            try {
                const data = await fetchAPI('/links');
                const tbody = document.getElementById('links-tbody');
                tbody.innerHTML = '';
                
                Object.entries(data.links).sort((a,b) => new Date(b[1].created_at) - new Date(a[1].created_at)).forEach(([uid, l]) => {
                    const limitTxt = l.limit_bytes === 0 ? '∞ نامحدود' : formatBytes(l.limit_bytes);
                    const usedTxt = formatBytes(l.used_bytes);
                    const pct = l.limit_bytes === 0 ? 0 : Math.min(100, (l.used_bytes / l.limit_bytes) * 100);
                    const isOk = l.active && (l.limit_bytes === 0 || l.used_bytes < l.limit_bytes);
                    
                    const statusDot = isOk ? '<span class="flex items-center gap-1.5 text-emerald-400 bg-emerald-400/10 px-2.5 py-1 rounded-md text-xs font-bold w-max"><span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>متصل</span>' 
                                           : '<span class="flex items-center gap-1.5 text-red-400 bg-red-400/10 px-2.5 py-1 rounded-md text-xs font-bold w-max"><span class="w-2 h-2 rounded-full bg-red-400"></span>مسدود</span>';
                    
                    const tr = document.createElement('tr');
                    tr.className = 'hover:bg-neutral-900/50 transition duration-200';
                    tr.innerHTML = `
                        <td class="p-5 font-bold text-white text-base">
                            ${l.label}
                            <div class="text-[10px] text-gray-500 font-mono mt-1 opacity-50">${uid}</div>
                        </td>
                        <td class="p-5">
                            <div class="text-gray-300 font-mono text-sm mb-1.5">${usedTxt} <span class="text-gray-600">/</span> ${limitTxt}</div>
                            <div class="w-32 bg-neutral-800 h-1.5 rounded-full overflow-hidden"><div class="bg-blue-500 h-full rounded-full" style="width: ${pct}%"></div></div>
                        </td>
                        <td class="p-5">${statusDot}</td>
                        <td class="p-5 text-center">
                            <div class="flex items-center justify-center gap-2">
                                <button onclick="showSubModal('${uid}')" class="text-xs bg-primary/20 text-primary hover:bg-primary hover:text-white px-4 py-2 rounded-lg transition font-bold shadow-lg shadow-primary/10">سابسکرایپشن</button>
                                <button onclick="deleteLink('${uid}')" class="text-xs bg-red-500/10 text-red-500 hover:bg-red-500 hover:text-white px-4 py-2 rounded-lg transition font-bold">حذف</button>
                            </div>
                        </td>
                    `;
                    tbody.appendChild(tr);
                });
            } catch(e) { console.error(e); }
        }

        async function createMultipack(e) {
            e.preventDefault();
            const btn = e.target.querySelector('button[type="submit"]');
            const originalText = btn.innerHTML;
            btn.innerHTML = '<span class="animate-spin text-xl">↻</span> در حال پیکربندی...';
            btn.disabled = true;
            
            const payload = {
                label: document.getElementById('mp-label').value,
                limit_gb: parseFloat(document.getElementById('mp-volume').value),
                days: parseInt(document.getElementById('mp-days').value)
            };

            try {
                const res = await fetchAPI('/multipack', 'POST', payload);
                if(res.ok) {
                    const term = document.getElementById('live-logs');
                    term.innerHTML += `<div class="text-green-400">[System] User ${payload.label} generated successfully with Shadowsocks AEAD.</div>`;
                    document.getElementById('multipack-form').reset();
                    showSubModal(res.uuid); // Automatically show sub link
                }
            } catch(err) {
                alert('خطا در ارتباط با سرور.');
            }
            btn.innerHTML = originalText;
            btn.disabled = false;
        }

        async function deleteLink(uid) {
            if(!confirm('هشدار: آیا از حذف دائمی این کاربر مطمئن هستید؟ تمام اتصالات فورا قطع خواهند شد.')) return;
            await fetchAPI(`/links/${uid}`, 'DELETE');
            loadLinks();
        }

        function showSubModal(uid) {
            const host = window.location.host;
            const subUrl = `https://${host}/sub/${uid}`;
            document.getElementById('sub-link-display').innerText = subUrl;
            document.getElementById('sub-modal').classList.remove('hidden');
        }

        function closeModal() {
            document.getElementById('sub-modal').classList.add('hidden');
        }

        function copySubLink() {
            const text = document.getElementById('sub-link-display').innerText;
            navigator.clipboard.writeText(text);
            const btn = document.querySelector('#sub-modal .btn-primary');
            const orig = btn.innerHTML;
            btn.innerHTML = '✅ کپی شد!';
            setTimeout(() => btn.innerHTML = orig, 2000);
        }

        // Startup
        loadStats();
    </script>
</body>
</html>
"""

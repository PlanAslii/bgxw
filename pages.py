# pages.py
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="fa" dir="rtl" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>X4G Core - Dark Edition</title>
    <script src="https://cdn.tailwindcss.com"></script>
    <script>
        tailwind.config = {
            darkMode: 'class',
            theme: {
                extend: {
                    colors: {
                        black: '#050505',
                        neutral: { 850: '#1a1a1a', 900: '#121212', 950: '#0a0a0a' }
                    },
                    fontFamily: { sans: ['Tahoma', 'Arial', 'sans-serif'] }
                }
            }
        }
    </script>
    <style>
        body { background-color: #000; color: #fff; }
        .glass-panel { background: rgba(20, 20, 20, 0.7); backdrop-filter: blur(10px); border: 1px solid #333; }
        .btn-primary { background: #fff; color: #000; transition: all 0.2s; font-weight: bold; }
        .btn-primary:hover { background: #ccc; }
        .btn-danger { background: #dc2626; color: #fff; }
        .btn-danger:hover { background: #b91c1c; }
        input, select { background: #111; border: 1px solid #333; color: white; padding: 0.5rem; border-radius: 0.375rem; width: 100%; outline: none; }
        input:focus, select:focus { border-color: #666; }
        .fade-in { animation: fadeIn 0.3s ease-in-out; }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: translateY(0); } }
    </style>
</head>
<body class="min-h-screen font-sans selection:bg-white selection:text-black">
    
    <!-- Navbar -->
    <nav class="glass-panel sticky top-0 z-50 px-6 py-4 flex justify-between items-center shadow-md">
        <div class="text-2xl font-extrabold tracking-tighter">X4G <span class="text-gray-500 font-light">CORE</span></div>
        <div class="flex gap-4">
            <button onclick="showTab('dashboard')" class="text-sm font-medium text-gray-300 hover:text-white transition">داشبورد</button>
            <button onclick="showTab('links')" class="text-sm font-medium text-gray-300 hover:text-white transition">مدیریت کانفیگ‌ها</button>
        </div>
    </nav>

    <main class="container mx-auto p-6 max-w-5xl mt-6 fade-in">
        
        <!-- Tab: Dashboard -->
        <div id="tab-dashboard" class="space-y-8">
            <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
                <div class="glass-panel p-6 rounded-2xl flex flex-col items-center justify-center text-center">
                    <div class="text-gray-400 text-sm mb-2">تعداد کل کانفیگ‌ها</div>
                    <div class="text-4xl font-bold" id="stat-links">0</div>
                </div>
                <div class="glass-panel p-6 rounded-2xl flex flex-col items-center justify-center text-center">
                    <div class="text-gray-400 text-sm mb-2">ترافیک مصرفی کل</div>
                    <div class="text-4xl font-bold" id="stat-traffic">0 GB</div>
                </div>
                <div class="glass-panel p-6 rounded-2xl flex flex-col items-center justify-center text-center">
                    <div class="text-gray-400 text-sm mb-2">کاربران آنلاین</div>
                    <div class="text-4xl font-bold" id="stat-online">0</div>
                </div>
            </div>

            <!-- Multi-pack Generator -->
            <div class="glass-panel p-8 rounded-2xl border border-neutral-800">
                <h2 class="text-xl font-bold mb-6 flex items-center gap-2">
                    <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13 10V3L4 14h7v7l9-11h-7z"></path></svg>
                    ساخت مولتی‌پک (Multi-Protocol Config)
                </h2>
                <p class="text-gray-400 text-sm mb-6">با این ابزار یک گروه حاوی کانفیگ‌های VLESS و Trojan (نسخه‌های WS و xHTTP) ساخته می‌شود که همگی از یک حجم مشترک استفاده می‌کنند.</p>
                
                <form id="multipack-form" class="grid grid-cols-1 md:grid-cols-2 gap-6" onsubmit="createMultipack(event)">
                    <div>
                        <label class="block text-sm text-gray-400 mb-1">نام/شناسه کاربر</label>
                        <input type="text" id="mp-label" required placeholder="مثال: Ali-VIP">
                    </div>
                    <div>
                        <label class="block text-sm text-gray-400 mb-1">حجم ترافیک (گیگابایت) - 0 برای نامحدود</label>
                        <input type="number" id="mp-volume" min="0" value="50" required>
                    </div>
                    <div>
                        <label class="block text-sm text-gray-400 mb-1">اعتبار (روز) - 0 برای نامحدود</label>
                        <input type="number" id="mp-days" min="0" value="30" required>
                    </div>
                    <div class="flex items-end">
                        <button type="submit" class="btn-primary w-full py-2.5 rounded-lg">🚀 ایجاد گروه مولتی پروتکل</button>
                    </div>
                </form>
            </div>
        </div>

        <!-- Tab: Links Management -->
        <div id="tab-links" class="hidden space-y-6">
            <div class="flex justify-between items-center">
                <h2 class="text-2xl font-bold">مدیریت کانفیگ‌ها و پک‌ها</h2>
                <button onclick="loadLinks()" class="text-sm text-gray-400 hover:text-white underline">🔄 رفرش لیست</button>
            </div>
            <div class="glass-panel rounded-2xl overflow-hidden">
                <table class="w-full text-right text-sm">
                    <thead class="bg-neutral-900 border-b border-neutral-800 text-gray-400">
                        <tr>
                            <th class="p-4">نام</th>
                            <th class="p-4">مصرف / کل</th>
                            <th class="p-4">وضعیت</th>
                            <th class="p-4 text-center">عملیات</th>
                        </tr>
                    </thead>
                    <tbody id="links-tbody" class="divide-y divide-neutral-800">
                        <!-- Rows will be injected here via JS -->
                    </tbody>
                </table>
            </div>
        </div>

    </main>

    <!-- Modal for showing Subscription Link -->
    <div id="sub-modal" class="fixed inset-0 bg-black/80 backdrop-blur-sm hidden z-50 flex items-center justify-center">
        <div class="glass-panel p-8 rounded-2xl max-w-lg w-full m-4 shadow-2xl relative fade-in">
            <button onclick="closeModal()" class="absolute top-4 left-4 text-gray-400 hover:text-white">✕</button>
            <h3 class="text-xl font-bold mb-4">لینک سابسکرایپشن</h3>
            <p class="text-sm text-gray-400 mb-6">این لینک را کپی کرده و در برنامه‌هایی مثل V2rayNG, Nekobox یا Streisand وارد کنید. این ساب شامل تمامی پروتکل‌های VLESS و Trojan است.</p>
            <div class="bg-black p-4 rounded-lg border border-neutral-800 font-mono text-sm break-all mb-4 select-all" id="sub-link-display">
                https://example.com/sub/...
            </div>
            <button onclick="copySubLink()" class="btn-primary w-full py-2 rounded-lg">کپی کردن لینک</button>
        </div>
    </div>

    <script>
        function showTab(tab) {
            document.getElementById('tab-dashboard').classList.add('hidden');
            document.getElementById('tab-links').classList.add('hidden');
            document.getElementById(`tab-${tab}`).classList.remove('hidden');
            if(tab === 'dashboard') loadStats();
            if(tab === 'links') loadLinks();
        }

        function formatBytes(bytes) {
            if (bytes === 0) return '0 B';
            const k = 1024, sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }

        async function fetchAPI(endpoint, method = 'GET', body = null) {
            const opts = { method, headers: {'Content-Type': 'application/json'} };
            if (body) opts.body = JSON.stringify(body);
            const res = await fetch(`/api/panel${endpoint}`, opts);
            return res.json();
        }

        async function loadStats() {
            try {
                const data = await fetchAPI('/stats');
                document.getElementById('stat-links').innerText = data.total_links;
                document.getElementById('stat-traffic').innerText = formatBytes(data.total_traffic_bytes);
                document.getElementById('stat-online').innerText = data.online_users;
            } catch(e) { console.error(e); }
        }

        async function loadLinks() {
            try {
                const data = await fetchAPI('/links');
                const tbody = document.getElementById('links-tbody');
                tbody.innerHTML = '';
                
                Object.entries(data.links).forEach(([uid, l]) => {
                    const limitTxt = l.limit_bytes === 0 ? 'نامحدود' : formatBytes(l.limit_bytes);
                    const usedTxt = formatBytes(l.used_bytes);
                    const isOk = l.active && (l.limit_bytes === 0 || l.used_bytes < l.limit_bytes);
                    const statusDot = isOk ? '<span class="text-green-500">🟢 فعال</span>' : '<span class="text-red-500">🔴 قطع</span>';
                    
                    const tr = document.createElement('tr');
                    tr.className = 'hover:bg-neutral-900 transition';
                    tr.innerHTML = `
                        <td class="p-4 font-medium">${l.label}</td>
                        <td class="p-4 text-gray-300 font-mono text-xs">${usedTxt} / ${limitTxt}</td>
                        <td class="p-4">${statusDot}</td>
                        <td class="p-4 text-center space-x-2 space-x-reverse">
                            <button onclick="showSubModal('${uid}')" class="text-xs bg-neutral-800 hover:bg-neutral-700 px-3 py-1.5 rounded transition">لینک ساب</button>
                            <button onclick="deleteLink('${uid}')" class="text-xs text-red-400 hover:text-red-300 bg-red-950/30 px-3 py-1.5 rounded transition">حذف</button>
                        </td>
                    `;
                    tbody.appendChild(tr);
                });
            } catch(e) { console.error(e); }
        }

        async function createMultipack(e) {
            e.preventDefault();
            const btn = e.target.querySelector('button[type="submit"]');
            btn.innerText = 'در حال ساخت...';
            btn.disabled = true;
            
            const payload = {
                label: document.getElementById('mp-label').value,
                limit_gb: parseFloat(document.getElementById('mp-volume').value),
                days: parseInt(document.getElementById('mp-days').value)
            };

            try {
                const res = await fetchAPI('/multipack', 'POST', payload);
                if(res.ok) {
                    alert('پک با موفقیت ساخته شد!');
                    document.getElementById('multipack-form').reset();
                    loadStats();
                } else {
                    alert('خطا در ساخت پک');
                }
            } catch(err) {
                console.error(err);
                alert('ارتباط با سرور قطع است');
            }
            btn.innerText = '🚀 ایجاد گروه مولتی پروتکل';
            btn.disabled = false;
        }

        async function deleteLink(uid) {
            if(!confirm('آیا از حذف این کانفیگ مطمئن هستید؟')) return;
            await fetchAPI(`/links/${uid}`, 'DELETE');
            loadLinks();
            loadStats();
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
            alert('لینک کپی شد!');
        }

        // Initialize
        loadStats();
    </script>
</body>
</html>
"""

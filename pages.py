# pages.py
DASHBOARD_HTML = """
<!DOCTYPE html>
<html lang="fa" dir="rtl" class="dark">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>OXNet Core Pro - Advanced Dashboard</title>
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
        .btn-success { background: linear-gradient(135deg, #10b981 0%, #059669 100%); color: #fff; }
        .btn-success:hover { filter: brightness(1.2); }
        input, select { background: #0a0a0a; border: 1px solid #333; color: white; padding: 0.6rem 1rem; border-radius: 0.5rem; width: 100%; outline: none; transition: border 0.2s; }
        input:focus, select:focus { border-color: #3b82f6; box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.2); }
        .fade-in { animation: fadeIn 0.4s cubic-bezier(0.4, 0, 0.2, 1); }
        @keyframes fadeIn { from { opacity: 0; transform: translateY(15px); } to { opacity: 1; transform: translateY(0); } }
        ::-webkit-scrollbar { width: 8px; height: 8px; }
        ::-webkit-scrollbar-track { background: #050505; }
        ::-webkit-scrollbar-thumb { background: #333; border-radius: 4px; }
        ::-webkit-scrollbar-thumb:hover { background: #555; }
        .terminal { background: #0a0a0a; font-family: 'Fira Code', monospace; color: #4ade80; border: 1px solid #222; }
        .stat-card { position: relative; overflow: hidden; }
        .stat-card::after { content: ''; position: absolute; top: 0; left: 0; width: 100%; height: 2px; background: linear-gradient(90deg, transparent, var(--color), transparent); opacity: 0.5; }
        
        /* مودال ویرایش */
        .modal-overlay { background: rgba(0,0,0,0.8); backdrop-filter: blur(8px); }
        .modal-content { max-height: 90vh; overflow-y: auto; }
        
        /* لاگین فرم */
        .login-form { max-width: 400px; margin: 0 auto; }
        
        /* نشانگر پروتکل */
        .protocol-badge { display: inline-block; padding: 2px 10px; border-radius: 12px; font-size: 10px; font-weight: bold; }
        .protocol-vless { background: #3b82f6; color: #fff; }
        .protocol-trojan { background: #8b5cf6; color: #fff; }
        .protocol-vmess { background: #10b981; color: #fff; }
        .protocol-ss { background: #f59e0b; color: #fff; }
        .protocol-mtproto { background: #ef4444; color: #fff; }
    </style>
</head>
<body class="min-h-screen flex selection:bg-primary selection:text-white">
    
    <!-- Modal Login -->
    <div id="login-modal" class="fixed inset-0 bg-black/90 backdrop-blur-md z-50 flex items-center justify-center p-4">
        <div class="glass-panel p-8 rounded-3xl max-w-md w-full fade-in border border-primary/30 shadow-2xl shadow-primary/20">
            <div class="text-center mb-8">
                <div class="w-16 h-16 bg-primary/20 text-primary rounded-2xl flex items-center justify-center mx-auto mb-4 text-3xl font-bold">OX</div>
                <h2 class="text-2xl font-black">ورود به پنل OXNet</h2>
                <p class="text-sm text-gray-400 mt-2">لطفاً رمز عبور خود را وارد کنید</p>
                <div id="default-pass-hint" class="mt-2 text-xs text-yellow-500 bg-yellow-500/10 p-2 rounded-lg hidden">
                    رمز پیش‌فرض: <span id="default-pass-display" class="font-mono font-bold"></span>
                </div>
            </div>
            <form id="login-form" onsubmit="login(event)" class="space-y-4">
                <div>
                    <label class="block text-xs font-semibold text-gray-400 mb-1">رمز عبور</label>
                    <input type="password" id="login-password" required placeholder="رمز عبور خود را وارد کنید" class="text-center">
                </div>
                <button type="submit" class="btn-primary w-full py-3 rounded-xl text-lg">ورود به پنل</button>
                <div id="login-error" class="text-red-500 text-sm text-center hidden"></div>
            </form>
        </div>
    </div>

    <aside class="w-64 glass-panel border-l border-neutral-800 hidden md:flex flex-col h-screen sticky top-0 z-40">
        <div class="p-6 border-b border-neutral-800 flex items-center justify-center gap-3">
            <div class="w-10 h-10 rounded-xl bg-gradient-to-br from-primary to-blue-800 flex items-center justify-center font-bold text-xl shadow-lg shadow-blue-900/50">OX</div>
            <div class="text-2xl font-black tracking-tighter">OXNet <span class="text-primary font-light">PRO</span></div>
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
            <button onclick="showTab('settings')" id="nav-settings" class="w-full flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-xl text-gray-400 hover:bg-neutral-800 hover:text-white transition">
                <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z"></path><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"></path></svg>
                تنظیمات
            </button>
        </nav>
        <div class="p-4 border-t border-neutral-800">
            <div class="text-xs text-center text-gray-500">هسته هوشمند OXNet-Core v4.0</div>
            <div class="text-xs text-center text-gray-600 mt-1">VLESS • Trojan • VMESS • SS • MTProto</div>
        </div>
    </aside>

    <main class="flex-1 overflow-y-auto" id="main-content">
        <nav class="md:hidden glass-panel sticky top-0 z-50 px-4 py-3 flex justify-between items-center">
            <div class="text-xl font-black">OXNet <span class="text-primary font-light">PRO</span></div>
            <div class="flex gap-2">
                <button onclick="showTab('dashboard')" class="text-xs font-medium text-gray-300 bg-neutral-800 px-3 py-1.5 rounded">داشبورد</button>
                <button onclick="showTab('links')" class="text-xs font-medium text-gray-300 bg-neutral-800 px-3 py-1.5 rounded">مدیریت</button>
                <button onclick="showTab('settings')" class="text-xs font-medium text-gray-300 bg-neutral-800 px-3 py-1.5 rounded">تنظیمات</button>
            </div>
        </nav>

        <div class="container mx-auto p-4 md:p-8 max-w-7xl" id="tabs-container">
            
            <!-- Tab Dashboard -->
            <div id="tab-dashboard" class="space-y-8 fade-in">
                <div class="grid grid-cols-2 md:grid-cols-5 gap-4">
                    <div class="glass-panel stat-card p-5 rounded-2xl flex flex-col" style="--color: #3b82f6;">
                        <div class="text-gray-400 text-xs font-bold uppercase tracking-wider mb-2">CPU</div>
                        <div class="text-3xl font-black flex items-end gap-1"><span id="sys-cpu">0</span><span class="text-lg text-gray-500 font-normal">%</span></div>
                        <div class="w-full bg-neutral-800 h-1.5 rounded-full mt-3 overflow-hidden"><div id="bar-cpu" class="bg-primary h-full rounded-full transition-all duration-1000" style="width: 0%"></div></div>
                    </div>
                    <div class="glass-panel stat-card p-5 rounded-2xl flex flex-col" style="--color: #8b5cf6;">
                        <div class="text-gray-400 text-xs font-bold uppercase tracking-wider mb-2">RAM</div>
                        <div class="text-3xl font-black flex items-end gap-1"><span id="sys-ram">0</span><span class="text-lg text-gray-500 font-normal">%</span></div>
                        <div class="w-full bg-neutral-800 h-1.5 rounded-full mt-3 overflow-hidden"><div id="bar-ram" class="bg-purple-500 h-full rounded-full transition-all duration-1000" style="width: 0%"></div></div>
                    </div>
                    <div class="glass-panel stat-card p-5 rounded-2xl flex flex-col" style="--color: #10b981;">
                        <div class="text-gray-400 text-xs font-bold uppercase tracking-wider mb-2">آنلاین</div>
                        <div class="text-3xl font-black text-accent" id="stat-online">0</div>
                    </div>
                    <div class="glass-panel stat-card p-5 rounded-2xl flex flex-col" style="--color: #f59e0b;">
                        <div class="text-gray-400 text-xs font-bold uppercase tracking-wider mb-2">ترافیک کل</div>
                        <div class="text-3xl font-black text-yellow-500" id="stat-traffic">0 GB</div>
                    </div>
                    <div class="glass-panel stat-card p-5 rounded-2xl flex flex-col" style="--color: #ef4444;">
                        <div class="text-gray-400 text-xs font-bold uppercase tracking-wider mb-2">کانفیگ‌ها</div>
                        <div class="text-3xl font-black text-red-500" id="stat-links">0</div>
                    </div>
                </div>

                <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
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
                        <h2 class="text-lg font-bold mb-5 relative z-10">🚀 ساخت مولتی‌پک</h2>
                        <p class="text-xs text-gray-400 mb-5 leading-relaxed relative z-10">شامل: VLESS, Trojan, VMESS, Shadowsocks, MTProto</p>
                        
                        <form id="multipack-form" class="space-y-4 relative z-10" onsubmit="createMultipack(event)">
                            <div>
                                <label class="block text-xs font-semibold text-gray-400 mb-1">نام کاربر</label>
                                <input type="text" id="mp-label" required placeholder="User-XYZ">
                            </div>
                            <div class="grid grid-cols-2 gap-4">
                                <div>
                                    <label class="block text-xs font-semibold text-gray-400 mb-1">حجم (GB)</label>
                                    <input type="number" id="mp-volume" min="0" value="50" required>
                                </div>
                                <div>
                                    <label class="block text-xs font-semibold text-gray-400 mb-1">اعتبار (روز)</label>
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
                    <h3 class="text-lg font-bold mb-4">🖥️ ترمینال زنده</h3>
                    <div class="terminal rounded-xl p-4 h-48 overflow-y-auto text-xs leading-relaxed" id="live-logs">
                        <div class="text-gray-500"># OXNet Core Initialized. Awaiting connections...</div>
                    </div>
                </div>
            </div>

            <!-- Tab Links -->
            <div id="tab-links" class="hidden space-y-6 fade-in">
                <div class="flex flex-col md:flex-row justify-between items-start md:items-center gap-4">
                    <div>
                        <h2 class="text-2xl font-black">مدیریت کانفیگ‌ها</h2>
                        <p class="text-gray-400 text-sm mt-1">کنترل کامل روی حجم، زمان و دسترسی‌ها</p>
                    </div>
                    <button onclick="loadLinks()" class="btn-primary px-4 py-2 rounded-lg text-sm flex items-center gap-2">
                        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
                        بروزرسانی
                    </button>
                </div>
                <div class="glass-panel rounded-2xl overflow-hidden border border-neutral-800">
                    <div class="overflow-x-auto">
                        <table class="w-full text-right text-sm whitespace-nowrap">
                            <thead class="bg-neutral-900/80 border-b border-neutral-800 text-gray-400 text-xs uppercase tracking-wider">
                                <tr>
                                    <th class="p-5 font-semibold">شناسه / نام</th>
                                    <th class="p-5 font-semibold">مصرف</th>
                                    <th class="p-5 font-semibold">وضعیت</th>
                                    <th class="p-5 font-semibold">پروتکل‌ها</th>
                                    <th class="p-5 font-semibold text-center">عملیات</th>
                                </tr>
                            </thead>
                            <tbody id="links-tbody" class="divide-y divide-neutral-800">
                            </tbody>
                        </table>
                    </div>
                </div>
            </div>

            <!-- Tab Settings -->
            <div id="tab-settings" class="hidden space-y-6 fade-in">
                <h2 class="text-2xl font-black">تنظیمات پنل</h2>
                
                <div class="glass-panel p-6 rounded-2xl max-w-lg">
                    <h3 class="text-lg font-bold mb-4">🔐 تغییر رمز عبور</h3>
                    <form id="change-password-form" onsubmit="changePassword(event)" class="space-y-4">
                        <div>
                            <label class="block text-xs font-semibold text-gray-400 mb-1">رمز فعلی</label>
                            <input type="password" id="old-password" required>
                        </div>
                        <div>
                            <label class="block text-xs font-semibold text-gray-400 mb-1">رمز جدید</label>
                            <input type="password" id="new-password" required minlength="6">
                        </div>
                        <div>
                            <label class="block text-xs font-semibold text-gray-400 mb-1">تکرار رمز جدید</label>
                            <input type="password" id="confirm-password" required>
                        </div>
                        <button type="submit" class="btn-success w-full py-3 rounded-xl">تغییر رمز عبور</button>
                        <div id="password-result" class="text-sm text-center hidden"></div>
                    </form>
                </div>
                
                <div class="glass-panel p-6 rounded-2xl max-w-lg">
                    <h3 class="text-lg font-bold mb-4">📊 اطلاعات سیستم</h3>
                    <div class="space-y-2 text-sm">
                        <div class="flex justify-between border-b border-neutral-800 pb-2">
                            <span class="text-gray-400">نسخه هسته</span>
                            <span class="font-mono">OXNet-Core v4.0</span>
                        </div>
                        <div class="flex justify-between border-b border-neutral-800 pb-2">
                            <span class="text-gray-400">پروتکل‌های پشتیبانی شده</span>
                            <span class="font-mono text-xs">VLESS, Trojan, VMESS, SS, MTProto</span>
                        </div>
                        <div class="flex justify-between border-b border-neutral-800 pb-2">
                            <span class="text-gray-400">تعداد کانفیگ‌ها</span>
                            <span id="settings-link-count" class="font-mono">0</span>
                        </div>
                        <div class="flex justify-between">
                            <span class="text-gray-400">کاربران آنلاین</span>
                            <span id="settings-online-count" class="font-mono">0</span>
                        </div>
                    </div>
                </div>
            </div>

        </div>
    </main>

    <!-- Modal Subscription -->
    <div id="sub-modal" class="fixed inset-0 bg-black/90 backdrop-blur-md hidden z-50 flex items-center justify-center p-4">
        <div class="glass-panel p-6 md:p-8 rounded-3xl max-w-2xl w-full relative fade-in border border-primary/30 shadow-2xl shadow-primary/20">
            <button onclick="closeModal()" class="absolute top-5 left-5 w-8 h-8 flex items-center justify-center rounded-full bg-neutral-800 text-gray-400 hover:text-white transition">✕</button>
            <div class="w-12 h-12 bg-primary/20 text-primary rounded-2xl flex items-center justify-center mb-6">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"></path></svg>
            </div>
            <h3 class="text-2xl font-black mb-2">لینک سابسکرایپشن</h3>
            <p class="text-sm text-gray-400 mb-6 leading-relaxed">شامل VLESS, Trojan, VMESS, Shadowsocks, MTProto</p>
            
            <div class="bg-neutral-950 p-5 rounded-xl border border-neutral-800 font-mono text-sm break-all mb-6 select-all relative group cursor-text shadow-inner" id="sub-link-display">
                https://example.com/sub/...
            </div>
            <button onclick="copySubLink()" class="btn-primary w-full py-4 rounded-xl text-lg flex items-center justify-center gap-2 shadow-lg">
                <svg class="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M8 5H6a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2v-1M8 5a2 2 0 002 2h2a2 2 0 002-2M8 5a2 2 0 012-2h2a2 2 0 012 2m0 0h2a2 2 0 012 2v3m2 4H10m0 0l3-3m-3 3l3 3"></path></svg>
                کپی لینک
            </button>
        </div>
    </div>

    <!-- Modal Edit -->
    <div id="edit-modal" class="fixed inset-0 bg-black/90 backdrop-blur-md hidden z-50 flex items-center justify-center p-4">
        <div class="glass-panel p-6 md:p-8 rounded-3xl max-w-lg w-full relative fade-in border border-primary/30 shadow-2xl shadow-primary/20 modal-content">
            <button onclick="closeEditModal()" class="absolute top-5 left-5 w-8 h-8 flex items-center justify-center rounded-full bg-neutral-800 text-gray-400 hover:text-white transition">✕</button>
            <h3 class="text-2xl font-black mb-2">✏️ ویرایش کانفیگ</h3>
            <p class="text-sm text-gray-400 mb-6">تغییرات را اعمال کنید</p>
            
            <form id="edit-form" onsubmit="saveEdit(event)" class="space-y-4">
                <input type="hidden" id="edit-uid">
                <div>
                    <label class="block text-xs font-semibold text-gray-400 mb-1">نام کاربر</label>
                    <input type="text" id="edit-label" required>
                </div>
                <div class="grid grid-cols-2 gap-4">
                    <div>
                        <label class="block text-xs font-semibold text-gray-400 mb-1">حجم (GB)</label>
                        <input type="number" id="edit-volume" min="0" required>
                    </div>
                    <div>
                        <label class="block text-xs font-semibold text-gray-400 mb-1">اعتبار (روز)</label>
                        <input type="number" id="edit-days" min="0" required>
                    </div>
                </div>
                <div>
                    <label class="block text-xs font-semibold text-gray-400 mb-1">حداکثر IP همزمان</label>
                    <input type="number" id="edit-ip-limit" min="0" value="0">
                </div>
                <div>
                    <label class="block text-xs font-semibold text-gray-400 mb-1">محدودیت سرعت (KB/s)</label>
                    <input type="number" id="edit-speed-limit" min="0" value="0">
                </div>
                <div class="flex items-center gap-3">
                    <input type="checkbox" id="edit-active" class="w-5 h-5 accent-primary">
                    <label for="edit-active" class="text-sm text-gray-300">فعال</label>
                </div>
                <div class="flex gap-3 pt-2">
                    <button type="submit" class="btn-success flex-1 py-3 rounded-xl">ذخیره تغییرات</button>
                    <button type="button" onclick="closeEditModal()" class="btn-danger flex-1 py-3 rounded-xl">انصراف</button>
                </div>
                <div id="edit-result" class="text-sm text-center hidden"></div>
            </form>
        </div>
    </div>

    <script>
        // --- State ---
        let authToken = localStorage.getItem('oxnet_token') || '';
        let isAuthenticated = false;

        // --- Authentication ---
        async function login(event) {
            event.preventDefault();
            const password = document.getElementById('login-password').value;
            const errorEl = document.getElementById('login-error');
            
            try {
                const res = await fetch('/api/auth/login', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({password})
                });
                const data = await res.json();
                
                if (data.ok) {
                    authToken = data.token;
                    localStorage.setItem('oxnet_token', authToken);
                    isAuthenticated = true;
                    document.getElementById('login-modal').style.display = 'none';
                    loadStats();
                    loadLinks();
                } else {
                    errorEl.textContent = '❌ رمز عبور اشتباه است';
                    errorEl.classList.remove('hidden');
                }
            } catch(e) {
                errorEl.textContent = '❌ خطا در ارتباط با سرور';
                errorEl.classList.remove('hidden');
            }
        }

        async function checkAuth() {
            // Check if we have a token and try to load stats
            if (authToken) {
                try {
                    const res = await fetch('/api/panel/stats', {
                        headers: {'Authorization': 'Basic ' + btoa('admin:' + authToken)}
                    });
                    if (res.ok) {
                        isAuthenticated = true;
                        document.getElementById('login-modal').style.display = 'none';
                        loadStats();
                        loadLinks();
                        return true;
                    }
                } catch(e) {}
            }
            
            // Check default password
            try {
                const res = await fetch('/api/auth/default-password');
                const data = await res.json();
                if (data.default_password) {
                    document.getElementById('default-pass-hint').classList.remove('hidden');
                    document.getElementById('default-pass-display').textContent = data.default_password;
                }
            } catch(e) {}
            
            document.getElementById('login-modal').style.display = 'flex';
            return false;
        }

        async function changePassword(event) {
            event.preventDefault();
            const oldPass = document.getElementById('old-password').value;
            const newPass = document.getElementById('new-password').value;
            const confirmPass = document.getElementById('confirm-password').value;
            const resultEl = document.getElementById('password-result');
            
            if (newPass !== confirmPass) {
                resultEl.textContent = '❌ رمزهای جدید مطابقت ندارند';
                resultEl.className = 'text-sm text-center text-red-500';
                resultEl.classList.remove('hidden');
                return;
            }
            
            if (newPass.length < 6) {
                resultEl.textContent = '❌ رمز جدید باید حداقل 6 کاراکتر باشد';
                resultEl.className = 'text-sm text-center text-red-500';
                resultEl.classList.remove('hidden');
                return;
            }
            
            try {
                const res = await fetch('/api/auth/change-password', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'Authorization': 'Basic ' + btoa('admin:' + authToken)
                    },
                    body: JSON.stringify({old_password: oldPass, new_password: newPass})
                });
                const data = await res.json();
                
                if (data.ok) {
                    resultEl.textContent = '✅ ' + data.message;
                    resultEl.className = 'text-sm text-center text-green-500';
                    document.getElementById('change-password-form').reset();
                } else {
                    resultEl.textContent = '❌ ' + data.error;
                    resultEl.className = 'text-sm text-center text-red-500';
                }
                resultEl.classList.remove('hidden');
            } catch(e) {
                resultEl.textContent = '❌ خطا در ارتباط با سرور';
                resultEl.className = 'text-sm text-center text-red-500';
                resultEl.classList.remove('hidden');
            }
        }

        // --- UI Navigation ---
        function showTab(tab) {
            document.querySelectorAll('#tabs-container > div').forEach(el => el.classList.add('hidden'));
            document.getElementById(`tab-${tab}`).classList.remove('hidden');
            
            document.querySelectorAll('aside nav button, .md\\:hidden nav button').forEach(b => {
                b.className = "w-full flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-xl text-gray-400 hover:bg-neutral-800 hover:text-white transition";
            });
            const activeBtn = document.getElementById(`nav-${tab}`);
            if(activeBtn) activeBtn.className = "w-full flex items-center gap-3 px-4 py-3 text-sm font-medium rounded-xl bg-primary/10 text-primary transition";

            if(tab === 'dashboard') loadStats();
            if(tab === 'links') loadLinks();
            if(tab === 'settings') {
                fetch('/api/panel/links', {
                    headers: {'Authorization': 'Basic ' + btoa('admin:' + authToken)}
                }).then(r => r.json()).then(data => {
                    document.getElementById('settings-link-count').textContent = Object.keys(data.links || {}).length;
                });
                fetch('/api/panel/stats', {
                    headers: {'Authorization': 'Basic ' + btoa('admin:' + authToken)}
                }).then(r => r.json()).then(data => {
                    document.getElementById('settings-online-count').textContent = data.online_users || 0;
                });
            }
        }

        // --- Utils ---
        function formatBytes(bytes) {
            if (bytes === 0) return '0 B';
            const k = 1024, sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }

        function getProtocolBadge(protocol) {
            const map = {
                'vless': 'VLESS', 'vless-ws': 'VLESS', 'vless-xhttp': 'VLESS', 'vless-grpc': 'VLESS', 'vless-quic': 'VLESS',
                'trojan': 'Trojan', 'trojan-ws': 'Trojan', 'trojan-xhttp': 'Trojan', 'trojan-grpc': 'Trojan',
                'vmess': 'VMESS', 'vmess-ws': 'VMESS', 'vmess-xhttp': 'VMESS', 'vmess-grpc': 'VMESS',
                'shadowsocks': 'SS', 'shadowsocks-xhttp': 'SS',
                'mtproto': 'MTProto'
            };
            const cls = map[protocol] ? `protocol-${map[protocol].toLowerCase()}` : '';
            return `<span class="protocol-badge ${cls}">${map[protocol] || protocol}</span>`;
        }

        // --- API Helper ---
        async function fetchAPI(endpoint, method = 'GET', body = null) {
            const opts = { 
                method, 
                headers: {
                    'Content-Type': 'application/json',
                    'Authorization': 'Basic ' + btoa('admin:' + authToken)
                }
            };
            if (body) opts.body = JSON.stringify(body);
            const res = await fetch(`/api/panel${endpoint}`, opts);
            if (!res.ok) {
                if (res.status === 401) {
                    localStorage.removeItem('oxnet_token');
                    authToken = '';
                    isAuthenticated = false;
                    document.getElementById('login-modal').style.display = 'flex';
                }
                throw new Error(`HTTP ${res.status}`);
            }
            return res.json();
        }

        // --- Chart ---
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

        // --- Polling ---
        let lastTraffic = 0;
        async function loadStats() {
            if(document.getElementById('tab-dashboard').classList.contains('hidden')) return;
            if (!authToken) return;
            try {
                const data = await fetchAPI('/stats');
                document.getElementById('stat-traffic').innerText = formatBytes(data.total_traffic_bytes);
                document.getElementById('stat-online').innerText = data.online_users || 0;
                document.getElementById('stat-links').innerText = data.total_links || 0;
                
                if(data.system) {
                    document.getElementById('sys-cpu').innerText = data.system.cpu || 0;
                    document.getElementById('bar-cpu').style.width = `${data.system.cpu || 0}%`;
                    document.getElementById('sys-ram').innerText = data.system.ram || 0;
                    document.getElementById('bar-ram').style.width = `${data.system.ram || 0}%`;
                }

                const now = new Date();
                const timeStr = `${now.getHours().toString().padStart(2,'0')}:${now.getMinutes().toString().padStart(2,'0')}:${now.getSeconds().toString().padStart(2,'0')}`;
                const currentTrafficMB = data.total_traffic_bytes / (1024*1024);
                let diff = currentTrafficMB - lastTraffic;
                if (lastTraffic === 0) diff = 0;
                lastTraffic = currentTrafficMB;

                if(chartData.labels.length > 15) { chartData.labels.shift(); chartData.datasets[0].data.shift(); }
                chartData.labels.push(timeStr);
                chartData.datasets[0].data.push(diff);
                trafficChart.update();

                const term = document.getElementById('live-logs');
                if(data.active_connections && data.active_connections.length > 0) {
                    const conn = data.active_connections[Math.floor(Math.random() * data.active_connections.length)];
                    const div = document.createElement('div');
                    div.innerHTML = `<span class="text-blue-400">[${timeStr}]</span> ${conn.transport || 'TCP'} from <span class="text-white">${conn.ip || 'unknown'}</span> [${formatBytes(conn.bytes || 0)}]`;
                    term.appendChild(div);
                    if(term.childElementCount > 20) term.removeChild(term.firstChild);
                    term.scrollTop = term.scrollHeight;
                }
            } catch(e) { console.error(e); }
        }
        
        setInterval(loadStats, 3000);

        // --- Link Management ---
        async function loadLinks() {
            if (!authToken) return;
            try {
                const data = await fetchAPI('/links');
                const tbody = document.getElementById('links-tbody');
                tbody.innerHTML = '';
                
                Object.entries(data.links || {}).sort((a,b) => new Date(b[1].created_at) - new Date(a[1].created_at)).forEach(([uid, l]) => {
                    const limitTxt = l.limit_bytes === 0 ? '∞' : formatBytes(l.limit_bytes);
                    const usedTxt = formatBytes(l.used_bytes || 0);
                    const pct = l.limit_bytes === 0 ? 0 : Math.min(100, ((l.used_bytes || 0) / l.limit_bytes) * 100);
                    const isOk = l.active !== false && (l.limit_bytes === 0 || (l.used_bytes || 0) < l.limit_bytes);
                    
                    const statusDot = isOk ? 
                        '<span class="flex items-center gap-1.5 text-emerald-400 bg-emerald-400/10 px-2.5 py-1 rounded-md text-xs font-bold w-max"><span class="w-2 h-2 rounded-full bg-emerald-400 animate-pulse"></span>فعال</span>' : 
                        '<span class="flex items-center gap-1.5 text-red-400 bg-red-400/10 px-2.5 py-1 rounded-md text-xs font-bold w-max"><span class="w-2 h-2 rounded-full bg-red-400"></span>غیرفعال</span>';
                    
                    // پروتکل‌های این کاربر
                    const protocols = ['vless', 'trojan', 'vmess', 'shadowsocks', 'mtproto'];
                    const protoBadges = protocols.map(p => getProtocolBadge(p)).join(' ');
                    
                    const tr = document.createElement('tr');
                    tr.className = 'hover:bg-neutral-900/50 transition duration-200';
                    tr.innerHTML = `
                        <td class="p-5">
                            <div class="font-bold text-white text-base">${l.label || 'بدون نام'}</div>
                            <div class="text-[10px] text-gray-500 font-mono mt-1 opacity-50">${uid}</div>
                            ${l.expires_at ? `<div class="text-[10px] text-gray-600 mt-0.5">⏳ ${new Date(l.expires_at).toLocaleDateString('fa-IR')}</div>` : ''}
                        </td>
                        <td class="p-5">
                            <div class="text-gray-300 font-mono text-sm mb-1.5">${usedTxt} <span class="text-gray-600">/</span> ${limitTxt}</div>
                            <div class="w-32 bg-neutral-800 h-1.5 rounded-full overflow-hidden"><div class="bg-blue-500 h-full rounded-full" style="width: ${pct}%"></div></div>
                        </td>
                        <td class="p-5">${statusDot}</td>
                        <td class="p-5">
                            <div class="flex flex-wrap gap-1">${protoBadges}</div>
                        </td>
                        <td class="p-5 text-center">
                            <div class="flex items-center justify-center gap-2 flex-wrap">
                                <button onclick="showSubModal('${uid}')" class="text-xs bg-primary/20 text-primary hover:bg-primary hover:text-white px-3 py-1.5 rounded-lg transition font-bold shadow-lg shadow-primary/10">ساب</button>
                                <button onclick="openEditModal('${uid}')" class="text-xs bg-yellow-500/20 text-yellow-500 hover:bg-yellow-500 hover:text-white px-3 py-1.5 rounded-lg transition font-bold">ویرایش</button>
                                <button onclick="deleteLink('${uid}')" class="text-xs bg-red-500/10 text-red-500 hover:bg-red-500 hover:text-white px-3 py-1.5 rounded-lg transition font-bold">حذف</button>
                            </div>
                        </td>
                    `;
                    tbody.appendChild(tr);
                });
            } catch(e) { console.error(e); }
        }

        async function createMultipack(e) {
            e.preventDefault();
            if (!authToken) return;
            const btn = e.target.querySelector('button[type="submit"]');
            const originalText = btn.innerHTML;
            btn.innerHTML = '<span class="animate-spin text-xl">↻</span> در حال ساخت...';
            btn.disabled = true;
            
            const payload = {
                label: document.getElementById('mp-label').value,
                limit_gb: parseFloat(document.getElementById('mp-volume').value) || 0,
                days: parseInt(document.getElementById('mp-days').value) || 0
            };

            try {
                const res = await fetchAPI('/multipack', 'POST', payload);
                if(res.ok) {
                    const term = document.getElementById('live-logs');
                    term.innerHTML += `<div class="text-green-400">[System] کاربر ${payload.label} ساخته شد.</div>`;
                    document.getElementById('multipack-form').reset();
                    showSubModal(res.uuid);
                    loadLinks();
                }
            } catch(err) {
                alert('خطا در ارتباط با سرور.');
            }
            btn.innerHTML = originalText;
            btn.disabled = false;
        }

        async function deleteLink(uid) {
            if(!confirm('آیا از حذف این کاربر مطمئن هستید؟')) return;
            if (!authToken) return;
            try {
                await fetchAPI(`/links/${uid}`, 'DELETE');
                loadLinks();
            } catch(e) { alert('خطا در حذف'); }
        }

        // --- Edit Modal ---
        let editingUid = null;
        
        async function openEditModal(uid) {
            if (!authToken) return;
            try {
                const data = await fetchAPI(`/links/${uid}`);
                const link = data.link;
                editingUid = uid;
                
                document.getElementById('edit-uid').value = uid;
                document.getElementById('edit-label').value = link.label || '';
                
                // تبدیل bytes به GB برای نمایش
                const limitGB = link.limit_bytes > 0 ? (link.limit_bytes / (1024**3)).toFixed(1) : 0;
                document.getElementById('edit-volume').value = limitGB;
                
                // محاسبه روزهای باقی‌مانده
                let days = 0;
                if (link.expires_at) {
                    const exp = new Date(link.expires_at);
                    const now = new Date();
                    days = Math.ceil((exp - now) / (1000 * 60 * 60 * 24));
                    if (days < 0) days = 0;
                }
                document.getElementById('edit-days').value = days;
                document.getElementById('edit-ip-limit').value = link.ip_limit || 0;
                document.getElementById('edit-speed-limit').value = link.speed_limit_bytes ? Math.round(link.speed_limit_bytes / 1024) : 0;
                document.getElementById('edit-active').checked = link.active !== false;
                
                document.getElementById('edit-modal').classList.remove('hidden');
                document.getElementById('edit-result').classList.add('hidden');
            } catch(e) {
                alert('خطا در دریافت اطلاعات');
            }
        }

        function closeEditModal() {
            document.getElementById('edit-modal').classList.add('hidden');
            editingUid = null;
        }

        async function saveEdit(event) {
            event.preventDefault();
            if (!editingUid) return;
            
            const btn = event.target.querySelector('button[type="submit"]');
            const origText = btn.innerHTML;
            btn.innerHTML = '⏳ در حال ذخیره...';
            btn.disabled = true;
            
            const resultEl = document.getElementById('edit-result');
            
            try {
                const payload = {
                    label: document.getElementById('edit-label').value,
                    limit_bytes: parseFloat(document.getElementById('edit-volume').value) * 1024**3,
                    ip_limit: parseInt(document.getElementById('edit-ip-limit').value) || 0,
                    speed_limit_bytes: parseInt(document.getElementById('edit-speed-limit').value) * 1024 || 0,
                    active: document.getElementById('edit-active').checked
                };
                
                // محاسبه تاریخ انقضا
                const days = parseInt(document.getElementById('edit-days').value) || 0;
                if (days > 0) {
                    const exp = new Date();
                    exp.setDate(exp.getDate() + days);
                    payload.expires_at = exp.toISOString();
                } else {
                    payload.expires_at = null;
                }
                
                const res = await fetchAPI(`/links/${editingUid}`, 'PUT', payload);
                
                if (res.ok) {
                    resultEl.textContent = '✅ تغییرات با موفقیت ذخیره شد';
                    resultEl.className = 'text-sm text-center text-green-500';
                    resultEl.classList.remove('hidden');
                    setTimeout(() => {
                        closeEditModal();
                        loadLinks();
                    }, 1500);
                } else {
                    resultEl.textContent = '❌ خطا در ذخیره تغییرات';
                    resultEl.className = 'text-sm text-center text-red-500';
                    resultEl.classList.remove('hidden');
                }
            } catch(e) {
                resultEl.textContent = '❌ خطا در ارتباط با سرور';
                resultEl.className = 'text-sm text-center text-red-500';
                resultEl.classList.remove('hidden');
            }
            
            btn.innerHTML = origText;
            btn.disabled = false;
        }

        // --- Subscription Modal ---
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

        // --- Init ---
        document.addEventListener('DOMContentLoaded', () => {
            checkAuth();
            
            // وقتی روی لینک‌های ناوبری کلیک می‌شه
            document.querySelectorAll('aside nav button, .md\\:hidden nav button').forEach(btn => {
                btn.addEventListener('click', () => {
                    if (!isAuthenticated) {
                        document.getElementById('login-modal').style.display = 'flex';
                    }
                });
            });
        });

        // اگر روی مودال کلیک بشه بیرون
        document.getElementById('login-modal').addEventListener('click', function(e) {
            if (e.target === this && isAuthenticated) {
                this.style.display = 'none';
            }
        });
    </script>
</body>
</html>
"""

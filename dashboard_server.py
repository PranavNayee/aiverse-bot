#!/usr/bin/env python3
"""
AIVerse Bot - Ultra-Modern Animated Command Center & System Architecture
Includes:
- Interactive 9:16 Video Reel Player (Hero & Pop-Up Theater)
- 100% Mobile Responsive Layout (iPhone, Android, Tablet, Desktop)
- Full "About System Architecture" View with End-to-End Pipeline Documentation
- Action Launchpad (Post Now, Dry Run, Pre-Flight Check, Auto-Reply, Global Pause/Resume)
- Terminal Log Streamer & Real-Time IST Countdown Clock
"""

import http.server
import socketserver
import json
import subprocess
import os
import urllib.request
import urllib.parse
import threading
import time
import webbrowser
from datetime import datetime, timezone, timedelta

PORT = 8080
REPO = "PranavNayee/aiverse-bot"
IG_USER_ID = "17841479592722450"
IG_TOKEN = "EAAUim1AzK9MBSZC5nX55gGjCeuEk6yzhApCCVZBgVGSJGQqhC564ZCZCu9fniiGDdXIbIEyO3nd7EJXK97W5ZC4ZB0DOr7RUM2i928B4GlMfzZBZCd7VXSTWZBBtpGhpov56gxp0XyC6jBW1JSubuF9ZA7GVD1JmNkNLXktyO0ZBKFZBj6wZC1mCrIQBo4MZBwlMocuX49OOVsZC4c7OfvRQS7zGTNDU5CFCBsBlpsqgsD4HJwNuB1FlbJkqwvMlQZDZD"

def run_cmd(cmd_list, timeout=25):
    try:
        r = subprocess.run(cmd_list, capture_output=True, text=True, timeout=timeout)
        return r.returncode, r.stdout.strip(), r.stderr.strip()
    except Exception as e:
        return 1, "", str(e)

def get_workflows_status():
    code, out, _ = run_cmd(["gh", "workflow", "list", "--repo", REPO, "--json", "id,name,state,path"])
    if code == 0:
        try:
            return json.loads(out)
        except Exception:
            pass
    return []

def get_recent_runs(limit=10):
    code, out, _ = run_cmd(["gh", "run", "list", "--repo", REPO, "--limit", str(limit), 
                            "--json", "databaseId,name,status,conclusion,createdAt,workflowName,url"])
    if code == 0:
        try:
            return json.loads(out)
        except Exception:
            pass
    return []

def get_run_logs(run_id):
    code, out, err = run_cmd(["gh", "run", "view", str(run_id), "--repo", REPO, "--log"], timeout=30)
    if code == 0:
        lines = out.split("\n")
        return "\n".join(lines[-300:]) if len(lines) > 300 else out
    return err or "Log not ready or workflow in progress..."

def get_instagram_posts(limit=8):
    url = (f"https://graph.facebook.com/v21.0/{IG_USER_ID}/media?"
           f"fields=id,caption,media_type,permalink,thumbnail_url,media_url,timestamp&limit={limit}&access_token={IG_TOKEN}")
    code, out, _ = run_cmd(["curl", "-s", url])
    if code == 0 and out:
        try:
            data = json.loads(out)
            return data.get("data", [])
        except Exception:
            pass
    return []

def trigger_workflow(workflow_file, inputs=None):
    cmd = ["gh", "workflow", "run", workflow_file, "--repo", REPO]
    if inputs:
        for k, v in inputs.items():
            cmd.extend(["--field", f"{k}={v}"])
    code, out, err = run_cmd(cmd)
    return code == 0, out or err

def set_workflow_state(workflow_file, enable=True):
    action = "enable" if enable else "disable"
    code, out, err = run_cmd(["gh", "workflow", action, workflow_file, "--repo", REPO])
    return code == 0, out or err

def cancel_run(run_id):
    code, out, err = run_cmd(["gh", "run", "cancel", str(run_id), "--repo", REPO])
    return code == 0, out or err

HTML_PAGE = """<!DOCTYPE html>
<html lang="en" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">
  <meta name="referrer" content="no-referrer">
  <title>AIVerse OS &middot; Autonomous Reel Automation</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css">
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@300;400;500;600;700;800&family=JetBrains+Mono:wght@400;500;700&display=swap" rel="stylesheet">
  
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          fontFamily: {
            sans: ['"Plus Jakarta Sans"', 'sans-serif'],
            mono: ['"JetBrains Mono"', 'monospace']
          },
          colors: {
            dark: '#07090e',
            darker: '#040508',
            panel: '#0e131f',
            panelBorder: '#1c2438',
            neonEmerald: '#10b981',
            neonCyan: '#06b6d4',
            neonViolet: '#8b5cf6',
            neonPink: '#f43f5e',
            neonAmber: '#f59e0b'
          },
          animation: {
            'blob': 'blob 14s infinite',
            'shimmer': 'shimmer 2.5s infinite linear',
            'spin-slow': 'spin 12s linear infinite'
          },
          keyframes: {
            blob: {
              '0%, 100%': { transform: 'translate(0px, 0px) scale(1)' },
              '33%': { transform: 'translate(40px, -60px) scale(1.15)' },
              '66%': { transform: 'translate(-30px, 30px) scale(0.92)' }
            },
            shimmer: {
              '0%': { transform: 'translateX(-100%)' },
              '100%': { transform: 'translateX(200%)' }
            }
          }
        }
      }
    }
  </script>

  <style>
    .bg-grid {
      background-image: radial-gradient(rgba(255, 255, 255, 0.07) 1px, transparent 1px);
      background-size: 28px 28px;
    }
    .glass-card {
      background: rgba(14, 19, 31, 0.78);
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      border: 1px solid rgba(255, 255, 255, 0.08);
    }
    .glass-card:hover {
      border-color: rgba(16, 185, 129, 0.35);
      box-shadow: 0 0 35px -5px rgba(16, 185, 129, 0.12);
    }
    .glass-header {
      background: rgba(7, 9, 14, 0.90);
      backdrop-filter: blur(24px);
      border-bottom: 1px solid rgba(255, 255, 255, 0.08);
    }
    .shimmer-btn {
      position: relative;
      overflow: hidden;
    }
    .shimmer-btn::after {
      content: '';
      position: absolute;
      top: 0; left: 0; right: 0; bottom: 0;
      background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
      transform: translateX(-100%);
      animation: shimmer 3s infinite;
    }
    .phone-frame {
      box-shadow: 0 25px 60px -15px rgba(0, 0, 0, 0.8), 0 0 35px rgba(16, 185, 129, 0.25);
    }
    ::-webkit-scrollbar { width: 5px; height: 5px; }
    ::-webkit-scrollbar-track { background: #07090e; }
    ::-webkit-scrollbar-thumb { background: #1c2438; border-radius: 999px; }
    ::-webkit-scrollbar-thumb:hover { background: #10b981; }
  </style>
</head>
<body class="bg-dark text-slate-100 min-h-screen flex flex-col font-sans antialiased overflow-x-hidden selection:bg-neonEmerald selection:text-black">

  <!-- Ambient Animated Lighting Spheres -->
  <div class="fixed inset-0 pointer-events-none overflow-hidden z-0">
    <div class="absolute -top-32 -left-32 w-72 sm:w-96 h-72 sm:h-96 bg-emerald-500/15 rounded-full blur-3xl animate-blob"></div>
    <div class="absolute top-1/3 -right-32 w-72 sm:w-96 h-72 sm:h-96 bg-cyan-500/15 rounded-full blur-3xl animate-blob animation-delay-2000"></div>
    <div class="absolute -bottom-32 left-1/4 w-72 sm:w-96 h-72 sm:h-96 bg-violet-600/15 rounded-full blur-3xl animate-blob animation-delay-4000"></div>
    <div class="absolute inset-0 bg-grid opacity-50"></div>
  </div>

  <!-- Top Glass Bar with Navigation Tabs -->
  <header class="glass-header sticky top-0 z-40 transition-all duration-300">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-18 sm:h-20 flex items-center justify-between relative z-10">
      
      <!-- Brand Logo & Tab Navigation -->
      <div class="flex items-center space-x-3 sm:space-x-6">
        <div class="flex items-center space-x-3">
          <div class="relative group cursor-pointer">
            <div class="absolute -inset-1 bg-gradient-to-r from-neonEmerald to-neonCyan rounded-2xl blur opacity-70 group-hover:opacity-100 transition duration-300"></div>
            <div class="relative w-10 sm:w-12 h-10 sm:h-12 rounded-xl bg-panel flex items-center justify-center border border-white/10 text-neonEmerald text-xl sm:text-2xl font-black">
              <i class="fa-solid fa-atom animate-spin-slow"></i>
            </div>
          </div>
          <div>
            <div class="flex items-center space-x-1.5 sm:space-x-2">
              <h1 class="text-base sm:text-xl font-extrabold tracking-tight bg-gradient-to-r from-white via-slate-100 to-neonEmerald bg-clip-text text-transparent">
                AIVerse OS
              </h1>
              <span class="hidden xs:inline-block text-[9px] sm:text-[10px] font-mono px-2 py-0.5 rounded-full bg-neonCyan/10 text-neonCyan border border-neonCyan/30 font-bold uppercase tracking-wider">v4.0</span>
            </div>
            <p class="hidden sm:block text-xs text-slate-400 mt-0.5">@aiverse.agent &middot; Autonomous Hinglish Creator</p>
          </div>
        </div>

        <!-- Navigation Tabs (Control Center / About Architecture) -->
        <nav class="flex items-center p-1 rounded-xl bg-darker/80 border border-white/10 text-xs font-semibold">
          <button onclick="switchTab('dashboard')" id="navTabDashboard" class="px-3 sm:px-4 py-1.5 sm:py-2 rounded-lg bg-neonEmerald/15 text-neonEmerald border border-neonEmerald/30 font-bold transition flex items-center space-x-1.5">
            <i class="fa-solid fa-sliders text-xs"></i>
            <span>Controls</span>
          </button>
          <button onclick="switchTab('about')" id="navTabAbout" class="px-3 sm:px-4 py-1.5 sm:py-2 rounded-lg text-slate-400 hover:text-white transition flex items-center space-x-1.5">
            <i class="fa-solid fa-circle-info text-xs"></i>
            <span>Architecture</span>
          </button>
        </nav>
      </div>

      <!-- Right Controls & Clock -->
      <div class="flex items-center space-x-2 sm:space-x-3">
        
        <!-- Live Clock (Desktop) -->
        <div class="hidden lg:flex items-center space-x-2 px-3.5 py-1.5 rounded-xl bg-panel/80 border border-panelBorder/80 font-mono text-xs">
          <div class="flex items-center space-x-1 text-cyan-400">
            <i class="fa-regular fa-clock text-[10px]"></i>
            <span id="liveClock" class="font-bold">--:--:-- IST</span>
          </div>
        </div>

        <!-- Master Switch (Pause / Resume) -->
        <button onclick="toggleGlobalAutomation()" id="btnGlobalToggle" class="px-3 sm:px-4 py-2 sm:py-2.5 rounded-xl text-xs font-bold flex items-center space-x-1.5 sm:space-x-2 transition-all duration-300 shadow-lg transform active:scale-95 bg-amber-500/10 text-amber-300 border border-amber-500/30 hover:bg-amber-500/20">
          <i class="fa-solid fa-pause text-xs"></i>
          <span class="hidden sm:inline">Pause Automation</span>
          <span class="sm:hidden">Pause</span>
        </button>

        <!-- Refresh Button -->
        <button onclick="refreshAll()" class="w-9 sm:w-10 h-9 sm:h-10 rounded-xl bg-panel border border-panelBorder flex items-center justify-center text-slate-400 hover:text-white hover:border-slate-600 transition-all transform active:scale-90" title="Refresh Feed">
          <i id="refreshIcon" class="fa-solid fa-arrows-rotate text-xs sm:text-sm"></i>
        </button>

      </div>
    </div>
  </header>

  <!-- Real-Time In-Progress Workflow Banner -->
  <div id="activeRunBanner" class="hidden relative z-30 bg-gradient-to-r from-emerald-950 via-panel to-cyan-950 border-b border-neonEmerald/40 py-3 px-4 shadow-xl">
    <div class="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-3 text-xs sm:text-sm">
      <div class="flex items-center space-x-2.5">
        <div class="relative flex h-2.5 w-2.5">
          <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-neonEmerald opacity-75"></span>
          <span class="relative inline-flex rounded-full h-2.5 w-2.5 bg-neonEmerald"></span>
        </div>
        <div class="flex items-center space-x-1.5">
          <span class="font-extrabold text-white">LIVE RUNNING:</span>
          <span id="activeRunName" class="text-neonEmerald font-mono font-semibold truncate max-w-[200px] sm:max-w-xs">Generating & Posting Reel...</span>
        </div>
      </div>
      <div class="flex items-center space-x-2">
        <button onclick="openLiveLogModal()" class="px-3 py-1 rounded-lg text-xs font-semibold bg-cyan-500/10 text-cyan-300 border border-cyan-500/30 hover:bg-cyan-500/20 transition flex items-center space-x-1">
          <i class="fa-solid fa-terminal text-[10px]"></i>
          <span>Log</span>
        </button>
        <button onclick="cancelActiveRun()" class="px-3 py-1 rounded-lg text-xs font-semibold bg-red-500/10 text-red-400 border border-red-500/30 hover:bg-red-500/20 transition flex items-center space-x-1">
          <i class="fa-solid fa-stop text-[9px]"></i>
          <span>Abort</span>
        </button>
      </div>
    </div>
  </div>

  <!-- Toast Notification -->
  <div id="toast" class="fixed bottom-6 right-4 sm:right-8 z-50 transform translate-y-28 opacity-0 transition-all duration-300 pointer-events-none max-w-sm">
    <div class="glass-card px-4 sm:px-5 py-3 rounded-2xl border border-neonEmerald/50 text-white text-xs sm:text-sm flex items-center space-x-2.5 shadow-2xl">
      <i id="toastIcon" class="fa-solid fa-circle-check text-neonEmerald text-base sm:text-lg"></i>
      <span id="toastMsg" class="font-medium">Action processed</span>
    </div>
  </div>

  <!-- MAIN TAB 1: CONTROL DASHBOARD -->
  <main id="tabDashboard" class="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8 flex-1 space-y-6 sm:space-y-8 w-full">

    <!-- HERO SECTION: LATEST GENERATED REEL PLAYER (Mobile Responsive) -->
    <div class="glass-card rounded-3xl p-5 sm:p-8 border border-white/10 relative overflow-hidden">
      <div class="absolute -right-20 -top-20 w-80 h-80 bg-neonEmerald/10 rounded-full blur-3xl pointer-events-none"></div>
      
      <div class="flex flex-col lg:flex-row items-center gap-6 sm:gap-8">
        
        <!-- Interactive 9:16 Mobile Video Frame -->
        <div class="w-full max-w-[240px] xs:max-w-[270px] sm:max-w-[290px] flex-shrink-0 mx-auto">
          <div class="phone-frame relative aspect-[9/16] rounded-[2.2rem] sm:rounded-[2.5rem] bg-darker p-2.5 sm:p-3 border-4 border-slate-800/90 shadow-2xl overflow-hidden group">
            
            <!-- Phone Notch -->
            <div class="absolute top-3.5 left-1/2 -translate-x-1/2 w-16 sm:w-20 h-3.5 sm:h-4 bg-slate-800 rounded-full z-20 flex items-center justify-center">
              <div class="w-2 sm:w-2.5 h-2 sm:h-2.5 rounded-full bg-slate-900 mr-2"></div>
              <div class="w-6 sm:w-8 h-1 sm:h-1.5 rounded-full bg-slate-900"></div>
            </div>

            <!-- HTML5 Video Player -->
            <div class="w-full h-full rounded-[1.8rem] sm:rounded-[2rem] overflow-hidden bg-black relative">
              <video id="heroVideoPlayer" class="w-full h-full object-cover" controls playsinline loop preload="metadata" poster="">
                <source id="heroVideoSource" src="" type="video/mp4">
                Your browser does not support HTML5 video.
              </video>

              <div class="absolute top-3 left-3 z-10 pointer-events-none">
                <span class="inline-flex items-center px-2 py-0.5 rounded-full text-[9px] font-black bg-pink-500/90 text-white tracking-wider shadow">
                  <i class="fa-brands fa-instagram mr-1"></i> LIVE REEL
                </span>
              </div>
            </div>

          </div>
        </div>

        <!-- Reel Metadata & Controls -->
        <div class="flex-1 flex flex-col justify-between space-y-4 sm:space-y-5 text-left w-full">
          <div>
            <div class="flex flex-wrap items-center gap-2 mb-2 sm:mb-3">
              <span class="px-2.5 py-0.5 sm:py-1 rounded-full text-[10px] sm:text-xs font-mono font-bold bg-neonEmerald/10 text-neonEmerald border border-neonEmerald/30">
                <i class="fa-solid fa-circle-check mr-1"></i> LATEST PUBLISHED REEL
              </span>
              <span id="heroReelDate" class="text-[10px] sm:text-xs font-mono text-slate-400">Published Today</span>
            </div>

            <h2 id="heroReelTitle" class="text-xl sm:text-2xl lg:text-3xl font-extrabold text-white tracking-tight">
              Loading latest reel...
            </h2>

            <div class="mt-3 sm:mt-4 p-3.5 sm:p-4 rounded-2xl bg-darker/60 border border-white/5">
              <p class="text-[10px] sm:text-xs font-mono text-slate-400 uppercase tracking-wider mb-1 flex items-center justify-between">
                <span>Caption & Hook Script</span>
                <button onclick="copyHeroCaption()" class="text-neonCyan hover:underline text-[10px] sm:text-[11px] normal-case">
                  <i class="fa-regular fa-copy mr-1"></i> Copy Caption
                </button>
              </p>
              <p id="heroReelCaption" class="text-xs text-slate-300 leading-relaxed font-sans line-clamp-3 sm:line-clamp-4">
                Querying latest reel from Instagram Graph API...
              </p>
            </div>
          </div>

          <!-- Feature Specs Matrix -->
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-2.5 sm:gap-3">
            <div class="p-2.5 sm:p-3 rounded-xl bg-panel/60 border border-white/5">
              <span class="text-[9px] sm:text-[10px] font-mono text-slate-500 block uppercase">Voice Model</span>
              <span class="text-xs font-bold text-white mt-0.5 block truncate">Gemini Charon</span>
            </div>
            <div class="p-2.5 sm:p-3 rounded-xl bg-panel/60 border border-white/5">
              <span class="text-[9px] sm:text-[10px] font-mono text-slate-500 block uppercase">Language</span>
              <span class="text-xs font-bold text-white mt-0.5 block">Hinglish AI</span>
            </div>
            <div class="p-2.5 sm:p-3 rounded-xl bg-panel/60 border border-white/5">
              <span class="text-[9px] sm:text-[10px] font-mono text-slate-500 block uppercase">Animation</span>
              <span class="text-xs font-bold text-neonEmerald mt-0.5 block">Seekho Bot 2D</span>
            </div>
            <div class="p-2.5 sm:p-3 rounded-xl bg-panel/60 border border-white/5">
              <span class="text-[9px] sm:text-[10px] font-mono text-slate-500 block uppercase">Platforms</span>
              <span class="text-xs font-bold text-neonCyan mt-0.5 block">IG + YouTube</span>
            </div>
          </div>

          <!-- Direct Watch Buttons -->
          <div class="flex flex-wrap items-center gap-2.5 sm:gap-3 pt-1">
            <a id="heroInstagramLink" href="https://www.instagram.com/aiverse.agent/" target="_blank" class="w-full sm:w-auto px-4 sm:px-5 py-2.5 rounded-xl font-bold text-xs bg-gradient-to-r from-pink-500 to-rose-600 hover:from-pink-600 hover:to-rose-700 text-white shadow-lg shadow-pink-900/30 transition flex items-center justify-center space-x-2">
              <i class="fa-brands fa-instagram text-sm"></i>
              <span>Watch on Instagram</span>
            </a>
            <a id="heroDownloadLink" href="#" download="aiverse_reel.mp4" target="_blank" class="w-full sm:w-auto px-4 py-2.5 rounded-xl font-bold text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition flex items-center justify-center space-x-2">
              <i class="fa-solid fa-download text-sm text-neonEmerald"></i>
              <span>Download MP4</span>
            </a>
          </div>

        </div>

      </div>
    </div>

    <!-- Quick Stats Grid -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-5">
      
      <!-- Card 1: Account -->
      <div class="glass-card rounded-2xl p-5 relative overflow-hidden transition-all duration-300">
        <div class="flex items-center justify-between">
          <span class="text-[11px] font-semibold text-slate-400 uppercase tracking-wider font-mono">Target Account</span>
          <div class="w-7 h-7 rounded-lg bg-pink-500/10 flex items-center justify-center text-pink-400">
            <i class="fa-brands fa-instagram text-sm"></i>
          </div>
        </div>
        <div class="mt-2.5">
          <a href="https://www.instagram.com/aiverse.agent/" target="_blank" class="text-lg font-bold text-white hover:text-pink-400 transition flex items-center space-x-1.5">
            <span>@aiverse.agent</span>
            <i class="fa-solid fa-arrow-up-right-from-square text-[10px] opacity-60"></i>
          </a>
          <p class="text-[10px] text-slate-400 font-mono mt-0.5">UID: 17841479592722450</p>
        </div>
        <div class="mt-3 pt-2.5 border-t border-white/5 flex items-center justify-between text-xs">
          <span class="text-slate-400 text-[11px]">System User Token</span>
          <span class="text-neonEmerald font-bold text-[11px] flex items-center">
            <i class="fa-solid fa-infinity mr-1 text-[10px]"></i> Never Expires
          </span>
        </div>
      </div>

      <!-- Card 2: YouTube Shorts -->
      <div class="glass-card rounded-2xl p-5 relative overflow-hidden transition-all duration-300">
        <div class="flex items-center justify-between">
          <span class="text-[11px] font-semibold text-slate-400 uppercase tracking-wider font-mono">YouTube Shorts</span>
          <div class="w-7 h-7 rounded-lg bg-red-500/10 flex items-center justify-center text-red-400">
            <i class="fa-brands fa-youtube text-sm"></i>
          </div>
        </div>
        <div class="mt-2.5">
          <p class="text-lg font-bold text-white">Cross-Post Sync</p>
          <p class="text-[10px] text-slate-400 font-mono mt-0.5">Automated Dual-Distribution</p>
        </div>
        <div class="mt-3 pt-2.5 border-t border-white/5 flex items-center justify-between text-xs">
          <span class="text-slate-400 text-[11px]">OAuth Refresh</span>
          <span class="text-neonEmerald font-bold text-[11px] flex items-center">
            <i class="fa-solid fa-check mr-1 text-[10px]"></i> Connected
          </span>
        </div>
      </div>

      <!-- Card 3: Next Scheduled Post -->
      <div class="glass-card rounded-2xl p-5 relative overflow-hidden transition-all duration-300">
        <div class="flex items-center justify-between">
          <span class="text-[11px] font-semibold text-slate-400 uppercase tracking-wider font-mono">Next Slot Countdown</span>
          <div class="w-7 h-7 rounded-lg bg-cyan-500/10 flex items-center justify-center text-cyan-400">
            <i class="fa-solid fa-stopwatch text-sm"></i>
          </div>
        </div>
        <div class="mt-2.5">
          <p id="countdownTimer" class="text-lg font-bold text-neonCyan font-mono">--h --m --s</p>
          <p class="text-[10px] text-slate-400 mt-0.5">Slots: 08:00 AM & 07:00 PM IST</p>
        </div>
        <div class="mt-3 pt-2.5 border-t border-white/5 flex items-center justify-between text-xs">
          <span class="text-slate-400 text-[11px]">Review Mode</span>
          <span class="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 font-mono text-[9px] font-bold border border-emerald-500/20">AUTO</span>
        </div>
      </div>

      <!-- Card 4: AI & Animation Engine -->
      <div class="glass-card rounded-2xl p-5 relative overflow-hidden transition-all duration-300">
        <div class="flex items-center justify-between">
          <span class="text-[11px] font-semibold text-slate-400 uppercase tracking-wider font-mono">Curriculum Bank</span>
          <div class="w-7 h-7 rounded-lg bg-violet-500/10 flex items-center justify-center text-violet-400">
            <i class="fa-solid fa-graduation-cap text-sm"></i>
          </div>
        </div>
        <div class="mt-2.5">
          <p class="text-lg font-bold text-white">224 Master Items</p>
          <p class="text-[10px] text-slate-400 font-mono mt-0.5">100 Lessons + 70 Tricks + Alerts</p>
        </div>
        <div class="mt-3 pt-2.5 border-t border-white/5 flex items-center justify-between text-xs">
          <span class="text-slate-400 text-[11px]">Runner Status</span>
          <span class="text-neonEmerald font-bold text-[11px] font-mono">100% Operational</span>
        </div>
      </div>

    </div>

    <!-- Action Launchpad -->
    <div class="glass-card rounded-3xl p-5 sm:p-7 relative overflow-hidden border border-white/10">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-5 border-b border-white/10">
        <div>
          <h2 class="text-base sm:text-lg font-bold text-white flex items-center space-x-2">
            <span class="w-2.5 h-2.5 rounded-full bg-neonEmerald glow-live"></span>
            <span>Manual Action Launchpad</span>
          </h2>
          <p class="text-xs text-slate-400 mt-0.5">Direct manual triggers for the GitHub Actions automation runner</p>
        </div>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-5">
        
        <!-- Action 1: Post Reel Now -->
        <button onclick="triggerAction('post_now')" class="shimmer-btn p-4 sm:p-5 rounded-2xl bg-gradient-to-br from-emerald-600 via-teal-600 to-cyan-600 text-white shadow-xl shadow-emerald-900/40 text-left transition-all duration-300 transform active:scale-95 group">
          <div class="flex items-center justify-between">
            <div class="w-10 sm:w-11 h-10 sm:h-11 rounded-xl bg-white/20 flex items-center justify-center text-white text-lg">
              <i class="fa-solid fa-paper-plane"></i>
            </div>
            <span class="text-[9px] font-bold uppercase tracking-wider bg-black/30 px-2 py-0.5 rounded-full border border-white/20">LIVE POST</span>
          </div>
          <div class="mt-3">
            <h3 class="font-extrabold text-sm sm:text-base">Post Reel Now</h3>
            <p class="text-[11px] text-emerald-100/80 mt-0.5 leading-relaxed">Generates script, voice, 2D visuals & posts immediately</p>
          </div>
        </button>

        <!-- Action 2: Dry Run Preview -->
        <button onclick="triggerAction('dry_run')" class="p-4 sm:p-5 rounded-2xl bg-panel/90 hover:bg-slate-800/90 border border-panelBorder hover:border-cyan-500/50 text-white text-left transition-all duration-300 transform active:scale-95 group shadow-lg">
          <div class="flex items-center justify-between">
            <div class="w-10 sm:w-11 h-10 sm:h-11 rounded-xl bg-cyan-500/10 flex items-center justify-center text-cyan-400 text-lg">
              <i class="fa-solid fa-flask-vial"></i>
            </div>
            <span class="text-[9px] font-bold uppercase tracking-wider bg-cyan-500/10 text-cyan-400 px-2 py-0.5 rounded-full border border-cyan-500/30">TEST</span>
          </div>
          <div class="mt-3">
            <h3 class="font-extrabold text-sm sm:text-base">Dry-Run Preview</h3>
            <p class="text-[11px] text-slate-400 mt-0.5 leading-relaxed">Renders complete MP4 video as artifact without posting</p>
          </div>
        </button>

        <!-- Action 3: Pre-Flight Check -->
        <button onclick="triggerAction('check')" class="p-4 sm:p-5 rounded-2xl bg-panel/90 hover:bg-slate-800/90 border border-panelBorder hover:border-violet-500/50 text-white text-left transition-all duration-300 transform active:scale-95 group shadow-lg">
          <div class="flex items-center justify-between">
            <div class="w-10 sm:w-11 h-10 sm:h-11 rounded-xl bg-violet-500/10 flex items-center justify-center text-violet-400 text-lg">
              <i class="fa-solid fa-stethoscope"></i>
            </div>
            <span class="text-[9px] font-bold uppercase tracking-wider bg-violet-500/10 text-violet-400 px-2 py-0.5 rounded-full border border-violet-500/30">CHECK</span>
          </div>
          <div class="mt-3">
            <h3 class="font-extrabold text-sm sm:text-base">Pre-Flight Check</h3>
            <p class="text-[11px] text-slate-400 mt-0.5 leading-relaxed">Verifies Meta token, Gemini voice quota, Supabase & fonts</p>
          </div>
        </button>

        <!-- Action 4: Auto-Engagement Loop -->
        <button onclick="triggerAction('engage')" class="p-4 sm:p-5 rounded-2xl bg-panel/90 hover:bg-slate-800/90 border border-panelBorder hover:border-amber-500/50 text-white text-left transition-all duration-300 transform active:scale-95 group shadow-lg">
          <div class="flex items-center justify-between">
            <div class="w-10 sm:w-11 h-10 sm:h-11 rounded-xl bg-amber-500/10 flex items-center justify-center text-amber-400 text-lg">
              <i class="fa-solid fa-comments"></i>
            </div>
            <span class="text-[9px] font-bold uppercase tracking-wider bg-amber-500/10 text-amber-400 px-2 py-0.5 rounded-full border border-amber-500/30">ENGAGE</span>
          </div>
          <div class="mt-3">
            <h3 class="font-extrabold text-sm sm:text-base">Auto-Reply & Learn</h3>
            <p class="text-[11px] text-slate-400 mt-0.5 leading-relaxed">Sends prompts to commenters & updates hook analytics</p>
          </div>
        </button>

      </div>
    </div>

    <!-- Live Published Reels Section -->
    <div class="glass-card rounded-3xl p-5 sm:p-7 border border-white/10">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-3 pb-5 border-b border-white/10">
        <div>
          <h2 class="text-base sm:text-lg font-bold text-white flex items-center space-x-2">
            <i class="fa-brands fa-instagram text-pink-500"></i>
            <span>Published Reels Gallery</span>
          </h2>
          <p class="text-xs text-slate-400 mt-0.5">Tap any reel to preview & listen directly in the dashboard theater</p>
        </div>
        <div>
          <a href="https://www.instagram.com/aiverse.agent/" target="_blank" class="inline-flex px-3.5 py-1.5 rounded-xl text-xs font-bold bg-pink-500/10 text-pink-400 border border-pink-500/30 hover:bg-pink-500/20 transition items-center space-x-1.5">
            <span>Instagram Feed</span>
            <i class="fa-solid fa-arrow-up-right-from-square text-[9px]"></i>
          </a>
        </div>
      </div>

      <div id="postsGrid" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 sm:gap-6 mt-5">
        <div class="col-span-full py-12 text-center text-slate-500 font-mono text-xs">
          <i class="fa-solid fa-circle-notch fa-spin text-neonEmerald text-lg mr-2"></i>
          <span>Loading reels gallery...</span>
        </div>
      </div>
    </div>

    <!-- Lower Section: Workflows & GitHub Run History -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">

      <!-- Workflows Control List -->
      <div class="glass-card rounded-3xl p-5 sm:p-6 border border-white/10 lg:col-span-1 flex flex-col justify-between">
        <div>
          <div class="flex items-center justify-between pb-3.5 border-b border-white/10">
            <h2 class="text-sm sm:text-base font-bold text-white flex items-center space-x-2">
              <i class="fa-solid fa-sliders text-neonCyan text-xs"></i>
              <span>Workflow Schedules</span>
            </h2>
            <span class="text-[10px] font-mono text-slate-400">Independent</span>
          </div>
          <p class="text-xs text-slate-400 mt-2 mb-4">Toggle background cron jobs:</p>

          <div id="workflowsList" class="space-y-2.5">
            <div class="py-6 text-center text-slate-500 text-xs font-mono">
              <i class="fa-solid fa-circle-notch fa-spin mr-1 text-neonCyan"></i> Fetching workflows...
            </div>
          </div>
        </div>

        <div class="mt-5 pt-3.5 border-t border-white/5 text-[10px] text-slate-500 flex items-center justify-between">
          <span>GitHub Actions Runner: Linux x64</span>
          <span class="text-neonEmerald font-mono">Online</span>
        </div>
      </div>

      <!-- Live Execution Table -->
      <div class="glass-card rounded-3xl p-5 sm:p-6 border border-white/10 lg:col-span-2">
        <div class="flex items-center justify-between pb-3.5 border-b border-white/10">
          <div>
            <h2 class="text-sm sm:text-base font-bold text-white flex items-center space-x-2">
              <i class="fa-solid fa-list-check text-neonEmerald text-xs"></i>
              <span>Execution Pipeline History</span>
            </h2>
            <p class="text-xs text-slate-400 mt-0.5">Live status of recent workflow executions</p>
          </div>
          <a href="https://github.com/PranavNayee/aiverse-bot/actions" target="_blank" class="text-xs text-slate-400 hover:text-white font-mono flex items-center space-x-1">
            <span>Actions Console</span>
            <i class="fa-solid fa-arrow-up-right-from-square text-[9px]"></i>
          </a>
        </div>

        <div class="overflow-x-auto mt-3">
          <table class="w-full text-left text-xs">
            <thead class="text-[9px] uppercase font-mono text-slate-400 border-b border-white/5">
              <tr>
                <th class="py-2.5 px-2.5">Status</th>
                <th class="py-2.5 px-2.5">Workflow Name</th>
                <th class="py-2.5 px-2.5">Date</th>
                <th class="py-2.5 px-2.5 text-right">Log</th>
              </tr>
            </thead>
            <tbody id="runsTableBody" class="divide-y divide-white/5 font-mono text-slate-300">
              <tr>
                <td colspan="4" class="py-6 text-center text-slate-500">
                  <i class="fa-solid fa-circle-notch fa-spin mr-1 text-neonEmerald"></i> Loading history...
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

    </div>

  </main>

  <!-- MAIN TAB 2: ABOUT SYSTEM ARCHITECTURE VIEW (Detailed Documentation) -->
  <main id="tabAbout" class="hidden relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6 sm:py-8 flex-1 space-y-6 sm:space-y-8 w-full">

    <!-- Header Banner -->
    <div class="glass-card rounded-3xl p-6 sm:p-8 border border-white/10 relative overflow-hidden">
      <div class="absolute -right-16 -top-16 w-72 h-72 bg-neonCyan/10 rounded-full blur-3xl pointer-events-none"></div>
      
      <div class="flex items-center space-x-2.5 mb-2">
        <span class="px-2.5 py-0.5 rounded-full text-xs font-mono font-bold bg-neonCyan/10 text-neonCyan border border-neonCyan/30">
          SYSTEM SPECIFICATION
        </span>
        <span class="text-xs text-slate-400 font-mono">Architecture & Pipeline Blueprint</span>
      </div>
      
      <h2 class="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
        How AIVerse Bot Works: End-to-End Automation
      </h2>
      <p class="text-xs sm:text-sm text-slate-300 max-w-3xl mt-2 leading-relaxed">
        AIVerse is a 100% autonomous educational media engine designed to teach Artificial Intelligence in engaging Hinglish. 
        It writes scripts, generates expressive voiceovers, renders 2D animated mascot videos with synchronized word-level captions, 
        and publishes to Instagram Reels and YouTube Shorts on a strict cron schedule with self-healing deadlock prevention.
      </p>
    </div>

    <!-- 8-Stage Pipeline Flowchart Cards -->
    <div class="space-y-4">
      <h3 class="text-lg font-bold text-white flex items-center space-x-2">
        <i class="fa-solid fa-diagram-project text-neonEmerald"></i>
        <span>The 8-Stage Automated Reel Pipeline</span>
      </h3>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        
        <!-- Stage 1 -->
        <div class="glass-card rounded-2xl p-5 border border-white/10 hover:border-neonEmerald/40 transition">
          <div class="flex items-center justify-between text-xs font-mono text-neonEmerald mb-2">
            <span>STAGE 01</span>
            <i class="fa-solid fa-book-bookmark text-base"></i>
          </div>
          <h4 class="font-extrabold text-sm text-white">Curriculum Selection</h4>
          <p class="text-xs text-slate-400 mt-1.5 leading-relaxed">
            Picks the next slot's topic from a 224-item educational syllabus (100 core AI lessons, 70 practical tricks, 25 scam alerts, and 29 fun facts) with slot rotation.
          </p>
        </div>

        <!-- Stage 2 -->
        <div class="glass-card rounded-2xl p-5 border border-white/10 hover:border-neonCyan/40 transition">
          <div class="flex items-center justify-between text-xs font-mono text-neonCyan mb-2">
            <span>STAGE 02</span>
            <i class="fa-solid fa-pen-nib text-base"></i>
          </div>
          <h4 class="font-extrabold text-sm text-white">AI Script Generation</h4>
          <p class="text-xs text-slate-400 mt-1.5 leading-relaxed">
            Google Gemini 3.6 Flash crafts a high-retention 30s Hinglish script with an irresistible hook, real-world analogy, clear 3-step value, and comment-prompt call-to-action.
          </p>
        </div>

        <!-- Stage 3 -->
        <div class="glass-card rounded-2xl p-5 border border-white/10 hover:border-neonViolet/40 transition">
          <div class="flex items-center justify-between text-xs font-mono text-neonViolet mb-2">
            <span>STAGE 03</span>
            <i class="fa-solid fa-shield-halved text-base"></i>
          </div>
          <h4 class="font-extrabold text-sm text-white">3-Stage Fact Check</h4>
          <p class="text-xs text-slate-400 mt-1.5 leading-relaxed">
            Automated verification pass checks for technical accuracy, zero AI hallucinations, safety guidelines, and viral readability before audio synthesis begins.
          </p>
        </div>

        <!-- Stage 4 -->
        <div class="glass-card rounded-2xl p-5 border border-white/10 hover:border-neonPink/40 transition">
          <div class="flex items-center justify-between text-xs font-mono text-neonPink mb-2">
            <span>STAGE 04</span>
            <i class="fa-solid fa-microphone-lines text-base"></i>
          </div>
          <h4 class="font-extrabold text-sm text-white">Voice Synthesis (Charon)</h4>
          <p class="text-xs text-slate-400 mt-1.5 leading-relaxed">
            Synthesizes lifelike natural Indian-accented Hinglish audio using Gemini Charon voice. Generates precise per-word timing metadata for karaoke subtitles.
          </p>
        </div>

        <!-- Stage 5 -->
        <div class="glass-card rounded-2xl p-5 border border-white/10 hover:border-amber-400/40 transition">
          <div class="flex items-center justify-between text-xs font-mono text-amber-400 mb-2">
            <span>STAGE 05</span>
            <i class="fa-solid fa-film text-base"></i>
          </div>
          <h4 class="font-extrabold text-sm text-white">2D Character & Video Render</h4>
          <p class="text-xs text-slate-400 mt-1.5 leading-relaxed">
            Python 2D vector engine renders 'Seekho Bot' with lip-sync, gestures, dynamic stat callouts, soft background music ducking, and 1080x1920 30FPS MP4 video.
          </p>
        </div>

        <!-- Stage 6 -->
        <div class="glass-card rounded-2xl p-5 border border-white/10 hover:border-blue-400/40 transition">
          <div class="flex items-center justify-between text-xs font-mono text-blue-400 mb-2">
            <span>STAGE 06</span>
            <i class="fa-solid fa-cloud-arrow-up text-base"></i>
          </div>
          <h4 class="font-extrabold text-sm text-white">Cloud Queue & Storage</h4>
          <p class="text-xs text-slate-400 mt-1.5 leading-relaxed">
            Uploads high-resolution MP4 video and custom thumbnail to Supabase public storage. Writes atomic optimistic lock in pending.json to prevent race conditions.
          </p>
        </div>

        <!-- Stage 7 -->
        <div class="glass-card rounded-2xl p-5 border border-white/10 hover:border-emerald-400/40 transition">
          <div class="flex items-center justify-between text-xs font-mono text-emerald-400 mb-2">
            <span>STAGE 07</span>
            <i class="fa-brands fa-instagram text-base"></i>
          </div>
          <h4 class="font-extrabold text-sm text-white">Dual Distribution (IG + YT)</h4>
          <p class="text-xs text-slate-400 mt-1.5 leading-relaxed">
            Decoupled publisher uploads video to Instagram Reels via Meta Graph API container endpoint and cross-posts directly to YouTube Shorts with SEO tags.
          </p>
        </div>

        <!-- Stage 8 -->
        <div class="glass-card rounded-2xl p-5 border border-white/10 hover:border-teal-400/40 transition">
          <div class="flex items-center justify-between text-xs font-mono text-teal-400 mb-2">
            <span>STAGE 08</span>
            <i class="fa-solid fa-arrows-spin text-base"></i>
          </div>
          <h4 class="font-extrabold text-sm text-white">Auto-Reply & Learn Loop</h4>
          <p class="text-xs text-slate-400 mt-1.5 leading-relaxed">
            Monitors comments for keywords (e.g., 'PROMPT', 'NOTES'), automatically sends resources to viewers, and updates the hook-learning matrix based on view retention.
          </p>
        </div>

      </div>
    </div>

    <!-- Integrations & Tech Stack Breakdown -->
    <div class="glass-card rounded-3xl p-6 sm:p-8 border border-white/10 space-y-6">
      <h3 class="text-lg font-bold text-white flex items-center space-x-2">
        <i class="fa-solid fa-cubes text-neonCyan"></i>
        <span>Full Integration & Technology Stack</span>
      </h3>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-5">
        
        <div class="p-4 rounded-2xl bg-darker/60 border border-white/5 space-y-1.5">
          <div class="flex items-center space-x-2 text-pink-400 font-bold text-sm">
            <i class="fa-brands fa-instagram text-base"></i>
            <span>Meta Graph API (Instagram)</span>
          </div>
          <p class="text-xs text-slate-400 leading-relaxed">
            Connected to <strong class="text-white">@aiverse.agent</strong> (`17841479592722450`) using a <strong class="text-neonEmerald">Permanent System User Token</strong> with `Expires: Never`. Posts Reels, fetches engagement insights, and handles comment triggers.
          </p>
        </div>

        <div class="p-4 rounded-2xl bg-darker/60 border border-white/5 space-y-1.5">
          <div class="flex items-center space-x-2 text-red-400 font-bold text-sm">
            <i class="fa-brands fa-youtube text-base"></i>
            <span>YouTube Data API v3</span>
          </div>
          <p class="text-xs text-slate-400 leading-relaxed">
            Automated OAuth2 refresh token pipeline uploads each reel as a vertical YouTube Short with hashtags, custom thumbnails, and automatic playlist organization.
          </p>
        </div>

        <div class="p-4 rounded-2xl bg-darker/60 border border-white/5 space-y-1.5">
          <div class="flex items-center space-x-2 text-emerald-400 font-bold text-sm">
            <i class="fa-solid fa-brain text-base"></i>
            <span>Google Gemini AI & Voice</span>
          </div>
          <p class="text-xs text-slate-400 leading-relaxed">
            Gemini 3.6 Flash for high-speed script generation & hook optimization. Gemini Charon voice model synthesizes human-like natural Hinglish narration with word timestamps.
          </p>
        </div>

        <div class="p-4 rounded-2xl bg-darker/60 border border-white/5 space-y-1.5">
          <div class="flex items-center space-x-2 text-cyan-400 font-bold text-sm">
            <i class="fa-solid fa-database text-base"></i>
            <span>Supabase Cloud Storage</span>
          </div>
          <p class="text-xs text-slate-400 leading-relaxed">
            Stores media assets in a public CDN bucket (`cartoon-reels`). Manages `pending.json`, `history.json`, and `stats.json` for queue management and self-healing locks.
          </p>
        </div>

        <div class="p-4 rounded-2xl bg-darker/60 border border-white/5 space-y-1.5">
          <div class="flex items-center space-x-2 text-violet-400 font-bold text-sm">
            <i class="fa-brands fa-github text-base"></i>
            <span>GitHub Actions CI/CD</span>
          </div>
          <p class="text-xs text-slate-400 leading-relaxed">
            Cloud execution runner on Ubuntu-latest. Runs redundant cron triggers (9 daily backup schedules), pre-flight diagnostic checks, and manual workflow dispatch triggers.
          </p>
        </div>

        <div class="p-4 rounded-2xl bg-darker/60 border border-white/5 space-y-1.5">
          <div class="flex items-center space-x-2 text-amber-400 font-bold text-sm">
            <i class="fa-solid fa-compact-disc text-base"></i>
            <span>FFmpeg Media Engine</span>
          </div>
          <p class="text-xs text-slate-400 leading-relaxed">
            Encodes 1080x1920 30FPS H.264 video with AAC audio. Handles audio ducking (music softens when character speaks), font rasterization (Noto Sans + Emoji), and subtitles.
          </p>
        </div>

      </div>
    </div>

    <!-- Redundancy & Posting Schedule Specifications -->
    <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
      
      <div class="glass-card rounded-3xl p-6 border border-white/10 space-y-3">
        <h3 class="text-base font-bold text-white flex items-center space-x-2">
          <i class="fa-solid fa-clock text-cyan-400"></i>
          <span>Posting Schedule (IST India Time)</span>
        </h3>
        <p class="text-xs text-slate-300 leading-relaxed">
          The bot operates on two peak Indian social media engagement windows:
        </p>
        <ul class="space-y-2 text-xs font-mono text-slate-300">
          <li class="p-2.5 rounded-xl bg-darker/60 border border-white/5 flex items-center justify-between">
            <span class="text-neonEmerald font-bold">Slot 1: 08:00 AM IST</span>
            <span class="text-slate-400">Morning Drive Peak</span>
          </li>
          <li class="p-2.5 rounded-xl bg-darker/60 border border-white/5 flex items-center justify-between">
            <span class="text-neonCyan font-bold">Slot 2: 07:00 PM IST</span>
            <span class="text-slate-400">Evening Prime Peak</span>
          </li>
        </ul>
        <p class="text-[11px] text-slate-400 pt-1 leading-relaxed">
          Each reel is automatically generated hours ahead of time. If GitHub's cron runner is slightly delayed, a 180-minute late grace period ensures the reel still publishes smoothly.
        </p>
      </div>

      <div class="glass-card rounded-3xl p-6 border border-white/10 space-y-3">
        <h3 class="text-base font-bold text-white flex items-center space-x-2">
          <i class="fa-solid fa-shield-virus text-neonEmerald"></i>
          <span>Fail-Safe & Self-Healing Architecture</span>
        </h3>
        <ul class="space-y-2 text-xs text-slate-300">
          <li class="p-2 rounded-xl bg-darker/60 border border-white/5 flex items-start space-x-2">
            <i class="fa-solid fa-circle-check text-neonEmerald mt-0.5"></i>
            <span><strong>Decoupled Publishing:</strong> If Instagram API is temporarily slow, YouTube Shorts publishes independently without crashing.</span>
          </li>
          <li class="p-2 rounded-xl bg-darker/60 border border-white/5 flex items-start space-x-2">
            <i class="fa-solid fa-circle-check text-neonEmerald mt-0.5"></i>
            <span><strong>Queue Auto-Clearing:</strong> If a reel fails 3 attempts or sits stale >24h, it is auto-archived into Supabase so subsequent reels are never blocked.</span>
          </li>
          <li class="p-2 rounded-xl bg-darker/60 border border-white/5 flex items-start space-x-2">
            <i class="fa-solid fa-circle-check text-neonEmerald mt-0.5"></i>
            <span><strong>Duplicate Guard:</strong> Compares caption hashes against recent Instagram media before publishing to ensure zero duplicate posts.</span>
          </li>
        </ul>
      </div>

    </div>

  </main>

  <!-- POPUP VIDEO THEATER MODAL (Mobile Responsive) -->
  <div id="videoModal" class="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/85 backdrop-blur-xl hidden transition-all duration-300">
    <div class="glass-card w-full max-w-4xl rounded-3xl border border-neonEmerald/40 overflow-hidden shadow-2xl flex flex-col lg:flex-row max-h-[92vh]">
      
      <!-- Video Container -->
      <div class="w-full lg:w-[360px] bg-black flex items-center justify-center relative p-3 sm:p-4 flex-shrink-0">
        <div class="w-full max-w-[240px] xs:max-w-[260px] aspect-[9/16] rounded-2xl overflow-hidden bg-darker border-2 border-slate-800 shadow-xl relative">
          <video id="modalVideoPlayer" class="w-full h-full object-cover" controls playsinline autoplay loop>
            <source id="modalVideoSource" src="" type="video/mp4">
          </video>
        </div>
      </div>

      <!-- Video Details & Actions -->
      <div class="p-5 sm:p-6 flex-1 flex flex-col justify-between bg-panel/90 text-left overflow-y-auto">
        <div>
          <div class="flex items-center justify-between pb-3 border-b border-white/10">
            <span class="text-xs font-mono font-bold text-neonEmerald flex items-center">
              <span class="w-2 h-2 rounded-full bg-neonEmerald mr-2 animate-ping"></span>
              REEL PREVIEW THEATER
            </span>
            <button onclick="closeVideoModal()" class="text-slate-400 hover:text-white transition p-1">
              <i class="fa-solid fa-xmark text-lg"></i>
            </button>
          </div>

          <h3 id="modalVideoTitle" class="text-lg sm:text-xl font-bold text-white mt-3 sm:mt-4">Reel Title</h3>
          <p id="modalVideoDate" class="text-xs text-slate-400 font-mono mt-1">Date</p>

          <div class="mt-3 sm:mt-4 p-3.5 sm:p-4 rounded-xl bg-darker/60 border border-white/5 text-xs text-slate-300 leading-relaxed max-h-40 sm:max-h-52 overflow-y-auto" id="modalVideoCaption">
            Full Caption
          </div>
        </div>

        <div class="mt-4 sm:mt-6 pt-3.5 border-t border-white/10 flex flex-wrap items-center justify-between gap-2.5">
          <div class="flex flex-wrap items-center gap-2">
            <a id="modalInstagramLink" href="#" target="_blank" class="px-3.5 py-1.5 rounded-xl text-xs font-bold bg-pink-500 hover:bg-pink-600 text-white transition flex items-center space-x-1.5 shadow">
              <i class="fa-brands fa-instagram text-xs"></i>
              <span>Instagram</span>
            </a>
            <a id="modalDownloadLink" href="#" download="aiverse_reel.mp4" target="_blank" class="px-3 py-1.5 rounded-xl text-xs font-bold bg-slate-800 hover:bg-slate-700 text-white border border-slate-700 transition flex items-center space-x-1">
              <i class="fa-solid fa-download text-[11px] text-neonEmerald"></i>
              <span>Download</span>
            </a>
          </div>
          <button onclick="closeVideoModal()" class="text-xs text-slate-400 hover:text-white font-mono">
            Close [ESC]
          </button>
        </div>
      </div>

    </div>
  </div>

  <!-- Live Terminal Log Modal -->
  <div id="logModal" class="fixed inset-0 z-50 flex items-center justify-center p-3 sm:p-4 bg-black/80 backdrop-blur-md hidden transition-all duration-300">
    <div class="glass-card w-full max-w-4xl rounded-3xl border border-neonCyan/40 overflow-hidden shadow-2xl flex flex-col max-h-[85vh]">
      <div class="px-5 py-3.5 bg-panel border-b border-white/10 flex items-center justify-between">
        <div class="flex items-center space-x-2.5">
          <div class="flex space-x-1">
            <span class="w-2.5 h-2.5 rounded-full bg-red-500/80"></span>
            <span class="w-2.5 h-2.5 rounded-full bg-yellow-500/80"></span>
            <span class="w-2.5 h-2.5 rounded-full bg-emerald-500/80"></span>
          </div>
          <span class="text-xs font-mono font-bold text-white ml-2 flex items-center space-x-1.5 truncate max-w-[220px] sm:max-w-none">
            <i class="fa-solid fa-terminal text-neonCyan text-xs"></i>
            <span id="logModalTitle">Runner Output Log</span>
          </span>
        </div>
        <button onclick="closeLogModal()" class="text-slate-400 hover:text-white transition">
          <i class="fa-solid fa-xmark text-lg"></i>
        </button>
      </div>

      <div class="p-4 sm:p-6 bg-darker flex-1 overflow-y-auto font-mono text-[11px] sm:text-xs text-emerald-400 leading-relaxed whitespace-pre-wrap selection:bg-emerald-500 selection:text-black" id="terminalOutput">
        Loading runner stream...
      </div>

      <div class="px-5 py-2.5 bg-panel border-t border-white/10 flex items-center justify-between text-[11px] font-mono text-slate-400">
        <span>Tail 300 Lines</span>
        <button onclick="fetchCurrentModalLog()" class="text-cyan-400 hover:underline">
          <i class="fa-solid fa-rotate-right mr-1"></i> Refresh Log
        </button>
      </div>
    </div>
  </div>

  <footer class="relative z-10 border-t border-white/5 py-5 sm:py-6 text-center text-xs text-slate-500 font-mono px-4">
    <span>AIVerse Automation Bot &middot; Multi-Agent Educational Reel Generator &middot; Port 8080</span>
  </footer>

  <script>
    let isGlobalActive = true;
    let activeRunId = null;
    let currentViewingRunId = null;
    let allPostsData = [];

    // Tab Switcher (Controls vs About System Architecture)
    function switchTab(tab) {
      const tabDash = document.getElementById('tabDashboard');
      const tabAbt = document.getElementById('tabAbout');
      const navDash = document.getElementById('navTabDashboard');
      const navAbt = document.getElementById('navTabAbout');

      if (tab === 'about') {
        tabDash.classList.add('hidden');
        tabAbt.classList.remove('hidden');
        navAbt.className = "px-3 sm:px-4 py-1.5 sm:py-2 rounded-lg bg-neonCyan/15 text-neonCyan border border-neonCyan/30 font-bold transition flex items-center space-x-1.5";
        navDash.className = "px-3 sm:px-4 py-1.5 sm:py-2 rounded-lg text-slate-400 hover:text-white transition flex items-center space-x-1.5";
        window.scrollTo({ top: 0, behavior: 'smooth' });
      } else {
        tabAbt.classList.add('hidden');
        tabDash.classList.remove('hidden');
        navDash.className = "px-3 sm:px-4 py-1.5 sm:py-2 rounded-lg bg-neonEmerald/15 text-neonEmerald border border-neonEmerald/30 font-bold transition flex items-center space-x-1.5";
        navAbt.className = "px-3 sm:px-4 py-1.5 sm:py-2 rounded-lg text-slate-400 hover:text-white transition flex items-center space-x-1.5";
      }
    }

    function updateClock() {
      const now = new Date();
      const istTime = new Date(now.getTime() + (now.getTimezoneOffset() + 330) * 60000);
      
      const clockEl = document.getElementById('liveClock');
      if (clockEl) {
        clockEl.textContent = istTime.toLocaleTimeString('en-US', { hour12: false }) + ' IST';
      }

      const currentHours = istTime.getHours();
      const currentMinutes = istTime.getMinutes();
      const currentSeconds = istTime.getSeconds();

      let targetHour = 19;
      if (currentHours < 8) {
        targetHour = 8;
      } else if (currentHours >= 19) {
        targetHour = 32;
      }

      const totalCurrentSec = currentHours * 3600 + currentMinutes * 60 + currentSeconds;
      const targetSec = (targetHour > 24 ? targetHour - 24 : targetHour) * 3600;
      let diffSec = (targetHour >= 24 ? (24*3600 - totalCurrentSec) + (8*3600) : targetSec - totalCurrentSec);

      const h = Math.floor(diffSec / 3600);
      const m = Math.floor((diffSec % 3600) / 60);
      const s = diffSec % 60;

      const timerEl = document.getElementById('countdownTimer');
      if (timerEl) {
        timerEl.textContent = `${String(h).padStart(2, '0')}h ${String(m).padStart(2, '0')}m ${String(s).padStart(2, '0')}s`;
      }
    }
    setInterval(updateClock, 1000);
    updateClock();

    function showToast(msg, isSuccess = true) {
      const toast = document.getElementById('toast');
      const toastMsg = document.getElementById('toastMsg');
      const toastIcon = document.getElementById('toastIcon');
      toastMsg.textContent = msg;
      toastIcon.className = isSuccess ? 'fa-solid fa-circle-check text-neonEmerald text-base sm:text-lg' : 'fa-solid fa-triangle-exclamation text-neonPink text-base sm:text-lg';
      toast.classList.remove('translate-y-28', 'opacity-0');
      setTimeout(() => {
        toast.classList.add('translate-y-28', 'opacity-0');
      }, 4000);
    }

    async function fetchJSON(url, opts = {}) {
      try {
        const res = await fetch(url, opts);
        return await res.json();
      } catch (e) {
        return null;
      }
    }

    async function loadStatus() {
      const data = await fetchJSON('/api/status');
      if (!data) return;

      const wfList = document.getElementById('workflowsList');
      if (data.workflows && data.workflows.length > 0) {
        let anyActive = false;
        wfList.innerHTML = data.workflows.map(wf => {
          const isActive = wf.state === 'active';
          if (isActive) anyActive = true;
          return `
            <div class="flex items-center justify-between p-3 rounded-2xl bg-darker/60 border border-white/5 hover:border-white/10 transition">
              <div>
                <p class="text-xs font-bold text-white tracking-wide">${wf.name}</p>
                <p class="text-[10px] font-mono text-slate-500">${wf.path.split('/').pop()}</p>
              </div>
              <button onclick="toggleWorkflow('${wf.path}', ${isActive})" class="px-2.5 py-1 rounded-full text-[9px] font-mono font-bold transition transform active:scale-95 ${
                isActive 
                  ? 'bg-neonEmerald/10 text-neonEmerald border border-neonEmerald/30 hover:bg-neonEmerald/20' 
                  : 'bg-neonPink/10 text-neonPink border border-neonPink/30 hover:bg-neonPink/20'
              }">
                ${isActive ? 'ENABLED' : 'PAUSED'}
              </button>
            </div>
          `;
        }).join('');

        isGlobalActive = anyActive;
        const btn = document.getElementById('btnGlobalToggle');
        if (isGlobalActive) {
          btn.innerHTML = '<i class="fa-solid fa-pause text-xs"></i><span class="hidden sm:inline">Pause All Automation</span><span class="sm:hidden">Pause</span>';
          btn.className = "px-3 sm:px-4 py-2 sm:py-2.5 rounded-xl text-xs font-bold flex items-center space-x-1.5 sm:space-x-2 transition-all duration-300 shadow-lg transform active:scale-95 bg-amber-500/10 text-amber-300 border border-amber-500/30 hover:bg-amber-500/20";
        } else {
          btn.innerHTML = '<i class="fa-solid fa-play text-xs"></i><span class="hidden sm:inline">Resume All Automation</span><span class="sm:hidden">Resume</span>';
          btn.className = "px-3 sm:px-4 py-2 sm:py-2.5 rounded-xl text-xs font-bold flex items-center space-x-1.5 sm:space-x-2 transition-all duration-300 shadow-lg transform active:scale-95 bg-neonEmerald/10 text-neonEmerald border border-neonEmerald/30 hover:bg-neonEmerald/20";
        }
      }
    }

    async function loadRuns() {
      const runs = await fetchJSON('/api/runs');
      if (!runs) return;

      const tbody = document.getElementById('runsTableBody');
      const activeBanner = document.getElementById('activeRunBanner');
      const activeRunName = document.getElementById('activeRunName');

      let currentActive = null;

      tbody.innerHTML = runs.map(r => {
        let statusBadge = '';
        if (r.status === 'in_progress' || r.status === 'queued') {
          currentActive = r;
          statusBadge = '<span class="inline-flex items-center px-2 py-0.5 rounded-full text-[9px] font-bold bg-amber-500/15 text-amber-300 border border-amber-500/30"><i class="fa-solid fa-spinner fa-spin mr-1"></i> RUNNING</span>';
        } else if (r.conclusion === 'success') {
          statusBadge = '<span class="inline-flex items-center px-2 py-0.5 rounded-full text-[9px] font-bold bg-neonEmerald/15 text-neonEmerald border border-neonEmerald/30"><i class="fa-solid fa-check mr-1"></i> SUCCESS</span>';
        } else if (r.conclusion === 'failure') {
          statusBadge = '<span class="inline-flex items-center px-2 py-0.5 rounded-full text-[9px] font-bold bg-neonPink/15 text-neonPink border border-neonPink/30"><i class="fa-solid fa-xmark mr-1"></i> FAILED</span>';
        } else {
          statusBadge = `<span class="inline-flex items-center px-2 py-0.5 rounded-full text-[9px] font-bold bg-slate-800 text-slate-400">${r.conclusion || r.status}</span>`;
        }

        const dateStr = new Date(r.createdAt).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });

        return `
          <tr class="hover:bg-panel/60 transition group">
            <td class="py-2.5 px-2.5">${statusBadge}</td>
            <td class="py-2.5 px-2.5 font-medium text-white truncate max-w-[140px] sm:max-w-none">${r.name || r.workflowName}</td>
            <td class="py-2.5 px-2.5 text-slate-400 whitespace-nowrap">${dateStr}</td>
            <td class="py-2.5 px-2.5 text-right">
              <button onclick="viewRunLog(${r.databaseId}, '${r.name || r.workflowName}')" class="px-2 py-0.5 rounded-lg bg-panelBorder/60 hover:bg-panelBorder text-neonCyan hover:text-white transition inline-flex items-center space-x-1">
                <i class="fa-solid fa-terminal text-[9px]"></i>
                <span>Log</span>
              </button>
            </td>
          </tr>
        `;
      }).join('');

      if (currentActive) {
        activeRunId = currentActive.databaseId;
        activeRunName.textContent = `${currentActive.name} (#${currentActive.databaseId})`;
        activeBanner.classList.remove('hidden');
      } else {
        activeRunId = null;
        activeBanner.classList.add('hidden');
      }
    }

    async function loadPosts() {
      const posts = await fetchJSON('/api/posts');
      const grid = document.getElementById('postsGrid');
      if (!posts || posts.length === 0) {
        grid.innerHTML = '<div class="col-span-full py-12 text-center text-slate-500 font-mono text-xs">No recent reels found in feed.</div>';
        return;
      }

      allPostsData = posts;

      // Update Hero Section
      const latest = posts[0];
      if (latest) {
        const lines = (latest.caption || 'New AIVerse Reel').split('\\n');
        const heroTitle = lines[0] || 'AIVerse Reel';
        const heroCaption = lines.slice(1).join('\\n').trim() || latest.caption;
        const dateStr = new Date(latest.timestamp).toLocaleDateString('en-IN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });

        document.getElementById('heroReelTitle').textContent = heroTitle;
        document.getElementById('heroReelDate').textContent = `Published on ${dateStr}`;
        document.getElementById('heroReelCaption').textContent = heroCaption;
        document.getElementById('heroInstagramLink').href = latest.permalink;

        const videoPlayer = document.getElementById('heroVideoPlayer');
        const videoSource = document.getElementById('heroVideoSource');
        const downloadLink = document.getElementById('heroDownloadLink');

        if (latest.media_url) {
          videoSource.src = latest.media_url;
          videoPlayer.poster = latest.thumbnail_url || '';
          videoPlayer.load();
          downloadLink.href = latest.media_url;
        }
      }

      // Render Gallery
      grid.innerHTML = posts.map((p, idx) => {
        const thumb = p.thumbnail_url || p.media_url || 'https://images.unsplash.com/photo-1618005182384-a83a8bd57fbe?w=600&auto=format&fit=crop&q=80';
        const dateStr = new Date(p.timestamp).toLocaleDateString('en-IN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
        const captionLines = (p.caption || 'New AIVerse Reel').split('\\n');
        const title = captionLines[0] || 'AIVerse Reel';

        return `
          <div class="glass-card rounded-2xl overflow-hidden border border-white/10 hover:border-pink-500/40 transition-all duration-300 flex flex-col group shadow-lg">
            
            <div class="relative aspect-[9/13] bg-darker overflow-hidden cursor-pointer" onclick="openVideoModal(${idx})">
              <img src="${thumb}" alt="Reel thumbnail" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-500 ease-out">
              <div class="absolute inset-0 bg-gradient-to-t from-darker via-transparent to-black/20 opacity-90"></div>
              
              <div class="absolute top-2.5 left-2.5 bg-gradient-to-r from-pink-500 to-rose-500 text-white text-[9px] font-black px-2 py-0.5 rounded-full flex items-center space-x-1 shadow">
                <i class="fa-brands fa-instagram"></i>
                <span>REEL</span>
              </div>

              <div class="absolute top-2.5 right-2.5 bg-black/60 backdrop-blur-md text-slate-300 text-[9px] font-mono px-2 py-0.5 rounded-full border border-white/10">
                ${dateStr}
              </div>

              <div class="absolute inset-0 flex items-center justify-center opacity-85 group-hover:opacity-100 transition-opacity duration-300 bg-black/20 group-hover:bg-black/40 backdrop-blur-[1px]">
                <div class="w-11 sm:w-13 h-11 sm:h-13 rounded-full bg-pink-500/90 text-white flex items-center justify-center text-lg sm:text-xl shadow-2xl transform scale-90 group-hover:scale-110 transition duration-300">
                  <i class="fa-solid fa-play ml-1"></i>
                </div>
              </div>
            </div>

            <div class="p-3.5 flex-1 flex flex-col justify-between bg-panel/40">
              <div>
                <h3 class="text-xs font-extrabold text-white group-hover:text-pink-400 transition line-clamp-2">${title}</h3>
              </div>

              <div class="mt-3 pt-2.5 border-t border-white/5 flex items-center justify-between">
                <button onclick="openVideoModal(${idx})" class="text-[10px] font-bold text-neonEmerald hover:underline flex items-center space-x-1">
                  <i class="fa-solid fa-play text-[8px]"></i>
                  <span>Watch Reel</span>
                </button>
                <a href="${p.permalink}" target="_blank" class="text-slate-400 hover:text-white text-xs">
                  <i class="fa-solid fa-arrow-up-right-from-square text-[9px]"></i>
                </a>
              </div>
            </div>

          </div>
        `;
      }).join('');
    }

    function openVideoModal(idx) {
      const p = allPostsData[idx];
      if (!p) return;

      const lines = (p.caption || 'AIVerse Reel').split('\\n');
      const title = lines[0] || 'AIVerse Reel';
      const caption = lines.slice(1).join('\\n').trim() || p.caption;
      const dateStr = new Date(p.timestamp).toLocaleDateString('en-IN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });

      document.getElementById('modalVideoTitle').textContent = title;
      document.getElementById('modalVideoDate').textContent = `Published on ${dateStr}`;
      document.getElementById('modalVideoCaption').textContent = caption;
      document.getElementById('modalInstagramLink').href = p.permalink;

      const modalPlayer = document.getElementById('modalVideoPlayer');
      const modalSource = document.getElementById('modalVideoSource');
      const downloadLink = document.getElementById('modalDownloadLink');

      if (p.media_url) {
        modalSource.src = p.media_url;
        modalPlayer.load();
        modalPlayer.play().catch(() => {});
        downloadLink.href = p.media_url;
      }

      document.getElementById('videoModal').classList.remove('hidden');
    }

    function closeVideoModal() {
      const modalPlayer = document.getElementById('modalVideoPlayer');
      modalPlayer.pause();
      document.getElementById('videoModal').classList.add('hidden');
    }

    function copyHeroCaption() {
      const cap = document.getElementById('heroReelCaption').textContent;
      navigator.clipboard.writeText(cap);
      showToast('Caption copied to clipboard!', true);
    }

    async function triggerAction(actionName) {
      showToast(`Initiating: ${actionName}...`, true);
      const res = await fetchJSON('/api/action/trigger', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: actionName })
      });
      if (res && res.ok) {
        showToast(`Action dispatched to GitHub runner!`, true);
        setTimeout(refreshAll, 1500);
      } else {
        showToast(`Failed: ${res ? res.message : 'Error'}`, false);
      }
    }

    async function toggleWorkflow(path, currentState) {
      const action = currentState ? 'disable' : 'enable';
      showToast(`${action === 'enable' ? 'Enabling' : 'Pausing'} workflow schedule...`, true);
      const res = await fetchJSON('/api/action/workflow_toggle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: path, enable: !currentState })
      });
      if (res && res.ok) {
        showToast(`Workflow status updated!`, true);
        loadStatus();
      }
    }

    async function toggleGlobalAutomation() {
      const shouldEnable = !isGlobalActive;
      showToast(`${shouldEnable ? 'Resuming' : 'Pausing'} all automated schedules...`, true);
      const res = await fetchJSON(shouldEnable ? '/api/action/resume' : '/api/action/pause', { method: 'POST' });
      if (res && res.ok) {
        showToast(shouldEnable ? 'All automations resumed!' : 'All automations paused!', true);
        loadStatus();
      }
    }

    async function cancelActiveRun() {
      if (!activeRunId) return;
      if (!confirm(`Cancel workflow execution #${activeRunId}?`)) return;
      showToast(`Terminating workflow run #${activeRunId}...`, true);
      const res = await fetchJSON('/api/action/cancel', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ run_id: activeRunId })
      });
      if (res && res.ok) {
        showToast('Cancel signal delivered', true);
        setTimeout(refreshAll, 2500);
      }
    }

    async function viewRunLog(runId, name) {
      currentViewingRunId = runId;
      document.getElementById('logModalTitle').textContent = `Log &middot; ${name} (#${runId})`;
      document.getElementById('terminalOutput').textContent = 'Connecting to GitHub Runner log stream...';
      document.getElementById('logModal').classList.remove('hidden');
      await fetchCurrentModalLog();
    }

    async function fetchCurrentModalLog() {
      if (!currentViewingRunId) return;
      const res = await fetchJSON(`/api/log?run_id=${currentViewingRunId}`);
      const term = document.getElementById('terminalOutput');
      if (res && res.log) {
        term.textContent = res.log;
        term.scrollTop = term.scrollHeight;
      } else {
        term.textContent = 'Runner output currently unavailable or initializing...';
      }
    }

    function openLiveLogModal() {
      if (activeRunId) {
        viewRunLog(activeRunId, 'Active Workflow Run');
      }
    }

    function closeLogModal() {
      document.getElementById('logModal').classList.add('hidden');
      currentViewingRunId = null;
    }

    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape') {
        closeVideoModal();
        closeLogModal();
      }
    });

    async function refreshAll() {
      const icon = document.getElementById('refreshIcon');
      if (icon) icon.classList.add('fa-spin');
      await Promise.all([loadStatus(), loadRuns(), loadPosts()]);
      if (icon) icon.classList.remove('fa-spin');
    }

    refreshAll();
    setInterval(refreshAll, 12000);
  </script>
</body>
</html>
"""

class DashboardHandler(http.server.BaseHTTPRequestHandler):
    def _send_json(self, data, status=200):
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(json.dumps(data).encode("utf-8"))

    def do_GET(self):
        url = urllib.parse.urlparse(self.path)
        params = urllib.parse.parse_qs(url.query)

        if url.path == "/" or url.path == "/index.html" or url.path == "/about":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            docs_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "docs", "index.html")
            if os.path.exists(docs_path):
                with open(docs_path, "rb") as f:
                    self.wfile.write(f.read())
            else:
                self.wfile.write(HTML_PAGE.encode("utf-8"))

        elif url.path == "/api/status":
            wfs = get_workflows_status()
            self._send_json({"ok": True, "workflows": wfs, "account": "aiverse.agent", "user_id": IG_USER_ID})

        elif url.path == "/api/runs":
            runs = get_recent_runs(10)
            self._send_json(runs)

        elif url.path == "/api/posts":
            posts = get_instagram_posts(8)
            self._send_json(posts)

        elif url.path == "/api/log":
            run_id = params.get("run_id", [None])[0]
            if run_id:
                log_data = get_run_logs(run_id)
                self._send_json({"ok": True, "log": log_data})
            else:
                self._send_json({"ok": False, "error": "Missing run_id"})
        else:
            self.send_error(404, "Not Found")

    def do_POST(self):
        url = urllib.parse.urlparse(self.path)
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length).decode("utf-8") if length > 0 else "{}"
        try:
            payload = json.loads(body)
        except Exception:
            payload = {}

        if url.path == "/api/action/trigger":
            act = payload.get("action")
            if act == "post_now":
                ok, msg = trigger_workflow(".github/workflows/daily.yml", {"post_now": "true", "force_new": "true", "dry_run": "false"})
            elif act == "dry_run":
                ok, msg = trigger_workflow(".github/workflows/daily.yml", {"dry_run": "true"})
            elif act == "check":
                ok, msg = trigger_workflow(".github/workflows/check.yml")
            elif act == "engage":
                ok, msg = trigger_workflow(".github/workflows/engage.yml")
            else:
                ok, msg = False, "Unknown action"
            self._send_json({"ok": ok, "message": msg})

        elif url.path == "/api/action/workflow_toggle":
            path = payload.get("path")
            enable = payload.get("enable", True)
            ok, msg = set_workflow_state(path, enable=enable)
            self._send_json({"ok": ok, "message": msg})

        elif url.path == "/api/action/pause":
            results = []
            for w in ["daily.yml", "post.yml", "engage.yml", "weekly.yml"]:
                ok, _ = set_workflow_state(f".github/workflows/{w}", enable=False)
                results.append(ok)
            self._send_json({"ok": all(results)})

        elif url.path == "/api/action/resume":
            results = []
            for w in ["daily.yml", "post.yml", "engage.yml", "weekly.yml"]:
                ok, _ = set_workflow_state(f".github/workflows/{w}", enable=True)
                results.append(ok)
            self._send_json({"ok": all(results)})

        elif url.path == "/api/action/cancel":
            run_id = payload.get("run_id")
            if run_id:
                ok, msg = cancel_run(run_id)
                self._send_json({"ok": ok, "message": msg})
            else:
                self._send_json({"ok": False, "error": "Missing run_id"})
        else:
            self.send_error(404, "Not Found")


def run_server():
    server_address = ("", PORT)
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(server_address, DashboardHandler) as httpd:
        print(f"\\n==================================================")
        print(f"🎛️  AIVerse OS Command Center & Architecture is LIVE!")
        print(f"👉 Open in your browser: http://localhost:{PORT}")
        print(f"==================================================\\n")
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()

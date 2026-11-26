#!/usr/bin/env python3
"""
AIVerse Bot - Ultra-Modern Animated Command Center with In-Dashboard Video Player
Futuristic glassmorphic UI with dynamic particle mesh, live countdown, terminal log streaming,
action controls, and an interactive 9:16 Video Reel Player to preview and play generated reels directly!
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
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <meta name="referrer" content="no-referrer">
  <title>AIVerse OS &middot; AI Reel Command Center</title>
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
            'pulse-glow': 'pulse-glow 2s infinite ease-in-out',
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
            },
            'pulse-glow': {
              '0%, 100%': { opacity: '1', filter: 'drop-shadow(0 0 16px rgba(16, 185, 129, 0.7))' },
              '50%': { opacity: '0.4', filter: 'drop-shadow(0 0 4px rgba(16, 185, 129, 0.1))' }
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
      background: rgba(14, 19, 31, 0.75);
      backdrop-filter: blur(20px);
      -webkit-backdrop-filter: blur(20px);
      border: 1px solid rgba(255, 255, 255, 0.08);
    }
    .glass-card:hover {
      border-color: rgba(16, 185, 129, 0.35);
      box-shadow: 0 0 35px -5px rgba(16, 185, 129, 0.12);
    }
    .glass-header {
      background: rgba(7, 9, 14, 0.88);
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
      box-shadow: 0 25px 60px -15px rgba(0, 0, 0, 0.8), 0 0 40px rgba(16, 185, 129, 0.2);
    }
    ::-webkit-scrollbar { width: 6px; height: 6px; }
    ::-webkit-scrollbar-track { background: #07090e; }
    ::-webkit-scrollbar-thumb { background: #1c2438; border-radius: 999px; }
    ::-webkit-scrollbar-thumb:hover { background: #10b981; }
  </style>
</head>
<body class="bg-dark text-slate-100 min-h-screen flex flex-col font-sans antialiased overflow-x-hidden selection:bg-neonEmerald selection:text-black">

  <!-- Ambient Animated Lighting Spheres -->
  <div class="fixed inset-0 pointer-events-none overflow-hidden z-0">
    <div class="absolute -top-32 -left-32 w-96 h-96 bg-emerald-500/15 rounded-full blur-3xl animate-blob"></div>
    <div class="absolute top-1/4 -right-32 w-96 h-96 bg-cyan-500/15 rounded-full blur-3xl animate-blob animation-delay-2000"></div>
    <div class="absolute -bottom-32 left-1/3 w-96 h-96 bg-violet-600/15 rounded-full blur-3xl animate-blob animation-delay-4000"></div>
    <div class="absolute inset-0 bg-grid opacity-60"></div>
  </div>

  <!-- Top Glass Bar -->
  <header class="glass-header sticky top-0 z-40 transition-all duration-300">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-20 flex items-center justify-between relative z-10">
      
      <!-- Brand Logo -->
      <div class="flex items-center space-x-4">
        <div class="relative group cursor-pointer">
          <div class="absolute -inset-1 bg-gradient-to-r from-neonEmerald to-neonCyan rounded-2xl blur opacity-70 group-hover:opacity-100 transition duration-300"></div>
          <div class="relative w-12 h-12 rounded-xl bg-panel flex items-center justify-center border border-white/10 text-neonEmerald text-2xl font-black">
            <i class="fa-solid fa-atom animate-spin-slow"></i>
          </div>
        </div>
        <div>
          <div class="flex items-center space-x-2">
            <h1 class="text-xl font-extrabold tracking-tight bg-gradient-to-r from-white via-slate-100 to-neonEmerald bg-clip-text text-transparent">
              AIVerse OS
            </h1>
            <span class="text-[10px] font-mono px-2 py-0.5 rounded-full bg-neonCyan/10 text-neonCyan border border-neonCyan/30 font-bold uppercase tracking-wider">v3.5 Video Preview</span>
          </div>
          <p class="text-xs text-slate-400 flex items-center space-x-1.5 mt-0.5">
            <span class="text-slate-300 font-medium">@aiverse.agent</span>
            <span>&middot;</span>
            <span class="text-slate-400">Autonomous Hinglish AI Creator</span>
          </p>
        </div>
      </div>

      <!-- Live Clock & Top Controls -->
      <div class="flex items-center space-x-4">
        
        <div class="hidden md:flex items-center space-x-3 px-4 py-2 rounded-xl bg-panel/80 border border-panelBorder/80 font-mono text-xs">
          <div class="flex items-center space-x-1.5 text-cyan-400">
            <i class="fa-regular fa-clock"></i>
            <span id="liveClock" class="font-bold">--:--:-- IST</span>
          </div>
          <span class="text-slate-600">|</span>
          <div class="text-slate-400 flex items-center space-x-1">
            <span>Next:</span>
            <span id="nextSlotBadge" class="text-neonEmerald font-bold">19:00 IST</span>
          </div>
        </div>

        <!-- Master Switch (Pause / Resume) -->
        <button onclick="toggleGlobalAutomation()" id="btnGlobalToggle" class="px-4 py-2.5 rounded-xl text-xs font-bold flex items-center space-x-2 transition-all duration-300 shadow-lg transform hover:scale-[1.03] active:scale-[0.97] bg-amber-500/10 text-amber-300 border border-amber-500/30 hover:bg-amber-500/20">
          <i class="fa-solid fa-pause"></i>
          <span>Pause Automation</span>
        </button>

        <!-- Refresh Button -->
        <button onclick="refreshAll()" class="w-10 h-10 rounded-xl bg-panel border border-panelBorder flex items-center justify-center text-slate-400 hover:text-white hover:border-slate-600 transition-all transform hover:rotate-180 duration-500" title="Refresh Feed">
          <i id="refreshIcon" class="fa-solid fa-arrows-rotate text-sm"></i>
        </button>

      </div>
    </div>
  </header>

  <!-- Real-Time In-Progress Workflow Banner -->
  <div id="activeRunBanner" class="hidden relative z-30 bg-gradient-to-r from-emerald-950 via-panel to-cyan-950 border-b border-neonEmerald/40 py-3.5 px-4 shadow-xl">
    <div class="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4 text-sm">
      <div class="flex items-center space-x-3">
        <div class="relative flex h-3 w-3">
          <span class="animate-ping absolute inline-flex h-full w-full rounded-full bg-neonEmerald opacity-75"></span>
          <span class="relative inline-flex rounded-full h-3 w-3 bg-neonEmerald"></span>
        </div>
        <div class="flex items-center space-x-2">
          <span class="font-extrabold text-white tracking-wide">LIVE WORKFLOW RUNNING:</span>
          <span id="activeRunName" class="text-neonEmerald font-mono font-semibold">Generating & Posting Reel...</span>
        </div>
      </div>
      <div class="flex items-center space-x-3">
        <button onclick="openLiveLogModal()" class="px-3.5 py-1.5 rounded-lg text-xs font-semibold bg-cyan-500/10 text-cyan-300 border border-cyan-500/30 hover:bg-cyan-500/20 transition flex items-center space-x-1.5">
          <i class="fa-solid fa-terminal text-cyan-400"></i>
          <span>Stream Terminal Log</span>
        </button>
        <button onclick="cancelActiveRun()" class="px-3 py-1.5 rounded-lg text-xs font-semibold bg-red-500/10 text-red-400 border border-red-500/30 hover:bg-red-500/20 transition flex items-center space-x-1">
          <i class="fa-solid fa-stop text-[10px]"></i>
          <span>Abort Run</span>
        </button>
      </div>
    </div>
  </div>

  <!-- Toast Notification -->
  <div id="toast" class="fixed bottom-8 right-8 z-50 transform translate-y-28 opacity-0 transition-all duration-300 pointer-events-none">
    <div class="glass-card px-5 py-3.5 rounded-2xl border border-neonEmerald/50 text-white text-sm flex items-center space-x-3 shadow-2xl">
      <i id="toastIcon" class="fa-solid fa-circle-check text-neonEmerald text-lg"></i>
      <span id="toastMsg" class="font-medium">Action processed</span>
    </div>
  </div>

  <!-- Main Content Container -->
  <main class="relative z-10 max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 space-y-8 w-full">

    <!-- HERO SECTION: LATEST GENERATED REEL PLAYER -->
    <div class="glass-card rounded-3xl p-6 sm:p-8 border border-white/10 relative overflow-hidden">
      <div class="absolute -right-20 -top-20 w-80 h-80 bg-neonEmerald/10 rounded-full blur-3xl pointer-events-none"></div>
      
      <div class="flex flex-col lg:flex-row items-center gap-8">
        
        <!-- Interactive 9:16 Mobile Video Frame -->
        <div class="w-full max-w-[280px] sm:max-w-[300px] flex-shrink-0">
          <div class="phone-frame relative aspect-[9/16] rounded-[2.5rem] bg-darker p-3 border-4 border-slate-800/90 shadow-2xl overflow-hidden group">
            
            <!-- Phone Speaker Notch -->
            <div class="absolute top-4 left-1/2 -translate-x-1/2 w-20 h-4 bg-slate-800 rounded-full z-20 flex items-center justify-center">
              <div class="w-3 h-3 rounded-full bg-slate-900 mr-2"></div>
              <div class="w-8 h-1.5 rounded-full bg-slate-900"></div>
            </div>

            <!-- HTML5 Video Player -->
            <div class="w-full h-full rounded-[2rem] overflow-hidden bg-black relative">
              <video id="heroVideoPlayer" class="w-full h-full object-cover" controls playsinline loop preload="metadata" poster="">
                <source id="heroVideoSource" src="" type="video/mp4">
                Your browser does not support HTML5 video.
              </video>

              <!-- Floating Live Tag -->
              <div class="absolute top-4 left-4 z-10 pointer-events-none">
                <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-[10px] font-black bg-pink-500/90 text-white tracking-wider shadow">
                  <i class="fa-brands fa-instagram mr-1"></i> REEL PREVIEW
                </span>
              </div>
            </div>

          </div>
        </div>

        <!-- Reel Metadata & Controls -->
        <div class="flex-1 flex flex-col justify-between space-y-5 text-left w-full">
          <div>
            <div class="flex flex-wrap items-center gap-2 mb-3">
              <span class="px-3 py-1 rounded-full text-xs font-mono font-bold bg-neonEmerald/10 text-neonEmerald border border-neonEmerald/30">
                <i class="fa-solid fa-circle-check mr-1.5"></i> LATEST PUBLISHED REEL
              </span>
              <span id="heroReelDate" class="text-xs font-mono text-slate-400">Published Today</span>
            </div>

            <h2 id="heroReelTitle" class="text-2xl sm:text-3xl font-extrabold text-white tracking-tight">
              Loading latest reel...
            </h2>

            <div class="mt-4 p-4 rounded-2xl bg-darker/60 border border-white/5">
              <p class="text-xs font-mono text-slate-400 uppercase tracking-wider mb-1.5 flex items-center justify-between">
                <span>Caption & Hook Script</span>
                <button onclick="copyHeroCaption()" class="text-neonCyan hover:underline text-[11px] normal-case">
                  <i class="fa-regular fa-copy mr-1"></i> Copy Caption
                </button>
              </p>
              <p id="heroReelCaption" class="text-xs text-slate-300 leading-relaxed font-sans line-clamp-4">
                Querying latest reel from Instagram Graph API...
              </p>
            </div>
          </div>

          <!-- Feature Specs Matrix -->
          <div class="grid grid-cols-2 sm:grid-cols-4 gap-3">
            <div class="p-3 rounded-xl bg-panel/60 border border-white/5">
              <span class="text-[10px] font-mono text-slate-500 block uppercase">Voice Model</span>
              <span class="text-xs font-bold text-white mt-0.5 block">Gemini Charon</span>
            </div>
            <div class="p-3 rounded-xl bg-panel/60 border border-white/5">
              <span class="text-[10px] font-mono text-slate-500 block uppercase">Language</span>
              <span class="text-xs font-bold text-white mt-0.5 block">Hinglish AI</span>
            </div>
            <div class="p-3 rounded-xl bg-panel/60 border border-white/5">
              <span class="text-[10px] font-mono text-slate-500 block uppercase">Animation</span>
              <span class="text-xs font-bold text-neonEmerald mt-0.5 block">2D Character Sync</span>
            </div>
            <div class="p-3 rounded-xl bg-panel/60 border border-white/5">
              <span class="text-[10px] font-mono text-slate-500 block uppercase">Platforms</span>
              <span class="text-xs font-bold text-neonCyan mt-0.5 block">IG Reels + YouTube</span>
            </div>
          </div>

          <!-- Direct Watch Buttons -->
          <div class="flex flex-wrap items-center gap-3 pt-2">
            <a id="heroInstagramLink" href="https://www.instagram.com/aiverse.agent/" target="_blank" class="px-5 py-2.5 rounded-xl font-bold text-xs bg-gradient-to-r from-pink-500 to-rose-600 hover:from-pink-600 hover:to-rose-700 text-white shadow-lg shadow-pink-900/30 transition flex items-center space-x-2">
              <i class="fa-brands fa-instagram text-sm"></i>
              <span>Watch on Instagram</span>
            </a>
            <a id="heroDownloadLink" href="#" download="aiverse_reel.mp4" target="_blank" class="px-4 py-2.5 rounded-xl font-bold text-xs bg-slate-800 hover:bg-slate-700 text-slate-200 border border-slate-700 transition flex items-center space-x-2">
              <i class="fa-solid fa-download text-sm text-neonEmerald"></i>
              <span>Download MP4</span>
            </a>
          </div>

        </div>

      </div>
    </div>

    <!-- Quick Stats Grid -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
      
      <!-- Card 1: Account -->
      <div class="glass-card rounded-2xl p-6 relative overflow-hidden transition-all duration-300 group">
        <div class="flex items-center justify-between">
          <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider font-mono">Instagram Target</span>
          <div class="w-8 h-8 rounded-lg bg-pink-500/10 flex items-center justify-center text-pink-400">
            <i class="fa-brands fa-instagram text-base"></i>
          </div>
        </div>
        <div class="mt-3">
          <a href="https://www.instagram.com/aiverse.agent/" target="_blank" class="text-xl font-bold text-white hover:text-pink-400 transition flex items-center space-x-1.5">
            <span>@aiverse.agent</span>
            <i class="fa-solid fa-arrow-up-right-from-square text-xs opacity-60"></i>
          </a>
          <p class="text-[11px] text-slate-400 font-mono mt-0.5">UID: 17841479592722450</p>
        </div>
        <div class="mt-4 pt-3 border-t border-white/5 flex items-center justify-between text-xs">
          <span class="text-slate-400">Token Status</span>
          <span class="inline-flex items-center text-neonEmerald font-bold">
            <i class="fa-solid fa-infinity text-xs mr-1"></i> Never Expires
          </span>
        </div>
      </div>

      <!-- Card 2: YouTube Shorts -->
      <div class="glass-card rounded-2xl p-6 relative overflow-hidden transition-all duration-300 group">
        <div class="flex items-center justify-between">
          <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider font-mono">YouTube Shorts</span>
          <div class="w-8 h-8 rounded-lg bg-red-500/10 flex items-center justify-center text-red-400">
            <i class="fa-brands fa-youtube text-base"></i>
          </div>
        </div>
        <div class="mt-3">
          <p class="text-xl font-bold text-white">Cross-Post Sync</p>
          <p class="text-[11px] text-slate-400 font-mono mt-0.5">Automated Dual-Distribution</p>
        </div>
        <div class="mt-4 pt-3 border-t border-white/5 flex items-center justify-between text-xs">
          <span class="text-slate-400">OAuth Refresh</span>
          <span class="text-neonEmerald font-bold flex items-center">
            <i class="fa-solid fa-check mr-1 text-[10px]"></i> Connected
          </span>
        </div>
      </div>

      <!-- Card 3: Next Scheduled Post -->
      <div class="glass-card rounded-2xl p-6 relative overflow-hidden transition-all duration-300 group">
        <div class="flex items-center justify-between">
          <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider font-mono">Next Slot Countdown</span>
          <div class="w-8 h-8 rounded-lg bg-cyan-500/10 flex items-center justify-center text-cyan-400">
            <i class="fa-solid fa-stopwatch text-base"></i>
          </div>
        </div>
        <div class="mt-3">
          <p id="countdownTimer" class="text-xl font-bold text-neonCyan font-mono">--h --m --s</p>
          <p class="text-[11px] text-slate-400 mt-0.5">Slots: 08:00 AM & 07:00 PM IST</p>
        </div>
        <div class="mt-4 pt-3 border-t border-white/5 flex items-center justify-between text-xs">
          <span class="text-slate-400">Review Mode</span>
          <span class="px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 font-mono text-[10px] font-bold border border-emerald-500/20">AUTO-PUBLISH</span>
        </div>
      </div>

      <!-- Card 4: AI & Animation Engine -->
      <div class="glass-card rounded-2xl p-6 relative overflow-hidden transition-all duration-300 group">
        <div class="flex items-center justify-between">
          <span class="text-xs font-semibold text-slate-400 uppercase tracking-wider font-mono">Generation Matrix</span>
          <div class="w-8 h-8 rounded-lg bg-violet-500/10 flex items-center justify-center text-violet-400">
            <i class="fa-solid fa-microchip text-base"></i>
          </div>
        </div>
        <div class="mt-3">
          <p class="text-xl font-bold text-white">Gemini + Charon</p>
          <p class="text-[11px] text-slate-400 font-mono mt-0.5">2D Character & Vector Render</p>
        </div>
        <div class="mt-4 pt-3 border-t border-white/5 flex items-center justify-between text-xs">
          <span class="text-slate-400">Content Syllabus</span>
          <span class="text-neonViolet font-bold font-mono">224 Master Items</span>
        </div>
      </div>

    </div>

    <!-- Action Launchpad (Interactive Buttons) -->
    <div class="glass-card rounded-3xl p-6 sm:p-8 relative overflow-hidden border border-white/10">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 pb-6 border-b border-white/10">
        <div>
          <h2 class="text-lg font-bold text-white flex items-center space-x-2.5">
            <span class="w-2.5 h-2.5 rounded-full bg-neonEmerald glow-live"></span>
            <span>Manual Action Launchpad</span>
          </h2>
          <p class="text-xs text-slate-400 mt-1">Direct triggers into the GitHub Actions automation runner</p>
        </div>
        <div class="flex items-center space-x-2">
          <span class="text-xs font-mono text-slate-400">Active Series:</span>
          <span class="px-2.5 py-1 rounded-lg bg-white/5 text-white font-mono text-xs border border-white/10 font-bold">AIVerse #1-#100</span>
        </div>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mt-6">
        
        <!-- Action 1: Post Reel Right Now -->
        <button onclick="triggerAction('post_now')" class="shimmer-btn p-5 rounded-2xl bg-gradient-to-br from-emerald-600 via-teal-600 to-cyan-600 text-white shadow-xl shadow-emerald-900/40 text-left transition-all duration-300 transform hover:scale-[1.03] active:scale-[0.97] group">
          <div class="flex items-center justify-between">
            <div class="w-12 h-12 rounded-xl bg-white/20 flex items-center justify-center text-white text-xl group-hover:rotate-12 transition">
              <i class="fa-solid fa-paper-plane"></i>
            </div>
            <span class="text-[10px] font-bold uppercase tracking-wider bg-black/30 px-2.5 py-1 rounded-full border border-white/20">LIVE POST</span>
          </div>
          <div class="mt-4">
            <h3 class="font-extrabold text-base">Post Reel Now</h3>
            <p class="text-xs text-emerald-100/80 mt-1 leading-relaxed">Generates script, character animation & posts live to IG & YouTube</p>
          </div>
        </button>

        <!-- Action 2: Dry Run Preview -->
        <button onclick="triggerAction('dry_run')" class="p-5 rounded-2xl bg-panel/90 hover:bg-slate-800/90 border border-panelBorder hover:border-cyan-500/50 text-white text-left transition-all duration-300 transform hover:scale-[1.03] active:scale-[0.97] group shadow-lg">
          <div class="flex items-center justify-between">
            <div class="w-12 h-12 rounded-xl bg-cyan-500/10 flex items-center justify-center text-cyan-400 text-xl group-hover:scale-110 transition">
              <i class="fa-solid fa-flask-vial"></i>
            </div>
            <span class="text-[10px] font-bold uppercase tracking-wider bg-cyan-500/10 text-cyan-400 px-2.5 py-1 rounded-full border border-cyan-500/30">TEST PREVIEW</span>
          </div>
          <div class="mt-4">
            <h3 class="font-extrabold text-base">Dry-Run Preview</h3>
            <p class="text-xs text-slate-400 mt-1 leading-relaxed">Renders complete MP4 video as artifact without posting to feed</p>
          </div>
        </button>

        <!-- Action 3: Pre-Flight Check -->
        <button onclick="triggerAction('check')" class="p-5 rounded-2xl bg-panel/90 hover:bg-slate-800/90 border border-panelBorder hover:border-violet-500/50 text-white text-left transition-all duration-300 transform hover:scale-[1.03] active:scale-[0.97] group shadow-lg">
          <div class="flex items-center justify-between">
            <div class="w-12 h-12 rounded-xl bg-violet-500/10 flex items-center justify-center text-violet-400 text-xl group-hover:scale-110 transition">
              <i class="fa-solid fa-stethoscope"></i>
            </div>
            <span class="text-[10px] font-bold uppercase tracking-wider bg-violet-500/10 text-violet-400 px-2.5 py-1 rounded-full border border-violet-500/30">DIAGNOSTIC</span>
          </div>
          <div class="mt-4">
            <h3 class="font-extrabold text-base">Pre-Flight Check</h3>
            <p class="text-xs text-slate-400 mt-1 leading-relaxed">Verifies Meta token, Gemini voice quota, Supabase storage & fonts</p>
          </div>
        </button>

        <!-- Action 4: Auto-Engagement Loop -->
        <button onclick="triggerAction('engage')" class="p-5 rounded-2xl bg-panel/90 hover:bg-slate-800/90 border border-panelBorder hover:border-amber-500/50 text-white text-left transition-all duration-300 transform hover:scale-[1.03] active:scale-[0.97] group shadow-lg">
          <div class="flex items-center justify-between">
            <div class="w-12 h-12 rounded-xl bg-amber-500/10 flex items-center justify-center text-amber-400 text-xl group-hover:scale-110 transition">
              <i class="fa-solid fa-comments"></i>
            </div>
            <span class="text-[10px] font-bold uppercase tracking-wider bg-amber-500/10 text-amber-400 px-2.5 py-1 rounded-full border border-amber-500/30">ENGAGEMENT</span>
          </div>
          <div class="mt-4">
            <h3 class="font-extrabold text-base">Auto-Reply & Learn</h3>
            <p class="text-xs text-slate-400 mt-1 leading-relaxed">Delivers prompt packs to commenters & updates hook analytics</p>
          </div>
        </button>

      </div>
    </div>

    <!-- Live Published Reels Section (Visual Grid with In-Dashboard Play Buttons) -->
    <div class="glass-card rounded-3xl p-6 sm:p-8 border border-white/10">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-6 border-b border-white/10">
        <div>
          <h2 class="text-lg font-bold text-white flex items-center space-x-2.5">
            <i class="fa-brands fa-instagram text-pink-500 text-xl"></i>
            <span>Published Reels Gallery</span>
          </h2>
          <p class="text-xs text-slate-400 mt-1">Click any reel to play directly inside the dashboard</p>
        </div>
        <div class="flex items-center space-x-3">
          <a href="https://www.instagram.com/aiverse.agent/" target="_blank" class="px-4 py-2 rounded-xl text-xs font-bold bg-pink-500/10 text-pink-400 border border-pink-500/30 hover:bg-pink-500/20 transition flex items-center space-x-1.5">
            <span>Open Instagram Profile</span>
            <i class="fa-solid fa-arrow-up-right-from-square text-[10px]"></i>
          </a>
        </div>
      </div>

      <!-- Reels Grid -->
      <div id="postsGrid" class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-6 mt-6">
        <div class="col-span-full py-16 text-center text-slate-500 text-sm">
          <i class="fa-solid fa-circle-notch fa-spin text-neonEmerald text-2xl mr-2"></i>
          <p class="mt-2 font-mono text-xs text-slate-400">Loading reels gallery...</p>
        </div>
      </div>
    </div>

    <!-- Lower Section: Workflows & GitHub Run History -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">

      <!-- Workflows Control List -->
      <div class="glass-card rounded-3xl p-6 border border-white/10 lg:col-span-1 flex flex-col justify-between">
        <div>
          <div class="flex items-center justify-between pb-4 border-b border-white/10">
            <h2 class="text-base font-bold text-white flex items-center space-x-2">
              <i class="fa-solid fa-sliders text-neonCyan"></i>
              <span>Workflow Schedules</span>
            </h2>
            <span class="text-[10px] font-mono text-slate-400">Independent</span>
          </div>
          <p class="text-xs text-slate-400 mt-2 mb-4">Toggle individual cron triggers without affecting others:</p>

          <div id="workflowsList" class="space-y-3">
            <div class="py-6 text-center text-slate-500 text-xs font-mono">
              <i class="fa-solid fa-circle-notch fa-spin mr-1 text-neonCyan"></i> Fetching workflows...
            </div>
          </div>
        </div>

        <div class="mt-6 pt-4 border-t border-white/5 text-[11px] text-slate-500 flex items-center justify-between">
          <span>GitHub Actions Runner: Linux x64</span>
          <span class="text-neonEmerald font-mono">All Green</span>
        </div>
      </div>

      <!-- Live Execution Table -->
      <div class="glass-card rounded-3xl p-6 border border-white/10 lg:col-span-2">
        <div class="flex items-center justify-between pb-4 border-b border-white/10">
          <div>
            <h2 class="text-base font-bold text-white flex items-center space-x-2">
              <i class="fa-solid fa-list-check text-neonEmerald"></i>
              <span>Execution Pipeline History</span>
            </h2>
            <p class="text-xs text-slate-400 mt-0.5">Live status of recent workflow executions</p>
          </div>
          <a href="https://github.com/PranavNayee/aiverse-bot/actions" target="_blank" class="text-xs text-slate-400 hover:text-white font-mono flex items-center space-x-1">
            <span>GitHub Console</span>
            <i class="fa-solid fa-arrow-up-right-from-square text-[9px]"></i>
          </a>
        </div>

        <div class="overflow-x-auto mt-4">
          <table class="w-full text-left text-xs">
            <thead class="text-[10px] uppercase font-mono text-slate-400 border-b border-white/5">
              <tr>
                <th class="py-3 px-3">Status</th>
                <th class="py-3 px-3">Workflow Name</th>
                <th class="py-3 px-3">Executed At</th>
                <th class="py-3 px-3 text-right">Console Log</th>
              </tr>
            </thead>
            <tbody id="runsTableBody" class="divide-y divide-white/5 font-mono text-slate-300">
              <tr>
                <td colspan="4" class="py-8 text-center text-slate-500">
                  <i class="fa-solid fa-circle-notch fa-spin mr-1 text-neonEmerald"></i> Loading execution history...
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

    </div>

  </main>

  <!-- POPUP VIDEO THEATER MODAL -->
  <div id="videoModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/85 backdrop-blur-xl hidden transition-all duration-300">
    <div class="glass-card w-full max-w-4xl rounded-3xl border border-neonEmerald/40 overflow-hidden shadow-2xl flex flex-col lg:flex-row max-h-[90vh]">
      
      <!-- Video Container -->
      <div class="w-full lg:w-[360px] bg-black flex items-center justify-center relative p-3">
        <div class="w-full max-w-[280px] aspect-[9/16] rounded-2xl overflow-hidden bg-darker border-2 border-slate-800 shadow-xl relative">
          <video id="modalVideoPlayer" class="w-full h-full object-cover" controls playsinline autoplay loop>
            <source id="modalVideoSource" src="" type="video/mp4">
          </video>
        </div>
      </div>

      <!-- Video Details & Actions -->
      <div class="p-6 flex-1 flex flex-col justify-between bg-panel/90 text-left overflow-y-auto">
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

          <h3 id="modalVideoTitle" class="text-xl font-bold text-white mt-4">Reel Title</h3>
          <p id="modalVideoDate" class="text-xs text-slate-400 font-mono mt-1">Date</p>

          <div class="mt-4 p-4 rounded-xl bg-darker/60 border border-white/5 text-xs text-slate-300 leading-relaxed max-h-48 overflow-y-auto" id="modalVideoCaption">
            Full Caption
          </div>
        </div>

        <div class="mt-6 pt-4 border-t border-white/10 flex flex-wrap items-center justify-between gap-3">
          <div class="flex items-center space-x-2">
            <a id="modalInstagramLink" href="#" target="_blank" class="px-4 py-2 rounded-xl text-xs font-bold bg-pink-500 hover:bg-pink-600 text-white transition flex items-center space-x-1.5 shadow">
              <i class="fa-brands fa-instagram text-sm"></i>
              <span>Open on Instagram</span>
            </a>
            <a id="modalDownloadLink" href="#" download="aiverse_reel.mp4" target="_blank" class="px-3.5 py-2 rounded-xl text-xs font-bold bg-slate-800 hover:bg-slate-700 text-white border border-slate-700 transition flex items-center space-x-1.5">
              <i class="fa-solid fa-download text-xs text-neonEmerald"></i>
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
  <div id="logModal" class="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/80 backdrop-blur-md hidden transition-all duration-300">
    <div class="glass-card w-full max-w-4xl rounded-3xl border border-neonCyan/40 overflow-hidden shadow-2xl flex flex-col max-h-[85vh]">
      <div class="px-6 py-4 bg-panel border-b border-white/10 flex items-center justify-between">
        <div class="flex items-center space-x-3">
          <div class="flex space-x-1.5">
            <span class="w-3 h-3 rounded-full bg-red-500/80"></span>
            <span class="w-3 h-3 rounded-full bg-yellow-500/80"></span>
            <span class="w-3 h-3 rounded-full bg-emerald-500/80"></span>
          </div>
          <span class="text-xs font-mono font-bold text-white ml-2 flex items-center space-x-1.5">
            <i class="fa-solid fa-terminal text-neonCyan"></i>
            <span id="logModalTitle">Runner Output Log</span>
          </span>
        </div>
        <button onclick="closeLogModal()" class="text-slate-400 hover:text-white transition">
          <i class="fa-solid fa-xmark text-lg"></i>
        </button>
      </div>

      <div class="p-6 bg-darker flex-1 overflow-y-auto font-mono text-xs text-emerald-400 leading-relaxed whitespace-pre-wrap selection:bg-emerald-500 selection:text-black" id="terminalOutput">
        Loading runner stream...
      </div>

      <div class="px-6 py-3 bg-panel border-t border-white/10 flex items-center justify-between text-xs font-mono text-slate-400">
        <span>Tail 300 Lines &middot; Auto-Refreshed</span>
        <button onclick="fetchCurrentModalLog()" class="text-cyan-400 hover:underline">
          <i class="fa-solid fa-rotate-right mr-1"></i> Refresh Log
        </button>
      </div>
    </div>
  </div>

  <footer class="relative z-10 border-t border-white/5 py-6 text-center text-xs text-slate-500 font-mono">
    <span>AIVerse Automation Bot &middot; Multi-Agent Educational Reel Generator</span>
  </footer>

  <script>
    let isGlobalActive = true;
    let activeRunId = null;
    let currentViewingRunId = null;
    let allPostsData = [];

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

      const badgeEl = document.getElementById('nextSlotBadge');
      if (badgeEl) {
        badgeEl.textContent = (targetHour === 8 || targetHour === 32) ? '08:00 IST' : '19:00 IST';
      }
    }
    setInterval(updateClock, 1000);
    updateClock();

    function showToast(msg, isSuccess = true) {
      const toast = document.getElementById('toast');
      const toastMsg = document.getElementById('toastMsg');
      const toastIcon = document.getElementById('toastIcon');
      toastMsg.textContent = msg;
      toastIcon.className = isSuccess ? 'fa-solid fa-circle-check text-neonEmerald text-lg' : 'fa-solid fa-triangle-exclamation text-neonPink text-lg';
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
            <div class="flex items-center justify-between p-3.5 rounded-2xl bg-darker/60 border border-white/5 hover:border-white/10 transition">
              <div>
                <p class="text-xs font-bold text-white tracking-wide">${wf.name}</p>
                <p class="text-[10px] font-mono text-slate-500">${wf.path.split('/').pop()}</p>
              </div>
              <button onclick="toggleWorkflow('${wf.path}', ${isActive})" class="px-3 py-1 rounded-full text-[10px] font-mono font-bold transition transform active:scale-95 ${
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
          btn.innerHTML = '<i class="fa-solid fa-pause"></i><span>Pause All Automation</span>';
          btn.className = "px-4 py-2.5 rounded-xl text-xs font-bold flex items-center space-x-2 transition-all duration-300 shadow-lg transform hover:scale-[1.03] active:scale-[0.97] bg-amber-500/10 text-amber-300 border border-amber-500/30 hover:bg-amber-500/20";
        } else {
          btn.innerHTML = '<i class="fa-solid fa-play"></i><span>Resume All Automation</span>';
          btn.className = "px-4 py-2.5 rounded-xl text-xs font-bold flex items-center space-x-2 transition-all duration-300 shadow-lg transform hover:scale-[1.03] active:scale-[0.97] bg-neonEmerald/10 text-neonEmerald border border-neonEmerald/30 hover:bg-neonEmerald/20";
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
          statusBadge = '<span class="inline-flex items-center px-2.5 py-1 rounded-full text-[10px] font-bold bg-amber-500/15 text-amber-300 border border-amber-500/30"><i class="fa-solid fa-spinner fa-spin mr-1.5"></i> RUNNING</span>';
        } else if (r.conclusion === 'success') {
          statusBadge = '<span class="inline-flex items-center px-2.5 py-1 rounded-full text-[10px] font-bold bg-neonEmerald/15 text-neonEmerald border border-neonEmerald/30"><i class="fa-solid fa-check mr-1.5"></i> SUCCESS</span>';
        } else if (r.conclusion === 'failure') {
          statusBadge = '<span class="inline-flex items-center px-2.5 py-1 rounded-full text-[10px] font-bold bg-neonPink/15 text-neonPink border border-neonPink/30"><i class="fa-solid fa-xmark mr-1.5"></i> FAILED</span>';
        } else {
          statusBadge = `<span class="inline-flex items-center px-2.5 py-1 rounded-full text-[10px] font-bold bg-slate-800 text-slate-400">${r.conclusion || r.status}</span>`;
        }

        const dateStr = new Date(r.createdAt).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });

        return `
          <tr class="hover:bg-panel/60 transition group">
            <td class="py-3 px-3">${statusBadge}</td>
            <td class="py-3 px-3 font-medium text-white group-hover:text-neonCyan transition">${r.name || r.workflowName}</td>
            <td class="py-3 px-3 text-slate-400">${dateStr}</td>
            <td class="py-3 px-3 text-right">
              <button onclick="viewRunLog(${r.databaseId}, '${r.name || r.workflowName}')" class="px-2.5 py-1 rounded-lg bg-panelBorder/60 hover:bg-panelBorder text-neonCyan hover:text-white transition inline-flex items-center space-x-1">
                <i class="fa-solid fa-terminal text-[10px]"></i>
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

      // Update Hero Section with the Latest Reel
      const latest = posts[0];
      if (latest) {
        const lines = (latest.caption || 'New AIVerse Reel').split('\\n');
        const heroTitle = lines[0] || 'AIVerse Masterclass Reel';
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
          <div class="glass-card rounded-2xl overflow-hidden border border-white/10 hover:border-pink-500/40 transition-all duration-500 flex flex-col group transform hover:-translate-y-1 shadow-lg">
            
            <div class="relative aspect-[9/13] bg-darker overflow-hidden cursor-pointer" onclick="openVideoModal(${idx})">
              <img src="${thumb}" alt="Reel thumbnail" class="w-full h-full object-cover group-hover:scale-105 transition-transform duration-700 ease-out">
              <div class="absolute inset-0 bg-gradient-to-t from-darker via-transparent to-black/20 opacity-90"></div>
              
              <div class="absolute top-3 left-3 bg-gradient-to-r from-pink-500 to-rose-500 text-white text-[10px] font-black px-2.5 py-0.5 rounded-full flex items-center space-x-1.5 shadow-lg">
                <i class="fa-brands fa-instagram"></i>
                <span>REEL</span>
              </div>

              <div class="absolute top-3 right-3 bg-black/60 backdrop-blur-md text-slate-300 text-[10px] font-mono px-2 py-0.5 rounded-full border border-white/10">
                ${dateStr}
              </div>

              <!-- Animated Play Center Button -->
              <div class="absolute inset-0 flex items-center justify-center opacity-85 group-hover:opacity-100 transition-opacity duration-300 bg-black/20 group-hover:bg-black/40 backdrop-blur-[1px]">
                <div class="w-14 h-14 rounded-full bg-pink-500/90 text-white flex items-center justify-center text-xl shadow-2xl transform scale-90 group-hover:scale-110 transition duration-300">
                  <i class="fa-solid fa-play ml-1"></i>
                </div>
              </div>
            </div>

            <div class="p-4 flex-1 flex flex-col justify-between bg-panel/40">
              <div>
                <h3 class="text-xs font-extrabold text-white group-hover:text-pink-400 transition line-clamp-2">${title}</h3>
              </div>

              <div class="mt-3 pt-3 border-t border-white/5 flex items-center justify-between">
                <button onclick="openVideoModal(${idx})" class="text-[11px] font-bold text-neonEmerald hover:underline flex items-center space-x-1">
                  <i class="fa-solid fa-play text-[9px]"></i>
                  <span>Watch Reel</span>
                </button>
                <a href="${p.permalink}" target="_blank" class="text-slate-400 hover:text-white text-xs">
                  <i class="fa-solid fa-arrow-up-right-from-square text-[10px]"></i>
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

    // Keyboard shortcut ESC to close modals
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

    // Auto-refresh every 12 seconds
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

        if url.path == "/" or url.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
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
        print(f"🎛️  AIVerse OS Command Center with Video Preview is LIVE!")
        print(f"👉 Open in your browser: http://localhost:{PORT}")
        print(f"==================================================\\n")
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()

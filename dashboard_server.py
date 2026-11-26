#!/usr/bin/env python3
"""
AIVerse Bot - Web Control Dashboard Server
Serves a responsive, real-time dashboard to monitor progress and start/stop bot actions.
Uses standard Python library (no external pip dependencies needed).
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
from datetime import datetime, timezone

PORT = 8080
REPO = "PranavNayee/aiverse-bot"
IG_USER_ID = "17841479592722450"
IG_TOKEN = "EAAUim1AzK9MBSZC5nX55gGjCeuEk6yzhApCCVZBgVGSJGQqhC564ZCZCu9fniiGDdXIbIEyO3nd7EJXK97W5ZC4ZB0DOr7RUM2i928B4GlMfzZBZCd7VXSTWZBBtpGhpov56gxp0XyC6jBW1JSubuF9ZA7GVD1JmNkNLXktyO0ZBKFZBj6wZC1mCrIQBo4MZBwlMocuX49OOVsZC4c7OfvRQS7zGTNDU5CFCBsBlpsqgsD4HJwNuB1FlbJkqwvMlQZDZD"

def run_cmd(cmd_list):
    try:
        r = subprocess.run(cmd_list, capture_output=True, text=True, timeout=25)
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

def get_instagram_posts(limit=6):
    url = (f"https://graph.facebook.com/v21.0/{IG_USER_ID}/media?"
           f"fields=id,caption,media_type,permalink,thumbnail_url,media_url,timestamp&limit={limit}&access_token={IG_TOKEN}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AIVerse-Dashboard/1.0"})
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read().decode())
            return data.get("data", [])
    except Exception as e:
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
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>AIVerse Bot Command Center</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: {
            dark: '#0B0F19',
            card: '#111827',
            cardBorder: '#1F2937',
            neonGreen: '#10B981',
            neonBlue: '#3B82F6',
            neonPurple: '#8B5CF6'
          }
        }
      }
    }
  </script>
  <style>
    @keyframes pulse-glow {
      0%, 100% { opacity: 1; filter: drop-shadow(0 0 12px rgba(16, 185, 129, 0.6)); }
      50% { opacity: 0.6; filter: drop-shadow(0 0 4px rgba(16, 185, 129, 0.2)); }
    }
    .glow-live { animation: pulse-glow 2s infinite ease-in-out; }
    .glass { background: rgba(17, 24, 39, 0.85); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.08); }
    ::-webkit-scrollbar { width: 8px; height: 8px; }
    ::-webkit-scrollbar-track { background: #0b0f19; }
    ::-webkit-scrollbar-thumb { background: #1f2937; border-radius: 4px; }
    ::-webkit-scrollbar-thumb:hover { background: #374151; }
  </style>
</head>
<body class="bg-dark text-slate-100 min-h-screen flex flex-col font-sans antialiased">

  <!-- Top Navbar -->
  <header class="border-b border-gray-800 glass sticky top-0 z-50">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
      <div class="flex items-center space-x-3">
        <div class="w-10 h-10 rounded-xl bg-gradient-to-tr from-emerald-500 to-cyan-500 flex items-center justify-center shadow-lg shadow-emerald-500/20">
          <i class="fa-solid fa-robot text-dark text-xl font-bold"></i>
        </div>
        <div>
          <h1 class="text-lg font-bold bg-gradient-to-r from-white via-slate-200 to-emerald-400 bg-clip-text text-transparent">
            AIVerse Bot Command Center
          </h1>
          <p class="text-xs text-slate-400">@storysfrombittu ➔ @aiverse.agent · Reels & Shorts</p>
        </div>
      </div>

      <!-- Live Status & Pause Switch -->
      <div class="flex items-center space-x-4">
        <div id="statusPill" class="flex items-center space-x-2 px-3 py-1.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30">
          <span class="w-2 h-2 rounded-full bg-emerald-400 glow-live"></span>
          <span id="statusText">SYSTEM ACTIVE</span>
        </div>
        
        <button onclick="toggleGlobalAutomation()" id="btnGlobalToggle" class="px-4 py-2 rounded-lg text-xs font-semibold flex items-center space-x-2 transition shadow-md bg-amber-500/10 text-amber-400 border border-amber-500/30 hover:bg-amber-500/20">
          <i class="fa-solid fa-pause"></i>
          <span>Pause Automation</span>
        </button>

        <button onclick="refreshAll()" class="p-2 rounded-lg text-slate-400 hover:text-white hover:bg-slate-800 transition text-sm" title="Refresh">
          <i id="refreshIcon" class="fa-solid fa-rotate"></i>
        </button>
      </div>
    </div>
  </header>

  <!-- In-Progress Running Banner (Hidden by default) -->
  <div id="activeRunBanner" class="hidden bg-gradient-to-r from-emerald-950 via-slate-900 to-cyan-950 border-b border-emerald-500/30 py-3 px-4">
    <div class="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-3 text-sm">
      <div class="flex items-center space-x-3">
        <i class="fa-solid fa-circle-notch fa-spin text-emerald-400 text-lg"></i>
        <div>
          <span class="font-semibold text-white">Active Run in Progress:</span>
          <span id="activeRunName" class="text-emerald-300 ml-1">Daily Reel Generation & Publishing</span>
        </div>
      </div>
      <div class="flex items-center space-x-3">
        <a id="activeRunLink" href="#" target="_blank" class="text-xs text-cyan-400 hover:underline flex items-center space-x-1">
          <span>View on GitHub</span>
          <i class="fa-solid fa-arrow-up-right-from-square text-[10px]"></i>
        </a>
        <button onclick="cancelActiveRun()" class="px-3 py-1 bg-red-500/20 hover:bg-red-500/30 text-red-400 border border-red-500/30 rounded text-xs font-medium transition">
          <i class="fa-solid fa-xmark mr-1"></i> Stop Run
        </button>
      </div>
    </div>
  </div>

  <!-- Notification Banner -->
  <div id="toast" class="fixed bottom-6 right-6 z-50 transform translate-y-20 opacity-0 transition-all duration-300 pointer-events-none">
    <div class="glass px-5 py-3 rounded-xl border border-emerald-500/40 text-emerald-300 text-sm flex items-center space-x-3 shadow-2xl">
      <i id="toastIcon" class="fa-solid fa-circle-check text-emerald-400"></i>
      <span id="toastMsg">Action executed successfully</span>
    </div>
  </div>

  <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 flex-1 space-y-8 w-full">

    <!-- Hero Stats Grid -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5">
      <!-- Card 1: Account -->
      <div class="glass rounded-2xl p-5 relative overflow-hidden border border-gray-800 hover:border-slate-700 transition">
        <div class="flex items-center justify-between">
          <span class="text-xs font-medium text-slate-400 uppercase tracking-wider">Instagram</span>
          <i class="fa-brands fa-instagram text-pink-500 text-xl"></i>
        </div>
        <p class="text-xl font-bold mt-2 text-white">@aiverse.agent</p>
        <div class="flex items-center space-x-2 mt-3 text-xs text-emerald-400">
          <i class="fa-solid fa-shield-halved"></i>
          <span>Permanent Token (Never Expires)</span>
        </div>
      </div>

      <!-- Card 2: YouTube -->
      <div class="glass rounded-2xl p-5 relative overflow-hidden border border-gray-800 hover:border-slate-700 transition">
        <div class="flex items-center justify-between">
          <span class="text-xs font-medium text-slate-400 uppercase tracking-wider">YouTube Shorts</span>
          <i class="fa-brands fa-youtube text-red-500 text-xl"></i>
        </div>
        <p class="text-xl font-bold mt-2 text-white">Cross-Posting Active</p>
        <div class="flex items-center space-x-2 mt-3 text-xs text-slate-400">
          <i class="fa-solid fa-link"></i>
          <span>Auto-published alongside Reels</span>
        </div>
      </div>

      <!-- Card 3: Next Slot -->
      <div class="glass rounded-2xl p-5 relative overflow-hidden border border-gray-800 hover:border-slate-700 transition">
        <div class="flex items-center justify-between">
          <span class="text-xs font-medium text-slate-400 uppercase tracking-wider">Daily Schedule</span>
          <i class="fa-solid fa-clock text-cyan-400 text-xl"></i>
        </div>
        <p class="text-xl font-bold mt-2 text-white">08:00 & 19:00 IST</p>
        <div class="flex items-center space-x-2 mt-3 text-xs text-cyan-400">
          <i class="fa-solid fa-bolt"></i>
          <span id="slotStatus">Auto-mode: 2 reels / day</span>
        </div>
      </div>

      <!-- Card 4: Bot Health -->
      <div class="glass rounded-2xl p-5 relative overflow-hidden border border-gray-800 hover:border-slate-700 transition">
        <div class="flex items-center justify-between">
          <span class="text-xs font-medium text-slate-400 uppercase tracking-wider">Bot Health</span>
          <i class="fa-solid fa-heart-pulse text-emerald-400 text-xl"></i>
        </div>
        <p class="text-xl font-bold mt-2 text-emerald-400">100% Operational</p>
        <div class="flex items-center space-x-2 mt-3 text-xs text-slate-400">
          <i class="fa-solid fa-microchip text-slate-500"></i>
          <span>Gemini AI + Charon Voice</span>
        </div>
      </div>
    </div>

    <!-- Quick Action Control Bar -->
    <div class="glass rounded-2xl p-6 border border-gray-800">
      <div class="flex flex-col md:flex-row md:items-center justify-between gap-4 border-b border-gray-800/80 pb-5">
        <div>
          <h2 class="text-base font-bold text-white flex items-center space-x-2">
            <i class="fa-solid fa-gamepad text-emerald-400"></i>
            <span>Interactive Controls & Actions</span>
          </h2>
          <p class="text-xs text-slate-400 mt-0.5">Trigger on-demand actions or manage automated background schedules</p>
        </div>
      </div>

      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4 mt-5">
        <!-- Action 1: Post Reel Now -->
        <button onclick="triggerAction('post_now')" class="p-4 rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 hover:from-emerald-500 hover:to-teal-500 text-white shadow-lg shadow-emerald-900/30 text-left transition transform hover:-translate-y-0.5 group">
          <div class="flex items-center justify-between">
            <i class="fa-solid fa-paper-plane text-2xl group-hover:scale-110 transition"></i>
            <span class="text-[10px] uppercase font-bold bg-black/20 px-2 py-0.5 rounded">Live Post</span>
          </div>
          <div class="mt-3">
            <h3 class="font-bold text-sm">Post Reel Right Now</h3>
            <p class="text-xs text-emerald-100/70 mt-0.5">Creates, animates & posts immediately to IG & YT</p>
          </div>
        </button>

        <!-- Action 2: Dry Run Test -->
        <button onclick="triggerAction('dry_run')" class="p-4 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700/80 text-white text-left transition transform hover:-translate-y-0.5 group">
          <div class="flex items-center justify-between">
            <i class="fa-solid fa-flask text-2xl text-cyan-400 group-hover:scale-110 transition"></i>
            <span class="text-[10px] uppercase font-bold bg-cyan-500/10 text-cyan-400 px-2 py-0.5 rounded">Test Run</span>
          </div>
          <div class="mt-3">
            <h3 class="font-bold text-sm">Dry-Run Preview</h3>
            <p class="text-xs text-slate-400 mt-0.5">Renders full video as downloadable artifact (no post)</p>
          </div>
        </button>

        <!-- Action 3: Pre-Flight Check -->
        <button onclick="triggerAction('check')" class="p-4 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700/80 text-white text-left transition transform hover:-translate-y-0.5 group">
          <div class="flex items-center justify-between">
            <i class="fa-solid fa-stethoscope text-2xl text-purple-400 group-hover:scale-110 transition"></i>
            <span class="text-[10px] uppercase font-bold bg-purple-500/10 text-purple-400 px-2 py-0.5 rounded">Diagnostic</span>
          </div>
          <div class="mt-3">
            <h3 class="font-bold text-sm">Pre-Flight Check</h3>
            <p class="text-xs text-slate-400 mt-0.5">Validates APIs, voice, storage, and Instagram token</p>
          </div>
        </button>

        <!-- Action 4: Auto-Engage -->
        <button onclick="triggerAction('engage')" class="p-4 rounded-xl bg-slate-800 hover:bg-slate-700 border border-slate-700/80 text-white text-left transition transform hover:-translate-y-0.5 group">
          <div class="flex items-center justify-between">
            <i class="fa-solid fa-comments text-2xl text-amber-400 group-hover:scale-110 transition"></i>
            <span class="text-[10px] uppercase font-bold bg-amber-500/10 text-amber-400 px-2 py-0.5 rounded">Engage</span>
          </div>
          <div class="mt-3">
            <h3 class="font-bold text-sm">Auto-Reply & Learn</h3>
            <p class="text-xs text-slate-400 mt-0.5">Replies to comments with keywords & updates analytics</p>
          </div>
        </button>
      </div>
    </div>

    <!-- Live Published Reels Section -->
    <div class="glass rounded-2xl p-6 border border-gray-800">
      <div class="flex items-center justify-between border-b border-gray-800/80 pb-4 mb-5">
        <div>
          <h2 class="text-base font-bold text-white flex items-center space-x-2">
            <i class="fa-brands fa-instagram text-pink-500"></i>
            <span>Recently Published Reels on Instagram</span>
          </h2>
          <p class="text-xs text-slate-400 mt-0.5">Live content published from @aiverse.agent feed</p>
        </div>
        <a href="https://www.instagram.com/aiverse.agent/" target="_blank" class="text-xs text-emerald-400 hover:text-emerald-300 font-semibold flex items-center space-x-1">
          <span>View Profile</span>
          <i class="fa-solid fa-arrow-up-right-from-square text-[10px]"></i>
        </a>
      </div>

      <div id="postsGrid" class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-5">
        <div class="col-span-full py-8 text-center text-slate-500 text-sm">
          <i class="fa-solid fa-circle-notch fa-spin mr-2"></i> Loading recent reels...
        </div>
      </div>
    </div>

    <!-- Active Schedules & GitHub Runs Table -->
    <div class="grid grid-cols-1 lg:grid-cols-3 gap-6">

      <!-- Schedule Workflows Toggle Switch List -->
      <div class="glass rounded-2xl p-6 border border-gray-800 lg:col-span-1">
        <h2 class="text-base font-bold text-white flex items-center space-x-2 mb-4">
          <i class="fa-solid fa-sliders text-cyan-400"></i>
          <span>Workflow Automation</span>
        </h2>
        <div id="workflowsList" class="space-y-3">
          <div class="py-4 text-center text-slate-500 text-xs">
            <i class="fa-solid fa-circle-notch fa-spin mr-1"></i> Loading workflows...
          </div>
        </div>
      </div>

      <!-- Recent GitHub Action Runs -->
      <div class="glass rounded-2xl p-6 border border-gray-800 lg:col-span-2">
        <div class="flex items-center justify-between mb-4">
          <h2 class="text-base font-bold text-white flex items-center space-x-2">
            <i class="fa-solid fa-list-check text-emerald-400"></i>
            <span>GitHub Actions Run History</span>
          </h2>
          <a href="https://github.com/PranavNayee/aiverse-bot/actions" target="_blank" class="text-xs text-slate-400 hover:text-white flex items-center space-x-1">
            <span>All Runs</span>
            <i class="fa-solid fa-arrow-up-right-from-square text-[10px]"></i>
          </a>
        </div>
        
        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs text-slate-300">
            <thead class="text-[11px] uppercase text-slate-400 border-b border-gray-800">
              <tr>
                <th class="py-2.5 px-3">Status</th>
                <th class="py-2.5 px-3">Workflow</th>
                <th class="py-2.5 px-3">Date</th>
                <th class="py-2.5 px-3 text-right">Actions</th>
              </tr>
            </thead>
            <tbody id="runsTableBody" class="divide-y divide-gray-800/60">
              <tr>
                <td colspan="4" class="py-6 text-center text-slate-500">
                  <i class="fa-solid fa-circle-notch fa-spin mr-1"></i> Loading execution history...
                </td>
              </tr>
            </tbody>
          </table>
        </div>
      </div>

    </div>

  </main>

  <footer class="border-t border-gray-800/60 py-4 text-center text-xs text-slate-500">
    AIVerse Automation Bot &middot; Powered by DeepSeek / Gemini / Meta Graph API &middot; Running locally on port 8080
  </footer>

  <script>
    let isGlobalActive = true;
    let activeRunId = null;

    function showToast(msg, isSuccess = true) {
      const toast = document.getElementById('toast');
      const toastMsg = document.getElementById('toastMsg');
      const toastIcon = document.getElementById('toastIcon');
      toastMsg.textContent = msg;
      toastIcon.className = isSuccess ? 'fa-solid fa-circle-check text-emerald-400' : 'fa-solid fa-triangle-exclamation text-red-400';
      toast.classList.remove('translate-y-20', 'opacity-0');
      setTimeout(() => {
        toast.classList.add('translate-y-20', 'opacity-0');
      }, 4000);
    }

    async function fetchJSON(url, opts = {}) {
      try {
        const res = await fetch(url, opts);
        return await res.json();
      } catch (e) {
        console.error("Fetch error:", e);
        return null;
      }
    }

    async function loadStatus() {
      const data = await fetchJSON('/api/status');
      if (!data) return;

      // Update workflows
      const wfList = document.getElementById('workflowsList');
      if (data.workflows && data.workflows.length > 0) {
        let allDisabled = true;
        let anyActive = false;
        wfList.innerHTML = data.workflows.map(wf => {
          const isActive = wf.state === 'active';
          if (isActive) anyActive = true;
          return `
            <div class="flex items-center justify-between p-3 rounded-xl bg-slate-900/60 border border-slate-800">
              <div>
                <p class="text-xs font-semibold text-white">${wf.name}</p>
                <p class="text-[10px] text-slate-400">${wf.path}</p>
              </div>
              <button onclick="toggleWorkflow('${wf.path}', ${isActive})" class="px-2.5 py-1 rounded text-[11px] font-semibold border transition ${
                isActive 
                  ? 'bg-emerald-500/10 text-emerald-400 border-emerald-500/30 hover:bg-emerald-500/20' 
                  : 'bg-red-500/10 text-red-400 border-red-500/30 hover:bg-red-500/20'
              }">
                ${isActive ? 'Active' : 'Paused'}
              </button>
            </div>
          `;
        }).join('');

        isGlobalActive = anyActive;
        const statusPill = document.getElementById('statusPill');
        const statusText = document.getElementById('statusText');
        const btnGlobalToggle = document.getElementById('btnGlobalToggle');

        if (isGlobalActive) {
          statusPill.className = "flex items-center space-x-2 px-3 py-1.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/30";
          statusText.textContent = "SYSTEM ACTIVE";
          btnGlobalToggle.innerHTML = '<i class="fa-solid fa-pause"></i><span>Pause All Automation</span>';
          btnGlobalToggle.className = "px-4 py-2 rounded-lg text-xs font-semibold flex items-center space-x-2 transition shadow-md bg-amber-500/10 text-amber-400 border border-amber-500/30 hover:bg-amber-500/20";
        } else {
          statusPill.className = "flex items-center space-x-2 px-3 py-1.5 rounded-full text-xs font-semibold bg-red-500/10 text-red-400 border border-red-500/30";
          statusText.textContent = "AUTOMATION PAUSED";
          btnGlobalToggle.innerHTML = '<i class="fa-solid fa-play"></i><span>Resume All Automation</span>';
          btnGlobalToggle.className = "px-4 py-2 rounded-lg text-xs font-semibold flex items-center space-x-2 transition shadow-md bg-emerald-500/10 text-emerald-400 border border-emerald-500/30 hover:bg-emerald-500/20";
        }
      }
    }

    async function loadRuns() {
      const runs = await fetchJSON('/api/runs');
      if (!runs) return;

      const tbody = document.getElementById('runsTableBody');
      const activeBanner = document.getElementById('activeRunBanner');
      const activeRunName = document.getElementById('activeRunName');
      const activeRunLink = document.getElementById('activeRunLink');

      let currentActive = null;

      tbody.innerHTML = runs.map(r => {
        let statusBadge = '';
        if (r.status === 'in_progress' || r.status === 'queued') {
          currentActive = r;
          statusBadge = '<span class="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium bg-amber-500/20 text-amber-300 border border-amber-500/30"><i class="fa-solid fa-spinner fa-spin mr-1"></i> Running</span>';
        } else if (r.conclusion === 'success') {
          statusBadge = '<span class="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium bg-emerald-500/20 text-emerald-400 border border-emerald-500/30"><i class="fa-solid fa-check mr-1"></i> Success</span>';
        } else if (r.conclusion === 'failure') {
          statusBadge = '<span class="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium bg-red-500/20 text-red-400 border border-red-500/30"><i class="fa-solid fa-xmark mr-1"></i> Failed</span>';
        } else {
          statusBadge = `<span class="inline-flex items-center px-2 py-0.5 rounded text-[10px] font-medium bg-slate-700 text-slate-300">${r.conclusion || r.status}</span>`;
        }

        const dateStr = new Date(r.createdAt).toLocaleString('en-IN', { timeZone: 'Asia/Kolkata', month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });

        return `
          <tr class="hover:bg-slate-800/40 transition">
            <td class="py-2.5 px-3">${statusBadge}</td>
            <td class="py-2.5 px-3 font-medium text-white">${r.name || r.workflowName}</td>
            <td class="py-2.5 px-3 text-slate-400">${dateStr}</td>
            <td class="py-2.5 px-3 text-right">
              <a href="${r.url}" target="_blank" class="text-cyan-400 hover:text-cyan-300 font-medium">Log <i class="fa-solid fa-arrow-up-right-from-square text-[9px] ml-0.5"></i></a>
            </td>
          </tr>
        `;
      }).join('');

      if (currentActive) {
        activeRunId = currentActive.databaseId;
        activeRunName.textContent = `${currentActive.name} (#${currentActive.databaseId})`;
        activeRunLink.href = currentActive.url;
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
        grid.innerHTML = '<div class="col-span-full py-8 text-center text-slate-500 text-sm">No recent reels found.</div>';
        return;
      }

      grid.innerHTML = posts.map(p => {
        const thumb = p.thumbnail_url || p.media_url || 'https://via.placeholder.com/300x450/111827/10b981?text=AIVerse+Reel';
        const dateStr = new Date(p.timestamp).toLocaleDateString('en-IN', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' });
        const captionPreview = (p.caption || 'New AIVerse Reel').split('\\n')[0];

        return `
          <div class="glass rounded-xl overflow-hidden border border-gray-800 hover:border-slate-700 transition flex flex-col group">
            <div class="relative aspect-[9/12] bg-slate-900 overflow-hidden">
              <img src="${thumb}" alt="Reel thumbnail" class="w-full h-full object-cover group-hover:scale-105 transition duration-300">
              <div class="absolute inset-0 bg-gradient-to-t from-dark via-transparent to-transparent opacity-80"></div>
              <span class="absolute top-3 left-3 bg-pink-500/90 text-white text-[10px] font-bold px-2 py-0.5 rounded-full flex items-center space-x-1 shadow">
                <i class="fa-brands fa-instagram"></i>
                <span>Reel</span>
              </span>
              <span class="absolute bottom-3 left-3 text-[11px] text-slate-300">
                <i class="fa-regular fa-calendar mr-1"></i>${dateStr}
              </span>
            </div>
            <div class="p-4 flex-1 flex flex-col justify-between">
              <p class="text-xs text-slate-200 font-medium line-clamp-2">${captionPreview}</p>
              <div class="mt-3 pt-3 border-t border-gray-800/80 flex items-center justify-between">
                <span class="text-[10px] text-emerald-400 font-semibold">Published Live</span>
                <a href="${p.permalink}" target="_blank" class="text-xs text-white bg-slate-800 hover:bg-slate-700 px-3 py-1.5 rounded-lg font-medium transition flex items-center space-x-1.5">
                  <span>Watch</span>
                  <i class="fa-solid fa-play text-[10px] text-pink-400"></i>
                </a>
              </div>
            </div>
          </div>
        `;
      }).join('');
    }

    async function triggerAction(actionName) {
      showToast(`Initiating action: ${actionName}...`, true);
      const res = await fetchJSON('/api/action/trigger', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ action: actionName })
      });
      if (res && res.ok) {
        showToast(`Action dispatched successfully!`, true);
        setTimeout(refreshAll, 2000);
      } else {
        showToast(`Failed: ${res ? res.error : 'Unknown error'}`, false);
      }
    }

    async function toggleWorkflow(path, currentState) {
      const action = currentState ? 'disable' : 'enable';
      showToast(`${action === 'enable' ? 'Enabling' : 'Pausing'} workflow...`, true);
      const res = await fetchJSON('/api/action/workflow_toggle', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ path: path, enable: !currentState })
      });
      if (res && res.ok) {
        showToast(`Workflow updated!`, true);
        loadStatus();
      } else {
        showToast(`Failed to update workflow state`, false);
      }
    }

    async function toggleGlobalAutomation() {
      const shouldEnable = !isGlobalActive;
      showToast(`${shouldEnable ? 'Resuming' : 'Pausing'} all automation schedules...`, true);
      const res = await fetchJSON(shouldEnable ? '/api/action/resume' : '/api/action/pause', { method: 'POST' });
      if (res && res.ok) {
        showToast(shouldEnable ? 'All automations resumed!' : 'All automations paused!', true);
        loadStatus();
      } else {
        showToast('Operation failed', false);
      }
    }

    async function cancelActiveRun() {
      if (!activeRunId) return;
      if (!confirm(`Are you sure you want to cancel the currently running workflow #${activeRunId}?`)) return;
      showToast(`Cancelling run #${activeRunId}...`, true);
      const res = await fetchJSON('/api/action/cancel', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ run_id: activeRunId })
      });
      if (res && res.ok) {
        showToast('Run cancellation signal sent.', true);
        setTimeout(refreshAll, 3000);
      } else {
        showToast('Could not cancel run', false);
      }
    }

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
        if url.path == "/" or url.path == "/index.html":
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.end_headers()
            self.wfile.write(HTML_PAGE.encode("utf-8"))
        elif url.path == "/api/status":
            wfs = get_workflows_status()
            self._send_json({"ok": True, "workflows": wfs, "account": "aiverse.agent", "user_id": IG_USER_ID})
        elif url.path == "/api/runs":
            runs = get_recent_runs(12)
            self._send_json(runs)
        elif url.path == "/api/posts":
            posts = get_instagram_posts(6)
            self._send_json(posts)
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
            # Disable core automated schedules
            results = []
            for w in ["daily.yml", "post.yml", "engage.yml", "weekly.yml"]:
                ok, _ = set_workflow_state(f".github/workflows/{w}", enable=False)
                results.append(ok)
            self._send_json({"ok": all(results)})

        elif url.path == "/api/action/resume":
            # Re-enable core automated schedules
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
        print(f"🎛️  AIVerse Bot Command Center is LIVE!")
        print(f"👉 Open in your browser: http://localhost:{PORT}")
        print(f"==================================================\\n")
        try:
            webbrowser.open(f"http://localhost:{PORT}")
        except Exception:
            pass
        httpd.serve_forever()

if __name__ == "__main__":
    run_server()

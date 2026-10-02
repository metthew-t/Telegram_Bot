# 🚨 CRITICAL: Keep Render Service Alive 24/7

## ⚠️ The Problem

**Render FREE tier has a hard limitation:**
- Sleeps after 15 minutes of NO EXTERNAL HTTP requests
- Internal pings from same server DON'T count as external traffic
- When sleeping, Telegram bot CANNOT respond to messages
- Service wakes up when someone accesses the website, but bot misses all messages sent during sleep

**Your exact issue:** Bot works fine when someone is using the website, but after 6+ hours of no web access, bot stops responding until someone logs in.

---

## ✅ SOLUTION: External Monitoring (100% FREE)

You MUST use an external service to ping your Render URL. This is **REQUIRED** for 24/7 bot operation on free tier.

### Option 1: UptimeRobot (EASIEST - Recommended) ⭐

**Step-by-step:**

1. **Go to:** https://uptimerobot.com/

2. **Sign up:** Click "Register" (free, no credit card needed)

3. **Add Monitor:**
   - Click "**+ Add New Monitor**" button
   
4. **Configure Monitor:**
   ```
   Monitor Type: HTTP(s)
   Friendly Name: ASTU Counselling Bot
   URL (or IP): https://telegram-bot-backend-8h8w.onrender.com/health/
   Monitoring Interval: 5 minutes
   Monitor Timeout: 30 seconds
   ```

5. **Click "Create Monitor"**

6. **Verify it's working:**
   - Monitor should show "Up" status with green checkmark
   - Check your Render logs after 5 minutes - you should see requests from UptimeRobot

**Result:** Your bot will work 24/7! UptimeRobot will ping every 5 minutes to keep Render awake.

---

### Option 2: Cron-job.org (Alternative)

1. Go to: https://cron-job.org/en/
2. Register free account
3. Click "**Create cronjob**"
4. Configure:
   ```
   Title: ASTU Bot Keep-Alive
   Address: https://telegram-bot-backend-8h8w.onrender.com/health/
   Schedule: */5 * * * * (every 5 minutes)
   ```
5. Save

---

### Option 3: Better Uptime (Alternative)

1. Go to: https://betteruptime.com/
2. Sign up (free plan available)
3. Add new monitor with your Render URL
4. Set check interval to 5 minutes

---

## 🧪 How to Test After Setup

1. **Set up UptimeRobot** (takes 2 minutes)
2. **Wait 30 minutes** without accessing the website
3. **Send a Telegram message as a user**
4. **Bot should respond immediately** ✅

If bot doesn't respond, check:
- UptimeRobot shows "Up" status
- Render logs show requests from UptimeRobot IP
- No error messages in Render logs

---

## 📊 Current System Status

| Component | Status | Details |
|-----------|--------|---------|
| Internal keep-alive script | ✅ Active | Pings every 5 min (insufficient for sleep prevention) |
| External monitoring | ⚠️ **REQUIRED** | Must set up UptimeRobot or similar |
| Bot auto-restart | ✅ Active | Restarts automatically if crashes |
| Email notifications | ✅ Working | Independent of sleep status |

---

## ❓ Why Internal Script Isn't Enough

The built-in `keep_alive.sh` script IS running and pinging `/health/` every 5 minutes. You can see this in Render logs:

```
[2026-10-01 21:10:20] GET /health/ HTTP/1.1" 200
[2026-10-01 21:15:20] GET /health/ HTTP/1.1" 200
```

**BUT:** Render free tier ignores internal traffic (pings from same server). It only counts EXTERNAL requests from outside the server.

**Solution:** External service (UptimeRobot) sends EXTERNAL requests → Render stays awake!

---

## 💰 Alternative: Upgrade Render Plan

If you don't want to use external monitoring:
- Upgrade to Render "Starter" plan: **$7/month**
- No sleep timeout on paid plans
- Bot works 24/7 without external monitoring

But UptimeRobot is **100% FREE** and works perfectly!

---

## 🎯 Action Required

**You MUST complete ONE of these options for 24/7 bot operation:**

✅ **Option A:** Set up UptimeRobot (2 minutes, free forever)  
✅ **Option B:** Set up Cron-job.org (5 minutes, free forever)  
💰 **Option C:** Upgrade Render to paid plan ($7/month)

**Without external monitoring, your bot will ALWAYS sleep after 15 minutes of no web traffic.**

---

## 📞 Need Help?

If you set up UptimeRobot and bot still doesn't respond after 30 minutes:
1. Check UptimeRobot dashboard - is monitor "Up" or "Down"?
2. Check Render logs - do you see requests from UptimeRobot?
3. Send me the error messages and we'll troubleshoot

---

**⚡ TAKE ACTION NOW:** Go to https://uptimerobot.com/ and set up monitoring in 2 minutes!

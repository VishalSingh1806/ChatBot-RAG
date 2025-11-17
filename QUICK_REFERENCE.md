# ReCircle Chatbot - Quick Reference Card

## 🎯 Quick Summary

Your chatbot is ready to embed on WordPress! Here's what to do:

## 📦 What We Built

✅ **Backend CORS updated** - Allows recircle.in to access the chatbot API
✅ **Frontend configured** - Uses production API when embedded
✅ **Embed code created** - Simple iframe solution
✅ **Test page created** - Ready for W3Schools testing
✅ **Documentation written** - Complete integration guide

## 🚀 Next Steps (In Order)

### 1️⃣ Deploy Backend Changes (YOU MUST DO THIS FIRST!)

```bash
cd /mnt/d/AI-ChatBot
sudo docker-compose down
sudo docker-compose up -d --build
```

**Why?** The CORS changes allowing recircle.in won't work until you redeploy.

### 2️⃣ Test on W3Schools

1. Go to: https://www.w3schools.com/html/tryit.asp?filename=tryhtml_default
2. Copy content from: `w3schools-test.html`
3. Paste and click "Run"
4. Verify chatbot appears and works

### 3️⃣ Send to WordPress Developer

**File to send:** `EMBED_CODE.html`

**Instructions for them:**
> Install the "Insert Headers and Footers" WordPress plugin, then paste the code from EMBED_CODE.html into the "Scripts in Footer" section and save.

## 📄 Files Reference

| File | Purpose |
|------|---------|
| `EMBED_CODE.html` | **Give this to WordPress dev** - The embed code |
| `w3schools-test.html` | **Use this for testing** - W3Schools test page |
| `WORDPRESS_INTEGRATION.md` | Complete integration guide with all methods |
| `DEPLOYMENT_SUMMARY.md` | Technical summary of all changes |
| `QUICK_REFERENCE.md` | This file - Quick reference |

## 💻 The Embed Code (Copy-Paste Ready)

```html
<iframe
    id="recircle-chatbot-iframe"
    src="https://rebot.recircle.in"
    style="
        position: fixed;
        bottom: 0;
        right: 0;
        width: 100%;
        height: 100%;
        border: none;
        z-index: 999999;
        pointer-events: none;
    "
    allow="cross-origin"
    title="ReCircle Chatbot"
></iframe>

<script>
(function() {
    var iframe = document.getElementById('recircle-chatbot-iframe');
    if (iframe) {
        iframe.addEventListener('load', function() {
            iframe.style.pointerEvents = 'auto';
        });
    }
})();
</script>
```

## ✅ Checklist Before Going Live

- [ ] Backend redeployed with CORS changes
- [ ] Tested on W3Schools successfully
- [ ] Chatbot bubble appears at bottom-right
- [ ] Can open chat and fill form
- [ ] Can send messages and get responses
- [ ] Sent embed code to WordPress developer
- [ ] WordPress developer added code to site
- [ ] Verified on live recircle.in site
- [ ] Tested on mobile device

## 🎨 What Users Will See

1. **Pulsing green chat bubble** at bottom-right corner
2. **Welcome popup** greeting them
3. **Form** to collect their details (first-time only)
4. **Chat interface** to ask EPR questions
5. **Download button** to save chat transcript

## 🆘 Quick Troubleshooting

**Chatbot not showing?**
- Did you redeploy backend? (Step 1)
- Check browser console for errors (F12)
- Verify https://rebot.recircle.in loads

**Form not submitting?**
- Check CORS settings in backend
- Ensure backend is running
- Check browser console for errors

**Sessions not persisting?**
- Ensure both sites use HTTPS
- Check cookie settings in browser

## 📞 Need Help?

- Email: info@recircle.in
- Phone: 9004240004

---

**Ready to deploy?** Follow steps 1-3 above in order!

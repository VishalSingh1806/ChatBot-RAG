# WordPress Integration Guide for ReCircle Chatbot

This guide explains how to embed the ReCircle EPR Chatbot on your WordPress website.

## Overview

The chatbot will appear as a floating widget in the bottom-right corner of all pages on recircle.in, exactly like how it appears on rebot.recircle.in.

## Prerequisites

- Backend API is already deployed at: `https://rebot.recircle.in`
- CORS is configured to allow `recircle.in` and `www.recircle.in`
- Frontend is deployed and accessible

## Integration Method: iframe Embed

We're using an iframe approach which is the simplest and most reliable method for WordPress.

## Embed Code for WordPress

Add this code to your WordPress site before the closing `</body>` tag:

### Option 1: Full Page Widget (Recommended)

```html
<!-- ReCircle Chatbot Widget -->
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

### Option 2: Compact Widget (Alternative)

If you want a smaller, more compact version:

```html
<!-- ReCircle Chatbot Widget - Compact Version -->
<iframe
    id="recircle-chatbot-compact"
    src="https://rebot.recircle.in"
    style="
        position: fixed;
        bottom: 20px;
        right: 20px;
        width: 400px;
        height: 600px;
        border: none;
        border-radius: 10px;
        box-shadow: 0 20px 80px rgba(0,0,0,0.3);
        z-index: 999999;
    "
    title="ReCircle Chatbot"
></iframe>
```

## How to Add to WordPress

### Method 1: Using Theme Footer (Recommended)

1. Go to WordPress Admin Dashboard
2. Navigate to **Appearance → Theme File Editor**
3. Find and open `footer.php`
4. Paste the embed code just before the `</body>` tag
5. Click **Update File**

### Method 2: Using a Plugin

1. Install the **Insert Headers and Footers** plugin
2. Go to **Settings → Insert Headers and Footers**
3. Paste the embed code in the **Scripts in Footer** section
4. Click **Save**

### Method 3: Using Custom HTML Widget

1. Go to **Appearance → Widgets**
2. Add a **Custom HTML** widget to your footer
3. Paste the embed code
4. Save the widget

## Testing on W3Schools

Before deploying to WordPress, you can test the embed code:

1. Go to: https://www.w3schools.com/html/tryit.asp?filename=tryhtml_default
2. Replace ALL the code with the test code below:
3. Click "Run"

### Test Code for W3Schools:

```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ReCircle Chatbot Test</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            padding: 40px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
        }
        .container {
            max-width: 800px;
            margin: 0 auto;
            background: white;
            padding: 40px;
            border-radius: 10px;
            box-shadow: 0 10px 40px rgba(0,0,0,0.2);
        }
        h1 { color: #184040; }
        p { line-height: 1.6; color: #666; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Welcome to ReCircle!</h1>
        <p>This is a test page for the ReCircle EPR Compliance Chatbot.</p>
        <p>Look for the chatbot widget in the bottom-right corner!</p>
    </div>

    <!-- ReCircle Chatbot Widget -->
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
</body>
</html>
```

## Expected Behavior

1. **On Page Load**: You should see a pulsing green chat bubble in the bottom-right corner
2. **Welcome Popup**: A small welcome message appears next to the bubble
3. **On Click**: The chatbot expands into a full chat interface
4. **User Form**: New users fill out their details (name, email, phone, organization)
5. **Chat**: Users can ask questions about EPR compliance

## Troubleshooting

### Chatbot not appearing?

1. **Check CORS**: Ensure your domain is in the allowed origins list (already configured for recircle.in)
2. **Check iframe loading**: Open browser console (F12) and look for errors
3. **Check URL**: Verify `https://rebot.recircle.in` is accessible

### Cookie/Session issues?

The chatbot uses cookies to maintain sessions. Ensure your WordPress site:
- Is served over HTTPS (for secure cookies)
- Allows third-party cookies (or same-site cookies if on same domain)

### Mobile responsiveness?

The chatbot is fully responsive and will adapt to mobile screens automatically.

## Backend Deployment Notes

After making changes to CORS settings, you need to redeploy the backend:

```bash
# On your GCP server
cd /mnt/d/AI-ChatBot
sudo docker-compose down
sudo docker-compose up -d --build
```

## Support

For issues or questions:
- Email: info@recircle.in
- Phone: 9004240004

## Next Steps

1. ✅ Test the embed code on W3Schools
2. ✅ Verify the chatbot loads and functions correctly
3. ✅ Add the code to your WordPress site
4. ✅ Test on your live site
5. ✅ Monitor for any issues

---

**Created:** 2024-11-17
**Last Updated:** 2024-11-17
**Version:** 1.0

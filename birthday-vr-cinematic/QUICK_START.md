# ⚡ Quick Start - Just 3 Steps

## Step 1: Run It Locally

```bash
cd birthday-vr
python -m http.server 8000
# Or: python3 -m http.server 8000
# Or: npx http-server
```

Open your browser to: **http://localhost:8000**

## Step 2: Test It

1. Click **START EXPERIENCE**
2. Watch the 75-second cinematic experience
3. Verify audio and animations play smoothly

## Step 3: Customize (Optional)

Edit `js/experience.js`:

```javascript
const EXPERIENCE = {
    birthdayName: 'Michael',        // ← Change to their name
    fromName: 'Sarah',              // ← Change to your name
    message: {
        line1: 'Thank you for being there.',
        line2: 'Thank you for everything you\'ve done for me.',
        line3: 'You mean more to me than words can explain.',
        final: 'May life give back to you\nall the light you have given me.'
        // ↑ Customize these messages
    }
};
```

Reload the page to see changes.

## Step 4: Deploy to Internet

### Easiest: Netlify

1. Push your folder to GitHub
2. Go to [netlify.com](https://netlify.com)
3. Click "New site from Git"
4. Select your repo
5. Deploy
6. Done! Get a shareable HTTPS link

### Alternative: GitHub Pages

1. Create repo: `username/birthday-vr`
2. Upload files
3. Settings → Pages → Deploy from main
4. Live at: `https://username.github.io/birthday-vr`

## Step 5: Open in VR Headset

1. Get the HTTPS URL from your deployment
2. Open in Meta Quest Browser (or Oculus Browser)
3. Click **ENTER VR**
4. Experience in VR! 🎮

---

**That's it!** Your VR birthday experience is ready.

For detailed customization, see [README.md](README.md)

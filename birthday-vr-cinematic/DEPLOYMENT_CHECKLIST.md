# Deployment & Customization Checklist

## Quick Setup (5 minutes)

- [ ] Download the `birthday-vr` folder
- [ ] Open `index.html` in your browser (or use a local server)
- [ ] Click "START EXPERIENCE" to test
- [ ] Confirm animation and particles work

## Customization (15-30 minutes)

### Names & Messages
- [ ] Edit `js/experience.js` - Update `EXPERIENCE.birthdayName` and `EXPERIENCE.fromName`
- [ ] Update `EXPERIENCE.message` with your custom text
- [ ] Test by reloading the page

### Audio (Optional but Recommended)
- [ ] Record or obtain voice-over audio files (see README for script)
- [ ] Record or obtain background piano music
- [ ] Convert to MP3 format (44.1kHz, mono or stereo)
- [ ] Replace files in `assets/audio/`
  - [ ] `voiceover.mp3`
  - [ ] `piano-music.mp3`
  - [ ] `dark-ambience.mp3` (optional)
  - [ ] `nature-ambience.mp3` (optional)

### Professional 3D Characters (Optional but Recommended)
- [ ] Create or obtain animated GLB files
- [ ] Ensure animation clips are named correctly (see README)
- [ ] Place in `assets/models/`
  - [ ] `girl.glb`
  - [ ] `man.glb`
- [ ] Test in browser - should use your models instead of procedural ones

## Deployment (10 minutes)

### Option A: GitHub Pages
- [ ] Create GitHub account (if needed)
- [ ] Create new repository `birthday-vr`
- [ ] Upload all files (including assets/ folder)
- [ ] Enable GitHub Pages in Settings
- [ ] Test at `https://YOUR_USERNAME.github.io/birthday-vr`

### Option B: Netlify
- [ ] Create Netlify account
- [ ] Connect to GitHub repository
- [ ] Auto-deploy on push
- [ ] Get custom domain
- [ ] Test in browser

### Option C: Cloudflare Pages
- [ ] Go to pages.cloudflare.com
- [ ] Connect GitHub repository
- [ ] Deploy
- [ ] Test at `https://your-project.pages.dev`

### Option D: Vercel
- [ ] Go to vercel.com
- [ ] Import GitHub repository
- [ ] Deploy
- [ ] Test at `https://your-project.vercel.app`

## Testing

### Desktop Testing
- [ ] Open on Chrome/Edge/Firefox
- [ ] Click START
- [ ] Verify animation plays smoothly
- [ ] Check volume/audio works
- [ ] Full sequence completes (75 seconds)

### Mobile Testing
- [ ] Open on phone/tablet
- [ ] Rotate device - camera follows
- [ ] Tap START button
- [ ] Experience plays smoothly
- [ ] Full sequence completes

### VR Testing (Meta Quest, etc.)
- [ ] Deploy to HTTPS first (required)
- [ ] Open URL in VR headset browser
- [ ] Click "ENTER VR" button
- [ ] Put on headset
- [ ] Verify spatial audio works
- [ ] Full sequence completes in VR

## Final Checklist

- [ ] All files uploaded to server
- [ ] Audio files are in place
- [ ] Character models (if using) are in place
- [ ] HTTPS is enabled (required for VR)
- [ ] Tested on desktop
- [ ] Tested on mobile
- [ ] Tested in VR (if available)
- [ ] All customizations complete
- [ ] Ready to share!

## Share with Recipient

1. Copy the HTTPS URL from your deployed site
2. Send via email, message, or QR code
3. For best experience: suggest using VR headset
4. For desktop: suggest headphones and dark room
5. Mention it's a ~75 second experience

## Troubleshooting Quick Fixes

| Issue | Fix |
|-------|-----|
| Audio not playing | Check browser console, ensure click START first, check audio file paths |
| Low FPS in VR | Reduce particle count in `js/particles.js` |
| Characters look wrong | Check GLB model names and animation clip names |
| Site won't load | Verify all files uploaded, check console for 404 errors |
| VR button missing | Try different VR browser, enable WebXR in settings |
| Slow loading | Compress GLB models with Draco, reduce audio bitrate to 128kbps |

---

**Pro Tip**: Keep the original project folder as a backup. Test every change before sharing!

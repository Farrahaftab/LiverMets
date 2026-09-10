# 🎬 Birthday VR - Cinematic Edition

A **professional-grade cinematic VR experience** built with Three.js and WebXR. Approximately 75 seconds of immersive storytelling.

## ✨ What This Is

A deeply personal animated fairytale VR experience:

- **Dark Opening** - Volumetric lighting, atmospheric fog, emotional isolation
- **Arrival** - Spatial audio footsteps, warm light entering darkness
- **Connection** - Emotional hand-touch moment with golden particle pulse
- **Transformation** - World morphs from dark to beautiful golden-hour valley
- **Gratitude** - Characters walk toward hope-filled horizon
- **Birthday Message** - Elegant cinematic text sequence
- **Fade** - Peaceful, beautiful ending

Works in:
- ✅ Meta Quest and WebXR VR headsets
- ✅ Desktop Chrome/Edge/Firefox with full 3D
- ✅ Mobile/tablet with gyroscope control

## 🎯 IMPORTANT NOTES - READ FIRST

### Character Assets
This version uses **tasteful silhouette placeholders** instead of crude geometry when professional models are missing.

**To use high-quality characters:**
1. Create or obtain animated GLB/GLTF character models
2. Place them in `assets/models/`:
   - `girl.glb` - Animated female character
   - `man.glb` - Animated male character
3. The experience automatically detects and loads them

**Check your browser console** for messages showing which assets loaded.

### Development Mode
To see detailed console logging during desktop preview:

Edit `js/experience.js`:
```javascript
const DEVELOPMENT_MODE = true;  // Shows FPS, timeline, particles in top-left
```

## 🚀 Quick Start

### Step 1: Run Locally

```bash
cd birthday-vr-cinematic

# Python 3
python -m http.server 8000

# OR Python 2
python -m SimpleHTTPServer 8000

# OR Node.js
npx http-server
```

Open: **http://localhost:8000**

### Step 2: Test It

1. See the elegant start screen
2. Click **START EXPERIENCE**
3. Watch the full 75-second cinematic sequence
4. Check browser console (F12) for asset loading info

**Note:** First load may take a few seconds for Three.js to initialize.

### Step 3: Customize Names & Message

Edit `js/experience.js` - change these at the top:

```javascript
const EXPERIENCE = {
    birthdayName: 'Michael',    // ← His name
    fromName: 'Sarah',          // ← Your name
    message: {
        title: 'Happy Birthday',
        line1: 'Thank you for being there.',
        line2: 'Thank you for everything you\'ve done for me.',
        line3: 'You mean more to me than words can explain.',
        final: 'May life give back to you\nall the light you have given me.'
    }
};
```

Reload the page - your text appears in the final scene.

### Step 4: Deploy to Internet

**Recommended: Netlify (Free)**

```bash
# Push to GitHub first
git push

# Then on netlify.com:
# 1. Click "New site from Git"
# 2. Connect your GitHub repo
# 3. Deploy (automatic)
# 4. Get HTTPS URL
```

Other free options:
- **GitHub Pages** - Free hosting, simple setup
- **Cloudflare Pages** - Fast CDN, free tier
- **Vercel** - One-click deploy from GitHub

### Step 5: Open in VR Headset

1. **Deploy to HTTPS first** (required for WebXR)
2. In Meta Quest Browser: Open your HTTPS URL
3. Click **ENTER VR** button
4. Put on your headset
5. Experience! 🎮

## 📁 Project Structure

```
birthday-vr-cinematic/
├── index.html                  ← Open this
├── css/style.css              ← Elegant styling
├── js/
│   ├── experience.js          ← Main controller (EDIT NAMES HERE)
│   ├── timeline.js            ← 75-second sequence
│   ├── characters.js          ← Asset loading + silhouette fallback
│   ├── environment.js         ← Cinematic dark/light scenes
│   ├── particles.js           ← Golden particle system
│   ├── audio.js               ← Spatial 3D audio
│   └── main.js                ← Bootstrap
└── assets/
    ├── models/                ← girl.glb, man.glb (optional)
    ├── audio/                 ← MP3 files (optional)
    └── environment/           ← (future use)
```

## 🎨 Asset Preparation

### 3D Character Models (Optional but Recommended)

Create or download animated GLB files:

**Girl character animation clips:**
- `SittingSad` - Sitting with knees to chest, looking down
- `LookUp` - Looking up toward the man
- `ReachHand` - Reaching hand
- `StandUp` - Standing up
- `IdleHappy` - Standing peacefully
- `Walk` - Walking animation

**Man character animation clips:**
- `WalkIn` - Entering the scene
- `Idle` - Standing calmly
- `ReachHand` - Reaching hand
- `Helping` - Helping pose
- `WalkTogether` - Walking beside girl

Save as:
- `assets/models/girl.glb`
- `assets/models/man.glb`

**How to create GLB files:**
1. Use Blender (free) or similar 3D software
2. Create character mesh with rigging
3. Create animation clips for each action
4. Export as `.glb` format
5. Place in `assets/models/`

The experience automatically loads them if present.

### Voice-Over Audio (Optional but Recommended)

Record clear voice-over following this script:

```
0-3s:   "There were moments when everything felt heavy...
         when I felt lost in my own darkness."

10-15s: "And then you came into my life...
         Maybe you never realised it, but your presence changed more than you know."

21-28s: "You held my hand when I needed someone.
         You gave me strength when I felt weak.
         You brought comfort into moments you may never even know were difficult."

38-43s: "You brought light into places that had become dark.
         You reminded me that life could still feel beautiful."

51-60s: "And today, on your birthday...
         [pause] I just want you to know something I probably don't say enough.
         [pause] You are incredibly important to me."
```

Export as MP3 (44.1kHz) and place at:
- `assets/audio/voiceover.mp3`

### Background Music (Optional)

Find or create a soft emotional piano piece (~75 seconds):
- Export as MP3
- Place at: `assets/audio/piano-music.mp3`

## 🎬 Visual Quality Features

✨ **Cinematic Lighting:**
- Physically-based renderer settings
- ACES filmic tone mapping
- Hemisphere lighting for depth
- Directional sun with proper shadows
- Rim lighting for emotional warmth

🌫️ **Atmospheric Effects:**
- Volumetric-feeling fog
- Blue-grey emotional opening scene
- Golden-hour color grading
- Procedurally generated environments

✨ **Particle System:**
- GPU-accelerated
- 5000-particle capacity
- Proper depth sorting
- Gradual fade lifecycle
- Wave emission patterns

🔊 **Spatial Audio:**
- 3D positioned sound
- Footsteps come from right-back
- Voice reverb in spaces
- Smooth fade transitions

## 🖥️ Development Mode

Enable console debugging in desktop mode only:

Edit `js/experience.js`:
```javascript
const DEVELOPMENT_MODE = true;
```

Shows in top-left:
- FPS counter
- Current timeline position
- Character count
- Particle count
- VR status

## 🛠️ Advanced Customization

### Change Timing

Edit `js/timeline.js`:

```javascript
this.addEvent(10, 'footstepsStart', () => {
    // Change "10" to adjust when event happens
});
```

### Adjust Lighting Intensity

Edit `js/environment.js`:

```javascript
const sunLight = new THREE.DirectionalLight(0xffd89b, 1.8);
sunLight.intensity = 2.5;  // Increase for brighter
```

### Modify Scene Duration

Edit `js/timeline.js`:

```javascript
this.duration = 75;  // Change total length in seconds
```

### Change Color Palette

Search in `js/environment.js` for hex colors like:
- `0xd4af37` - Gold
- `0x5a8c3a` - Grass green
- `0x1e4b7f` - Water blue
- `0xffd89b` - Sunset warmth

## ✅ Checklist Before Sharing

- [ ] Personalized his name in `js/experience.js`
- [ ] Customized all messages
- [ ] (Optional) Added professional character models
- [ ] (Optional) Added voice-over audio
- [ ] (Optional) Added background music
- [ ] Tested locally - runs smoothly
- [ ] Deployed to HTTPS
- [ ] Tested on mobile
- [ ] Tested in VR headset (if available)
- [ ] Checked browser console for any errors
- [ ] Ready to share!

## 🆘 Troubleshooting

| Issue | Solution |
|-------|----------|
| **Blank dark screen** | Wait 3-5 seconds for load, then click START |
| **Characters not showing** | Check console (F12) for "Professional .glb required" message - this is normal, use silhouettes or add models |
| **Audio not playing** | Click START first (browsers require user interaction), check console for audio messages |
| **Low FPS in VR** | Reduce particle count: edit `js/particles.js`, change `maxParticles: 5000` to `2000` |
| **VR button missing** | Use Meta Quest Browser or Chrome with WebXR enabled |
| **Models load slowly** | Compress GLB files with Draco compression in Blender |

## 📱 Browser Support

| Browser | Desktop | Mobile | VR |
|---------|---------|--------|-----|
| Chrome | ✅ | ✅ | ✅ |
| Edge | ✅ | ✅ | ✅ |
| Firefox | ✅ | ✅ | ⚠️ |
| Safari | ✅ | ⚠️ | ❌ |
| Meta Quest Browser | ✅ | ✅ | ✅ |

## 🎁 What Makes This Special

- ✨ **Cinematic Quality** - Professional lighting, effects, and presentation
- 🎬 **Fully Customizable** - Your names, your message, your story
- 🌍 **Universal** - Works on phone, desktop, and VR headsets
- ⚡ **Lightweight** - Only ~150KB total code (very fast loading)
- 🎨 **Beautiful Fallbacks** - Looks great even without custom assets
- 🔊 **Spatial Audio** - 3D sound positioning for immersion
- 💚 **Personal** - Built to communicate deep gratitude and importance

## 📊 Performance

- Target: **60 FPS** on desktop, **72 FPS** on VR headsets
- Typical load time: **3-5 seconds**
- Fallback silhouettes: Load instantly if models missing
- Particle budget: **5000 particles** maximum
- Draw calls: Optimized for mobile VR

## 🔐 Hosting Security

When deploying:
- Use HTTPS (all recommended hosts provide this)
- No sensitive data stored in code
- Audio/video files should be your own or licensed

## 💝 Final Notes

This experience communicates one feeling above all:

> "You came into a dark moment of my life, held my hand, helped me find the light again, and you became more important to me than you probably know."

It ends as a beautiful, hopeful birthday gift - not a sad story.

---

**Created with love** ❤️ for someone very special.

For detailed setup instructions, see **QUICK_START.md**

# Assets Folder

This folder contains all media files for the VR experience.

## Directory Structure

### `/models/` - 3D Character Models
Place your animated GLB files here:
- `girl.glb` - Animated female character
- `man.glb` - Animated male character

If these files are missing, the experience will automatically use beautiful procedural 3D character placeholders.

**How to prepare models:**
1. Create or download animated character models in Blender or similar software
2. Create animations for these actions:
   - Girl: SittingSad, LookUp, ReachHand, StandUp, IdleHappy, Walk
   - Man: WalkIn, Idle, ReachHand, Helping, WalkTogether
3. Export as `.glb` format (single file)
4. Place in this folder

### `/environment/` - Environment Models
Optional pre-built environment models:
- `dark_room.glb` - Dark scene environment
- `magical_valley.glb` - Light scene environment

If missing, procedurally generated environments are used automatically.

### `/audio/` - Sound Files
All audio should be MP3 format (44.1kHz recommended):

- `voiceover.mp3` - Voice-over narration (~60 seconds)
  - Record the emotional narration from the README
  - Keep voice clear and intimate
  
- `piano-music.mp3` - Background piano (~75 seconds)
  - Soft, emotional piano piece
  - Starts at 12 seconds into experience
  
- `dark-ambience.mp3` - Dark scene ambient sound (~10 seconds)
  - Subtle, peaceful ambience
  - No harsh sounds
  
- `footsteps.mp3` - Spatial footsteps (~3 seconds)
  - Soft footsteps sound
  - Creates spatial immersion
  
- `light-whoosh.mp3` - Magical transition sound (~1-2 seconds)
  - Soft, glowing sound effect
  - Plays when hands touch
  
- `nature-ambience.mp3` - Light scene ambient sound (~75 seconds)
  - Gentle birds, wind, nature sounds
  - Loop-friendly

**How to prepare audio:**
1. Record voice-over in quiet room with good microphone
2. Edit in Audacity or similar (free software)
3. Export as MP3, 44.1kHz, mono or stereo
4. Keep file sizes reasonable (< 5MB each)
5. Place in this folder

### `/textures/` - Optional Custom Textures
Add custom textures for characters or environment if using advanced models.

## Quick Notes

- All audio files are optional - the experience uses fallback sounds if missing
- Character models are optional - beautiful procedural models are used as fallback
- For best quality, add your own custom audio
- For most professional appearance, add GLB character models

## File Size Tips

- Voice-over: ~3-4 MB per minute
- Background music: ~2-3 MB per minute
- Compressed audio: Use 128-192 kbps bitrate
- Character models: Keep under 2 MB (use Draco compression in Blender)
- Texture sizes: 1024x1024 or smaller

## Testing Locally

When testing locally with `python -m http.server`:
- Audio files may be required to be CORS-compatible
- Modern browsers handle this automatically
- If issues occur, ensure files are in the correct folder

---

**Pro Tip:** Start with just the procedural version, then gradually add professional audio and models for maximum impact!

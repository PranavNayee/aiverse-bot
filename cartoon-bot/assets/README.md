# Assets Folder

This folder contains optional media assets for your cartoon bot.

## Structure

```
assets/
├── music/           # Background music tracks (MP3 or WAV)
├── intro.mp4        # Custom intro clip (optional)
└── outro.mp4        # Custom outro clip (optional)
```

## Music

Place royalty-free background music files in the `music/` folder:
- Format: MP3 or WAV
- The bot will randomly select one track per video
- Music auto-ducks under dialogue (volume lowers when characters speak)
- Final audio is normalized for consistent loudness

**Recommended sources for free music:**
- [YouTube Audio Library](https://www.youtube.com/audiolibrary)
- [Free Music Archive](https://freemusicarchive.org)
- [Incompetech](https://incompetech.com/music/royalty-free/)
- [Bensound](https://www.bensound.com)

## Custom Intro (Optional)

Create a custom `intro.mp4` file:
- Resolution: 1080x1920 (vertical)
- Duration: 2-3 seconds recommended
- Should show your channel branding/logo
- If not provided, a simple text intro is auto-generated

## Custom Outro (Optional)

Create a custom `outro.mp4` file:
- Resolution: 1080x1920 (vertical)
- Duration: 2-3 seconds recommended
- Should include your CTA (call-to-action) like "Follow for more!"
- If not provided, a simple text outro is auto-generated

## Disabling Features

You can disable intro/outro/transitions via GitHub Actions Variables:
- `ADD_INTRO=false` - Skip intro
- `ADD_OUTRO=false` - Skip outro
- `ADD_TRANSITIONS=false` - No crossfades between scenes
- `KARAOKE_SUBS=false` - Disable word-by-word karaoke subtitles

## Tips

1. **Keep intro/outro short** (under 3 seconds) - viewers skip long intros
2. **Use upbeat music** that matches your comedy style
3. **Test different tracks** to see what works best with your content
4. **Match your brand colors** in custom intro/outro for consistency

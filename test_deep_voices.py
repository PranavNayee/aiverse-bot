"""Test deeper male voices for AI Seekho"""
import asyncio
import edge_tts
import os

os.makedirs("deep_voice_samples", exist_ok=True)

# Sample Hinglish text (typical lesson narration)
SAMPLE_TEXT = "Namaste! Aaj hum seekhenge AI kya hai. Artificial Intelligence matlab machine jo insaan jaise soch sake. Yeh bahut interesting topic hai!"

VOICES = [
    ("1-Christopher-US", "en-US-ChristopherNeural", "+0%", "+0Hz", "Deep authoritative (News anchor)"),
    ("2-Guy-US", "en-US-GuyNeural", "+0%", "+0Hz", "Deep passionate (News)"),
    ("3-Andrew-US", "en-US-AndrewNeural", "+0%", "+0Hz", "Deep warm conversational"),
    ("4-Madhur-Hindi", "hi-IN-MadhurNeural", "+0%", "+0Hz", "Hindi male friendly"),
    ("5-Prabhat-Indian", "en-IN-PrabhatNeural", "+0%", "+0Hz", "Indian English male"),
    ("6-Andrew-Slower", "en-US-AndrewNeural", "-5%", "+0Hz", "Andrew slower pace"),
    ("7-Christopher-Slower", "en-US-ChristopherNeural", "-3%", "+0Hz", "Christopher teaching pace"),
]

async def generate_sample(name, voice, rate, pitch, description):
    output = f"deep_voice_samples/{name}.mp3"
    print(f"Generating {name}: {description}...")
    communicate = edge_tts.Communicate(SAMPLE_TEXT, voice, rate=rate, pitch=pitch)
    await communicate.save(output)
    print(f"  ✓ Saved to {output}")

async def main():
    print("=" * 60)
    print("TESTING DEEPER MALE VOICES FOR AI SEEKHO")
    print("=" * 60)
    print(f"\nSample text: {SAMPLE_TEXT}\n")
    
    for voice_config in VOICES:
        await generate_sample(*voice_config)
        print()
    
    print("=" * 60)
    print("✅ All samples generated in deep_voice_samples/")
    print("Listen to each and choose your favorite!")
    print("=" * 60)
    print("\nRECOMMENDATIONS:")
    print("• Christopher = Deepest, most authoritative (great for serious topics)")
    print("• Andrew = Deep + warm (best for conversational teaching)")
    print("• Guy = Deep + energetic (engaging but might be too much)")
    print("• Madhur = Hindi voice (natural for pure Hindi segments)")

if __name__ == "__main__":
    asyncio.run(main())

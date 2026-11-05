"""Test Indian voices for Hinglish (proper Hindi pronunciation)"""
import asyncio
import edge_tts
import os

os.makedirs("indian_voice_samples", exist_ok=True)

# REAL Hinglish text from your lesson
HINGLISH_TEXT = "AI, ML, aur Deep Learning mein farq kya hai? Socho ek dabba ke andar ek aur dabba, jaise AI ke andar ML hai aur ML ke andar Deep Learning. Deep Learning, ML ka ek sub-part hai jo many-layer neural networks use karta hai."

VOICES = [
    ("1-Prabhat-Indian-Male", "en-IN-PrabhatNeural", "+3%", "+0Hz", "Indian English Male - Good for Hinglish"),
    ("2-Madhur-Hindi-Male", "hi-IN-MadhurNeural", "+3%", "+0Hz", "Pure Hindi Male - Natural Hindi"),
    ("3-Neerja-Indian-Female", "en-IN-NeerjaNeural", "+3%", "+0Hz", "Indian English Female - Clear"),
    ("4-Swara-Hindi-Female", "hi-IN-SwaraNeural", "+3%", "+0Hz", "Pure Hindi Female"),
    ("5-Prabhat-Slower", "en-IN-PrabhatNeural", "+0%", "+0Hz", "Prabhat slower for clarity"),
    ("6-Madhur-Slower", "hi-IN-MadhurNeural", "+0%", "+0Hz", "Madhur slower"),
]

async def generate_sample(name, voice, rate, pitch, description):
    output = f"indian_voice_samples/{name}.mp3"
    print(f"Generating {name}: {description}...")
    communicate = edge_tts.Communicate(HINGLISH_TEXT, voice, rate=rate, pitch=pitch)
    await communicate.save(output)
    print(f"  ✓ Saved to {output}")

async def main():
    print("=" * 70)
    print("TESTING INDIAN VOICES FOR HINGLISH (PROPER HINDI PRONUNCIATION)")
    print("=" * 70)
    print(f"\nSample text:\n{HINGLISH_TEXT}\n")
    print("=" * 70)
    
    for voice_config in VOICES:
        await generate_sample(*voice_config)
        print()
    
    print("=" * 70)
    print("✅ All samples generated in indian_voice_samples/")
    print("=" * 70)
    print("\n🎙️ RECOMMENDATIONS FOR HINGLISH:")
    print("• Prabhat (en-IN-PrabhatNeural) = BEST for Hinglish (reads both Hindi & English)")
    print("• Madhur (hi-IN-MadhurNeural) = Good for Hindi-heavy content")
    print("• Neerja = Backup option (female voice)")
    print("\n⚠️ AVOID: US/UK voices (Andrew, Christopher) - they butcher Hindi words!")

if __name__ == "__main__":
    asyncio.run(main())

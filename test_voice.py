#!/usr/bin/env python3
"""Test different Indian voices for Hinglish education content"""
import sys, os
sys.path.insert(0, 'cartoon-bot/src')

import asyncio
import edge_tts

# Test sentence in Hinglish (natural mix)
TEST_SENTENCE = "Machine Learning ek aisa technique hai jahan computer khud se seekhta hai. Jaise aap roz chai peete ho aur dukaan wala yaad kar leta hai - 2 chammach cheeni, kam doodh. Exactly waise hi AI bhi data se pattern dhundh kar prediction karta hai!"

# Available Indian voices
VOICES = {
    "1. en-IN-NeerjaNeural (Female - Friendly)": {
        "voice": "en-IN-NeerjaNeural",
        "rate": "+5%",
        "pitch": "+8Hz",
        "description": "🌟 RECOMMENDED - Warm, friendly, perfect for teaching"
    },
    "2. en-IN-PrabhatNeural (Male - Professional)": {
        "voice": "en-IN-PrabhatNeural",
        "rate": "+6%",
        "pitch": "+3Hz",
        "description": "Professional, clear, good for technical content"
    },
    "3. hi-IN-SwaraNeural (Female - Hindi)": {
        "voice": "hi-IN-SwaraNeural",
        "rate": "+5%",
        "pitch": "+6Hz",
        "description": "Pure Hindi, warm tone"
    },
    "4. hi-IN-MadhurNeural (Male - Hindi)": {
        "voice": "hi-IN-MadhurNeural",
        "rate": "+5%",
        "pitch": "+3Hz",
        "description": "Pure Hindi, authoritative"
    },
}

async def generate_voice(name, config, output_file):
    """Generate TTS audio"""
    print(f"\nGenerating: {name}")
    print(f"  Voice: {config['voice']}")
    print(f"  Description: {config['description']}")
    
    communicate = edge_tts.Communicate(
        TEST_SENTENCE,
        config['voice'],
        rate=config['rate'],
        pitch=config['pitch']
    )
    
    await communicate.save(output_file)
    print(f"  ✅ Saved: {output_file}")

async def main():
    print("🎤 Testing Hinglish Voices for AI Seekho")
    print("=" * 60)
    print(f"\nTest sentence:")
    print(f'"{TEST_SENTENCE}"')
    print("=" * 60)
    
    os.makedirs("voice_tests", exist_ok=True)
    
    for name, config in VOICES.items():
        output_file = f"voice_tests/{name.split('.')[0].strip()}.mp3"
        await generate_voice(name, config, output_file)
    
    print("\n" + "=" * 60)
    print("✅ All voice samples generated!")
    print("\n📁 Listen to files in voice_tests/ folder:")
    print("   1 - Neerja (Female, Friendly) 🌟 RECOMMENDED")
    print("   2 - Prabhat (Male, Professional)")
    print("   3 - Swara (Female, Hindi)")
    print("   4 - Madhur (Male, Hindi)")
    print("\n💡 Current config uses: en-IN-NeerjaNeural (Friendly Female)")
    print("   This is the warmest, most educational-friendly voice!")

if __name__ == "__main__":
    asyncio.run(main())

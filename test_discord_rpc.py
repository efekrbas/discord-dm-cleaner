#!/usr/bin/env python3
"""
Test script for Discord Rich Presence functionality
This script demonstrates how the Discord activity works with the DM Cleaner
"""

import asyncio
import sys
import os
import time

# Add the current directory to the path so we can import from main.pyw
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main import DiscordRichPresence

def test_discord_rpc():
    """Test Discord Rich Presence functionality"""
    print("Discord Rich Presence Test")
    print("=" * 30)
    
    # Create Discord RPC instance
    rpc = DiscordRichPresence()
    
    # Try to connect
    print("Connecting to Discord...")
    connected = rpc.connect()
    
    if not connected:
        print("❌ Failed to connect to Discord RPC")
        print("Make sure Discord is running and you have Rich Presence enabled")
        return False
    
    print("✅ Connected to Discord RPC")
    
    # Test different activity states
    activities = [
        ("DM Cleaner Açık", "DM listesi yükleniyor..."),
        ("DM Temizleniyor", "Seçili DM'deki mesajlar siliniyor..."),
        ("Tüm DM'ler Temizleniyor", "Tüm mesajlar siliniyor..."),
        ("DM Temizleme Tamamlandı", "Toplam 150 mesaj silindi"),
        ("DM Cleaner Açık", "25 DM bulundu - Hazır")
    ]
    
    for i, (details, state) in enumerate(activities, 1):
        print(f"\nTest {i}/5: Setting activity...")
        print(f"  Details: {details}")
        print(f"  State: {state}")
        
        success = rpc.set_activity(details, state)
        if success:
            print("  ✅ Activity set successfully")
        else:
            print("  ❌ Failed to set activity")
        
        # Wait 2 seconds between each test
        time.sleep(2)
    
    # Clear activity
    print("\nClearing activity...")
    rpc.clear_activity()
    print("✅ Activity cleared")
    
    # Close connection
    rpc.close()
    print("✅ Connection closed")
    
    return True

def main():
    """Main test function"""
    print("Discord Rich Presence Test for DM Cleaner")
    print("=" * 50)
    print()
    print("This test will:")
    print("1. Connect to Discord RPC")
    print("2. Set various activity states")
    print("3. Clear the activity")
    print("4. Close the connection")
    print()
    print("Make sure Discord is running before starting the test!")
    print()
    
    input("Press Enter to start the test...")
    
    try:
        success = test_discord_rpc()
        if success:
            print("\n🎉 Test completed successfully!")
            print("Check your Discord status to see the activity changes.")
        else:
            print("\n❌ Test failed!")
    except KeyboardInterrupt:
        print("\n\nTest interrupted by user")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")

if __name__ == "__main__":
    main()

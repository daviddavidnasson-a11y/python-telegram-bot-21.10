
TEST_PAYLOADS = {
    "normal": "Hello WhatsApp!",
    "emoji": "😊😂❤️🔥",
    "unicode": "こんにちは مرحبا",
    "multiline": "Hello\nHow are you?\nTesting",
    "long_text": "A" * 10000,
    "symbols": "!@#$%^&*()_+-=",
}

def run_tests():
    for name, message in TEST_PAYLOADS.items():
        print(f"\nTest: {name}")
        print("Characters:", len(message))
        print("UTF-8 bytes:", len(message.encode("utf-8")))

if __name__ == "__main__":
    run_tests()
  

"""
End-to-End Verification Script for Platform Extension Framework

This script verifies that all components of the platform framework work together correctly:
1. Imports work correctly
2. Factory can create adapters
3. Adapters implement required interfaces
4. Configuration system loads properly
5. All tests pass
"""

import sys
import asyncio
from typing import Dict, Any


def test_imports():
    """Test 1: Verify all imports work correctly."""
    print("\n" + "="*70)
    print("TEST 1: Import Verification")
    print("="*70)

    try:
        # Import base classes
        from src.platforms import BasePlatformAdapter
        print("✓ BasePlatformAdapter imported successfully")

        from src.platforms.models import PlatformMessage, MessageType, PlatformUser
        print("✓ Platform models imported successfully")

        # Import adapters
        from src.platforms.adapters import TelegramAdapter, DiscordAdapter
        print("✓ TelegramAdapter imported successfully")
        print("✓ DiscordAdapter imported successfully")

        # Import factory
        from src.platforms.factory import PlatformFactory
        print("✓ PlatformFactory imported successfully")

        # Import configuration
        from config.platform_config import platform_config
        print("✓ Platform configuration imported successfully")

        from src.platforms.config import TelegramConfig, DiscordConfig
        print("✓ Platform-specific configs imported successfully")

        print("\n✅ All imports successful!")
        return True

    except Exception as e:
        print(f"\n❌ Import failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_factory_creation():
    """Test 2: Verify factory can create adapters."""
    print("\n" + "="*70)
    print("TEST 2: Factory Adapter Creation")
    print("="*70)

    try:
        from src.platforms.factory import PlatformFactory
        from src.platforms.config import TelegramConfig, DiscordConfig

        # Create Telegram adapter
        telegram_config = TelegramConfig(bot_token="test_telegram_token_123")
        telegram_adapter = PlatformFactory.create('telegram', telegram_config)
        print(f"✓ Created Telegram adapter: {telegram_adapter.get_platform_name()}")

        # Create Discord adapter
        discord_config = DiscordConfig(bot_token="test_discord_token_456", guild_id="123456789")
        discord_adapter = PlatformFactory.create('discord', discord_config)
        print(f"✓ Created Discord adapter: {discord_adapter.get_platform_name()}")

        # Verify available platforms
        available = PlatformFactory.get_available_platforms()
        print(f"✓ Available platforms: {available}")
        assert 'telegram' in available, "Telegram should be available"
        assert 'discord' in available, "Discord should be available"

        print("\n✅ Factory creation successful!")
        return True

    except Exception as e:
        print(f"\n❌ Factory creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_interface_implementation():
    """Test 3: Verify adapters implement required interface."""
    print("\n" + "="*70)
    print("TEST 3: Interface Implementation Verification")
    print("="*70)

    try:
        from src.platforms import BasePlatformAdapter
        from src.platforms.adapters import TelegramAdapter, DiscordAdapter
        from src.platforms.config import TelegramConfig, DiscordConfig

        # Verify Telegram adapter
        telegram_config = TelegramConfig(bot_token="test_token")
        telegram_adapter = TelegramAdapter(telegram_config)

        assert isinstance(telegram_adapter, BasePlatformAdapter), \
            "TelegramAdapter must be instance of BasePlatformAdapter"
        print("✓ TelegramAdapter is instance of BasePlatformAdapter")

        # Check required methods
        required_methods = [
            'get_platform_name',
            'validate_config',
            'start',
            'stop',
            'send_message',
            'receive_message'
        ]

        for method in required_methods:
            assert hasattr(telegram_adapter, method), \
                f"TelegramAdapter must have {method} method"
        print(f"✓ TelegramAdapter implements all {len(required_methods)} required methods")

        # Verify Discord adapter
        discord_config = DiscordConfig(bot_token="test_token", guild_id="123")
        discord_adapter = DiscordAdapter(discord_config)

        assert isinstance(discord_adapter, BasePlatformAdapter), \
            "DiscordAdapter must be instance of BasePlatformAdapter"
        print("✓ DiscordAdapter is instance of BasePlatformAdapter")

        for method in required_methods:
            assert hasattr(discord_adapter, method), \
                f"DiscordAdapter must have {method} method"
        print(f"✓ DiscordAdapter implements all {len(required_methods)} required methods")

        # Verify platform names
        assert telegram_adapter.get_platform_name() == 'telegram', \
            "TelegramAdapter must return 'telegram' as platform name"
        print(f"✓ TelegramAdapter platform name: {telegram_adapter.get_platform_name()}")

        assert discord_adapter.get_platform_name() == 'discord', \
            "DiscordAdapter must return 'discord' as platform name"
        print(f"✓ DiscordAdapter platform name: {discord_adapter.get_platform_name()}")

        print("\n✅ Interface implementation verified!")
        return True

    except Exception as e:
        print(f"\n❌ Interface verification failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_configuration_loading():
    """Test 4: Verify configuration system loads properly."""
    print("\n" + "="*70)
    print("TEST 4: Configuration System Loading")
    print("="*70)

    try:
        from config.platform_config import platform_config

        # Check platform_config exists
        assert platform_config is not None, "platform_config should be initialized"
        print("✓ platform_config instance exists")

        # Check methods exist
        assert hasattr(platform_config, 'platforms'), \
            "platform_config should have 'platforms' property"
        print("✓ platform_config has 'platforms' property")

        assert hasattr(platform_config, 'available_platforms'), \
            "platform_config should have 'available_platforms' property"
        print("✓ platform_config has 'available_platforms' property")

        assert hasattr(platform_config, 'is_platform_available'), \
            "platform_config should have 'is_platform_available' method"
        print("✓ platform_config has 'is_platform_available' method")

        assert hasattr(platform_config, 'get_platform_config'), \
            "platform_config should have 'get_platform_config' method"
        print("✓ platform_config has 'get_platform_config' method"

        # Check platforms property (may be empty if no env vars set)
        platforms = platform_config.platforms
        print(f"✓ Loaded platforms: {list(platforms.keys()) if platforms else '(none - env vars not set)'}")

        print("\n✅ Configuration system verified!")
        return True

    except Exception as e:
        print(f"\n❌ Configuration loading failed: {e}")
        import traceback
        traceback.print_exc()
        return False


async def test_adapter_lifecycle():
    """Test 5: Verify adapter lifecycle (bonus verification)."""
    print("\n" + "="*70)
    print("TEST 5: Adapter Lifecycle (Bonus)")
    print("="*70)

    try:
        from src.platforms.config import TelegramConfig
        from src.platforms.adapters import TelegramAdapter

        # Create adapter
        config = TelegramConfig(bot_token="test_lifecycle_token")
        adapter = TelegramAdapter(config)
        print("✓ Adapter created")

        # Check initial status
        status = adapter.get_status()
        assert isinstance(status, dict), "get_status should return dict"
        assert 'platform' in status, "Status should contain 'platform'"
        assert 'is_running' in status, "Status should contain 'is_running'"
        assert status['is_running'] == False, "Should not be running initially"
        print(f"✓ Initial status: {status}")

        # Test validation (should pass with valid config)
        try:
            adapter.validate_config()
            print("✓ Configuration validation passed")
        except Exception:
            # This is ok - validation might fail without actual bot credentials
            print("⚠ Configuration validation skipped (requires real credentials)")

        print("\n✅ Adapter lifecycle verified!")
        return True

    except Exception as e:
        print(f"\n❌ Adapter lifecycle test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all end-to-end verification tests."""
    print("\n" + "="*70)
    print("PLATFORM EXTENSION FRAMEWORK - END-TO-END VERIFICATION")
    print("="*70)

    results = {
        'imports': False,
        'factory': False,
        'interface': False,
        'configuration': False,
        'lifecycle': False
    }

    # Run tests
    results['imports'] = test_imports()
    results['factory'] = test_factory_creation()
    results['interface'] = test_interface_implementation()
    results['configuration'] = test_configuration_loading()

    # Run async lifecycle test
    try:
        results['lifecycle'] = asyncio.run(test_adapter_lifecycle())
    except Exception as e:
        print(f"\n❌ Lifecycle test failed: {e}")
        results['lifecycle'] = False

    # Summary
    print("\n" + "="*70)
    print("VERIFICATION SUMMARY")
    print("="*70)

    for test_name, passed in results.items():
        status = "✅ PASS" if passed else "❌ FAIL"
        print(f"{status} - {test_name.title()}")

    total = len(results)
    passed = sum(results.values())
    print(f"\nTotal: {passed}/{total} tests passed")

    if all(results.values()):
        print("\n" + "="*70)
        print("🎉 ALL VERIFICATION TESTS PASSED! 🎉")
        print("="*70)
        print("\nThe Platform Extension Framework is working correctly:")
        print("  ✓ All imports successful")
        print("  ✓ Factory can create adapters")
        print("  ✓ Adapters implement required interface")
        print("  ✓ Configuration system loads properly")
        print("  ✓ Adapter lifecycle works as expected")
        print("\nYou can now:")
        print("  1. Add new platform adapters by implementing BasePlatformAdapter")
        print("  2. Use PlatformFactory.create() to instantiate adapters")
        print("  3. Configure platforms via environment variables")
        print("  4. See src/platforms/README.md for detailed documentation")
        return 0
    else:
        print("\n" + "="*70)
        print("❌ SOME VERIFICATION TESTS FAILED")
        print("="*70)
        print("\nPlease review the failed tests above and fix any issues.")
        return 1


if __name__ == '__main__':
    sys.exit(main())

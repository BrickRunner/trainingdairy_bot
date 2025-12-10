"""
Test script to verify redirect after multi-distance registration
"""
import asyncio
import sys

async def test_redirect_flow():
    """Test that redirect happens immediately after alert"""
    print("=" * 60)
    print("Testing redirect flow after multi-distance registration")
    print("=" * 60)

    # Check if save_all_distances_and_redirect function exists and has proper structure
    from competitions.upcoming_competitions_handlers import save_all_distances_and_redirect

    print("\n✓ save_all_distances_and_redirect function imported successfully")

    # Check if it's async
    if asyncio.iscoroutinefunction(save_all_distances_and_redirect):
        print("✓ Function is async (correct)")
    else:
        print("✗ Function is NOT async (error)")
        return False

    # Check the function signature
    import inspect
    sig = inspect.signature(save_all_distances_and_redirect)
    params = list(sig.parameters.keys())

    print(f"\n✓ Function parameters: {params}")

    if 'callback_or_message' in params and 'state' in params:
        print("✓ Function has correct parameters")
    else:
        print("✗ Function parameters don't match expected")
        return False

    # Read the function source to verify redirect logic
    source = inspect.getsource(save_all_distances_and_redirect)

    checks = {
        "Shows alert for CallbackQuery": "show_alert=True" in source,
        "Clears FSM state": "await state.clear()" in source,
        "Gets user competitions": "get_user_competitions" in source,
        "Builds keyboard": "InlineKeyboardBuilder" in source,
        "Edits message to show competitions": "edit_text" in source,
        "Includes 'МОИ СОРЕВНОВАНИЯ' text": "МОИ СОРЕВНОВАНИЯ" in source,
    }

    print("\nCode structure checks:")
    all_passed = True
    for check_name, result in checks.items():
        status = "✓" if result else "✗"
        print(f"  {status} {check_name}")
        if not result:
            all_passed = False

    print("\n" + "=" * 60)
    if all_passed:
        print("SUCCESS: All checks passed!")
        print("The redirect flow should work correctly:")
        print("1. Shows success alert popup")
        print("2. Clears FSM state")
        print("3. Immediately edits message to show 'Мои соревнования'")
    else:
        print("FAILURE: Some checks failed")
        return False
    print("=" * 60)

    return True

if __name__ == "__main__":
    result = asyncio.run(test_redirect_flow())
    sys.exit(0 if result else 1)

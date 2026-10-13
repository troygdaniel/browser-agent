#!/usr/bin/env python3
"""
Demo script showing browser automation working without AI decision-making.

This demonstrates that all the core infrastructure works:
- Browser management
- Session handling
- Action execution
- Page state extraction
"""

import asyncio
from pathlib import Path
from browser_agent.browser.manager import BrowserManager
from browser_agent.agent.actions import Action


async def demo():
    """Run a simple automation demo."""
    print("=" * 60)
    print("Browser Agent - Manual Demo")
    print("=" * 60)

    # Initialize browser
    print("\n1. Starting browser...")
    browser_manager = BrowserManager(headless=False)
    await browser_manager.start()
    print("   ✓ Browser started")

    # Create session
    print("\n2. Creating browser session...")
    session = await browser_manager.create_session(session_id="demo-session")
    print(f"   ✓ Session created: {session.session_id}")

    # Execute predefined actions
    print("\n3. Executing automation sequence...\n")

    # Action 1: Navigate to example.com
    print("   Step 1: Navigate to example.com")
    await session.navigate("https://example.com")
    print("   ✓ Navigation complete")
    await asyncio.sleep(1)

    # Action 2: Get page state
    print("\n   Step 2: Extract page state")
    page_state = await session.get_page_state()
    print(f"   ✓ Page title: {page_state['title']}")
    print(f"   ✓ Page URL: {page_state['url']}")
    print(f"   ✓ Text content (first 100 chars): {page_state['text_content'][:100]}...")
    print(f"   ✓ Interactive elements found: {len(page_state['interactive_elements'])}")

    # Action 3: Take screenshot
    print("\n   Step 3: Take screenshot")
    screenshot_dir = Path("screenshots/demo")
    screenshot_dir.mkdir(parents=True, exist_ok=True)
    screenshot_path = screenshot_dir / "example.png"
    await session.screenshot(screenshot_path)
    print(f"   ✓ Screenshot saved: {screenshot_path}")

    # Action 4: Navigate to another page (Python.org)
    print("\n   Step 4: Navigate to Python.org")
    await session.navigate("https://www.python.org")
    print("   ✓ Navigation complete")
    await asyncio.sleep(1)

    # Action 5: Get new page state
    print("\n   Step 5: Extract new page state")
    page_state = await session.get_page_state()
    print(f"   ✓ Page title: {page_state['title']}")
    print(f"   ✓ Interactive elements: {len(page_state['interactive_elements'])}")

    # List some interactive elements
    if page_state['interactive_elements']:
        print("\n   Sample interactive elements:")
        for elem in page_state['interactive_elements'][:5]:
            elem_type = elem.get('type', 'unknown')
            if elem_type == 'link':
                print(f"     - Link: {elem.get('text', '')[:40]}")
            elif elem_type == 'button':
                print(f"     - Button: {elem.get('text', '')[:40]}")
            elif elem_type == 'input':
                print(f"     - Input: {elem.get('placeholder', '')[:40]}")

    # Save trace
    print("\n4. Saving trace...")
    trace_dir = Path("traces/demo")
    trace_dir.mkdir(parents=True, exist_ok=True)
    trace_path = trace_dir / "demo.zip"
    await browser_manager.close_session("demo-session", save_trace=True)
    print(f"   ✓ Trace saved: {trace_path}")

    # Cleanup
    print("\n5. Cleaning up...")
    await browser_manager.close_all()
    print("   ✓ Browser closed")

    print("\n" + "=" * 60)
    print("Demo Complete!")
    print("=" * 60)
    print("\nWhat this demonstrates:")
    print("  ✓ Browser automation works")
    print("  ✓ Page navigation works")
    print("  ✓ Page state extraction works")
    print("  ✓ Screenshot capture works")
    print("  ✓ Playwright traces work")
    print("\nNext steps:")
    print("  - For better AI performance, use a larger model:")
    print("    ollama pull qwen2.5:14b")
    print("  - Or use specialized browser automation models")
    print("  - Or implement domain-specific prompts for your use case")


if __name__ == "__main__":
    asyncio.run(demo())

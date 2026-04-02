"""Test script to interact with Bitrix24 API for real requests."""

import asyncio
from datetime import datetime
import sys
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent / "src"
sys.path.insert(0, str(src_path))

from bitrix_mcp.config import get_config  # noqa: E402
from bitrix_mcp.client import get_bitrix_client  # noqa: E402


async def main():
    """Main test function."""
    print("=" * 60)
    print("Bitrix24 Real API Test")
    print("=" * 60)

    # Load config
    bitrix_config, mcp_config = get_config()
    print("\n✓ Config loaded")
    print(f"  Webhook: {bitrix_config.webhook_url[:50]}...")

    # Connect to Bitrix24
    async with get_bitrix_client(bitrix_config) as client:
        print("✓ Connected to Bitrix24\n")

        # Step 1: Get project named "test"
        print("Step 1: Looking for project 'test'...")
        projects = await client.get_projects(filter_params={"?NAME": "test"})

        if projects:
            project = projects[0]
            project_id = project.get("ID")
            print(f"✓ Found project: {project.get('NAME')} (ID: {project_id})")
            print(f"  Description: {project.get('DESCRIPTION', 'N/A')}")
            print(f"  Active: {project.get('ACTIVE', 'N/A')}\n")
        else:
            print("✗ Project 'test' not found")
            print("  Available projects:")
            all_projects = await client.get_projects()
            for p in all_projects[:5]:
                print(f"    - {p.get('NAME')} (ID: {p.get('ID')})")
            return

        # Step 2: Create a task in the project
        print("Step 2: Creating test task...")
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        task_fields = {
            "TITLE": f"Test Task (API) - {timestamp}",
            "DESCRIPTION": "This is a test task created via Bitrix24 MCP API",
            "RESPONSIBLE_ID": 1,
            "PRIORITY": "2",
            "GROUP_ID": project_id,
            "ALLOW_CHANGE_DEADLINE": "Y",
        }

        print(f"  Creating task: {task_fields['TITLE']}")
        result = await client.create_task(task_fields)

        if result and isinstance(result, dict):
            task_id = result.get("id")
            print("✓ Task created successfully!")
            print(f"  Task ID: {task_id}")
            print(f"  Title: {task_fields['TITLE']}")
            print(f"  Project ID: {project_id}")
            print("  Status: Created\n")

            # Step 3: Verify the task
            print("Step 3: Verifying created task...")
            task = await client.get_task(task_id)
            if task:
                print("✓ Task verified successfully!")
                print(f"  ID: {task.get('id')}")
                print(f"  Title: {task.get('title')}")
                print(f"  Status: {task.get('status')}")
                print(f"  Description: {task.get('description', 'N/A')}\n")

                # Step 4: Test task operations
                print("Step 4: Testing task operations...")

                # Test update_task
                print("  Testing update_task...")
                try:
                    update_result = await client.update_task(
                        task_id, {"TITLE": "Updated Test Task"}
                    )
                    print(
                        f"    Result: {update_result} ✓"
                        if update_result
                        else f"    Result: {update_result} ✗"
                    )
                except Exception as e:
                    print(f"    Error: {e}")

                print("\n✓ All task operations tested!")
            else:
                print(f"✗ Could not verify task {task_id}")
        else:
            print("✗ Failed to create task")
            print(f"  Response: {result}")

        # Step 5: Get and display CRM data (leads or contacts)
        print("\nStep 5: Attempting to get CRM data (leads/contacts)...")

        try:
            # Try with specific select fields
            select_fields = ["ID", "NAME", "TITLE", "EMAIL", "PHONE", "STATUS_ID"]
            leads = await client.get_leads(select_fields=select_fields)
            if leads:
                print(f"✓ Found {len(leads)} leads (showing first 3):")
                for i, lead in enumerate(leads[:3], 1):
                    print(f"\n  Lead #{i}:")
                    print(f"    ID: {lead.get('ID')}")
                    print(f"    Name: {lead.get('NAME', 'N/A')}")
                    print(f"    Title: {lead.get('TITLE', 'N/A')}")
                    email = lead.get("EMAIL", [])
                    email_val = email[0].get("VALUE", "N/A") if email else "N/A"
                    print(f"    Email: {email_val}")
                    phone = lead.get("PHONE", [])
                    phone_val = phone[0].get("VALUE", "N/A") if phone else "N/A"
                    print(f"    Phone: {phone_val}")
                    print(f"    Status: {lead.get('STATUS_ID', 'N/A')}")

                    # Debug: Show raw structure of first lead
                    if i == 1:
                        print("\n    ℹ Raw data structure (first lead):")
                        print(
                            f"      Available fields: {', '.join(list(lead.keys())[:10])}..."
                        )
                        if lead.get("EMAIL"):
                            print(f"      EMAIL structure: {lead.get('EMAIL')}")
                        if lead.get("PHONE"):
                            print(f"      PHONE structure: {lead.get('PHONE')}")

                if len(leads) > 3:
                    print(f"\n  ... and {len(leads) - 3} more leads")
            else:
                print("✓ No leads found in system")
        except Exception as e:
            error_msg = str(e)
            if "401" in error_msg or "403" in error_msg:
                print("⚠ CRM data not accessible (permission issue):")
                print("  The webhook token doesn't have access to CRM.lead.list")
                print("  This is a Bitrix24 configuration issue, not a code issue.")
                print("\n  ℹ To fix:")
                print("    1. Go to Bitrix24 Settings > Integration > Webhooks")
                print("    2. Edit your webhook and enable CRM permissions")
                print(
                    "    3. Specifically check: crm.lead.list, crm.contact.list, etc."
                )
            else:
                print(f"✗ Error when accessing CRM data: {error_msg}")

        print("\n" + "=" * 60)
        print("Test completed!")
        print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())

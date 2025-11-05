"""Test graph data flow"""
import asyncio
import sys
import os

# Set UTF-8 encoding for Windows console
if os.name == 'nt':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')

sys.path.insert(0, '.')

from health.health_queries import get_current_month_metrics
from health.health_graphs import generate_health_graphs

async def main():
    user_id = 8296492604

    print("=" * 60)
    print("TESTING GRAPH DATA FLOW")
    print("=" * 60)

    # Step 1: Get metrics from DB
    print("\nStep 1: Getting metrics from database...")
    metrics = await get_current_month_metrics(user_id)
    print(f"Found {len(metrics)} records:")

    for m in metrics:
        print(f"  {m['date']}: pulse={m.get('morning_pulse')}, weight={m.get('weight')}, sleep={m.get('sleep_duration')}")

    # Step 2: Check what data will be used for graphs
    print("\nStep 2: Analyzing data for graphs...")
    print("Dates that should appear on graph:")
    from datetime import datetime
    for metric in metrics:
        metric_date = datetime.strptime(metric['date'], '%Y-%m-%d').date()
        print(f"  {metric_date} -> pulse={metric.get('morning_pulse')}, weight={metric.get('weight')}, sleep={metric.get('sleep_duration')}")

    # Step 3: Generate graph
    print("\nStep 3: Generating graph...")
    days_for_graph = len(metrics) if len(metrics) > 0 else 7
    print(f"Using days_for_graph parameter: {days_for_graph}")

    try:
        graph_buffer = await generate_health_graphs(metrics, days_for_graph)
        print(f"Graph generated successfully! Buffer size: {len(graph_buffer.getvalue())} bytes")

        # Save to file for inspection
        with open('test_health_graph.png', 'wb') as f:
            f.write(graph_buffer.getvalue())
        print("Graph saved to: test_health_graph.png")

    except Exception as e:
        print(f"ERROR generating graph: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())

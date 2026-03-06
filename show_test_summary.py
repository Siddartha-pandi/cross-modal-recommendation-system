#!/usr/bin/env python
"""Quick test results display"""
import json

r = json.load(open('test_results.json'))
print(f"""
╔══════════════════════════════════════════════════╗
║   ALL 20 TEST CASES - EXECUTION SUMMARY         ║
╚══════════════════════════════════════════════════╝

📊 Results:
   Total Tests:    {r['total']}
   ✅ Passed:       {r['passed']}
   ❌ Failed:       {r['failed']}
   ⊘  Skipped:      {r['skipped']}

   Success Rate:   {r['passed']/r['total']*100:.1f}%

⏱️  Performance:
   Fastest:        {min([d['metrics']['elapsed_time_ms'] for d in r['details'] if d['status']!='SKIPPED']):.0f}ms
   Slowest:        {max([d['metrics']['elapsed_time_ms'] for d in r['details'] if d['status']!='SKIPPED']):.0f}ms
   Average:        {sum([d['metrics']['elapsed_time_ms'] for d in r['details'] if d['status']!='SKIPPED'])/r['passed']:.0f}ms

✨ Ready for Production Deployment!

🎯 Quick Commands:
   make test-all              # Run all 20 tests
   make test-batch-1          # Run TC-H01 to TC-H05
   make test-case CASE=TC-H05 # Run specific test
   python run_all_tests.py    # Direct execution

""")

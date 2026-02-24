# Quick Database Check Script
from config import issues_collection

print("=" * 50)
print("URBANEYE DATABASE DIAGNOSTIC")
print("=" * 50)

# Count total issues
total = issues_collection.count_documents({})
print(f"\n✅ Total Issues in Database: {total}")

if total == 0:
    print("\n❌ NO ISSUES FOUND!")
    print("   This is why dashboard/issue management are empty.")
    print("\n💡 SOLUTION:")
    print("   1. Go to Citizen App: http://localhost:3000")
    print("   2. Submit a test issue with photo")
    print("   3. Refresh admin dashboard")
else:
    print(f"\n✅ Database has {total} issues")
    
    # Show sample
    print("\n📊 SAMPLE DATA:")
    print("-" * 50)
    issues = list(issues_collection.find().limit(2))
    for idx, issue in enumerate(issues, 1):
        print(f"\nIssue #{idx}:")
        print(f"  Type: {issue.get('issue_type', 'N/A')}")
        print(f"  Status: {issue.get('status', 'N/A')}")
        print(f"  Description: {issue.get('description', 'N/A')[:50]}...")
    
    # Show stats
    print("\n📈 STATISTICS:")
    print("-" * 50)
    pending = issues_collection.count_documents({"status": "Pending"})
    resolved = issues_collection.count_documents({"status": "Resolved"})
    assigned = issues_collection.count_documents({"status": "Assigned"})
    
    print(f"  Pending: {pending}")
    print(f"  Assigned: {assigned}")
    print(f"  Resolved: {resolved}")

print("\n" + "=" * 50)

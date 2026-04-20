"""
RBAC Migration Script
=====================

This script migrates existing user roles from 'GUARD' to 'SECURITY_GUARD'
to match the new RBAC model.

Run this script ONCE after deploying the RBAC refactoring.

Usage:
    python manage.py shell < RBAC_MIGRATION_SCRIPT.py
    
Or run interactively:
    python manage.py shell
    >>> exec(open('RBAC_MIGRATION_SCRIPT.py').read())
"""

from django.contrib.auth import get_user_model

User = get_user_model()

def migrate_roles():
    """Migrate GUARD role to SECURITY_GUARD"""
    
    print("=" * 60)
    print("RBAC Role Migration Script")
    print("=" * 60)
    
    # Count existing GUARD users
    guard_count = User.objects.filter(role='GUARD').count()
    
    if guard_count == 0:
        print("\n✅ No users with 'GUARD' role found.")
        print("   Migration not needed or already completed.")
        return
    
    print(f"\n📊 Found {guard_count} user(s) with 'GUARD' role")
    print("\n🔄 Migrating roles...")
    
    # Update GUARD to SECURITY_GUARD
    updated_count = User.objects.filter(role='GUARD').update(role='SECURITY_GUARD')
    
    print(f"\n✅ Successfully migrated {updated_count} user(s)")
    print("   GUARD → SECURITY_GUARD")
    
    # Verify migration
    remaining_guards = User.objects.filter(role='GUARD').count()
    security_guards = User.objects.filter(role='SECURITY_GUARD').count()
    
    print("\n📊 Current role distribution:")
    print(f"   - ADMIN: {User.objects.filter(role='ADMIN').count()}")
    print(f"   - SECURITY_INCHARGE: {User.objects.filter(role='SECURITY_INCHARGE').count()}")
    print(f"   - SECURITY_GUARD: {security_guards}")
    print(f"   - GUARD (old): {remaining_guards}")
    
    if remaining_guards == 0:
        print("\n✅ Migration completed successfully!")
    else:
        print(f"\n⚠️  Warning: {remaining_guards} user(s) still have 'GUARD' role")
        print("   Please investigate and re-run migration if needed.")
    
    print("=" * 60)

# Run migration
if __name__ == '__main__':
    migrate_roles()
else:
    # When imported or run via exec()
    migrate_roles()


from collections import Counter

from django.apps import apps
from rest_framework import serializers

from .validation import normalize_cnic

CNIC_DUPLICATE_MESSAGE = "This CNIC is already registered in the system."


def normalize_cnic_value(value: str) -> str:
    return normalize_cnic(value)


def ensure_unique_in_payload(cnics) -> None:
    normalized = [normalize_cnic_value(cnic) for cnic in cnics]
    counts = Counter(normalized)
    if any(count > 1 for count in counts.values()):
        raise serializers.ValidationError(CNIC_DUPLICATE_MESSAGE)


def _id_set(values):
    return {str(value) for value in values or [] if value is not None}


def find_cnic_conflicts(cnic, *, exclude=None):
    """
    Return CNIC-bearing records that already use this CNIC.

    Exclude keys:
      users, branches, super_admin_profiles: iterable primary keys
      branch_admin_user_branch_ids: branch IDs whose ADMIN user mirrors Branch.admin_cnic
    """
    normalized = normalize_cnic_value(cnic)
    exclude = exclude or {}
    exclude_users = _id_set(exclude.get("users"))
    exclude_branches = _id_set(exclude.get("branches"))
    exclude_profiles = _id_set(exclude.get("super_admin_profiles"))
    exclude_branch_admin_user_branch_ids = _id_set(
        exclude.get("branch_admin_user_branch_ids")
    )

    conflicts = []

    User = apps.get_model("accounts", "User")
    for user in User.objects.filter(cnic=normalized):
        user_id = str(user.pk)
        branch_id = str(user.branch_id) if getattr(user, "branch_id", None) else None
        if user_id in exclude_users:
            continue
        if (
            getattr(user, "role", None) == "ADMIN"
            and branch_id in exclude_branch_admin_user_branch_ids
        ):
            continue
        conflicts.append(("user", user_id))

    Branch = apps.get_model("tenancy", "Branch")
    for branch in Branch.objects.filter(admin_cnic=normalized):
        branch_id = str(branch.pk)
        if branch_id in exclude_branches:
            continue
        conflicts.append(("branch", branch_id))

    SuperAdminProfile = apps.get_model("tenancy", "SuperAdminProfile")
    for profile in SuperAdminProfile.objects.all():
        profile_id = str(profile.pk)
        if profile_id in exclude_profiles:
            continue
        for partner in profile.partners or []:
            try:
                partner_cnic = normalize_cnic_value(partner.get("cnic"))
            except serializers.ValidationError:
                continue
            if partner_cnic == normalized:
                conflicts.append(("super_admin_profile", profile_id))
                break

    return conflicts


def validate_cnic_available(cnic, *, exclude=None) -> str:
    normalized = normalize_cnic_value(cnic)
    if find_cnic_conflicts(normalized, exclude=exclude):
        raise serializers.ValidationError(CNIC_DUPLICATE_MESSAGE)
    return normalized

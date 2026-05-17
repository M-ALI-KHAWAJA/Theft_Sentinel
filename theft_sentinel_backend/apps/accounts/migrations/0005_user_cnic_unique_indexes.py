import re
from collections import defaultdict

from django.db import migrations, models


CNIC_RE = re.compile(r"[\s-]")


def _normalize_cnic(value):
    if value is None:
        return None
    digits = CNIC_RE.sub("", str(value).strip())
    if not digits:
        return None
    if len(digits) == 13 and digits.isdigit():
        return f"{digits[:5]}-{digits[5:12]}-{digits[12]}"
    return str(value).strip()


def _normalize_existing_cnics(apps, schema_editor):
    db = schema_editor.connection.database
    collections = set(db.list_collection_names())

    if "accounts_user" in collections:
        for doc in db["accounts_user"].find({"cnic": {"$exists": True}}):
            normalized = _normalize_cnic(doc.get("cnic"))
            if normalized != doc.get("cnic"):
                db["accounts_user"].update_one(
                    {"_id": doc["_id"]},
                    {"$set": {"cnic": normalized}},
                )

    if "branches" in collections:
        for doc in db["branches"].find({"admin_cnic": {"$exists": True}}):
            normalized = _normalize_cnic(doc.get("admin_cnic"))
            if normalized != doc.get("admin_cnic"):
                db["branches"].update_one(
                    {"_id": doc["_id"]},
                    {"$set": {"admin_cnic": normalized}},
                )

    if "super_admin_profile" in collections:
        for doc in db["super_admin_profile"].find({"partners": {"$exists": True}}):
            changed = False
            partners = []
            for partner in doc.get("partners") or []:
                item = dict(partner)
                normalized = _normalize_cnic(item.get("cnic"))
                if normalized != item.get("cnic"):
                    item["cnic"] = normalized
                    changed = True
                partners.append(item)
            if changed:
                db["super_admin_profile"].update_one(
                    {"_id": doc["_id"]},
                    {"$set": {"partners": partners}},
                )


def _duplicate_values(collection, field):
    values = defaultdict(list)
    for doc in collection.find({field: {"$type": "string"}}, {field: 1}):
        value = _normalize_cnic(doc.get(field))
        if value:
            values[value].append(doc["_id"])
    return {value: ids for value, ids in values.items() if len(ids) > 1}


def _partner_duplicates(collection):
    values = defaultdict(list)
    for doc in collection.find({"partners.cnic": {"$exists": True}}, {"partners": 1}):
        seen_in_doc = set()
        for partner in doc.get("partners") or []:
            value = _normalize_cnic(partner.get("cnic"))
            if not value:
                continue
            values[value].append(doc["_id"])
            if value in seen_in_doc:
                values[value].append(doc["_id"])
            seen_in_doc.add(value)
    return {value: ids for value, ids in values.items() if len(ids) > 1}


def _drop_non_unique_indexes_for_key(collection, key):
    for name, info in list(collection.index_information().items()):
        if name == "_id_":
            continue
        if info.get("key") == key and not info.get("unique"):
            collection.drop_index(name)


def _create_unique_indexes_when_safe(apps, schema_editor):
    db = schema_editor.connection.database
    collections = set(db.list_collection_names())

    if "accounts_user" in collections:
        users = db["accounts_user"]
        if not _duplicate_values(users, "cnic"):
            _drop_non_unique_indexes_for_key(users, [("cnic", 1)])
            users.create_index(
                [("cnic", 1)],
                name="accounts_user_cnic_unique_idx",
                unique=True,
                partialFilterExpression={"cnic": {"$type": "string"}},
            )
        else:
            users.create_index([("cnic", 1)], name="accounts_user_cnic_idx")
            print("WARNING: duplicate user CNIC values detected; unique user CNIC index skipped.")

    if "branches" in collections:
        branches = db["branches"]
        if not _duplicate_values(branches, "admin_cnic"):
            _drop_non_unique_indexes_for_key(branches, [("admin_cnic", 1)])
            branches.create_index(
                [("admin_cnic", 1)],
                name="branches_admin_cnic_unique_idx",
                unique=True,
                partialFilterExpression={"admin_cnic": {"$type": "string"}},
            )
        else:
            print("WARNING: duplicate branch admin CNIC values detected; unique branch CNIC index skipped.")

    if "super_admin_profile" in collections:
        profiles = db["super_admin_profile"]
        if not _partner_duplicates(profiles):
            _drop_non_unique_indexes_for_key(profiles, [("partners.cnic", 1)])
            profiles.create_index(
                [("partners.cnic", 1)],
                name="super_admin_profile_partners_cnic_unique_idx",
                unique=True,
                partialFilterExpression={"partners.cnic": {"$type": "string"}},
            )
        else:
            profiles.create_index(
                [("partners.cnic", 1)],
                name="super_admin_profile_partners_cnic_idx",
            )
            print("WARNING: duplicate partner CNIC values detected; unique partner CNIC index skipped.")


class Migration(migrations.Migration):
    dependencies = [
        ("accounts", "0004_user_branch_and_super_admin"),
        ("tenancy", "0003_rename_branches_tenant_branch_name_idx_branches_tenant__c5ffaa_idx_and_more"),
    ]

    operations = [
        migrations.AddField(
            model_name="user",
            name="cnic",
            field=models.CharField(blank=True, db_index=True, max_length=30, null=True),
        ),
        migrations.RunPython(_normalize_existing_cnics, migrations.RunPython.noop),
        migrations.RunPython(_create_unique_indexes_when_safe, migrations.RunPython.noop),
    ]

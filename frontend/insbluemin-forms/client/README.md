# INSBLUE:Forms

The basic idea revolves around using `fieldMatchAccess`, which atm can only be configured at form creation via the API. Each form will have a hidden field in
which we configure the required roles/permissions, which will be used when calling /form/<path>/submission, showing only those submissions which have the proper
role <> value pair.

```
"fieldMatchAccess": {
        "read": [
            {
                "formFieldPath": "data.privacy",
                "value": "public",
                "roles": [
                    "6738b7793354a41d59b518e9"
                ]
            },
            {
                "formFieldPath": "data.privacy",
                "value": "private",
                "roles": [
                    "6738b7783354a41d59b518e5"
                ]
            }
        ]
    },
```

This means that when the user uses the form on the flask side, insbluemin should inject the user permission in the field... i think?

6815de67e2488968fe77d242 - find what role this is

ok, so there are 2 distinct issues:

1. we need to filter the forms from being shown in the first place if the user doesn't have the proper role

    - then we need to make sure that the actual formio api route redirects if not an admin

2. we need to display submissions based on roles/permissions. normal user can access his own submissions for each form. department manager user can access all
   department submissions

3. the user needs to be able to access their own submission history, this works directly if using formio users resource.

for 1 i've identified several methods involving either the owner field, or a custom form field
for 2 i think fieldBased access can work and using the embedded formio roles/groups. in this way we don't need to create accounts for every user, only those
with elevated permissions.

## BUGS/TODO

- has_permissions works only for the sidebar items, it should actually redirect the whole page
- submission IDs (when viewing them in insbluemin) should be re-hashed as another security layer

Core Action Verbs (CRUD-Based)

| Verb     | Typical Meaning                      |
|----------|--------------------------------------|
| `create` | Add a new record or resource         |
| `read`   | View a single submission / data      |
| `view`   | View for UI/visual pages             |
| `update` | Modify an existing record            |
| `edit`   | Modify via a UI (may imply `update`) |
| `delete` | Remove a record                      |

Extended / Granular Verbs

| Verb        | Typical Meaning                                    |
|-------------|----------------------------------------------------|
| `submit`    | Send a completed form (common in form systems)     |
| `approve`   | Accept or validate a submission (review workflow)  |
| `reject`    | Decline a submission (often paired with `approve`) |
| `assign`    | Allocate a resource or responsibility to a user    |
| `archive`   | Mark as inactive without deletion                  |
| `restore`   | Reactivate an archived or soft-deleted record      |
| `publish`   | Make content publicly visible                      |
| `unpublish` | Revoke public visibility                           |
| `download`  | Export a file or dataset                           |
| `upload`    | Add files or documents                             |
| `list`      | Enumerate records without accessing details        |
| `configure` | Modify system-level or module-level settings       |
| `manage`    | Broad admin-level control over a module/resource   |

## Forms permissions documentation

| Verb         | Typical Meaning                      |
|--------------|--------------------------------------|
| `can_create` | Can create own submission            |
| `can_read`   | Can view form or read own submission |
| `can_update` | Can modify own submission            |
| `can_delete` | Can delete own submission            |

| Verb             | Typical Meaning                   |
|------------------|-----------------------------------|
| `can_read_all`   | Can view all forms or submissions |
| `can_update_all` | Can modify all submissions        |
| `can_delete_all` | Can delete all submissions        |

#### Department specific

| Verb             | Typical Meaning                      |
|------------------|--------------------------------------|
| `can_create:dep` | Can create own submission            |
| `can_read:dep`   | Can view form or read own submission |
| `can_update:dep` | Can modify own submission            |
| `can_delete:dep` | Can delete own submission            |

| Verb                 | Typical Meaning                   |
|----------------------|-----------------------------------|
| `can_read_all:dep`   | Can view all forms or submissions |
| `can_update_all:dep` | Can modify all submissions        |
| `can_delete_all:dep` | Can delete all submissions        |

# TODO:

Requires changing the user login shit. we now use a api@incdsb.ro account with a custom role to login, then we do the validation in flask if the header email
fits with the submissions one.

We need permissions at department level somehow.
We need to make fix something about permissions, maybe refresh session if user has been recently updated, something.

@has_permissions requiers all permissions to be present.

new _get_token causes login loop
# Deployment Guide — Plant Delivery & Office Inventory Management

## Overview

This guide explains how to promote the **PlantInventoryManagement** Power Platform solution through the three environments:

```
Dev  ──(export managed solution)──►  Test  ──(import & validate)──►  Prod
```

All deployment artefacts are managed as a single **managed Solution** in Power Platform, ensuring all components (Tables, Security Roles, Canvas App, Power Automate Flows) are versioned and promoted together.

---

## Environment Strategy

| Environment | Purpose | Who has access |
|---|---|---|
| **Dev** | Active development and testing by the build team | Developers, Admins |
| **Test** | UAT and stakeholder review | Testers, Business stakeholders |
| **Prod** | Live production environment | All end users |

Each environment has its own Dataverse instance and environment URL. Environment-specific values (URLs, emails, webhook URLs) are managed via **Environment Variables** inside the solution, so the same managed solution package can be imported into any environment without manual edits.

---

## Prerequisites

| Tool | Install command | Notes |
|---|---|---|
| Power Platform CLI (`pac`) | `winget install Microsoft.PowerAppsCLI` or [download](https://aka.ms/PowerAppsCLI) | v1.30+ recommended |
| .NET SDK | Required by `pac` on Windows | |
| Azure CLI | `winget install Microsoft.AzureCLI` | For authenticating service principal |
| Git | `winget install Git.Git` | For source control |

### Solution Naming Convention

| Environment | Solution Name |
|---|---|
| Dev | `PlantInventoryManagement` (unmanaged — editable) |
| Test / Prod | `PlantInventoryManagement` (managed — locked) |

---

## Step-by-Step: Manual Export / Import

### Step 1 — Authenticate to the Dev environment

```bash
# Authenticate interactively (browser pop-up)
pac auth create --url <YOUR_DEV_ENVIRONMENT_URL>

# OR authenticate using a service principal (CI/CD recommended)
pac auth create \
  --url <YOUR_DEV_ENVIRONMENT_URL> \
  --tenant <YOUR_TENANT_ID> \
  --applicationId <YOUR_SERVICE_PRINCIPAL_CLIENT_ID> \
  --clientSecret <YOUR_SERVICE_PRINCIPAL_CLIENT_SECRET>
```

### Step 2 — Export the solution from Dev as managed

```bash
pac solution export \
  --name PlantInventoryManagement \
  --path ./solution-export/PlantInventoryManagement_managed.zip \
  --managed true \
  --overwrite
```

> **Tip**: Increment the solution version number in Dev before each export:  
> Power Apps → Solutions → `PlantInventoryManagement` → Edit → Version

### Step 3 — Authenticate to the target environment (Test or Prod)

```bash
pac auth create --url <YOUR_TEST_OR_PROD_ENVIRONMENT_URL>
```

### Step 4 — Import the managed solution into the target environment

```bash
pac solution import \
  --path ./solution-export/PlantInventoryManagement_managed.zip \
  --activate-plugins true \
  --force-overwrite
```

### Step 5 — Set environment-specific variables

After import, update the **Environment Variable** values for the target environment:

```bash
# List current environment variable values
pac env list-variables --solution PlantInventoryManagement

# Update an environment variable value
pac env update-variable \
  --solution PlantInventoryManagement \
  --name lic_DataverseEnvironmentUrl \
  --value <YOUR_TARGET_ENVIRONMENT_URL>
```

Alternatively, update them in the Power Platform Admin Center:  
**Admin Center → Environments → [Target Env] → Solutions → PlantInventoryManagement → Environment Variables**

### Step 6 — Publish customisations

```bash
pac solution publish
```

---

## Environment Variables Reference

See `/deployment/solution-settings.json` for the full list. Key variables:

| Variable Name | Description | Example |
|---|---|---|
| `lic_DataverseEnvironmentUrl` | Dataverse environment URL | `https://yourorg.crm6.dynamics.com` |
| `lic_NotificationEmail` | Email address for alerts | `warehouse@yourorg.com` |
| `lic_TeamsChannelWebhookUrl` | Incoming webhook URL for Teams | `https://yourorg.webhook.office.com/...` |

---

## GitHub Actions Automated Deployment

For CI/CD deployment via GitHub Actions, see `/deployment/deploy.yml`.

Required repository secrets:

| Secret Name | Description |
|---|---|
| `PP_CLIENT_ID` | Service principal Application (client) ID |
| `PP_CLIENT_SECRET` | Service principal client secret |
| `PP_TENANT_ID` | Azure AD tenant ID |
| `PP_DEV_ENVIRONMENT_URL` | Dev environment URL |
| `PP_TEST_ENVIRONMENT_URL` | Test environment URL |
| `PP_PROD_ENVIRONMENT_URL` | Prod environment URL |

Set these in: **GitHub → Repository → Settings → Secrets and variables → Actions**

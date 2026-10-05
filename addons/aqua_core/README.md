# Aquaculture Core — End User Guide

## Overview

**Aquaculture Core** is an Odoo app for managing aquaculture operations and biological traceability. It helps teams track fish, shrimp, or other aquatic species from breeder stock through hatchery, nursery, grow-out, and harvest stages.

The app is designed around one main idea: every biological batch should be traceable through its lifecycle, including where it came from, where it moved, what stage it is in, what inputs were used, and what events happened to it.

## Main features

- Manage aquaculture companies, farms, and production units such as ponds, tanks, cages, hatchery tanks, nursery areas, and processing areas.
- Maintain species and lifecycle stages.
- Create and track biological batches.
- Generate and maintain Global Biological IDs for end-to-end traceability.
- Record parent-child batch relationships when batches are split, separated, merged, transferred, or created in parallel.
- Log batch events such as mortality, treatment, health checks, harvest, feeding, water quality checks, and notes.
- Record water quality readings.
- Record input consumption such as feed, medicine, chemicals, probiotics, fertilizers, and other inputs.
- View current production-unit status, current quantity, and estimated biomass.

## Who should use this app

This app is useful for:

- Aquaculture farm operators
- Hatchery, nursery, and grow-out managers
- Quality and traceability teams
- Production planners
- Operations supervisors
- Administrators who maintain farm, pond, tank, and species master data

## Key terms

### Aquaculture Company

A company or operating unit involved in the aquaculture chain. The app supports company types such as breeder, hatchery, nursery, grow-out, harvest and sales, central company, and other.

### Farm / Site

A physical farm, hatchery, nursery, grow-out site, or processing location owned by a company.

### Production Unit

A specific place where a batch is held or processed. Examples include ponds, tanks, cages, hapa units, broodstock tanks, spawning tanks, larvae tanks, nursery areas, processing areas, and warehouse areas.

### Species

The aquatic species being managed, such as tilapia, shrimp, crab, mollusk, or another species.

### Lifecycle Stage

The biological or operational stage of the batch. The app includes these default stages:

1. Breeder
2. Broodstock
3. Spawning
4. Egg
5. Larvae
6. Nursery 1
7. Nursery 2
8. Nursery 3
9. Grow-out
10. Harvest

### Global Biological ID

A traceability ID that links all related batches across the full lifecycle. It is intended to remain with the biological lineage as it moves between companies, farms, production units, and stages.

### Batch

A batch is a group of aquatic animals tracked together. A batch has a local batch number, species, stage, company, farm, production unit, quantity, average weight, biomass, mortality, status, and traceability links.

### Batch Relation

A parent-child link between batches. Relations are created when a batch is transferred, split, separated, merged, harvested, or created in parallel.

### Batch Event

A time-based record of something that happened to a batch. Some events are created automatically by the app, while users can also create manual events.

## Installation

1. Copy the `aqua_core` folder into your Odoo addons directory.
2. Restart the Odoo server.
3. In Odoo, go to **Apps**.
4. Update the Apps List if needed.
5. Search for **Aquaculture Core**.
6. Click **Install**.

The module depends on the standard Odoo apps/modules: **base**, **mail**, and **product**.

### Deployment note

The uploaded ZIP also contains macOS metadata folders such as `__MACOSX` and Python cache folders such as `__pycache__`. These are not needed for Odoo deployment. For a clean deployment, keep the `aqua_core` folder and remove unnecessary cache or metadata folders.

## First-time setup

After installation, open the **Aquaculture** menu.

### 1. Configure aquaculture companies

Go to:

**Aquaculture > Configuration > Aquaculture Companies**

For each company:

- Enable **Aquaculture Company**.
- Select the correct **Aquaculture Company Type**.
- Enter an **Aquaculture Code** if your organization uses company codes.

Company type is important because lifecycle stages can be restricted to specific company types. For example, hatchery stages are intended for hatchery companies, nursery stages for nursery companies, and grow-out stages for grow-out companies.

### 2. Create farms or sites

Go to:

**Aquaculture > Structure > Farms**

Create each farm or site and assign it to the correct company. Each farm needs a name and code. Farm codes must be unique within the same company.

### 3. Create production units

Go to:

**Aquaculture > Structure > Ponds / Tanks / Cages**

Create the ponds, tanks, cages, hatchery tanks, nursery areas, or processing areas used by the farm. Each production unit belongs to one farm.

Useful fields include:

- Name
- Code
- Farm
- Unit Type
- Capacity
- Water Type
- Notes

Production-unit codes must be unique within the same farm.

### 4. Review lifecycle stages

Go to:

**Aquaculture > Structure > Stages**

The module already includes default lifecycle stages. Review them before users start entering batches.

### 5. Create species

Go to:

**Aquaculture > Structure > Species**

Create the species you manage. Each species name must be unique.

### 6. Configure input products

Input consumption can use Odoo products. Create products for feed, medicine, chemicals, probiotics, fertilizers, and other inputs using the standard Odoo product menu.

## Main daily workflow

### Step 1: Create or select a Global Biological ID

A Global Biological ID is the main traceability reference.

When creating a new lifecycle from a **Breeder** batch, the app can automatically create a new Global Biological ID. For later lifecycle stages, users should select an existing Global Biological ID so the biological lineage remains connected.

### Step 2: Create a batch

Go to:

**Aquaculture > Traceability > Batches**

Create a batch and fill in:

- Global Biological ID
- Company
- Farm
- Production Unit
- Species
- Lifecycle Stage
- Quantity
- Average Weight
- Status
- Start Date
- Notes

The app calculates biomass as:

```text
Biomass kg = Quantity × Average Weight g / 1000
```

The app also calculates mortality rate and survival rate based on quantity and mortality quantity.

### Step 3: Use batch action buttons

On a batch form, users can use these action buttons:

- **Create Parallel Batch** — create another batch with the same biological identity and stage.
- **Split Batch** — split one batch into multiple child batches.
- **Separate Batch** — separate animals by size, quality, health, gender, location, or another reason.
- **Merge Batches** — combine multiple batches into one child batch.
- **Transfer Stage** — move a batch to another company, farm, production unit, or lifecycle stage.

Each operation creates traceability records and batch events.

### Step 4: Record water quality

Go to:

**Aquaculture > Operations > Water Quality**

Record measurements such as:

- Temperature
- pH
- Dissolved oxygen
- Salinity
- Ammonia
- Nitrite
- Alkalinity
- Notes

When a water quality record is created, the app also creates a related batch event.

### Step 5: Record input consumption

Go to:

**Aquaculture > Operations > Input Consumption**

Record inputs used by a batch, such as:

- Feed
- Medicine
- Chemical
- Probiotic
- Fertilizer
- Other

When an input consumption record is created, the app also creates a related batch event. Feed becomes a feeding event; medicine, chemical, and probiotic inputs become treatment events.

### Step 6: Review traceability

Open a batch and use the stat buttons to view:

- Global Biological ID
- Parent batches
- Child batches
- Events
- Water quality records
- Input consumption records

You can also go directly to:

**Aquaculture > Traceability > Global Biological IDs**

From a Global Biological ID, users can view related batches, events, and relations.

## Menus

The module adds a main menu called **Aquaculture**.

### Traceability

- Global Biological IDs
- Batches
- Batch Relations
- Batch Events

### Operations

- Water Quality
- Input Consumption

### Structure

- Farms
- Ponds / Tanks / Cages
- Species
- Stages

### Configuration

- Aquaculture Companies

## Record status guide

Batches can use these statuses:

- **Draft** — not yet active.
- **Active** — currently in use.
- **Transferred** — moved to another stage, company, farm, or production unit.
- **Completed** — completed operationally.
- **Harvested** — harvested.
- **Quarantine** — isolated or under observation.
- **Problem** — has an issue.
- **Closed** — no longer active.

## Data validation rules

The app prevents several common data-entry mistakes:

- Batch quantity cannot be negative.
- Average weight cannot be negative.
- Mortality quantity cannot be negative.
- Mortality quantity cannot exceed batch quantity.
- Water-quality pH must be between 0 and 14.
- Water-quality numeric values such as temperature, dissolved oxygen, salinity, ammonia, nitrite, and alkalinity cannot be negative.
- Input consumption quantity cannot be negative.
- A production unit capacity cannot be negative.
- A batch farm must belong to the selected company.
- A batch production unit must belong to the selected farm and company.
- A parent batch and child batch cannot be the same batch.

## Important operating notes

- The app is traceability-focused. Batch operations create child batches, relations, and events.
- Review your internal process for whether parent batch quantities should be adjusted or parent batches should be closed after split, separate, or merge operations. In this version, not every operation automatically reduces or closes the parent batch.
- Use **Archive** instead of deleting traceability records. The app blocks deletion of important records such as batches, global trace IDs, batch relations, events, water quality records, and input consumption records.
- Keep species, farms, production units, and stages clean and consistent before entering live production data.

## Example lifecycle

A typical flow may look like this:

1. Create a breeder batch.
2. The app creates or links a Global Biological ID.
3. Transfer the batch to broodstock or spawning.
4. Split spawning output into egg batches.
5. Transfer eggs into larvae tanks.
6. Separate or split larvae into nursery batches.
7. Transfer nursery batches to grow-out ponds.
8. Record feed, treatments, water quality, mortality, and health checks.
9. Transfer or merge batches for harvest.
10. Review the Global Biological ID to see the complete lineage.

## End-user example: merge two Global Biological IDs

This example shows what happens when two biological lineages must be merged into one batch. This is an exception workflow and should be approved by an Aquaculture Manager.

### Scenario

Two grow-out batches are already active:

| Global Biological ID | Local Batch | Company | Production Unit | Quantity | Status |
| --- | --- | --- | --- | ---: | --- |
| AQ-2026-000101 | GRO-A-101 | Grow-out Company | G-Pond-01 | 50,000 pcs | Active |
| AQ-2026-000102 | GRO-B-102 | Grow-out Company | G-Pond-02 | 48,000 pcs | Active |

The operation team decides to merge both batches into one harvest-ready batch:

| New Global Biological ID | New Local Batch | Company | Production Unit | Quantity | Status |
| --- | --- | --- | --- | ---: | --- |
| AQ-2026-000201 | HARVEST-MIX-01 | Harvest & Sales Company | FG-01 | 9,700 kg | Active |

### Why this needs manager approval

By default, the app does not allow merging batches from different Global Biological IDs. This protects biological traceability.

Only an **Aquaculture Manager** can approve a cross-global merge. When approved, the new Global Biological ID keeps the source IDs in its source history:

```text
AQ-2026-000201
├── Source Global ID: AQ-2026-000101
└── Source Global ID: AQ-2026-000102
```

### Steps for the end user

1. Go to **Aquaculture > Traceability > Batches**.
2. Open or select the two parent batches:
   - `GRO-A-101`
   - `GRO-B-102`
3. Click **Merge Batches**.
4. In the merge wizard, enter:
   - Target Company: `Harvest & Sales Company`
   - Target Farm: `Processing-01`
   - Target Production Unit: `FG-01`
   - Target Stage: `Harvest`
   - Quantity: `9700`
   - Average Weight: `1000`
5. If the batches have different Global Biological IDs, the manager enables **Cross-global Merge Override**.
6. Click **Merge**.

### Result after merge

The app creates one child batch:

```text
HARVEST-MIX-01
Global Biological ID: AQ-2026-000201
Source Global IDs:
- AQ-2026-000101
- AQ-2026-000102
```

The app also creates relation records:

| Parent Batch | Child Batch | Operation Type |
| --- | --- | --- |
| GRO-A-101 | HARVEST-MIX-01 | Merge |
| GRO-B-102 | HARVEST-MIX-01 | Merge |

### What users should verify

Open **AQ-2026-000201** from **Aquaculture > Traceability > Global Biological IDs** and confirm:

- The new merged batch appears under related batches.
- Both source Global Biological IDs are listed.
- Batch relations show both parent batches.
- Batch events include merge events.
- The new batch is in the correct company, farm, production unit, and harvest stage.

Open each parent batch and confirm:

- The downstream child relation points to `HARVEST-MIX-01`.
- The original Global Biological ID is still visible on the parent batch.
- The traceability history is preserved.

## Troubleshooting

### I cannot create a later-stage batch without a Global Biological ID

Select an existing Global Biological ID. The app only creates a new Global Biological ID automatically when starting from a breeder batch.

### The app says the stage does not match the company type

Check the company’s aquaculture type and the lifecycle stage configuration. Some stages are designed for specific company types.

### I cannot delete a record

Important traceability records should be archived instead of deleted. This protects the historical chain of custody.

### The production unit shows the wrong current state

Open the production unit and review its current batches. The current state is calculated from active batches and their statuses.

### Cross-global merge or manager override does not work

This package references an `aqua_core.group_aqua_manager` security group for manager-only overrides. An administrator or developer should confirm that this group is defined in the deployed module before relying on those overrides.

## Administrator notes

- All normal internal users currently receive broad access to the aquaculture models through `base.group_user` in the access file.
- If your organization needs stricter permissions, add dedicated aquaculture user and manager groups, then update the access rules.
- The module contains demo data for sample companies, farms, production units, species, batches, relations, water quality, inputs, and events. Use demo data for testing or training, not as production data.
- Clean deployment should exclude `__MACOSX` and `__pycache__` folders.

## Support checklist before going live

Before using this app in production, confirm:

- Company types are correct.
- Farms are assigned to the correct companies.
- Production units are assigned to the correct farms.
- Species list is complete.
- Lifecycle stages match your operational process.
- Batch numbering format is acceptable.
- User permissions match your organization’s responsibilities.
- Your team agrees on how to handle parent batch quantities after split, separate, merge, and transfer operations.
- Demo data is not installed in production unless intentionally required.

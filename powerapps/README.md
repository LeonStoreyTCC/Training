# Power Apps Canvas App — Plant Delivery & Office Inventory Management

## Overview

This canvas app provides office staff and administrators with a simple interface to submit plant delivery orders, track order status, and monitor warehouse inventory levels.

The app connects directly to Dataverse tables defined in `/dataverse/schema.json`.

---

## Screen List

| Screen Name | Audience | Purpose |
|---|---|---|
| **Home** | All users | Landing page with navigation buttons and role-based visibility |
| **Submit Order** | Office Manager, Admin | Browse available plants and submit a new delivery order |
| **My Orders** | All users | View and track the current user's submitted orders |
| **Inventory Dashboard** | Admin, Analyst, Warehouse | View current stock levels with low-stock highlighting |

---

## Navigation Flow

```
Home
 ├── [Submit New Order] ──► Submit Order ──► (on submit) ──► My Orders
 ├── [View My Orders]   ──► My Orders
 └── [Inventory Dashboard] ──► Inventory Dashboard   (Admin / Analyst only)
```

Back buttons on each screen return the user to **Home**.

---

## Key Formulas

### Submit Order — Patch Order Record

```powerfx
// Run on the Submit button's OnSelect property
// Step 1: Create the parent Orders record
Set(
    varNewOrder,
    Patch(
        Orders,
        Defaults(Orders),
        {
            'Requested By': LookUp(Users, 'Primary Email' = User().Email),
            'Order Date': Now(),
            Status: 'Status (Orders)'.Pending,
            Office: varUserOffice,
            Notes: txtNotes.Text
        }
    )
);

// Step 2: Create one Order Items record per line in the order collection
ForAll(
    colOrderItems,
    Patch(
        'Order Items',
        Defaults('Order Items'),
        {
            Order: varNewOrder,
            Plant: ThisRecord.Plant,
            'Quantity Requested': ThisRecord.Qty
        }
    )
);

// Step 3: Trigger the Order Confirmation Power Automate flow
OrderConfirmationFlow.Run(varNewOrder.'Order Number');

// Step 4: Navigate to My Orders and show a success notification
Notify("Order " & varNewOrder.'Order Number' & " submitted successfully.", NotificationType.Success);
Navigate(scrMyOrders, ScreenTransition.Fade);
```

### My Orders — Filter Gallery

```powerfx
// Gallery Items property — show only orders belonging to the current user
Filter(
    Orders,
    'Requested By'.'Primary Email' = User().Email
)
```

### My Orders — Status Badge Colour

```powerfx
// Fill property of the status badge rectangle
Switch(
    ThisItem.Status,
    'Status (Orders)'.Pending,    RGBA(255, 193, 7, 1),    // Amber
    'Status (Orders)'.Confirmed,  RGBA(13, 110, 253, 1),   // Blue
    'Status (Orders)'.'In Transit', RGBA(253, 126, 20, 1), // Orange
    'Status (Orders)'.Delivered,  RGBA(25, 135, 84, 1),    // Green
    RGBA(108, 117, 125, 1)                                  // Grey (default)
)
```

### Inventory Dashboard — Low Stock Highlight

```powerfx
// Fill property of each gallery row
If(
    ThisItem.'Quantity In Stock' < ThisItem.'Reorder Threshold',
    RGBA(255, 235, 235, 1),   // Light red background for low stock
    RGBA(255, 255, 255, 1)    // White background for healthy stock
)
```

### Inventory Dashboard — Inline Quantity Update

```powerfx
// OnSelect of the Save icon next to each inventory row
Patch(
    Inventory,
    ThisItem,
    {
        'Quantity In Stock': Value(txtQtyEdit.Text),
        'Last Updated': Now()
    }
);
Notify("Stock updated for " & ThisItem.'Plant Name', NotificationType.Success);
```

---

## Variable and Collection Naming Conventions

| Prefix | Type | Example | Purpose |
|---|---|---|---|
| `var` | Global Variable | `varUserRole`, `varNewOrder`, `varUserOffice` | App-wide state |
| `loc` | Local Variable | `locIsLoading` | Screen-scoped state |
| `col` | Collection | `colOrderItems` | In-memory data collections |
| `scr` | Screen reference | `scrHome`, `scrMyOrders` | Navigation targets |
| `txt` | TextInput control | `txtNotes`, `txtQtyEdit` | User text inputs |
| `gal` | Gallery control | `galInventory`, `galMyOrders` | Data galleries |
| `btn` | Button control | `btnSubmitOrder` | Action buttons |
| `lbl` | Label control | `lblOrderStatus` | Display labels |

### App-Level Variables (set in `App.OnStart`)

```powerfx
// App.OnStart
Set(varUserRole, LookUp(/* your role table or Entra group */, UserEmail = User().Email, Role));
Set(varUserOffice, LookUp(Offices, /* match current user to office */));
ClearCollect(colOrderItems, []);   // Initialise empty order basket
```

---

## How to Import the App into Power Apps

1. **Export the app** from the source environment:
   - Go to `make.powerapps.com` → **Apps** → select the app → **⋯ > Export package (.zip)**
   - Choose **Create as new** or **Update** for all resources.

2. **Import into the target environment**:
   - In the target environment, go to `make.powerapps.com` → **Apps** → **Import canvas app**
   - Upload the `.zip` package.
   - Resolve any data connection warnings by re-mapping the Dataverse connection to the target environment.

3. **Update environment references**:
   - Open the app in **Power Apps Studio**.
   - In the **Data** pane, remove the old Dataverse connections and re-add them pointing to the correct environment URL (see `/deployment/solution-settings.json`).

4. **Re-publish the app**:
   - Select **File → Save → Publish**.
   - Share the app with the relevant Entra ID security groups mapped to Dataverse security roles.

> **Tip**: For ALM deployments use managed Solutions instead of standalone app packages — see `/deployment/README.md`.

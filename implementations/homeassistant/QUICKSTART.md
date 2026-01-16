# Quick Start Guide - Somfy PoE Home Assistant Integration

Get your Somfy PoE motors working with Home Assistant in under 10 minutes!

## Prerequisites

Before you start, ensure you have:

- ✅ Somfy PoE motor installed and powered
- ✅ Motor connected to PoE+ switch (same network as Home Assistant)
- ✅ Motor's 4-digit PIN code (from label - **don't lose this!**)
- ✅ Home Assistant 2023.1 or newer
- ✅ Network supports mDNS/multicast (for auto-discovery)

## Installation Steps

### Step 1: Install the Integration

#### Option A: HACS (Recommended)

1. Open **HACS** in Home Assistant
2. Click the **3 dots** (top right)
3. Select **Custom repositories**
4. Add: `https://github.com/yourusername/somfy-poe`
5. Category: **Integration**
6. Click **Download**
7. **Restart** Home Assistant

#### Option B: Manual

1. Download `custom_components/somfy_poe/` from this repository
2. Copy to: `<ha_config>/custom_components/somfy_poe/`
3. **Restart** Home Assistant

### Step 2: Add Your Motor

1. Go to **Settings** → **Devices & Services**
2. Click **+ Add Integration** (bottom right)
3. Search for **Somfy PoE Motors**
4. Click on it

### Step 3: Choose Setup Method

You'll see two options:

#### Option 1: Automatic Discovery (Easiest)

1. Select **Automatic discovery (recommended)**
2. Click **Submit**
3. Wait 10 seconds while it scans your network
4. **If motors found:**
   - You'll see your motor(s) listed with name and IP
   - **Select your motor**
   - Click **Submit**
   - **Enter the 4-digit PIN** from your motor label
   - Click **Submit**
   - ✅ **Done!**

5. **If no motors found:**
   - You'll see a helpful error message
   - Click **Switch to manual configuration**
   - Continue with manual setup below

#### Option 2: Manual Configuration

If you chose manual OR auto-discovery didn't find motors:

1. Enter your motor's **IP address**
   - Find it in your router's DHCP client list
   - Or use Somfy Config Tool
2. Enter the **4-digit PIN** from motor label
3. Click **Submit**

✅ **Done!** Your motor is now ready to use.

## Step 4: Test Your Motor

### From Home Assistant UI

1. Go to **Settings** → **Devices & Services**
2. Find **Somfy PoE Motors**
3. Click on your motor device
4. You should see a **Cover** entity
5. Try the controls:
   - **▲** to open
   - **▼** to close
   - **■** to stop
   - Slider to set position

### From Developer Tools

1. Go to **Developer Tools** → **Services**
2. Try these services:

**Open blind:**
```yaml
service: cover.open_cover
target:
  entity_id: cover.your_motor_name
```

**Close blind:**
```yaml
service: cover.close_cover
target:
  entity_id: cover.your_motor_name
```

**Set to 50%:**
```yaml
service: cover.set_cover_position
target:
  entity_id: cover.your_motor_name
data:
  position: 50
```

**Identify motor (wink):**
```yaml
service: somfy_poe.wink
target:
  entity_id: cover.your_motor_name
```

## Step 5: Create Your First Automation

Let's close the blinds at sunset:

1. Go to **Settings** → **Automations & Scenes**
2. Click **+ Create Automation**
3. Click **Start with an empty automation**
4. Set up the trigger:
   - **Trigger type**: Sun
   - **Event**: Sunset
5. Set up the action:
   - **Action type**: Call service
   - **Service**: `cover.close_cover`
   - **Target**: Your motor entity
6. **Save** the automation

✅ Your blinds will now close automatically at sunset!

## Troubleshooting

### Motor Not Discovered

**Quick fixes:**
1. Verify motor has power (check PoE switch LED)
2. Ping the motor: `ping sfy_poe_XXXXXX.local`
3. Check if motor responds on port 55056
4. Try **Manual configuration** instead

**Network check:**
```bash
# From Home Assistant host
ping sfy_poe_160d00.local  # Replace with your motor hostname
```

### Authentication Failed

- ✓ Check PIN is correct (it's on the motor label)
- ✓ PIN must be exactly 4 digits
- ✓ Try power cycling the motor
- ✓ Ensure motor hasn't been factory reset

### Motor Not Responding

1. Check motor LED status
2. Verify network connectivity
3. Try power cycling the motor
4. Check Home Assistant logs:
   ```yaml
   # configuration.yaml
   logger:
     logs:
       custom_components.somfy_poe: debug
   ```

### Can't Find Motor IP Address

**Method 1: Router**
- Log into your router
- Check DHCP client list
- Look for `sfy_poe_XXXXXX`

**Method 2: Network Scanner**
- Use Fing app or Angry IP Scanner
- Look for devices on ports 55055-55056

**Method 3: Somfy Config Tool**
- Download from Somfy website
- Run the tool
- It will show all motors with IP addresses

## Next Steps

### Add More Motors

Simply repeat Step 2-3 for each additional motor. Each motor becomes a separate device in Home Assistant.

### Create Automations

**Morning routine:**
```yaml
automation:
  - alias: "Morning blinds"
    trigger:
      platform: time
      at: "07:00:00"
    action:
      service: cover.set_cover_position
      target:
        entity_id: cover.bedroom_blind
      data:
        position: 50
```

**Away mode:**
```yaml
automation:
  - alias: "Close all when away"
    trigger:
      platform: state
      entity_id: person.your_name
      to: "not_home"
    action:
      service: cover.close_cover
      target:
        entity_id:
          - cover.living_room_blind
          - cover.bedroom_blind
```

### Group Multiple Blinds

```yaml
# configuration.yaml
cover:
  - platform: group
    name: "Living Room Blinds"
    entities:
      - cover.blind_1
      - cover.blind_2
      - cover.blind_3
```

### Add to Dashboards

1. Go to your dashboard
2. Click **Edit**
3. Click **+ Add Card**
4. Choose **Entities Card**
5. Add your motor entities
6. **Save**

### Voice Control

If you have Google Home or Alexa integrated:

**Google:** "Hey Google, open the living room blinds"
**Alexa:** "Alexa, set living room blinds to 50 percent"

## Getting Help

- **Documentation**: See [README.md](README.md) for full details
- **Logs**: Settings → System → Logs
- **Issues**: [GitHub Issues](https://github.com/yourusername/somfy-poe/issues)

## Common Commands Reference

```yaml
# Open
service: cover.open_cover
target:
  entity_id: cover.blind_name

# Close
service: cover.close_cover
target:
  entity_id: cover.blind_name

# Stop
service: cover.stop_cover
target:
  entity_id: cover.blind_name

# Set Position (0=closed, 100=open)
service: cover.set_cover_position
target:
  entity_id: cover.blind_name
data:
  position: 75

# Identify Motor
service: somfy_poe.wink
target:
  entity_id: cover.blind_name
```

## Tips & Tricks

💡 **Tip 1**: Use DHCP reservations or static IPs for motors to prevent IP changes

💡 **Tip 2**: Label your motors in the Somfy Config Tool - these names appear in Home Assistant

💡 **Tip 3**: Use the wink service to identify which motor is which during setup

💡 **Tip 4**: Create scenes for different times of day (Morning, Day, Evening, Night)

💡 **Tip 5**: Add position sensors to automate based on sun position/angle

---

**Need more help?** Check the [full README](README.md) or open an [issue](https://github.com/yourusername/somfy-poe/issues).

🎉 **Enjoy your automated blinds!**

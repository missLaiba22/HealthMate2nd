# Ready Player Me Integration Setup Guide

## Overview
This implementation uses Ready Player Me API to provide avatar selection and customization for patients in the HealthMate app.

## Setup Steps

### 1. Create Ready Player Me Account
1. Go to https://studio.readyplayer.me/
2. Sign up for a free account
3. Create a new application

### 2. Get Your Application Details
From the Ready Player Me Studio, you need to get:
- **Application ID** (subdomain)
- **Application Subdomain**

### 3. Update Frontend Configuration
Replace `YOUR_RPM_APPLICATION_ID` in the following files with your actual Application ID:
- `frontend/src/screens/AvatarSelectionScreen.js` (line 9)
- `frontend/src/screens/AvatarCustomizationScreen.js` (line 9)

```javascript
const RPM_APP_ID = 'your-actual-app-id-here';
```

## How It Works

### Flow:
1. **User completes profile** → Navigates to Avatar Selection
2. **Avatar Selection Screen**:
   - Creates anonymous RPM user
   - Fetches 4 avatar templates (2 male, 2 female)
   - User selects a base avatar
   - Creates draft avatar from selected template
   - Saves avatar ID, RPM user ID, and token to backend
   - Navigates to customization screen

3. **Avatar Customization Screen**:
   - Fetches available assets (outfits, hair, glasses, etc.)
   - User can equip different items
   - Preview updates in real-time
   - Saves final avatar

4. **Patient Home Screen**:
   - Displays the user's avatar
   - Shows welcome message

## Database Fields

The following fields are stored in the patient profile:
- `avatar_id`: Ready Player Me avatar ID
- `rpm_user_id`: Ready Player Me user ID
- `rpm_token`: RPM authentication token for future customization

## Asset Categories

The customization screen supports these categories:
- Outfits (`outfit`)
- Hair Styles (`hairStyle`)
- Glasses (`glasses`)
- Face Masks (`faceMask`)
- Headwear (`headwear`)

Additional categories can be added by updating the `categories` array in `AvatarCustomizationScreen.js`.

## 3D GLB Rendering

Currently, the app uses placeholders for avatar preview. To implement 3D rendering:

### Option 1: Use expo-gl and expo-three
```bash
npm install expo-gl expo-three three@0.150.0
```

### Option 2: Use WebView to display GLB
The avatar can be viewed at:
```
https://models.readyplayer.me/[avatar-id].glb
```

### Option 3: Use Ready Player Me's iframe viewer
```html
<iframe src="https://readyplayer.me/avatar?frameApi&avatarId=[avatar-id]" />
```

## API Endpoints Used

1. **Create User**: `POST https://api.readyplayer.me/v1/users`
2. **Get Templates**: `GET https://api.readyplayer.me/v2/avatars/templates`
3. **Create Avatar**: `POST https://api.readyplayer.me/v2/avatars/templates/[template-id]`
4. **Update Avatar**: `PATCH https://api.readyplayer.me/v2/avatars/[avatar-id]`
5. **Save Avatar**: `PUT https://api.readyplayer.me/v2/avatars/[avatar-id]`
6. **Get Assets**: `GET https://api.readyplayer.me/v1/assets`
7. **Get Avatar GLB**: `GET https://models.readyplayer.me/[avatar-id].glb`

## Testing

1. Sign up as a patient
2. Complete profile setup
3. Select a base avatar from 4 options
4. Customize with different outfits, hair, accessories
5. Save and view on home screen

## Future Enhancements

- [ ] Integrate 3D GLB viewer
- [ ] Add color customization options
- [ ] Allow users to re-customize avatar from settings
- [ ] Add more asset categories
- [ ] Implement avatar animations
- [ ] Add avatar photo capture feature

## Troubleshooting

### Issue: "Failed to create Ready Player Me user"
- Check your Application ID is correct
- Verify network connectivity
- Check RPM API status

### Issue: "Failed to fetch assets"
- Ensure user authentication token is valid
- Check Application ID in headers
- Verify user ID is correct

### Issue: Avatar preview not showing
- Implement 3D viewer (currently showing placeholder)
- Check avatar ID is valid
- Verify GLB URL is accessible

## Support

For Ready Player Me API documentation:
https://docs.readyplayer.me/ready-player-me/api-reference

For issues with this implementation, check the console logs for detailed error messages.

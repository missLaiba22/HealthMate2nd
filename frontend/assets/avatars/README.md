# Avatar Files Directory

Upload your GLB avatar files to this directory with the following naming convention:

- `avatar1.glb`
- `avatar2.glb`
- `avatar3.glb`
- `avatar4.glb`
- `avatar5.glb`
- `avatar6.glb`

These files will be used to render 3D avatars in the application.

## Implementation Notes

Once you upload the GLB files:

1. Install the required package for 3D rendering:
   ```bash
   npm install expo-gl expo-three three@0.150.0
   ```

2. Update `AvatarSelectionScreen.js` to load actual GLB models instead of placeholder images.

3. Update `PatientHomeScreen.js` to render the selected avatar in 3D.

## Current Status

- Using placeholder images for now
- GLB files should be placed here
- The avatar ID (avatar1-avatar6) is stored in the database
- The actual GLB file path will be constructed based on the avatar ID

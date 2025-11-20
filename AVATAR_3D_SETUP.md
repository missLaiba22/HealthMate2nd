# 3D Avatar with Lipsync - Setup Guide

## Required Packages

Run these commands in the frontend directory:

```bash
npx expo install expo-gl
npm install three@0.160.0
npm install expo-three
npm install @react-three/fiber
npm install @react-three/drei
```

## Architecture Overview

The approach from your reference code uses:
1. **Three.js** - 3D rendering engine
2. **@react-three/fiber** - React wrapper for Three.js
3. **GLB Model Loading** - Load Ready Player Me avatars
4. **Morph Targets** - Animate facial expressions (lipsync)
5. **Audio Analysis** - Real-time audio amplitude detection
6. **Viseme Mapping** - Map phonemes to facial shapes

## Key Components Needed

### 1. AvatarViewer Component
- Renders the 3D GLB model
- Handles morph target animations
- Audio-driven lipsync

### 2. Audio Analysis
- Use Web Audio API (works in Expo)
- AnalyserNode for real-time amplitude
- ByteTimeDomainData for mouth movement

### 3. Morph Target Control
- Find mesh with morphTargetInfluences
- Map audio amplitude to morph values
- Common morph targets: viseme_aa, viseme_o, etc.

## Implementation Notes

For React Native/Expo, we need to use:
- `expo-gl` instead of HTML canvas
- `GLView` component instead of `<Canvas>`
- Three.js works the same way
- Audio handling through `expo-av` or Web Audio API

## Next Steps

1. Install packages above
2. Create `AvatarViewer3D.js` component
3. Integrate into PatientHomeScreen
4. Add audio playback with lipsync
5. Test with Ready Player Me GLB models

## Lipsync Flow

1. Play audio file
2. Audio analyser extracts amplitude
3. Map amplitude to morph target strength
4. Apply to mesh.morphTargetInfluences[index]
5. Avatar mouth moves in sync with audio

## Viseme Approach (Advanced)

If you want precise lipsync:
1. Use Rhubarb Lip Sync on backend (already in your code)
2. Get viseme timings (phoneme -> time mapping)
3. Schedule morph changes at specific times
4. Map visemes (A, B, C, etc.) to morph targets

The reference code already has this implemented - we just need to adapt it for React Native!

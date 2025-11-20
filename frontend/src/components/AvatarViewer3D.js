import React, { useRef, useEffect, useState, forwardRef, useImperativeHandle } from 'react';
import { View, StyleSheet, Platform } from 'react-native';
import { WebView } from 'react-native-webview';
import { Asset } from 'expo-asset';
import CONFIG from '../config';

const AvatarViewer3D = forwardRef(({ avatarUrl, audioUrl, autoPlay = false, style }, ref) => {
  const webViewRef = useRef(null);
  const [viewerReady, setViewerReady] = useState(false);
  const [htmlUri, setHtmlUri] = useState(null);

  useEffect(() => {
    loadHtmlFile();
  }, []);

  async function loadHtmlFile() {
    try {
      // Load the HTML file from assets
      const asset = Asset.fromModule(require('../../assets/avatar-viewer.html'));
      await asset.downloadAsync();
      setHtmlUri(asset.localUri || asset.uri);
    } catch (error) {
      console.error('Failed to load avatar viewer HTML:', error);
    }
  }

  useEffect(() => {
    if (viewerReady && avatarUrl) {
      // Proxy the GLB through backend to avoid CORS issues
      const proxiedUrl = `${CONFIG.API_URL}/avatar/proxy-glb?url=${encodeURIComponent(avatarUrl)}`;
      console.log('Original avatar URL:', avatarUrl);
      console.log('Proxied URL:', proxiedUrl);
      sendMessage({ type: 'loadAvatar', url: proxiedUrl });
    }
  }, [viewerReady, avatarUrl]);

  useEffect(() => {
    if (viewerReady && autoPlay && audioUrl) {
      sendMessage({ type: 'playAudio', url: audioUrl });
    }
  }, [viewerReady, audioUrl, autoPlay]);

  function sendMessage(data) {
    if (webViewRef.current) {
      webViewRef.current.postMessage(JSON.stringify(data));
    }
  }

  function handleMessage(event) {
    try {
      const data = JSON.parse(event.nativeEvent.data);
      console.log('Avatar viewer message:', data);

      switch (data.type) {
        case 'ready':
          setViewerReady(true);
          break;
        case 'loaded':
          console.log('Avatar loaded successfully');
          break;
        case 'morphsFound':
          console.log('Available morphs:', data.morphs);
          break;
        case 'error':
          console.error('Avatar viewer error:', data.message);
          break;
        case 'audioEnded':
          console.log('Audio playback ended');
          break;
      }
    } catch (error) {
      console.error('Failed to parse viewer message:', error);
    }
  }

  // Expose methods to parent component
  useImperativeHandle(ref, () => ({
    playAudio: (url) => sendMessage({ type: 'playAudio', url }),
    stopAudio: () => sendMessage({ type: 'stopAudio' }),
    testMorph: (strength = 1, duration = 800) => sendMessage({ type: 'testMorph', strength, duration }),
    loadAvatar: (url) => sendMessage({ type: 'loadAvatar', url }),
  }));

  if (!htmlUri) {
    return <View style={[styles.container, style]} />;
  }

  return (
    <View style={[styles.container, style]}>
      <WebView
        ref={webViewRef}
        source={{ uri: htmlUri }}
        onMessage={handleMessage}
        javaScriptEnabled={true}
        domStorageEnabled={true}
        mediaPlaybackRequiresUserAction={false}
        allowsInlineMediaPlayback={true}
        style={styles.webview}
        originWhitelist={['*']}
        allowFileAccess={true}
        allowUniversalAccessFromFileURLs={true}
        mixedContentMode="always"
        cacheEnabled={false}
        onError={(syntheticEvent) => {
          const { nativeEvent } = syntheticEvent;
          console.error('WebView error:', nativeEvent);
        }}
        onHttpError={(syntheticEvent) => {
          const { nativeEvent } = syntheticEvent;
          console.error('WebView HTTP error:', nativeEvent);
        }}
      />
    </View>
  );
});

export default AvatarViewer3D;

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: 'transparent',
  },
  webview: {
    flex: 1,
    backgroundColor: 'transparent',
  },
});

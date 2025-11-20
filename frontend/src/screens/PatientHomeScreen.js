import React, { useState, useEffect, useRef } from 'react';
import { View, Text, StyleSheet, ActivityIndicator, TouchableOpacity } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import AsyncStorage from '@react-native-async-storage/async-storage';
import CONFIG from '../config';
import AvatarViewer3D from '../components/AvatarViewer3D';
import LanguageSelector from '../components/LanguageSelector';

export default function PatientHomeScreen({ navigation }) {
  const [loading, setLoading] = useState(true);
  const [patientName, setPatientName] = useState('');
  const [avatarId, setAvatarId] = useState(null);
  const [avatarUrl, setAvatarUrl] = useState(null);
  const [selectedLanguage, setSelectedLanguage] = useState('en');
  const avatarViewerRef = useRef(null);

  useEffect(() => {
    fetchPatientProfile();
    loadLanguagePreference();
  }, []);

  async function loadLanguagePreference() {
    try {
      const savedLanguage = await AsyncStorage.getItem('preferred_language');
      if (savedLanguage) {
        setSelectedLanguage(savedLanguage);
      }
    } catch (error) {
      console.error('Error loading language preference:', error);
    }
  }

  async function handleLanguageChange(languageCode) {
    setSelectedLanguage(languageCode);
    try {
      await AsyncStorage.setItem('preferred_language', languageCode);
      console.log('Language changed to:', languageCode);
    } catch (error) {
      console.error('Error saving language preference:', error);
    }
  }

  async function fetchPatientProfile() {
    try {
      const token = await AsyncStorage.getItem('access_token');
      if (!token) {
        navigation.navigate('Login');
        return;
      }

      const response = await fetch(`${CONFIG.API_URL}/profile`, {
        method: 'GET',
        headers: {
          'Authorization': `Bearer ${token}`
        }
      });

      if (response.ok) {
        const profile = await response.json();
        setPatientName(profile.name || 'User');
        setAvatarId(profile.avatar_id);
        setAvatarUrl(profile.avatar_url);
        
        console.log('Profile loaded:', {
          name: profile.name,
          avatar_id: profile.avatar_id,
          avatar_url: profile.avatar_url
        });
      }
    } catch (error) {
      console.error('Error fetching profile:', error);
    } finally {
      setLoading(false);
    }
  }

  if (loading) {
    return (
      <View style={styles.loadingContainer}>
        <ActivityIndicator size="large" color="#60a5fa" />
      </View>
    );
  }

  return (
    <View style={{ flex: 1, backgroundColor: '#f8fafc' }}>
      <LinearGradient colors={["#e3f2fd", "#bbdefb"]} style={styles.header}>
        <View style={styles.headerTop}>
          <Text style={styles.greeting}>Hi {patientName},</Text>
          <Text style={styles.subtitle}>How can I help you?</Text>
        </View>
        
        <LanguageSelector
          selectedLanguage={selectedLanguage}
          onLanguageChange={handleLanguageChange}
        />
        
        {avatarUrl && (
          <View style={styles.avatarContainer}>
            <AvatarViewer3D
              ref={avatarViewerRef}
              avatarUrl={avatarUrl}
              style={styles.avatarViewer}
            />
          </View>
        )}
      </LinearGradient>

      <View style={styles.bottomSection}>
        <TouchableOpacity 
          style={styles.micButton}
          onPress={() => {
            if (avatarViewerRef.current) {
              avatarViewerRef.current.testMorph(1, 1000);
            }
          }}
        >
          <Text style={styles.micIcon}>🎤</Text>
        </TouchableOpacity>
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  loadingContainer: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
    backgroundColor: '#f8fafc',
  },
  header: {
    flex: 1,
    paddingTop: 60,
    paddingHorizontal: 20,
    borderBottomLeftRadius: 30,
    borderBottomRightRadius: 30,
    alignItems: 'center',
  },
  headerTop: {
    width: '100%',
    alignItems: 'center',
    marginBottom: 20,
  },
  greeting: {
    fontSize: 24,
    fontStyle: 'italic',
    color: '#1e3a8a',
    marginBottom: 5,
  },
  subtitle: {
    fontSize: 24,
    fontStyle: 'italic',
    color: '#1e3a8a',
  },
  avatarContainer: {
    flex: 1,
    width: '100%',
    maxWidth: 500,
    justifyContent: 'center',
    alignItems: 'center',
  },
  avatarViewer: {
    width: '100%',
    height: '100%',
  },
  bottomSection: {
    position: 'absolute',
    bottom: 40,
    left: 0,
    right: 0,
    alignItems: 'center',
  },
  micButton: {
    width: 80,
    height: 80,
    borderRadius: 40,
    backgroundColor: 'white',
    justifyContent: 'center',
    alignItems: 'center',
    shadowColor: '#000',
    shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.3,
    shadowRadius: 8,
    elevation: 8,
  },
  micIcon: {
    fontSize: 40,
  },
  avatarPlaceholder: {
    width: 120,
    height: 120,
    borderRadius: 60,
    backgroundColor: 'white',
    borderWidth: 4,
    borderColor: 'white',
    marginTop: 10,
    justifyContent: 'center',
    alignItems: 'center',
  },
  avatarText: {
    fontSize: 14,
    fontWeight: '600',
    color: '#1e3a8a',
  },
  avatarHint: {
    fontSize: 10,
    color: '#64748b',
    marginTop: 5,
  },
  content: {
    flex: 1,
    padding: 20,
  },
  question: {
    fontSize: 22,
    fontWeight: '600',
    color: '#1e3a8a',
    textAlign: 'center',
    marginTop: 20,
    marginBottom: 30,
  },
  featuresPlaceholder: {
    flex: 1,
    justifyContent: 'center',
    alignItems: 'center',
  },
  placeholderText: {
    fontSize: 16,
    color: '#94a3b8',
  },
});

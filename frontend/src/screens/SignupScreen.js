import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, KeyboardAvoidingView, Platform, Alert, ActivityIndicator } from 'react-native';
import { LinearGradient } from 'expo-linear-gradient';
import { Picker } from '@react-native-picker/picker'; // Updated Picker import
import CONFIG from '../config';

export default function SignupScreen({ navigation }) {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [role, setRole] = useState('patient'); // Default role
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState('');

  function onSignUp() {
    setLoading(true);
    const API_URL = `${CONFIG.API_URL}/auth/signup`;
    fetch(API_URL, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ email, password, role })
    })
      .then(async res => {
        const data = await res.json();
        if (!res.ok) throw new Error(data.detail || 'Signup failed');
        setMessage('Signup successful!');
        navigation.navigate('Login');
      })
      .catch(err => setMessage(`Error: ${err.message || String(err)}`))
      .finally(() => setLoading(false));
  }

  return (
    <KeyboardAvoidingView style={{ flex: 1 }} behavior={Platform.OS === 'ios' ? 'padding' : undefined}>
      <LinearGradient colors={["#e3f2fd", "#bbdefb"]} style={styles.header}>
        <Text style={styles.title}>Create account</Text>
      </LinearGradient>

      <View style={styles.card}>
        <Text style={styles.welcome}>Sign up</Text>
        <TextInput placeholder="Enter your email" value={email} onChangeText={setEmail} style={styles.input} keyboardType="email-address" autoCapitalize="none" />
        <TextInput placeholder="Enter your password" value={password} onChangeText={setPassword} style={styles.input} secureTextEntry />

        {/* Role Selector */}
        <Picker
          selectedValue={role}
          onValueChange={(itemValue) => setRole(itemValue)}
          style={styles.input}
        >
          <Picker.Item label="Patient" value="patient" />
          <Picker.Item label="Doctor" value="doctor" />
        </Picker>

        <TouchableOpacity onPress={() => navigation.navigate('Login')}>
          <Text style={styles.forgot}>Already have an account? <Text style={{fontWeight: '700'}}>Sign in</Text></Text>
        </TouchableOpacity>

        <TouchableOpacity style={styles.button} onPress={onSignUp} disabled={loading}>
          {loading ? <ActivityIndicator color="#1e3a8a" /> : <Text style={styles.buttonText}>Sign Up</Text>}
        </TouchableOpacity>
        {message ? <Text style={styles.message}>{message}</Text> : null}
      </View>
    </KeyboardAvoidingView>
  );
}

const styles = StyleSheet.create({
  header: { flex: 0.25, alignItems: 'center', justifyContent: 'center' },
  title: { fontSize: 28, fontWeight: '700', color: '#102a43', marginTop: 40 },
  card: { flex: 0.75, backgroundColor: '#fff', marginTop: -30, borderTopLeftRadius: 30, borderTopRightRadius: 30, padding: 24, alignItems: 'center' },
  welcome: { fontSize: 24, fontWeight: '700', marginBottom: 16 },
  input: { width: '90%', backgroundColor: '#f5f7fa', padding: 12, borderRadius: 12, marginBottom: 12 },
  forgot: { color: '#6b7280', marginVertical: 8 },
  button: { marginTop: 12, backgroundColor: '#dbeafe', paddingVertical: 14, paddingHorizontal: 48, borderRadius: 24 },
  buttonText: { color: '#1e3a8a', fontWeight: '700' },
  message: { marginTop: 12, color: '#1e3a8a', fontWeight: '700' }
});

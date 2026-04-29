# CEONodev2 - Voice-Enabled AI Agent

CEONodev2 is an enhanced version of the CEO Agent that integrates ElevenLabs voice technology for hands-free interaction.

## Features

- **Wake Word Detection**: Responds to "Alex" to start listening
- **Speech-to-Text**: Converts voice commands to text using Web Speech API
- **Text-to-Speech**: Uses ElevenLabs API for natural voice responses
- **Visual Feedback**: Dynamic status indicators and animations
- **Seamless Integration**: Works with existing task orchestration system

## Setup Instructions

### 1. Environment Variables

Create a `.env` file in the frontend directory with your ElevenLabs credentials:

```bash
cp .env.example .env
```

Then edit `.env` and add your credentials:

```env
REACT_APP_ELEVENLABS_API_KEY=your_actual_api_key_here
REACT_APP_ELEVENLABS_VOICE_ID=your_actual_voice_id_here
```

### 2. Get ElevenLabs Credentials

1. **API Key**: 
   - Go to [ElevenLabs Settings](https://elevenlabs.io/app/settings/api-keys)
   - Create or copy your API key

2. **Voice ID**:
   - Go to [ElevenLabs Voice Lab](https://elevenlabs.io/app/voice-lab)
   - Select a voice or create a custom one
   - Copy the Voice ID from the voice settings

### 3. Browser Permissions

Make sure your browser allows microphone access:
- Chrome/Edge: Click the microphone icon in the address bar
- Firefox: Go to Settings > Privacy & Security > Permissions
- Safari: Go to Preferences > Websites > Microphone

## Usage

1. **Toggle Voice Mode**: Click the "VOICE OFF/ON" toggle in the header
2. **Wake Word**: Say "Alex" to activate the agent
3. **Give Commands**: Speak your task after the agent responds
4. **Listen to Responses**: The agent will speak back using ElevenLabs TTS

### Example Interaction

```
User: "Alex"
Agent: "Yes, I'm listening. How can I help you?"
User: "Create a landing page for our new product"
Agent: "I understand you want me to: Create a landing page for our new product. Let me process this task."
[Agent processes task through existing orchestration system]
Agent: "Task has been completed successfully."
```

## Status Indicators

- **STANDING BY**: Waiting for wake word "Alex"
- **LISTENING**: Actively listening for commands
- **PROCESSING**: Converting speech and preparing task
- **SPEAKING**: Agent is responding with voice
- **THINKING/ROUTING**: Processing task through AI agents
- **TASK COMPLETE**: Task finished successfully

## Troubleshooting

### No Voice Recognition
- Check browser microphone permissions
- Ensure you're using HTTPS (required for Web Speech API)
- Try refreshing the page

### No Voice Output
- Verify ElevenLabs API key and Voice ID in `.env`
- Check browser console for API errors
- Ensure you have ElevenLabs credits available

### Wake Word Not Working
- Speak clearly and at normal volume
- Try saying "Alex" with different pronunciations
- Check that microphone is working in other applications

## Technical Details

### Dependencies Used
- **Web Speech API**: For speech recognition (built into modern browsers)
- **ElevenLabs API**: For text-to-speech conversion
- **React Hooks**: useState, useEffect, useRef, useCallback
- **Framer Motion**: For animations (inherited from CEONode)
- **Lucide React**: For icons

### Browser Compatibility
- Chrome/Chromium: Full support
- Firefox: Speech recognition support varies
- Safari: Limited speech recognition support
- Edge: Full support

### Security Notes
- API keys are stored in environment variables
- No sensitive data is logged
- Speech data is processed locally (Web Speech API)
- Only processed commands are sent to ElevenLabs

## Customization

### Voice Settings
You can modify voice parameters in the `speakText` function:

```javascript
voice_settings: {
  stability: 0.5,        // 0-1, higher = more stable
  similarity_boost: 0.5, // 0-1, higher = more similar to training
}
```

### Wake Word
To change the wake word from "Alex", modify the detection logic:

```javascript
if (!isWakeWordDetected && fullTranscript.includes('your-wake-word')) {
  // Wake word logic
}
```

### Language Support
To change the speech recognition language:

```javascript
recognitionRef.current.lang = 'hi-IN'; // For Hindi
// or
recognitionRef.current.lang = 'en-IN'; // For Indian English
```

## Future Enhancements

- [ ] Multi-language support (Hindi/English mixing)
- [ ] Custom wake word training
- [ ] Voice command shortcuts
- [ ] Conversation context memory
- [ ] Voice activity detection improvements
- [ ] Offline speech recognition fallback

## Contributing

When modifying CEONodev2:
1. Test voice functionality thoroughly
2. Ensure proper cleanup of audio resources
3. Handle edge cases (network failures, permission denials)
4. Maintain backward compatibility with existing CEONode

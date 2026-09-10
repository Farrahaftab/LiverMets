// Global configuration and logger - MUST LOAD FIRST
const DEVELOPMENT_MODE = false;  // Set to true for console debugging in desktop mode

const EXPERIENCE = {
    birthdayName: 'You',
    fromName: 'Your Friend',
    duration: 75,
    message: {
        title: 'Happy Birthday',
        line1: 'Thank you for being there.',
        line2: 'Thank you for everything you\'ve done for me.',
        line3: 'You mean more to me than words can explain.',
        final: 'May life give back to you\nall the light you have given me.'
    },
    characterModels: {
        girl: 'assets/models/girl.glb',
        man: 'assets/models/man.glb'
    },
    audioFiles: {
        darkAmbience: 'assets/audio/dark-ambience.mp3',
        footsteps: 'assets/audio/footsteps.mp3',
        pianoMusic: 'assets/audio/piano-music.mp3',
        voiceOver: 'assets/audio/voiceover.mp3',
        lightWhoosh: 'assets/audio/light-whoosh.mp3',
        natureAmbience: 'assets/audio/nature-ambience.mp3'
    }
};

const Logger = {
    log: (msg) => {
        if (DEVELOPMENT_MODE) console.log(`[Birthday VR] ${msg}`);
    },
    warn: (msg) => console.warn(`[Birthday VR] ${msg}`),
    error: (msg) => console.error(`[Birthday VR] ${msg}`)
};

// Show error message on page if something fails
function showErrorMessage(error) {
    const errorDiv = document.createElement('div');
    errorDiv.style.cssText = `
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: rgba(0, 0, 0, 0.9);
        color: #ff6b6b;
        padding: 40px;
        border-radius: 10px;
        font-family: monospace;
        max-width: 600px;
        z-index: 9999;
        text-align: center;
        border: 2px solid #ff6b6b;
    `;
    errorDiv.innerHTML = `
        <h2 style="color: #ff6b6b; margin-bottom: 20px;">Experience Initialization Error</h2>
        <p style="margin-bottom: 20px; color: #aaa;">${error}</p>
        <p style="color: #888; font-size: 12px;">Check browser console (F12) for details</p>
    `;
    document.body.appendChild(errorDiv);
    console.error('CRITICAL ERROR:', error);
}

// Global error handler
window.addEventListener('error', (event) => {
    console.error('JavaScript Error:', event.error);
    showErrorMessage(event.error?.message || 'Unknown error occurred');
});

window.addEventListener('unhandledrejection', (event) => {
    console.error('Unhandled Promise Rejection:', event.reason);
    showErrorMessage(event.reason?.message || 'Unhandled promise rejection');
});

class AudioManager {
    constructor(listener) {
        this.listener = listener;
        this.tracks = {};
        this.isInitialized = false;
        this.audioContext = null;
        this.masterGain = null;
    }

    async init() {
        if (this.isInitialized) return;

        const audioContext = this.listener.context;
        this.audioContext = audioContext;
        this.masterGain = this.listener.context.createGain();
        this.masterGain.connect(this.listener.context.destination);
        this.masterGain.gain.value = 0.7;

        this.isInitialized = true;
    }

    async loadAudio(name, filePath) {
        try {
            const audio = new THREE.Audio(this.listener);
            const audioLoader = new THREE.AudioLoader();

            const buffer = await audioLoader.loadAsync(filePath);
            audio.setBuffer(buffer);

            this.tracks[name] = audio;
            return audio;
        } catch (error) {
            console.warn(`Could not load audio ${filePath}. Using fallback.`, error);
            return this.createFallbackAudio(name);
        }
    }

    createFallbackAudio(name) {
        const audio = new THREE.Audio(this.listener);
        const bufferSize = 2 * this.audioContext.sampleRate;
        const noiseBuffer = this.audioContext.createBuffer(1, bufferSize, this.audioContext.sampleRate);

        if (name.includes('ambience') || name.includes('footstep')) {
            const data = noiseBuffer.getChannelData(0);
            for (let i = 0; i < bufferSize; i++) {
                data[i] = Math.random() * 0.1 - 0.05;
            }
        } else if (name.includes('piano') || name.includes('music')) {
            const data = noiseBuffer.getChannelData(0);
            const freq = 440;
            const sampleRate = this.audioContext.sampleRate;
            for (let i = 0; i < bufferSize; i++) {
                data[i] = 0.1 * Math.sin(2 * Math.PI * freq * i / sampleRate);
            }
        }

        audio.setBuffer(noiseBuffer);
        this.tracks[name] = audio;
        return audio;
    }

    playSound(name, options = {}) {
        if (!this.tracks[name]) return null;

        const audio = this.tracks[name];
        const {
            loop = false,
            volume = 1,
            position = null,
            fadeInDuration = 0
        } = options;

        audio.setLoop(loop);
        audio.setVolume(0);

        if (position) {
            audio.position.copy(position);
        }

        if (fadeInDuration > 0) {
            this.fadeIn(audio, volume, fadeInDuration);
        } else {
            audio.setVolume(volume);
        }

        if (!audio.isPlaying) {
            audio.play();
        }

        return audio;
    }

    stopSound(name, fadeDuration = 0) {
        if (!this.tracks[name]) return;

        const audio = this.tracks[name];

        if (fadeDuration > 0) {
            this.fadeOut(audio, fadeDuration);
        } else {
            audio.stop();
        }
    }

    fadeIn(audio, targetVolume, duration) {
        const startTime = performance.now();
        const startVolume = audio.getVolume();

        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / (duration * 1000), 1);
            audio.setVolume(startVolume + (targetVolume - startVolume) * progress);

            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };

        requestAnimationFrame(animate);
    }

    fadeOut(audio, duration) {
        const startTime = performance.now();
        const startVolume = audio.getVolume();

        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / (duration * 1000), 1);
            audio.setVolume(startVolume * (1 - progress));

            if (progress >= 1) {
                audio.stop();
            } else {
                requestAnimationFrame(animate);
            }
        };

        requestAnimationFrame(animate);
    }

    setVolume(name, volume) {
        if (this.tracks[name]) {
            this.tracks[name].setVolume(volume);
        }
    }

    getVolume(name) {
        if (this.tracks[name]) {
            return this.tracks[name].getVolume();
        }
        return 0;
    }

    update() {
        // Audio listener should be updated with camera position in main loop
    }

    dispose() {
        Object.values(this.tracks).forEach(audio => {
            if (audio.isPlaying) {
                audio.stop();
            }
        });
    }
}

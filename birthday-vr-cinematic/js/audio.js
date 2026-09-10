class AudioManager {
    constructor(listener) {
        this.listener = listener;
        this.tracks = {};
        this.isInitialized = false;
        this.audioContext = null;
        this.masterGain = null;
        this.silentBuffer = null;
    }

    async init() {
        if (this.isInitialized) return;

        try {
            const audioContext = this.listener.context;
            this.audioContext = audioContext;

            this.masterGain = this.listener.context.createGain();
            this.masterGain.connect(this.listener.context.destination);
            this.masterGain.gain.value = 0.7;

            this.createSilentBuffer();
            this.isInitialized = true;
        } catch (error) {
            Logger.warn('Audio initialization failed: ' + error.message);
            this.isInitialized = true;
        }
    }

    createSilentBuffer() {
        if (!this.audioContext) return;

        const bufferSize = this.audioContext.sampleRate;
        this.silentBuffer = this.audioContext.createBuffer(1, bufferSize, this.audioContext.sampleRate);
        const data = this.silentBuffer.getChannelData(0);
        for (let i = 0; i < bufferSize; i++) {
            data[i] = 0;
        }
    }

    async loadAudio(name, filePath) {
        try {
            Logger.log(`Loading audio: ${name}`);
            const audio = new THREE.Audio(this.listener);
            const audioLoader = new THREE.AudioLoader();

            const buffer = await audioLoader.loadAsync(filePath);
            audio.setBuffer(buffer);

            this.tracks[name] = audio;
            Logger.log(`✓ Audio loaded: ${name}`);
            return audio;
        } catch (error) {
            Logger.warn(`Optional audio missing: ${name}`);
            return this.createSilentAudio(name);
        }
    }

    createSilentAudio(name) {
        try {
            const audio = new THREE.Audio(this.listener);

            if (this.silentBuffer) {
                audio.setBuffer(this.silentBuffer);
            }

            this.tracks[name] = audio;
            return audio;
        } catch (error) {
            Logger.warn(`Could not create audio object for ${name}`);
            return this.createDummyAudio(name);
        }
    }

    createDummyAudio(name) {
        const dummy = {
            isPlaying: false,
            setBuffer: () => {},
            setLoop: () => {},
            setVolume: () => {},
            getVolume: () => 0,
            play: () => {},
            stop: () => {},
            pause: () => {},
            position: { copy: () => {}, x: 0, y: 0, z: 0 }
        };
        this.tracks[name] = dummy;
        return dummy;
    }

    playSound(name, options = {}) {
        const audio = this.tracks[name];
        if (!audio) {
            this.createDummyAudio(name);
            return this.tracks[name];
        }

        const {
            loop = false,
            volume = 1,
            position = null,
            fadeInDuration = 0
        } = options;

        try {
            if (audio.setLoop) audio.setLoop(loop);
            if (audio.setVolume) audio.setVolume(0);

            if (position && audio.position && audio.position.copy) {
                audio.position.copy(position);
            }

            if (fadeInDuration > 0) {
                this.fadeIn(audio, volume, fadeInDuration);
            } else {
                if (audio.setVolume) audio.setVolume(volume);
            }

            if (audio.play && !audio.isPlaying) {
                audio.play();
            }
        } catch (error) {
            Logger.warn(`Could not play sound ${name}: ${error.message}`);
        }

        return audio;
    }

    stopSound(name, fadeDuration = 0) {
        const audio = this.tracks[name];
        if (!audio) return;

        try {
            if (fadeDuration > 0) {
                this.fadeOut(audio, fadeDuration);
            } else {
                if (audio.stop) audio.stop();
            }
        } catch (error) {
            Logger.warn(`Could not stop sound ${name}`);
        }
    }

    fadeIn(audio, targetVolume, duration) {
        if (!audio || !audio.setVolume) return;

        try {
            const startTime = performance.now();
            const startVolume = audio.getVolume ? audio.getVolume() : 0;

            const animate = (currentTime) => {
                const elapsed = currentTime - startTime;
                const progress = Math.min(elapsed / (duration * 1000), 1);
                const newVolume = startVolume + (targetVolume - startVolume) * progress;

                if (audio.setVolume) {
                    audio.setVolume(newVolume);
                }

                if (progress < 1) {
                    requestAnimationFrame(animate);
                }
            };

            requestAnimationFrame(animate);
        } catch (error) {
            Logger.warn(`Fade in failed: ${error.message}`);
        }
    }

    fadeOut(audio, duration) {
        if (!audio || !audio.setVolume) return;

        try {
            const startTime = performance.now();
            const startVolume = audio.getVolume ? audio.getVolume() : 1;

            const animate = (currentTime) => {
                const elapsed = currentTime - startTime;
                const progress = Math.min(elapsed / (duration * 1000), 1);
                const newVolume = startVolume * (1 - progress);

                if (audio.setVolume) {
                    audio.setVolume(newVolume);
                }

                if (progress >= 1) {
                    if (audio.stop) audio.stop();
                } else {
                    requestAnimationFrame(animate);
                }
            };

            requestAnimationFrame(animate);
        } catch (error) {
            Logger.warn(`Fade out failed: ${error.message}`);
        }
    }

    setVolume(name, volume) {
        const audio = this.tracks[name];
        if (audio && audio.setVolume) {
            try {
                audio.setVolume(volume);
            } catch (error) {
                Logger.warn(`Could not set volume for ${name}`);
            }
        }
    }

    getVolume(name) {
        const audio = this.tracks[name];
        if (audio && audio.getVolume) {
            try {
                return audio.getVolume();
            } catch (error) {
                return 0;
            }
        }
        return 0;
    }

    dispose() {
        Object.values(this.tracks).forEach(audio => {
            try {
                if (audio && audio.isPlaying && audio.stop) {
                    audio.stop();
                }
            } catch (error) {
                Logger.warn('Error disposing audio');
            }
        });
    }
}

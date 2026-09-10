// Experience.js - Main VR experience controller
// Note: DEVELOPMENT_MODE, EXPERIENCE, and Logger are defined in config.js and loaded first

class Experience {
    constructor(canvas) {
        this.canvas = canvas;
        this.scene = null;
        this.camera = null;
        this.renderer = null;
        this.characterManager = null;
        this.environment = null;
        this.particleSystem = null;
        this.audioManager = null;
        this.timeline = null;

        this.isVR = false;
        this.textOverlay = null;
        this.fadePlane = null;
        this.fadeOutActive = false;

        this.debugInfo = null;

        this.init();
    }

    async init() {
        try {
            Logger.log('Initializing Experience...');

            this.setupThreeJS();
            Logger.log('✓ Three.js setup complete');

            await this.setupManagers();
            Logger.log('✓ Managers setup complete');

            await this.setupAudio();
            Logger.log('✓ Audio setup complete');

            this.setupVR();
            Logger.log('✓ VR setup complete');

            this.setupUI();
            Logger.log('✓ UI setup complete');

            this.checkWebXRSupport();
            Logger.log('Experience initialized successfully ✓');

            this.animate();
        } catch (error) {
            Logger.error('INITIALIZATION FAILED: ' + error.message);
            showErrorMessage('Initialization failed: ' + error.message);
        }
    }

    checkWebXRSupport() {
        if (navigator.xr) {
            navigator.xr.isSessionSupported('immersive-vr').then((supported) => {
                Logger.log(`WebXR immersive-vr support: ${supported}`);
            });
        } else {
            Logger.log('WebXR not available in this browser');
        }
    }

    setupThreeJS() {
        // Scene with dark background
        this.scene = new THREE.Scene();
        this.scene.background = new THREE.Color(0x000000);

        // Camera
        this.camera = new THREE.PerspectiveCamera(
            75,
            window.innerWidth / window.innerHeight,
            0.1,
            1000
        );
        this.camera.position.set(0, 1.6, 0);

        // Renderer with proper settings
        this.renderer = new THREE.WebGLRenderer({
            canvas: this.canvas,
            antialias: true,
            alpha: false,
            logarithmicDepthBuffer: true
        });

        this.renderer.setSize(window.innerWidth, window.innerHeight);
        this.renderer.setPixelRatio(Math.min(window.devicePixelRatio, 2));
        this.renderer.shadowMap.enabled = true;
        this.renderer.shadowMap.type = THREE.PCFShadowShadowMap;
        this.renderer.shadowMap.resolution = 2048;
        this.renderer.xr.enabled = true;
        this.renderer.tone = THREE.ACESFilmicToneMapping;
        this.renderer.toneMappingExposure = 1.2;

        // Audio listener
        this.audioListener = new THREE.AudioListener();
        this.camera.add(this.audioListener);

        window.addEventListener('resize', () => this.onWindowResize());

        Logger.log('Three.js setup complete');
    }

    async setupManagers() {
        try {
            Logger.log('Setting up character manager...');
            this.characterManager = new CharacterManager(this.scene);
            await this.characterManager.loadCharacter('girl', EXPERIENCE.characterModels.girl);
            await this.characterManager.loadCharacter('man', EXPERIENCE.characterModels.man);
            Logger.log('✓ Characters loaded');

            Logger.log('Setting up environment manager...');
            this.environment = new EnvironmentManager(this.scene, this.camera);
            this.environment.createDarkEnvironment();
            Logger.log('✓ Environment created');

            Logger.log('Setting up particle system...');
            this.particleSystem = new ParticleSystem(this.scene, this.camera, 5000);
            Logger.log('✓ Particle system ready');

            Logger.log('Setting up timeline...');
            this.timeline = new Timeline(this);
            Logger.log('✓ Timeline configured');
        } catch (error) {
            Logger.error('setupManagers error: ' + error.message);
            throw error;
        }
    }

    async setupAudio() {
        Logger.log('Initializing audio...');
        this.audioManager = new AudioManager(this.audioListener);
        await this.audioManager.init();

        for (const [name, path] of Object.entries(EXPERIENCE.audioFiles)) {
            const loaded = await this.audioManager.loadAudio(name, path);
            if (loaded) {
                Logger.log(`Audio loaded: ${name}`);
            }
        }
    }

    setupVR() {
        if (navigator.xr) {
            navigator.xr.isSessionSupported('immersive-vr').then((supported) => {
                if (supported) {
                    document.getElementById('vrButton').style.display = 'inline-block';
                    document.getElementById('vrButton').addEventListener('click', () => this.enterVR());
                    Logger.log('VR button enabled');
                }
            });
        }
    }

    setupUI() {
        const fadeGeometry = new THREE.PlaneGeometry(100, 100);
        const fadeMaterial = new THREE.MeshBasicMaterial({
            color: 0x000000,
            transparent: true,
            opacity: 0
        });
        this.fadePlane = new THREE.Mesh(fadeGeometry, fadeMaterial);
        this.fadePlane.position.z = -10;
        this.scene.add(this.fadePlane);

        this.createTextOverlay();
        this.createDevDebugDisplay();
    }

    createTextOverlay() {
        const canvas = document.createElement('canvas');
        canvas.width = 2048;
        canvas.height = 1024;
        const ctx = canvas.getContext('2d');

        const texture = new THREE.CanvasTexture(canvas);
        const material = new THREE.MeshBasicMaterial({
            map: texture,
            transparent: true,
            emissive: 0xffd700,
            emissiveMap: texture
        });

        const geometry = new THREE.PlaneGeometry(20, 10);
        this.textOverlay = new THREE.Mesh(geometry, material);
        this.textOverlay.position.set(0, 0, -15);
        this.textOverlay.visible = false;
        this.scene.add(this.textOverlay);

        this.textCanvas = canvas;
        this.textContext = ctx;
        this.textTexture = texture;
    }

    createDevDebugDisplay() {
        if (!DEVELOPMENT_MODE || this.isVR) return;

        const debugDiv = document.createElement('div');
        debugDiv.id = 'debugInfo';
        debugDiv.style.cssText = `
            position: fixed;
            top: 10px;
            left: 10px;
            background: rgba(0, 0, 0, 0.7);
            color: #0f0;
            font-family: monospace;
            font-size: 11px;
            padding: 10px;
            border: 1px solid #0f0;
            max-width: 300px;
            z-index: 999;
            pointer-events: none;
            line-height: 1.4;
        `;
        document.body.appendChild(debugDiv);
        this.debugInfo = debugDiv;
    }

    updateDebugDisplay() {
        if (!this.debugInfo) return;

        const info = [
            `FPS: ${Math.round(1000 / 16)}`,
            `Timeline: ${Math.round(this.timeline?.currentTime || 0)}s / ${this.timeline?.duration || 75}s`,
            `Characters: ${Object.keys(this.characterManager?.characters || {}).length}`,
            `Particles: ${this.particleSystem?.particles?.length || 0}`,
            `VR: ${this.isVR ? 'Yes' : 'No'}`
        ];

        this.debugInfo.innerHTML = info.join('<br>');
    }

    displayText(text, duration) {
        if (!this.textCanvas) return;

        const ctx = this.textContext;
        ctx.clearRect(0, 0, this.textCanvas.width, this.textCanvas.height);

        // Gradient text
        const gradient = ctx.createLinearGradient(0, 0, this.textCanvas.width, this.textCanvas.height);
        gradient.addColorStop(0, '#FFD700');
        gradient.addColorStop(1, '#FFA500');

        ctx.fillStyle = gradient;
        ctx.font = 'bold 100px "Segoe UI", Arial, sans-serif';
        ctx.textAlign = 'center';
        ctx.textBaseline = 'middle';
        ctx.shadowColor = 'rgba(255, 215, 0, 0.3)';
        ctx.shadowBlur = 30;

        const lines = text.split('\n');
        const lineHeight = 140;
        const totalHeight = lines.length * lineHeight;
        const startY = (this.textCanvas.height - totalHeight) / 2;

        lines.forEach((line, index) => {
            const y = startY + index * lineHeight + lineHeight / 2;
            ctx.fillText(line, this.textCanvas.width / 2, y);
        });

        this.textTexture.needsUpdate = true;
        this.textOverlay.visible = true;

        setTimeout(() => {
            this.textOverlay.visible = false;
        }, duration * 1000);
    }

    startBirthdayTextSequence() {
        this.particleSystem.emit({
            position: new THREE.Vector3(0, 0, -15),
            velocity: new THREE.Vector3(0, 1, 0),
            color: new THREE.Color(1.0, 0.84, 0.0),
            lifetime: 4,
            count: 150,
            spread: 8
        });
    }

    onWarmLightIntensify() {
        Logger.log('Intensifying warm light');
    }

    onHandsTouch() {
        Logger.log('Hands touched - emitting golden pulse');
        this.onGoldenPulse();
    }

    onGoldenPulse() {
        for (let i = 0; i < 3; i++) {
            setTimeout(() => {
                this.particleSystem.emitWave({
                    startPosition: new THREE.Vector3(0, 0.5, -3),
                    waveDirection: new THREE.Vector3(0, 1, 0),
                    radius: 3 + i * 2,
                    particleCount: 100,
                    lifetime: 2.5,
                    speed: 2 + i * 1
                });
            }, i * 200);
        }
    }

    startEnvironmentTransformation() {
        Logger.log('Starting environment transformation');
        this.particleSystem.emitWave({
            startPosition: new THREE.Vector3(0, 0, -3),
            waveDirection: new THREE.Vector3(0, 0.5, 0),
            radius: 4,
            particleCount: 200,
            lifetime: 3,
            speed: 2.5
        });

        for (let i = 1; i <= 4; i++) {
            setTimeout(() => {
                this.particleSystem.emitWave({
                    startPosition: new THREE.Vector3(0, 0, -3),
                    waveDirection: new THREE.Vector3(0, 1, 0),
                    radius: 5 + i * 4,
                    particleCount: 120,
                    lifetime: 3,
                    speed: 1.5 + i * 0.3
                });
            }, i * 600);
        }
    }

    animateCharacterMovement(characterName, startPos, endPos, duration) {
        const character = this.characterManager.getCharacter(characterName);
        if (!character || !character.model) return;

        const startTime = performance.now();

        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / (duration * 1000), 1);

            character.model.position.lerpVectors(startPos, endPos, progress);

            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };

        requestAnimationFrame(animate);
    }

    fadeToBlack(duration = 3) {
        if (!this.fadePlane) return;

        this.fadeOutActive = true;
        const startTime = performance.now();

        const animate = (currentTime) => {
            const elapsed = currentTime - startTime;
            const progress = Math.min(elapsed / (duration * 1000), 1);

            this.fadePlane.material.opacity = progress;

            if (progress < 1) {
                requestAnimationFrame(animate);
            }
        };

        requestAnimationFrame(animate);
    }

    startExperience() {
        if (!this.timeline) {
            Logger.error('Timeline not initialized');
            showErrorMessage('Timeline failed to initialize');
            return;
        }

        try {
            Logger.log('Starting experience...');

            if (this.audioManager && this.audioManager.audioContext) {
                if (this.audioManager.audioContext.state === 'suspended') {
                    this.audioManager.audioContext.resume().catch(() => {
                        Logger.warn('Audio context resume failed');
                    });
                }
            }

            document.getElementById('startScreen').classList.add('hidden');
            this.timeline.play();
        } catch (error) {
            Logger.error('Error starting experience: ' + error.message);
            showErrorMessage('Failed to start experience: ' + error.message);
        }
    }

    async enterVR() {
        if (!navigator.xr) return;

        try {
            Logger.log('Requesting WebXR immersive-vr session...');
            const session = await navigator.xr.requestSession('immersive-vr', {
                requiredFeatures: ['local-floor'],
                optionalFeatures: ['hand-tracking', 'dom-overlay'],
                domOverlay: { root: document.body }
            });

            this.renderer.xr.setSession(session);
            this.isVR = true;
            Logger.log('VR session started');
            this.startExperience();
        } catch (e) {
            Logger.error(`VR error: ${e.message}`);
            alert('Could not start VR. Try using Meta Quest Browser.');
        }
    }

    onWindowResize() {
        this.camera.aspect = window.innerWidth / window.innerHeight;
        this.camera.updateProjectionMatrix();
        this.renderer.setSize(window.innerWidth, window.innerHeight);
    }

    animate() {
        const deltaTime = 0.016;

        this.renderer.setAnimationLoop(() => {
            if (this.audioListener) {
                this.audioListener.position.copy(this.camera.position);
            }

            if (this.timeline) {
                this.timeline.update(deltaTime);
            }

            if (this.characterManager) {
                this.characterManager.updateAnimations(deltaTime);
            }

            if (this.particleSystem) {
                this.particleSystem.update(deltaTime);
            }

            if (DEVELOPMENT_MODE && !this.isVR) {
                this.updateDebugDisplay();
            }

            this.renderer.render(this.scene, this.camera);
        });
    }

    dispose() {
        if (this.characterManager) this.characterManager.dispose();
        if (this.environment) this.environment.dispose();
        if (this.particleSystem) this.particleSystem.dispose();
        if (this.audioManager) this.audioManager.dispose();
        if (this.renderer) this.renderer.dispose();
    }
}

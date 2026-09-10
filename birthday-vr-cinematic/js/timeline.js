class Timeline {
    constructor(experience) {
        this.experience = experience;
        this.isPlaying = false;
        this.currentTime = 0;
        this.duration = 75;
        this.events = [];
        this.completedEvents = new Set();
        this.setupTimeline();
    }

    setupTimeline() {
        Logger.log('Setting up timeline...');

        // SCENE 1: THE DARKNESS (0-10s)
        this.addEvent(0, 'scene1Start', () => {
            Logger.log('=== SCENE 1: THE DARKNESS (0s) ===');
            this.experience.environment.switchToDarkEnvironment();
            this.experience.audioManager.playSound('darkAmbience', {
                loop: true,
                volume: 0.3,
                fadeInDuration: 1
            });
        });

        this.addEvent(0.5, 'girlSitDown', () => {
            Logger.log('Girl sits down (0.5s)');
            const girl = this.experience.characterManager.getCharacter('girl');
            if (girl && girl.model) {
                girl.model.position.set(0, 0, -5);
                this.experience.characterManager.playAnimation('girl', 'SittingSad', {
                    loop: THREE.LoopOnce,
                    clampWhenFinished: true
                });
            }
        });

        this.addEvent(1.5, 'voiceOver1', () => {
            Logger.log('Voice over begins (1.5s)');
            this.experience.audioManager.playSound('voiceOver', {
                volume: 0.8,
                fadeInDuration: 0.5
            });
        });

        // SCENE 2: THEN YOU CAME (10-22s)
        this.addEvent(10, 'scene2Start', () => {
            Logger.log('=== SCENE 2: THEN YOU CAME (10s) ===');
            this.experience.audioManager.playSound('footsteps', {
                volume: 0.5,
                position: new THREE.Vector3(3, 0, -8)
            });
        });

        this.addEvent(10.5, 'manAppears', () => {
            Logger.log('Man enters (10.5s)');
            const man = this.experience.characterManager.getCharacter('man');
            if (man && man.model) {
                man.model.position.set(4, 0, -12);
                this.experience.characterManager.playAnimation('man', 'WalkIn', {
                    loop: THREE.LoopOnce,
                    clampWhenFinished: true
                });
            }
        });

        this.addEvent(11, 'voiceOver2', () => {
            Logger.log('Voice over continues (11s)');
        });

        this.addEvent(12, 'pianoMusicStarts', () => {
            Logger.log('Piano music begins (12s)');
            this.experience.audioManager.playSound('pianoMusic', {
                loop: false,
                volume: 0.6,
                fadeInDuration: 1.5
            });
        });

        this.addEvent(15, 'manWalksToGirl', () => {
            Logger.log('Man walks toward girl (15s)');
            this.experience.characterManager.playAnimation('man', 'Walk', {
                loop: true
            });
            this.experience.animateCharacterMovement('man',
                new THREE.Vector3(4, 0, -12),
                new THREE.Vector3(0.3, 0, -3.5),
                4
            );
        });

        // SCENE 3: THE HAND (22-36s)
        this.addEvent(22, 'scene3Start', () => {
            Logger.log('=== SCENE 3: THE HAND (22s) ===');
            this.experience.characterManager.stopAnimation('man');
            this.experience.characterManager.playAnimation('man', 'Idle', {
                loop: true
            });
        });

        this.addEvent(23, 'girlLooksUp', () => {
            Logger.log('Girl looks up (23s)');
            this.experience.characterManager.playAnimation('girl', 'LookUp', {
                loop: THREE.LoopOnce,
                clampWhenFinished: true
            });
        });

        this.addEvent(25, 'manReachesHand', () => {
            Logger.log('Man reaches hand (25s)');
            this.experience.characterManager.playAnimation('man', 'ReachHand', {
                loop: THREE.LoopOnce,
                clampWhenFinished: true
            });
        });

        this.addEvent(27, 'girlReachesHand', () => {
            Logger.log('Girl reaches hand (27s)');
            this.experience.characterManager.playAnimation('girl', 'ReachHand', {
                loop: THREE.LoopOnce,
                clampWhenFinished: true
            });
        });

        this.addEvent(31, 'handsTouchMoment', () => {
            Logger.log('💫 HANDS TOUCH - GOLDEN PULSE (31s) 💫');
            this.experience.onHandsTouch();

            this.experience.audioManager.playSound('lightWhoosh', {
                volume: 0.7
            });

            this.experience.particleSystem.emitWave({
                startPosition: new THREE.Vector3(0, 0.5, -3.5),
                waveDirection: new THREE.Vector3(0, 1, 0),
                radius: 2.5,
                particleCount: 150,
                lifetime: 2,
                speed: 3
            });

            this.experience.onGoldenPulse();
        });

        this.addEvent(32, 'voiceOver3', () => {
            Logger.log('Emotional voice over (32s)');
        });

        this.addEvent(34, 'girlStandsUp', () => {
            Logger.log('Girl stands up (34s)');
            this.experience.characterManager.playAnimation('girl', 'StandUp', {
                loop: THREE.LoopOnce,
                clampWhenFinished: true
            });
        });

        // SCENE 4: TRANSFORMATION (36-50s)
        this.addEvent(36, 'scene4Start', () => {
            Logger.log('=== SCENE 4: TRANSFORMATION (36s) ===');
            this.experience.startEnvironmentTransformation();
        });

        this.addEvent(38, 'voiceOver4', () => {
            Logger.log('Transformation voice over (38s)');
        });

        this.addEvent(41, 'switchToLightEnvironment', () => {
            Logger.log('🌅 ENVIRONMENT TRANSFORMS TO LIGHT (41s) 🌅');
            this.experience.environment.switchToLightEnvironment();
            this.experience.audioManager.stopSound('darkAmbience', 1);
            this.experience.audioManager.playSound('natureAmbience', {
                loop: true,
                volume: 0.3,
                fadeInDuration: 1.5
            });
        });

        this.addEvent(45, 'transformationComplete', () => {
            Logger.log('Transformation complete, magical particles (45s)');
            this.experience.particleSystem.emit({
                position: new THREE.Vector3(0, 3, 0),
                velocity: new THREE.Vector3(0, 1, 0),
                color: new THREE.Color(1.0, 0.84, 0.0),
                lifetime: 3,
                count: 80,
                spread: 12
            });
        });

        // SCENE 5: WHAT YOU MEAN (50-61s)
        this.addEvent(50, 'scene5Start', () => {
            Logger.log('=== SCENE 5: WHAT YOU MEAN (50s) ===');
            this.experience.characterManager.playAnimation('girl', 'Walk', {
                loop: true
            });
            this.experience.characterManager.playAnimation('man', 'WalkTogether', {
                loop: true
            });

            this.experience.animateCharacterMovement('girl',
                new THREE.Vector3(0.3, 0, -3.5),
                new THREE.Vector3(-6, 0, 20),
                4
            );

            this.experience.animateCharacterMovement('man',
                new THREE.Vector3(0.3, 0, -3.5),
                new THREE.Vector3(6, 0, 20),
                4
            );
        });

        this.addEvent(52, 'voiceOver5', () => {
            Logger.log('Birthday gratitude voice over (52s)');
        });

        // SCENE 6: HAPPY BIRTHDAY (61-72s)
        this.addEvent(61, 'scene6Start', () => {
            Logger.log('=== SCENE 6: HAPPY BIRTHDAY (61s) ===');
            this.experience.startBirthdayTextSequence();
        });

        this.addEvent(62, 'displayBirthdayText', () => {
            Logger.log('Displaying: HAPPY BIRTHDAY (62s)');
            this.experience.displayText('HAPPY BIRTHDAY', 3);
        });

        this.addEvent(65.5, 'displayThanksText', () => {
            Logger.log('Displaying: Thank you message (65.5s)');
            this.experience.displayText('Thank you for being there.', 2.5);
        });

        this.addEvent(68, 'displayMoreThanksText', () => {
            Logger.log('Displaying: More thanks (68s)');
            this.experience.displayText('Thank you for everything you\'ve done for me.', 2.5);
        });

        this.addEvent(70.5, 'displayImportanceText', () => {
            Logger.log('Displaying: Importance message (70.5s)');
            this.experience.displayText('You mean more to me than words can explain.', 3);
        });

        this.addEvent(73.5, 'displayFinalMessage', () => {
            Logger.log('Displaying: Final message (73.5s)');
            this.experience.displayText(
                'May life give back to you\nall the light you have given me.',
                4
            );
        });

        // FADE OUT
        this.addEvent(76, 'fadeToBlack', () => {
            Logger.log('Fading to black (76s)');
            this.experience.fadeToBlack(2);
            this.experience.audioManager.fadeOut('pianoMusic', 2);
        });

        this.addEvent(78, 'experienceEnd', () => {
            Logger.log('=== EXPERIENCE COMPLETE ===');
            this.isPlaying = false;
        });

        Logger.log('✓ Timeline setup complete');
    }

    addEvent(time, id, callback) {
        this.events.push({
            time: time,
            id: id,
            callback: callback,
            triggered: false
        });

        this.events.sort((a, b) => a.time - b.time);
    }

    play() {
        this.isPlaying = true;
        this.currentTime = 0;
        this.completedEvents.clear();
        Logger.log('▶️  Timeline playing');
    }

    pause() {
        this.isPlaying = false;
        Logger.log('⏸️  Timeline paused');
    }

    update(deltaTime) {
        if (!this.isPlaying) return;

        this.currentTime += deltaTime;

        this.events.forEach(event => {
            if (!event.triggered && this.currentTime >= event.time) {
                event.triggered = true;
                event.callback();
                this.completedEvents.add(event.id);
            }
        });

        if (this.currentTime >= this.duration) {
            this.isPlaying = false;
        }
    }

    reset() {
        this.currentTime = 0;
        this.isPlaying = false;
        this.completedEvents.clear();
        this.events.forEach(event => {
            event.triggered = false;
        });
        Logger.log('Timeline reset');
    }

    getProgress() {
        return Math.min(this.currentTime / this.duration, 1);
    }
}

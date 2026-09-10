class CharacterManager {
    constructor(scene) {
        this.scene = scene;
        this.characters = {};
        this.gltfLoader = new THREE.GLTFLoader();
    }

    async loadCharacter(name, modelPath) {
        try {
            Logger.log(`Loading character: ${name} from ${modelPath}`);
            const gltf = await this.gltfLoader.loadAsync(modelPath);
            const model = gltf.scene;

            model.castShadow = true;
            model.receiveShadow = true;
            model.traverse((child) => {
                if (child.isMesh) {
                    child.castShadow = true;
                    child.receiveShadow = true;
                }
            });

            const mixer = new THREE.AnimationMixer(model);
            const animations = {};
            const actions = {};

            if (gltf.animations && gltf.animations.length > 0) {
                gltf.animations.forEach((clip) => {
                    animations[clip.name] = clip;
                    Logger.log(`  Animation: ${clip.name}`);
                });
            }

            this.scene.add(model);

            this.characters[name] = {
                model: model,
                mixer: mixer,
                animations: animations,
                actions: actions,
                currentAnimation: null,
                isProceduralModel: false
            };

            Logger.log(`✓ Character loaded: ${name}`);
            return this.characters[name];
        } catch (error) {
            Logger.warn(`Could not load ${name} from ${modelPath}. Using placeholder silhouette.`);
            return this.createPlaceholderSilhouette(name);
        }
    }

    createPlaceholderSilhouette(name) {
        Logger.log(`Creating placeholder silhouette for: ${name}`);

        const group = new THREE.Group();
        const mixer = new THREE.AnimationMixer(group);

        const isGirl = name === 'girl';

        // Material for silhouette - ghosted/translucent
        const silhouetteMaterial = new THREE.MeshStandardMaterial({
            color: 0x1a1a2e,
            metalness: 0.0,
            roughness: 1.0,
            transparent: true,
            opacity: 0.4,
            emissive: 0x0a0a14,
            side: THREE.DoubleSide
        });

        // Simple head shape
        const headGeometry = new THREE.SphereGeometry(0.15, 16, 16);
        const head = new THREE.Mesh(headGeometry, silhouetteMaterial);
        head.position.y = 1.5;
        head.castShadow = true;

        // Body
        const bodyGeometry = new THREE.CylinderGeometry(0.12, 0.11, 0.5, 12);
        const body = new THREE.Mesh(bodyGeometry, silhouetteMaterial);
        body.position.y = 0.75;
        body.castShadow = true;

        // Arms
        const armGeometry = new THREE.CylinderGeometry(0.04, 0.038, 0.5, 8);
        const leftArm = new THREE.Mesh(armGeometry, silhouetteMaterial);
        leftArm.position.set(-0.16, 1.0, 0);
        leftArm.castShadow = true;

        const rightArm = new THREE.Mesh(armGeometry, silhouetteMaterial);
        rightArm.position.set(0.16, 1.0, 0);
        rightArm.castShadow = true;

        // Legs
        const legGeometry = new THREE.CylinderGeometry(0.045, 0.042, 0.5, 8);
        const leftLeg = new THREE.Mesh(legGeometry, silhouetteMaterial);
        leftLeg.position.set(-0.07, 0.25, 0);
        leftLeg.castShadow = true;

        const rightLeg = new THREE.Mesh(legGeometry, silhouetteMaterial);
        rightLeg.position.set(0.07, 0.25, 0);
        rightLeg.castShadow = true;

        group.add(head);
        group.add(body);
        group.add(leftArm);
        group.add(rightArm);
        group.add(leftLeg);
        group.add(rightLeg);

        group.castShadow = true;
        group.receiveShadow = true;

        // Store bones for animation
        group.bones = {
            head, body, leftArm, rightArm, leftLeg, rightLeg
        };

        this.scene.add(group);

        const character = {
            model: group,
            mixer: mixer,
            animations: this.createBasicAnimations(group, isGirl),
            actions: {},
            currentAnimation: null,
            isPlaceholder: true
        };

        this.characters[name] = character;

        // Show console message about missing asset
        Logger.warn(`═══════════════════════════════════════════`);
        Logger.warn(`Professional ${name}.glb REQUIRED`);
        Logger.warn(`═══════════════════════════════════════════`);
        Logger.warn(`Place a high-quality animated GLB/GLTF model at:`);
        Logger.warn(`  assets/models/${name}.glb`);
        Logger.warn(`═══════════════════════════════════════════`);

        return character;
    }

    createBasicAnimations(model, isGirl) {
        const animations = {};

        // Simple standing animation
        const standTrack = new THREE.VectorKeyframeTrack(
            '.bones.body.position',
            [0, 1],
            [0, 0.75, 0, 0, 0.75, 0]
        );
        animations['Idle'] = new THREE.AnimationClip('Idle', 1, [standTrack]);
        animations['IdleHappy'] = new THREE.AnimationClip('IdleHappy', 1, [standTrack]);
        animations['Walk'] = new THREE.AnimationClip('Walk', 1, [standTrack]);
        animations['WalkIn'] = new THREE.AnimationClip('WalkIn', 1, [standTrack]);
        animations['WalkTogether'] = new THREE.AnimationClip('WalkTogether', 1, [standTrack]);

        if (isGirl) {
            animations['SittingSad'] = new THREE.AnimationClip('SittingSad', 1, [
                new THREE.VectorKeyframeTrack('.bones.body.position', [0, 1], [0, 0.3, 0, 0, 0.3, 0])
            ]);
            animations['LookUp'] = new THREE.AnimationClip('LookUp', 1, [standTrack]);
            animations['ReachHand'] = new THREE.AnimationClip('ReachHand', 1, [standTrack]);
            animations['StandUp'] = new THREE.AnimationClip('StandUp', 1, [standTrack]);
        } else {
            animations['ReachHand'] = new THREE.AnimationClip('ReachHand', 1, [standTrack]);
            animations['Helping'] = new THREE.AnimationClip('Helping', 1, [standTrack]);
        }

        return animations;
    }

    playAnimation(characterName, animationName, options = {}) {
        const character = this.characters[characterName];
        if (!character) return null;

        const { loop = THREE.LoopOnce, clampWhenFinished = true } = options;

        if (character.animations[animationName]) {
            const clip = character.animations[animationName];
            const action = character.mixer.clipAction(clip);

            action.loop = loop;
            action.clampWhenFinished = clampWhenFinished;

            if (character.currentAnimation) {
                character.currentAnimation.stop();
            }

            character.currentAnimation = action;
            action.play();

            Logger.log(`Playing animation: ${characterName}.${animationName}`);
            return action;
        }

        return null;
    }

    stopAnimation(characterName) {
        const character = this.characters[characterName];
        if (character && character.currentAnimation) {
            character.currentAnimation.stop();
            character.currentAnimation = null;
        }
    }

    updateAnimations(deltaTime) {
        Object.values(this.characters).forEach(character => {
            if (character.mixer) {
                character.mixer.update(deltaTime);
            }
        });
    }

    getCharacter(name) {
        return this.characters[name];
    }

    dispose() {
        Object.values(this.characters).forEach(character => {
            if (character.mixer) {
                character.mixer.stopAllAction();
            }
            if (character.model) {
                character.model.traverse(child => {
                    if (child.geometry) child.geometry.dispose();
                    if (child.material) {
                        if (Array.isArray(child.material)) {
                            child.material.forEach(m => m.dispose());
                        } else {
                            child.material.dispose();
                        }
                    }
                });
            }
        });
    }
}

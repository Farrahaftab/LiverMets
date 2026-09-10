class EnvironmentManager {
    constructor(scene, camera) {
        this.scene = scene;
        this.camera = camera;
        this.darkEnvironment = null;
        this.lightEnvironment = null;
        this.currentEnvironment = null;
    }

    createDarkEnvironment() {
        Logger.log('Creating dark cinematic environment...');
        const env = new THREE.Group();

        // Fog for atmospheric depth
        this.scene.fog = new THREE.Fog(0x0a0e1a, 0.5, 80);

        // Floor - very subtle
        const floorGeometry = new THREE.PlaneGeometry(200, 200);
        const floorMaterial = new THREE.MeshStandardMaterial({
            color: 0x050508,
            metalness: 0.0,
            roughness: 0.95,
            side: THREE.FrontSide
        });
        const floor = new THREE.Mesh(floorGeometry, floorMaterial);
        floor.rotation.x = -Math.PI / 2;
        floor.receiveShadow = true;
        floor.position.y = -0.01;
        env.add(floor);

        // Ceiling (subtle)
        const ceilingGeometry = new THREE.PlaneGeometry(200, 200);
        const ceilingMaterial = new THREE.MeshStandardMaterial({
            color: 0x0a0a14,
            metalness: 0.0,
            roughness: 1.0,
            emissive: 0x050508
        });
        const ceiling = new THREE.Mesh(ceilingGeometry, ceilingMaterial);
        ceiling.rotation.x = Math.PI / 2;
        ceiling.position.y = 4;
        env.add(ceiling);

        // Volumetric-like lighting with hemisphere
        const hemisphereLight = new THREE.HemisphereLight(0x0a1a3a, 0x000000, 0.15);
        env.add(hemisphereLight);

        // Subtle rim light from above
        const rimLight = new THREE.DirectionalLight(0x1a2a4a, 0.25);
        rimLight.position.set(20, 10, 15);
        rimLight.target.position.set(0, 0, 0);
        env.add(rimLight);

        // Soft back light
        const backLight = new THREE.DirectionalLight(0x0a1a2a, 0.15);
        backLight.position.set(-15, 8, -20);
        env.add(backLight);

        // Ambient color-graded for emotional depth
        const ambientLight = new THREE.AmbientLight(0x0a1a2e, 0.1);
        env.add(ambientLight);

        this.darkEnvironment = env;
        this.scene.add(env);

        Logger.log('✓ Dark environment created');
        return env;
    }

    createLightEnvironment() {
        Logger.log('Creating light golden-hour environment...');
        const env = new THREE.Group();

        // Fog for atmospheric haze
        this.scene.fog = new THREE.Fog(0xf4d4b8, 40, 250);

        // Ground - grass-like
        const groundGeometry = new THREE.PlaneGeometry(400, 400);
        const groundMaterial = new THREE.MeshStandardMaterial({
            color: 0x5a8c3a,
            metalness: 0.0,
            roughness: 0.85,
            map: this.createGrassTexture()
        });
        const ground = new THREE.Mesh(groundGeometry, groundMaterial);
        ground.rotation.x = -Math.PI / 2;
        ground.receiveShadow = true;
        env.add(ground);

        // Gentle terrain variation
        const hillGeometry = new THREE.PlaneGeometry(500, 500, 15, 15);
        const positions = hillGeometry.attributes.position.array;
        for (let i = 2; i < positions.length; i += 3) {
            const x = positions[i - 2] * 0.01;
            const z = positions[i - 1] * 0.01;
            positions[i] = Math.sin(x) * Math.cos(z) * 3 + Math.sin(z * 0.5) * 2;
        }
        hillGeometry.attributes.position.needsUpdate = true;
        hillGeometry.computeVertexNormals();

        const hillMaterial = new THREE.MeshStandardMaterial({
            color: 0x6b9d45,
            metalness: 0.0,
            roughness: 0.85
        });
        const hills = new THREE.Mesh(hillGeometry, hillMaterial);
        hills.rotation.x = -Math.PI / 2;
        hills.position.y = 0.01;
        hills.receiveShadow = true;
        env.add(hills);

        // Water body
        const waterGeometry = new THREE.PlaneGeometry(200, 150);
        const waterMaterial = new THREE.MeshStandardMaterial({
            color: 0x1e4b7f,
            metalness: 0.7,
            roughness: 0.2,
            emissive: 0x2a5a8f,
            emissiveIntensity: 0.3
        });
        const water = new THREE.Mesh(waterGeometry, waterMaterial);
        water.rotation.x = -Math.PI / 2;
        water.position.set(80, 0.02, -50);
        water.receiveShadow = true;
        env.add(water);

        // Flowers scattered beautifully
        this.addFlowers(env, 150);

        // Distant mountains
        this.addMountains(env);

        // Sky - gradient sphere
        const skyGeometry = new THREE.SphereGeometry(500, 32, 32);
        const skyMaterial = new THREE.MeshBasicMaterial({
            side: THREE.BackSide
        });

        const canvas = document.createElement('canvas');
        canvas.width = 512;
        canvas.height = 512;
        const ctx = canvas.getContext('2d');

        // Golden hour gradient
        const gradient = ctx.createLinearGradient(0, 0, 0, 512);
        gradient.addColorStop(0.0, '#f4a869');
        gradient.addColorStop(0.3, '#f8c68f');
        gradient.addColorStop(0.5, '#fde5a8');
        gradient.addColorStop(0.7, '#e8d4b0');
        gradient.addColorStop(1.0, '#a8c5e8');
        ctx.fillStyle = gradient;
        ctx.fillRect(0, 0, 512, 512);

        const skyTexture = new THREE.CanvasTexture(canvas);
        skyMaterial.map = skyTexture;

        const sky = new THREE.Mesh(skyGeometry, skyMaterial);
        env.add(sky);

        // Main directional light - warm sunset
        const sunLight = new THREE.DirectionalLight(0xffd89b, 1.8);
        sunLight.position.set(-60, 80, 50);
        sunLight.castShadow = true;
        sunLight.shadow.mapSize.width = 4096;
        sunLight.shadow.mapSize.height = 4096;
        sunLight.shadow.camera.left = -150;
        sunLight.shadow.camera.right = 150;
        sunLight.shadow.camera.top = 150;
        sunLight.shadow.camera.bottom = -150;
        sunLight.shadow.camera.far = 300;
        sunLight.shadow.bias = -0.0005;
        env.add(sunLight);

        // Fill light - cool tones
        const fillLight = new THREE.DirectionalLight(0xb8d5f8, 0.5);
        fillLight.position.set(80, 40, -60);
        env.add(fillLight);

        // Rim light - subtle glow
        const rimLight = new THREE.DirectionalLight(0xffe0b0, 0.3);
        rimLight.position.set(-50, 20, -80);
        env.add(rimLight);

        // Ambient light
        const ambientLight = new THREE.AmbientLight(0xf5e6d3, 0.5);
        env.add(ambientLight);

        this.lightEnvironment = env;

        Logger.log('✓ Light environment created');
        return env;
    }

    createGrassTexture() {
        const canvas = document.createElement('canvas');
        canvas.width = 256;
        canvas.height = 256;
        const ctx = canvas.getContext('2d');

        // Base grass color
        ctx.fillStyle = '#5a8c3a';
        ctx.fillRect(0, 0, 256, 256);

        // Add subtle grass patterns
        for (let i = 0; i < 5000; i++) {
            const x = Math.random() * 256;
            const y = Math.random() * 256;
            const brightness = Math.random() > 0.7 ? 0.3 : -0.2;

            ctx.fillStyle = `rgba(0, 0, 0, ${Math.random() * 0.1 + brightness})`;
            ctx.fillRect(x, y, 2, 1);
        }

        const texture = new THREE.CanvasTexture(canvas);
        texture.wrapS = THREE.RepeatWrapping;
        texture.wrapT = THREE.RepeatWrapping;
        texture.repeat.set(4, 4);
        return texture;
    }

    addFlowers(env, count) {
        const flowerColors = [0xff6b9d, 0xffc0d9, 0xff8fab, 0xffb3d9, 0xffe0ec, 0xff6ba8];

        for (let i = 0; i < count; i++) {
            const x = (Math.random() - 0.5) * 350;
            const z = (Math.random() - 0.5) * 350;

            // Skip water area
            if (Math.abs(x - 80) < 100 && Math.abs(z + 50) < 75) continue;

            const petals = Math.floor(Math.random() * 4) + 5;
            const flowerGroup = new THREE.Group();

            // Stem
            const stemGeometry = new THREE.CylinderGeometry(0.04, 0.04, 0.7, 6);
            const stemMaterial = new THREE.MeshStandardMaterial({
                color: 0x3a6b2c,
                metalness: 0.0,
                roughness: 0.8
            });
            const stem = new THREE.Mesh(stemGeometry, stemMaterial);
            stem.position.y = 0.35;
            stem.castShadow = true;
            flowerGroup.add(stem);

            // Petals
            const color = new THREE.Color(flowerColors[Math.floor(Math.random() * flowerColors.length)]);
            for (let p = 0; p < petals; p++) {
                const angle = (p / petals) * Math.PI * 2;
                const petalGeometry = new THREE.SphereGeometry(0.09, 8, 8);
                const petalMaterial = new THREE.MeshStandardMaterial({
                    color: color,
                    metalness: 0.0,
                    roughness: 0.5,
                    emissive: new THREE.Color().copy(color).multiplyScalar(0.2)
                });
                const petal = new THREE.Mesh(petalGeometry, petalMaterial);
                petal.position.set(Math.cos(angle) * 0.14, 0.7, Math.sin(angle) * 0.14);
                petal.castShadow = true;
                flowerGroup.add(petal);
            }

            // Center
            const centerGeometry = new THREE.SphereGeometry(0.045, 8, 8);
            const centerMaterial = new THREE.MeshStandardMaterial({
                color: 0xffeb3b,
                metalness: 0.1,
                roughness: 0.4,
                emissive: 0xffd700,
                emissiveIntensity: 0.5
            });
            const center = new THREE.Mesh(centerGeometry, centerMaterial);
            center.position.y = 0.7;
            center.castShadow = true;
            flowerGroup.add(center);

            flowerGroup.position.set(x, 0, z);
            flowerGroup.castShadow = true;
            env.add(flowerGroup);
        }
    }

    addMountains(env) {
        const mountainGeometry = new THREE.ConeGeometry(100, 150, 32);
        const mountainMaterial = new THREE.MeshStandardMaterial({
            color: 0x8b9fb5,
            metalness: 0.0,
            roughness: 0.95,
            emissive: 0x7a8fa3,
            emissiveIntensity: 0.2
        });

        const mountain1 = new THREE.Mesh(mountainGeometry, mountainMaterial);
        mountain1.position.set(-120, 60, -200);
        mountain1.castShadow = true;
        mountain1.receiveShadow = true;
        env.add(mountain1);

        const mountain2 = new THREE.Mesh(mountainGeometry, mountainMaterial);
        mountain2.scale.set(1.4, 1.3, 1.4);
        mountain2.position.set(150, 70, -220);
        mountain2.castShadow = true;
        mountain2.receiveShadow = true;
        env.add(mountain2);

        const mountain3 = new THREE.Mesh(mountainGeometry, mountainMaterial);
        mountain3.scale.set(1.1, 1.1, 1.1);
        mountain3.position.set(0, 40, -250);
        mountain3.castShadow = true;
        mountain3.receiveShadow = true;
        env.add(mountain3);
    }

    switchToLightEnvironment() {
        if (this.currentEnvironment === this.lightEnvironment) return;

        Logger.log('Switching to light environment');

        if (this.darkEnvironment) {
            this.scene.remove(this.darkEnvironment);
        }

        if (!this.lightEnvironment) {
            this.createLightEnvironment();
        }

        this.currentEnvironment = this.lightEnvironment;
    }

    switchToDarkEnvironment() {
        if (this.currentEnvironment === this.darkEnvironment) return;

        Logger.log('Switching to dark environment');

        if (this.lightEnvironment) {
            this.scene.remove(this.lightEnvironment);
        }

        if (!this.darkEnvironment) {
            this.createDarkEnvironment();
        }

        this.currentEnvironment = this.darkEnvironment;
    }

    dispose() {
        const disposeNode = (node) => {
            node.traverse(child => {
                if (child.geometry) child.geometry.dispose();
                if (child.material) {
                    if (Array.isArray(child.material)) {
                        child.material.forEach(m => m.dispose());
                    } else {
                        child.material.dispose();
                    }
                }
            });
        };

        if (this.darkEnvironment) disposeNode(this.darkEnvironment);
        if (this.lightEnvironment) disposeNode(this.lightEnvironment);
    }
}

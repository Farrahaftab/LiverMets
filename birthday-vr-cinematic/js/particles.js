class ParticleSystem {
    constructor(scene, camera, maxParticles = 5000) {
        this.scene = scene;
        this.camera = camera;
        this.maxParticles = maxParticles;
        this.particles = [];
        this.particlePool = [];

        this.initGeometry();
    }

    initGeometry() {
        this.geometry = new THREE.BufferGeometry();

        const positions = new Float32Array(this.maxParticles * 3);
        const velocities = new Float32Array(this.maxParticles * 3);
        const ages = new Float32Array(this.maxParticles);
        const lifetimes = new Float32Array(this.maxParticles);
        const sizes = new Float32Array(this.maxParticles);
        const colors = new Float32Array(this.maxParticles * 3);

        for (let i = 0; i < this.maxParticles; i++) {
            positions[i * 3] = 0;
            positions[i * 3 + 1] = 0;
            positions[i * 3 + 2] = 0;
            ages[i] = 0;
            lifetimes[i] = 1;
            sizes[i] = 5;
            colors[i * 3] = 1;
            colors[i * 3 + 1] = 1;
            colors[i * 3 + 2] = 1;
        }

        this.geometry.setAttribute('position', new THREE.BufferAttribute(positions, 3));
        this.geometry.setAttribute('velocity', new THREE.BufferAttribute(velocities, 3));
        this.geometry.setAttribute('age', new THREE.BufferAttribute(ages, 1));
        this.geometry.setAttribute('lifetime', new THREE.BufferAttribute(lifetimes, 1));
        this.geometry.setAttribute('size', new THREE.BufferAttribute(sizes, 1));
        this.geometry.setAttribute('color', new THREE.BufferAttribute(colors, 3));

        const material = new THREE.PointsMaterial({
            size: 2,
            sizeAttenuation: true,
            transparent: true,
            fog: false,
            onBeforeCompile: (shader) => {
                shader.vertexShader = `
                    attribute float age;
                    attribute float lifetime;
                    varying float vAlpha;
                    varying vec3 vColor;

                    void main() {
                        vAlpha = max(0.0, 1.0 - (age / lifetime));
                        vAlpha *= vAlpha;
                        vColor = color;

                        vec4 mvPosition = modelViewMatrix * vec4(position, 1.0);
                        gl_PointSize = size * (1.0 - age / lifetime) * (-mvPosition.z / 100.0);
                        gl_Position = projectionMatrix * mvPosition;
                    }
                ` + shader.vertexShader.split('void main')[0];

                shader.fragmentShader = `
                    varying float vAlpha;
                    varying vec3 vColor;

                    void main() {
                        float d = length(gl_PointCoord - vec2(0.5));
                        if (d > 0.5) discard;

                        float circle = 1.0 - (d * 2.0);
                        circle *= circle;
                        gl_FragColor = vec4(vColor, vAlpha * circle * 0.8);
                    }
                ` + shader.fragmentShader;
            }
        });

        this.mesh = new THREE.Points(this.geometry, material);
        this.scene.add(this.mesh);
    }

    emit(options) {
        const {
            position = new THREE.Vector3(0, 0, 0),
            velocity = new THREE.Vector3(0, 0, 0),
            color = new THREE.Color(1, 1, 1),
            lifetime = 2,
            count = 1,
            spread = 0.1,
            speedVariation = 0.1
        } = options;

        for (let i = 0; i < count; i++) {
            const particle = this.getParticle();

            const spreadVec = new THREE.Vector3(
                (Math.random() - 0.5) * spread,
                (Math.random() - 0.5) * spread,
                (Math.random() - 0.5) * spread
            );

            particle.position.copy(position).add(spreadVec);
            particle.velocity.copy(velocity).multiplyScalar(1 + (Math.random() - 0.5) * speedVariation);
            particle.age = 0;
            particle.lifetime = lifetime;
            particle.color.copy(color);
            particle.size = 5 + Math.random() * 3;

            this.particles.push(particle);
        }

        this.updateBuffers();
    }

    emitWave(options) {
        const {
            startPosition = new THREE.Vector3(0, 0, 0),
            waveDirection = new THREE.Vector3(0, 0, 1),
            radius = 5,
            particleCount = 50,
            lifetime = 3,
            speed = 2
        } = options;

        for (let i = 0; i < particleCount; i++) {
            const angle = (i / particleCount) * Math.PI * 2;
            const offsetX = Math.cos(angle) * radius;
            const offsetZ = Math.sin(angle) * radius;

            const velocity = waveDirection.clone().normalize().multiplyScalar(speed);
            velocity.x += Math.cos(angle) * speed * 0.3;
            velocity.z += Math.sin(angle) * speed * 0.3;

            this.emit({
                position: startPosition.clone().add(new THREE.Vector3(offsetX, 0, offsetZ)),
                velocity: velocity,
                color: new THREE.Color(1.0, 0.84, 0.0),
                lifetime: lifetime,
                count: 1
            });
        }
    }

    getParticle() {
        if (this.particlePool.length > 0) {
            return this.particlePool.pop();
        }

        return {
            position: new THREE.Vector3(),
            velocity: new THREE.Vector3(),
            age: 0,
            lifetime: 1,
            color: new THREE.Color(),
            size: 5
        };
    }

    update(deltaTime) {
        const gravity = new THREE.Vector3(0, -0.5, 0);

        for (let i = this.particles.length - 1; i >= 0; i--) {
            const p = this.particles[i];
            p.age += deltaTime;

            if (p.age > p.lifetime) {
                this.particlePool.push(p);
                this.particles.splice(i, 1);
            } else {
                p.velocity.add(gravity.clone().multiplyScalar(deltaTime));
                p.position.add(p.velocity.clone().multiplyScalar(deltaTime));
            }
        }

        this.updateBuffers();
    }

    updateBuffers() {
        const positions = this.geometry.attributes.position.array;
        const velocities = this.geometry.attributes.velocity.array;
        const ages = this.geometry.attributes.age.array;
        const lifetimes = this.geometry.attributes.lifetime.array;
        const sizes = this.geometry.attributes.size.array;
        const colors = this.geometry.attributes.color.array;

        let updateRange = Math.min(this.particles.length, this.maxParticles);

        for (let i = 0; i < updateRange; i++) {
            const p = this.particles[i];

            positions[i * 3] = p.position.x;
            positions[i * 3 + 1] = p.position.y;
            positions[i * 3 + 2] = p.position.z;

            velocities[i * 3] = p.velocity.x;
            velocities[i * 3 + 1] = p.velocity.y;
            velocities[i * 3 + 2] = p.velocity.z;

            ages[i] = p.age;
            lifetimes[i] = p.lifetime;
            sizes[i] = p.size;

            colors[i * 3] = p.color.r;
            colors[i * 3 + 1] = p.color.g;
            colors[i * 3 + 2] = p.color.b;
        }

        this.geometry.attributes.position.needsUpdate = true;
        this.geometry.attributes.age.needsUpdate = true;
        this.geometry.attributes.lifetime.needsUpdate = true;
        this.geometry.attributes.size.needsUpdate = true;
        this.geometry.attributes.color.needsUpdate = true;

        this.geometry.setDrawRange(0, Math.min(this.particles.length, this.maxParticles));
    }

    clear() {
        this.particles = [];
        this.particlePool = [];
        this.updateBuffers();
    }

    dispose() {
        this.geometry.dispose();
        this.mesh.material.dispose();
        this.scene.remove(this.mesh);
    }
}

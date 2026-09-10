// Main initialization - with error handling to keep start screen visible

let experience = null;

window.addEventListener('DOMContentLoaded', () => {
    try {
        Logger.log('DOM Content Loaded');

        const canvas = document.getElementById('experienceCanvas');
        if (!canvas) {
            throw new Error('Canvas element not found');
        }

        Logger.log('Creating Experience...');
        experience = new Experience(canvas);
        Logger.log('Experience created successfully');

        // Setup start button
        const startButton = document.getElementById('startButton');
        if (startButton) {
            startButton.addEventListener('click', () => {
                try {
                    if (experience) {
                        Logger.log('START button clicked');
                        experience.startExperience();
                    }
                } catch (e) {
                    Logger.error('Error starting experience: ' + e.message);
                    showErrorMessage('Failed to start experience: ' + e.message);
                }
            });
            Logger.log('START button event listener attached');
        }
    } catch (error) {
        Logger.error('Initialization error: ' + error.message);
        showErrorMessage('Failed to initialize: ' + error.message);
    }
});

// Handle fullscreen on mobile
window.addEventListener('orientationchange', () => {
    try {
        if (experience && experience.renderer) {
            setTimeout(() => {
                experience.onWindowResize();
            }, 100);
        }
    } catch (e) {
        Logger.error('Orientation change error: ' + e.message);
    }
});

// Prevent context menu
document.addEventListener('contextmenu', (e) => {
    e.preventDefault();
});

// Handle visibility changes
document.addEventListener('visibilitychange', () => {
    try {
        if (document.hidden) {
            if (experience && experience.timeline) {
                experience.timeline.pause();
            }
        } else {
            if (experience && experience.timeline && !experience.isVR) {
                experience.timeline.play();
            }
        }
    } catch (e) {
        Logger.error('Visibility change error: ' + e.message);
    }
});

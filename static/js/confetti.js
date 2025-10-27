/**
 * Confetti Animation for Order Success Page
 * Creates a celebratory confetti effect with falling particles
 * Uses Canvas API with requestAnimationFrame for smooth performance
 */

(function() {
  'use strict';

  // Check if animation should play (prevent replay on refresh)
  const STORAGE_KEY = 'cartmax_confetti_shown';

  class ConfettiAnimation {
    constructor() {
      this.canvas = null;
      this.ctx = null;
      this.particles = [];
      this.animationId = null;
      this.isRunning = false;
      this.startTime = 0;
      this.duration = 4000; // 4 seconds in milliseconds
      this.particleCount = 80;

      // CartMax Brand Colors
      this.colors = [
        '#2563eb', // Primary Blue
        '#10b981', // Emerald Green
        '#f59e0b', // Amber/Orange
        '#8b5cf6', // Purple
        '#06b6d4', // Cyan
        '#ec4899', // Pink
        '#f97316', // Orange
        '#14b8a6', // Teal
      ];
    }

    /**
     * Initialize the confetti animation
     */
    init() {
      // Check if already shown in this session
      const sessionData = sessionStorage.getItem(STORAGE_KEY);
      if (sessionData === 'true') {
        return;
      }

      this.createCanvas();
      this.generateParticles();
      this.animate();

      // Mark as shown in this session
      sessionStorage.setItem(STORAGE_KEY, 'true');
    }

    /**
     * Create canvas element and add to DOM
     */
    createCanvas() {
      this.canvas = document.createElement('canvas');
      this.canvas.id = 'confetti-canvas';
      this.canvas.width = window.innerWidth;
      this.canvas.height = window.innerHeight;

      // Canvas styling
      Object.assign(this.canvas.style, {
        position: 'fixed',
        top: '0',
        left: '0',
        pointerEvents: 'none',
        zIndex: '9999',
      });

      document.body.appendChild(this.canvas);
      this.ctx = this.canvas.getContext('2d');

      // Handle window resize
      window.addEventListener('resize', () => this.handleResize());
    }

    /**
     * Handle window resize
     */
    handleResize() {
      if (this.canvas) {
        this.canvas.width = window.innerWidth;
        this.canvas.height = window.innerHeight;
      }
    }

    /**
     * Generate confetti particles
     */
    generateParticles() {
      for (let i = 0; i < this.particleCount; i++) {
        this.particles.push({
          x: Math.random() * this.canvas.width,
          y: -10,
          vx: (Math.random() - 0.5) * 8, // Horizontal velocity
          vy: Math.random() * 3 + 4, // Vertical velocity
          rotation: Math.random() * Math.PI * 2,
          rotationVelocity: (Math.random() - 0.5) * 0.2,
          size: Math.random() * 8 + 4,
          color: this.colors[Math.floor(Math.random() * this.colors.length)],
          shape: Math.floor(Math.random() * 3), // 0: square, 1: circle, 2: ribbon
          opacity: 1,
        });
      }
    }

    /**
     * Update particle physics
     */
    updateParticles(progress) {
      this.particles.forEach((particle) => {
        // Apply gravity
        particle.vy += 0.15;

        // Apply wind/drift
        particle.vx += (Math.random() - 0.5) * 0.2;
        particle.vx *= 0.99; // Air resistance

        // Update position
        particle.x += particle.vx;
        particle.y += particle.vy;

        // Update rotation
        particle.rotation += particle.rotationVelocity;

        // Fade out in last 20% of animation
        if (progress > 0.8) {
          particle.opacity = 1 - (progress - 0.8) * 5;
        }
      });
    }

    /**
     * Draw particles on canvas
     */
    drawParticles() {
      this.particles.forEach((particle) => {
        this.ctx.save();
        this.ctx.globalAlpha = particle.opacity;

        this.ctx.translate(particle.x, particle.y);
        this.ctx.rotate(particle.rotation);

        this.ctx.fillStyle = particle.color;

        switch (particle.shape) {
          case 0: // Square
            this.ctx.fillRect(
              -particle.size / 2,
              -particle.size / 2,
              particle.size,
              particle.size
            );
            break;
          case 1: // Circle
            this.ctx.beginPath();
            this.ctx.arc(0, 0, particle.size / 2, 0, Math.PI * 2);
            this.ctx.fill();
            break;
          case 2: // Ribbon/Rectangle
            this.ctx.fillRect(
              -particle.size / 2,
              -(particle.size / 4),
              particle.size,
              particle.size / 2
            );
            break;
        }

        this.ctx.restore();
      });
    }

    /**
     * Animation loop
     */
    animate() {
      if (!this.isRunning) {
        this.isRunning = true;
        this.startTime = Date.now();
      }

      const currentTime = Date.now();
      const elapsed = currentTime - this.startTime;
      const progress = Math.min(elapsed / this.duration, 1);

      // Clear canvas
      this.ctx.clearRect(0, 0, this.canvas.width, this.canvas.height);

      // Update and draw particles
      this.updateParticles(progress);
      this.drawParticles();

      // Continue animation if not complete
      if (progress < 1) {
        this.animationId = requestAnimationFrame(() => this.animate());
      } else {
        this.cleanup();
      }
    }

    /**
     * Cleanup animation and remove canvas
     */
    cleanup() {
      this.isRunning = false;
      if (this.animationId) {
        cancelAnimationFrame(this.animationId);
      }
      if (this.canvas && this.canvas.parentNode) {
        this.canvas.parentNode.removeChild(this.canvas);
      }
      window.removeEventListener('resize', () => this.handleResize());
    }
  }

  /**
   * Initialize confetti when DOM is ready
   */
  function initConfetti() {
    // Only init on order success page
    const confettiTrigger = document.querySelector('[data-confetti-trigger]');
    if (confettiTrigger || document.querySelector('h1:contains("Order Confirmed")')) {
      const confetti = new ConfettiAnimation();
      confetti.init();
    }
  }

  // Wait for DOM to be ready
  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initConfetti);
  } else {
    initConfetti();
  }
})();

<template>
  <div class="animated-gradient" />
</template>

<style scoped>
.animated-gradient {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 0;
  background:
    radial-gradient(
      ellipse 80% 60% at 30% 20%,
      rgba(79, 140, 255, 0.08) 0%,
      transparent 60%
    ),
    radial-gradient(
      ellipse 60% 80% at 70% 70%,
      rgba(124, 92, 240, 0.06) 0%,
      transparent 60%
    ),
    radial-gradient(
      ellipse 50% 50% at 60% 30%,
      rgba(79, 140, 255, 0.04) 0%,
      transparent 50%
    );
  animation: gradient-shift-1 18s ease-in-out infinite,
             gradient-shift-2 23s ease-in-out infinite;
}
</style>

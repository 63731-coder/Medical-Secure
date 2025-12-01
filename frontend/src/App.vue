<script setup>
import { RouterLink, RouterView } from 'vue-router';
</script>

<template>
  <header>
    <nav>
      <RouterLink to="/">Accueil</RouterLink> |
      <RouterLink to="/login">Se connecter</RouterLink> | 
      <RouterLink to="/about">A propos</RouterLink>
    </nav>
  </header>

  <main>
    <RouterView />
  </main>
</template>

<style scoped>
header {
  padding: 20px;
  background-color: #f0f0f0;
  margin-bottom: 20px;
}
</style>
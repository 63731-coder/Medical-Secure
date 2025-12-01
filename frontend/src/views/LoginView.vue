<script>
import axios from "axios";
import { deriveKeyFromPassword } from '../utils/crypto';

export default {
    name: "LoginPage",

    data() {
        return {
            username: "",
            password: "",
            errorMessage: ""
        };
    },

    methods: {
        async handleLogin() {
            try {
                const response = await axios.post("http://127.0.0.1:8000/api/token/", {
                    username: this.username,
                    password: this.password
                });

                console.log("Connexion réussie :", response.data);

                localStorage.setItem("accessToken", response.data.access);
                localStorage.setItem("refreshToken", response.data.refresh);
                deriveKeyFromPassword(this.password);

                this.$router.push("/");
            } catch (error) {
                console.error("Erreur de connexion", error);
                this.errorMessage = "Nom d'utilisateur ou mot de passe incorrect.";
            }
        }
    }
};
</script>

<template>
    <div class="login-container">
        <h2>Connexion</h2>
        <form @submit.prevent="handleLogin">
            <div class="form-group">
                <label>Nom d'utilisateur :</label>
                <input type="text" v-model="username" required />
            </div>

            <div class="form-group">
                <label>Mot de passe :</label>
                <input type="password" v-model="password" required />
            </div>

            <p v-if="errorMessage" class="error">{{ errorMessage }}</p>

            <button type="submit">Se connecter</button>
        </form>
    </div>
</template>

<style scoped>
.login-container {
    max-width: 300px;
    margin: 50px auto;
    padding: 20px;
    border: 1px solid #ccc;
    border-radius: 8px;
}

.form-group {
    margin-bottom: 15px;
}

label {
    display: block;
    margin-bottom: 5px;
}

input {
    width: 100%;
    padding: 8px;
    box-sizing: border-box;
}

button {
    width: 100%;
    padding: 10px;
    background-color: #4CAF50;
    color: white;
    border: none;
    cursor: pointer;
}

button:hover {
    background-color: #45a049;
}

.error {
    color: red;
    font-size: 0.9em;
}
</style>

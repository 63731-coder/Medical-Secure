import CryptoJS from 'crypto-js';

// Cette clé servira à chiffrer les données.
// Dans un vrai projet "Zero Trust", elle est dérivée du mot de passe de l'utilisateur
// et n'est JAMAIS envoyée au serveur.
let SECRET_KEY = null;

// Fonction pour générer la clé secrète à partir du mot de passe (lors du Login)
export const deriveKeyFromPassword = (password, salt = 'mon_sel_fixe_pour_le_projet') => {
    // On utilise PBKDF2 qui est standard pour transformer un mot de passe en clé robuste
    const key = CryptoJS.PBKDF2(password, salt, {
        keySize: 256 / 32,
        iterations: 1000
    });
    SECRET_KEY = key.toString();
    console.log("Clé de chiffrement générée (en mémoire uniquement).");
};

// Fonction pour chiffrer une donnée (ex: le nom du patient)
export const encryptData = (data) => {
    if (!SECRET_KEY) {
        console.error("Aucune clé de chiffrement définie ! L'utilisateur est-il connecté ?");
        return null;
    }
    return CryptoJS.AES.encrypt(data, SECRET_KEY).toString();
};

// Fonction pour déchiffrer une donnée (ex: pour afficher le dossier médical)
export const decryptData = (cipherText) => {
    if (!SECRET_KEY) return null;
    try {
        const bytes = CryptoJS.AES.decrypt(cipherText, SECRET_KEY);
        return bytes.toString(CryptoJS.enc.Utf8);
    } catch (e) {
        console.error("Erreur de déchiffrement", e);
        return "Donnée illisible";
    }
};
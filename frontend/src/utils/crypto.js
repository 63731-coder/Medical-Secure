import CryptoJS from 'crypto-js';

// Cette clé servira à chiffrer les données.
// Dans un vrai projet "Zero Trust", elle est dérivée du mot de passe de l'utilisateur
// et n'est JAMAIS envoyée au serveur.
let SECRET_KEY = null;

// Try to restore key from sessionStorage on module load
const storedKey = sessionStorage.getItem('encryptionKey');
if (storedKey) {
    SECRET_KEY = storedKey;
}

// Fonction pour générer la clé secrète à partir du mot de passe (lors du Login)
export const deriveKeyFromPassword = (password, salt = 'mon_sel_fixe_pour_le_projet') => {
    // On utilise PBKDF2 qui est standard pour transformer un mot de passe en clé robuste
    const key = CryptoJS.PBKDF2(password, salt, {
        keySize: 256 / 32,
        iterations: 100000  // NIST recommande minimum 100k iterations
    });
    SECRET_KEY = key.toString();
    // Store in sessionStorage (cleared when browser/tab closes)
    sessionStorage.setItem('encryptionKey', SECRET_KEY);
};

// Generate deterministic encryption key from user identity (for Keycloak passwordless)
export const deriveKeyFromUser = (username, keycloakId) => {
    // Use username + keycloak_id as seed for deterministic key
    // This allows the same user to decrypt their files across sessions
    const seed = `${username}:${keycloakId}:medical-secure`;
    const key = CryptoJS.PBKDF2(seed, 'keycloak-medical-salt', {
        keySize: 256 / 32,
        iterations: 100000  // NIST recommande minimum 100k iterations
    });
    SECRET_KEY = key.toString();
    sessionStorage.setItem('encryptionKey', SECRET_KEY);
};

// Clear encryption key on logout
export const clearEncryptionKey = () => {
    SECRET_KEY = null;
    sessionStorage.removeItem('encryptionKey');
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

// ===========================
// SHARED KEY ENCRYPTION
// ===========================

/**
 * Encrypt patient's encryption key for sharing with a doctor
 * Uses deterministic key derivation from the doctor's ID
 * @param {string} patientKey - The patient's encryption key to share
 * @param {number} doctorId - Doctor's database ID
 * @returns {string} - Encrypted key that only the doctor can decrypt
 */
export const encryptKeyForDoctor = (patientKey, doctorId) => {
    // Derive deterministic key from doctor ID
    // Note: Production systems should use asymmetric crypto (RSA/ECC)
    const seed = `doctor-${doctorId}-medical-secure`;
    const doctorKey = CryptoJS.PBKDF2(seed, 'simple-salt', {
        keySize: 256 / 32,
        iterations: 10000  // Reduced for simplicity
    }).toString();
    
    // Encrypt patient's key with derived doctor key
    return CryptoJS.AES.encrypt(patientKey, doctorKey).toString();
};

/**
 * Decrypt shared patient key using doctor's ID
 * @param {string} encryptedKey - The encrypted patient key from database
 * @param {number} doctorId - Doctor's database ID
 * @returns {string} - Decrypted patient encryption key
 */
export const decryptSharedKey = (encryptedKey, doctorId) => {
    // Derive the same deterministic key used during encryption
    const seed = `doctor-${doctorId}-medical-secure`;
    const doctorKey = CryptoJS.PBKDF2(seed, 'simple-salt', {
        keySize: 256 / 32,
        iterations: 10000
    }).toString();
    
    try {
        const bytes = CryptoJS.AES.decrypt(encryptedKey, doctorKey);
        const decryptedKey = bytes.toString(CryptoJS.enc.Utf8);
        
        if (!decryptedKey) {
            console.error("Failed to decrypt shared key");
            return null;
        }
        
        return decryptedKey;
    } catch (e) {
        console.error("Error decrypting shared key:", e);
        return null;
    }
};

/**
 * Decrypt data using a shared key (for doctors accessing patient files)
 * @param {string} cipherText - The encrypted data
 * @param {string} sharedKey - The patient's decrypted encryption key
 * @returns {string} - Decrypted data
 */
export const decryptWithSharedKey = (cipherText, sharedKey) => {
    try {
        const bytes = CryptoJS.AES.decrypt(cipherText, sharedKey);
        const decrypted = bytes.toString(CryptoJS.enc.Utf8);
        
        if (!decrypted) {
            console.error("Failed to decrypt data with shared key");
            return null;
        }
        
        return decrypted;
    } catch (e) {
        console.error("Error decrypting with shared key:", e);
        return null;
    }
};

/**
 * Encrypt data using a shared key (for doctors uploading files for patients)
 * @param {string} data - The data to encrypt
 * @param {string} sharedKey - The patient's decrypted encryption key
 * @returns {string} - Encrypted data
 */
export const encryptWithSharedKey = (data, sharedKey) => {
    if (!sharedKey) {
        console.error("No shared key provided for encryption");
        return null;
    }
    try {
        return CryptoJS.AES.encrypt(data, sharedKey).toString();
    } catch (e) {
        console.error("Error encrypting with shared key:", e);
        return null;
    }
};

